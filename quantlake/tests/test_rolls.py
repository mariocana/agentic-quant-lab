"""Roll calendar, continuous series and @ES check — synthetic data only."""
import importlib.util
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import polars as pl
import pytest
from deltalake import DeltaTable

import quantlake.gold.ingest as gold
import quantlake.reference.rolls as rolls_mod
from helpers import utc
from quantlake.gold.continuous import (
    check_no_straddle, compare_with_reference, continuous_1m, roll_differences, write_continuous,
)
from quantlake.reference.rolls import (
    SCHEMA, Contract, measure_gaps, parse_contract, read_rolls, roll_calendar, write_rolls,
)
from quantlake.storage import read_symbol

CHI = ZoneInfo("America/Chicago")
Z25_ROLL = utc(2025, 12, 10, 23, 0)   # Wed 17:00 CST, opens Thu 2025-12-11 (expiry 12-19 - 8)
H26_ROLL = utc(2026, 3, 11, 22, 0)    # Wed 17:00 CDT, opens Thu 2026-03-12


def chi(*a) -> datetime:
    return datetime(*a, tzinfo=CHI).astimezone(timezone.utc)


def _bars(code: str, start: datetime, n: int, close) -> pl.DataFrame:
    ts = [start + timedelta(minutes=i) for i in range(n)]
    closes = [float(close(i)) for i in range(n)]
    return pl.DataFrame({
        "symbol": [code] * n,
        "timestamp": pl.Series(ts, dtype=pl.Datetime("us", "UTC")),
        "open": closes, "high": [c + 0.25 for c in closes], "low": [c - 0.25 for c in closes],
        "close": closes, "volume": [10.0] * n,
    })


# ── calendar ───────────────────────────────────────────────────────────────

def test_parse_contract():
    assert parse_contract("ESZ25") == Contract(2025, 12, "ES")
    assert parse_contract("NQH26").code == "NQH26"
    assert parse_contract("ESH20").year == 2020
    for bad in ("ES", "ESZ2025", "esz25", "@ES", "ES_Z25"):
        with pytest.raises(ValueError):
            parse_contract(bad)


@pytest.mark.parametrize("code, expiry, roll", [
    ("ESZ25", date(2025, 12, 19), Z25_ROLL),
    ("ESH26", date(2026, 3, 20), H26_ROLL),
    ("ESU25", date(2025, 9, 19), utc(2025, 9, 10, 22, 0)),
    ("ESH20", date(2020, 3, 20), utc(2020, 3, 11, 22, 0)),
])
def test_expiry_and_roll(code, expiry, roll):
    c = parse_contract(code)
    assert c.expiry == expiry and c.expiry.weekday() == 4
    assert c.roll_day == expiry - timedelta(days=8) and c.roll_day.weekday() == 3  # Thursday
    assert c.roll_ts == roll
    local = c.roll_ts.astimezone(CHI)
    assert local.hour == 17 and local.weekday() == 2 and local.date() == c.roll_day - timedelta(days=1)


def test_roll_at_end_of_roll_day_when_constant_is_off(monkeypatch):
    monkeypatch.setattr(rolls_mod, "ROLL_AT_SESSION_OPEN", False)
    assert parse_contract("ESZ25").roll_ts == utc(2025, 12, 11, 23, 0)  # Thu 17:00 CST


def test_roll_calendar_covers_missing_contracts_and_roots():
    cal = roll_calendar(["ESU25", "ESH26", "NQZ25", "NQH26"])
    assert dict(cal.schema) == SCHEMA
    assert cal.select("symbol", "from_contract", "to_contract").rows() == [
        ("ES", "ESU25", "ESZ25"), ("ES", "ESZ25", "ESH26"), ("NQ", "NQZ25", "NQH26"),
    ]
    assert cal["gap_points"].null_count() == 3
    with pytest.raises(ValueError):
        roll_calendar(["ESF26"])


def test_measure_gaps_uses_last_common_minute_before_roll():
    z = _bars("ESZ25", Z25_ROLL - timedelta(minutes=70), 70, lambda i: 6000 + i * 0.25)   # stops at roll - 1 min
    h = _bars("ESH26", Z25_ROLL - timedelta(minutes=70), 130, lambda i: 6050 + i * 0.25)  # trades after roll too
    h = h.filter(pl.col("timestamp") != Z25_ROLL - timedelta(minutes=1))  # last minute only in Z25
    cal = measure_gaps(roll_calendar(["ESZ25", "ESH26"]), pl.concat([z, h]))
    assert cal["gap_points"].to_list() == [50.0]

    only_z = measure_gaps(roll_calendar(["ESZ25", "ESH26"]), z)
    assert only_z["gap_points"].to_list() == [None]


def test_write_and_read_rolls(tmp_path, monkeypatch):
    monkeypatch.setattr(rolls_mod, "REFERENCE_ROOT", tmp_path / "reference")
    cal = roll_calendar(["ESZ25", "ESH26"]).with_columns(pl.lit(50.0).alias("gap_points"))
    write_rolls(cal)
    write_rolls(cal)  # overwrite, not append
    assert read_rolls().equals(cal)
    assert dict(pl.from_arrow(DeltaTable(rolls_mod.table_path()).to_pyarrow_table()).schema) == SCHEMA
    assert DeltaTable(rolls_mod.table_path()).metadata().partition_columns == []


# ── continuous series ──────────────────────────────────────────────────────

def _two_contracts():
    start = Z25_ROLL - timedelta(hours=2)
    z = _bars("ESZ25", start, 240, lambda i: 6000 + i * 0.25)
    h = _bars("ESH26", start, 240, lambda i: 6050 + i * 0.25)
    return pl.concat([z, h])


def test_continuous_switches_contract_at_roll_and_offsets():
    bars = _two_contracts()
    cal = measure_gaps(roll_calendar(["ESZ25", "ESH26"]), bars)
    s = continuous_1m("ES", bars, cal)
    assert s["timestamp"].is_unique().all()
    before, after = s.filter(pl.col("timestamp") < Z25_ROLL), s.filter(pl.col("timestamp") >= Z25_ROLL)
    assert before["contract"].unique().to_list() == ["ESZ25"] and after["contract"].unique().to_list() == ["ESH26"]
    assert before["adj_offset"].unique().to_list() == [50.0] and after["adj_offset"].unique().to_list() == [0.0]
    assert s["symbol"].unique().to_list() == ["ES"]
    # back-adjusted series is continuous across the roll
    adj = s.with_columns((pl.col("close") + pl.col("adj_offset")).alias("adj"))
    last_z, first_h = adj.filter(pl.col("timestamp") < Z25_ROLL)["adj"][-1], adj.filter(pl.col("timestamp") >= Z25_ROLL)["adj"][0]
    assert first_h - last_z == 0.25  # one normal minute step, no 50-point jump


def test_unknown_gap_makes_older_offsets_null():
    bars = _two_contracts()
    s = continuous_1m("ES", bars, roll_calendar(["ESZ25", "ESH26"]))
    assert s.filter(pl.col("contract") == "ESZ25")["adj_offset"].null_count() > 0
    assert s.filter(pl.col("contract") == "ESH26")["adj_offset"].unique().to_list() == [0.0]


def test_straddle_check():
    bars = _two_contracts()
    s = continuous_1m("ES", bars, measure_gaps(roll_calendar(["ESZ25", "ESH26"]), bars))
    for tf in ("1m", "15m", "1h", "4h_cme", "1d_cme"):
        check_no_straddle(s, tf)
    with pytest.raises(ValueError, match="mix two contracts"):
        check_no_straddle(s, "4h")  # 20:00-24:00 UTC holds 17:00 CT (23:00 UTC)


def test_write_continuous_gold(lake, freeze_now):
    freeze_now(gold, utc(2026, 1, 1))
    bars = _two_contracts()
    s = continuous_1m("ES", bars, measure_gaps(roll_calendar(["ESZ25", "ESH26"]), bars))
    written = write_continuous(s, ["1h", "1d_cme"])
    assert written == {"1h": 4, "1d_cme": 2}
    g = read_symbol(str(lake["GOLD_ROOT"] / "multicharts_continuous" / "1d_cme"), "ES").sort("timestamp")
    assert g["timestamp"].to_list() == [chi(2025, 12, 9, 17), Z25_ROLL]
    assert g["contract"].to_list() == ["ESZ25", "ESH26"]
    assert g["adj_offset"].to_list() == [50.0, 0.0]
    assert g.schema["timestamp"] == pl.Datetime("us", "UTC") and g.schema["close"] == pl.Float64


# ── check vs @ES ───────────────────────────────────────────────────────────

def test_compare_with_reference_finds_a_later_tradestation_roll():
    # sessions opening Tue (ours Z25), Wed = our roll (ours H26), Sun → Mon (ours H26)
    opens = [chi(2025, 12, 9, 17), chi(2025, 12, 10, 17), chi(2025, 12, 14, 17)]
    z = pl.concat([_bars("ESZ25", o, 60, lambda i: 6000 + i * 0.25) for o in opens])
    h = pl.concat([_bars("ESH26", o, 60, lambda i: 6050 + i * 0.25 + (i % 3) * 0.25) for o in opens])
    bars = pl.concat([z, h])
    cal = roll_calendar(["ESZ25", "ESH26"])

    # TradeStation @ES: on Z25 for the first two sessions (back-adjusted +40), H26 from Sunday
    ts_on = {opens[0]: z, opens[1]: z, opens[2]: h}
    ref = pl.concat([
        src.filter((pl.col("timestamp") >= o) & (pl.col("timestamp") < o + timedelta(hours=1)))
        .with_columns(pl.lit("ES").alias("symbol"), pl.col("close") + (40.0 if src is z else 0.0))
        for o, src in ts_on.items()
    ])

    cmp = compare_with_reference(bars, ref, "ES", cal)
    assert cmp.select("session", "ours", "theirs").rows() == [
        (opens[0], "ESZ25", "ESZ25"), (opens[1], "ESH26", "ESZ25"), (opens[2], "ESH26", "ESH26"),
    ]
    assert cmp["offset"].to_list() == [40.0, 40.0, 0.0]

    diff = roll_differences(cmp, cal, "ES")
    assert diff.row(0, named=True)["ts_roll"] == opens[2]
    assert diff.row(0, named=True)["days_late"] == 4.0


# ── historical/multicharts_rolls.py on fake ExportBars CSVs ────────────────

def _export_csv(path: Path, start: datetime, n: int, close) -> None:
    lines = ["date,time,open,high,low,close,volume,ticks,upticks,downticks"]
    for i in range(n):
        c = (start + timedelta(minutes=i + 1)).astimezone(CHI)  # ExportBars writes the bar close, chart time
        p = close(i)
        lines.append(f"{c:%Y%m%d},{c:%H%M},{p},{p + 0.25},{p - 0.25},{p},10,5,6,4")
    path.write_text("\n".join(lines) + "\n")


def test_multicharts_rolls_script(lake, freeze_now, monkeypatch, tmp_path, capsys):
    freeze_now(gold, utc(2026, 1, 1))
    monkeypatch.setattr(rolls_mod, "REFERENCE_ROOT", tmp_path / "reference")
    folder = tmp_path / "multicharts"
    folder.mkdir()
    start = Z25_ROLL - timedelta(hours=2)
    _export_csv(folder / "ESZ25_1min.csv", start, 240, lambda i: 6000 + i * 0.25)
    _export_csv(folder / "ESH26_1min.csv", start, 240, lambda i: 6050 + i * 0.25)
    (folder / "ES_1min.csv").write_text("not a contract\n")  # the @ES export is ignored

    path = Path(__file__).parents[1] / "applications" / "historical" / "multicharts_rolls.py"
    spec = importlib.util.spec_from_file_location("multicharts_rolls", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "SILVER_ROOT", lake["SILVER_ROOT"])

    assert mod.ingest_contracts(folder) == ["ESH26", "ESZ25"]
    bars = mod.load_contract_bars()
    rolls = mod.build(bars)
    assert rolls["gap_points"].to_list() == [50.0]
    assert read_rolls().equals(rolls)
    g = read_symbol(str(lake["GOLD_ROOT"] / "multicharts_continuous" / "1h"), "ES")
    assert sorted(g["contract"].unique().to_list()) == ["ESH26", "ESZ25"]
    mod.check(bars, rolls)  # no @ES silver here: must not fail
    assert "gold/multicharts_continuous" in capsys.readouterr().out
