import importlib.util
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import polars as pl

import quantlake.gold.ingest as gold
from helpers import utc
from quantlake.silver.gaps import early_fridays, find_gaps, recurring_gaps, summarize
from quantlake.storage import read_symbol

CHI = ZoneInfo("America/Chicago")


def chi(*a) -> datetime:
    return datetime(*a, tzinfo=CHI).astimezone(timezone.utc)


def _bars(minutes: list[datetime], volume=lambda t: 10, ticks=lambda t: 5, close=lambda t: 1.0) -> pl.DataFrame:
    return pl.DataFrame({
        "timestamp": pl.Series(minutes, dtype=pl.Datetime("us", "UTC")),
        "open": [close(t) for t in minutes], "close": [close(t) for t in minutes],
        "volume": [float(volume(t)) for t in minutes], "ticks": [float(ticks(t)) for t in minutes],
    })


# ── single holes ───────────────────────────────────────────────────────────

def test_overnight_no_trade_gap_vs_rth_lost_bar():
    night = [chi(2016, 3, 2, 1, 0) + timedelta(minutes=i) for i in range(60)]
    day = [chi(2016, 3, 2, 10, 0) + timedelta(minutes=i) for i in range(60)]
    drop = {chi(2016, 3, 2, 1, 30), chi(2016, 3, 2, 1, 31), chi(2016, 3, 2, 10, 20)}
    minutes = [t for t in night + day if t not in drop]
    thin = {chi(2016, 3, 2, 1, 29), chi(2016, 3, 2, 1, 32)}
    df = _bars(
        minutes,
        volume=lambda t: 1 if t in thin else (20 if t.astimezone(CHI).hour < 5 else 500),
        ticks=lambda t: 1 if t in thin else 10,
        close=lambda t: 2000.0 if t.astimezone(CHI).hour < 5 else 2000.0 + (t.minute >= 21) * 2.0,
    )
    gaps = find_gaps(df).sort("before")
    assert gaps["missing"].to_list() == [2, 1]
    night_gap, day_gap = gaps.row(0, named=True), gaps.row(1, named=True)
    assert not night_gap["rth"] and night_gap["jump_ticks"] == 0 and night_gap["rel_vol_before"] < 0.1
    assert day_gap["rth"] and day_gap["jump_ticks"] == 8.0 and day_gap["hour_ct"] == 10

    s = summarize(gaps)
    assert s["by_year"].row(0, named=True)["missing_min"] == 3
    assert s["rth_with_jumps"].height == 1


def test_daily_halt_and_long_gaps_are_not_counted():
    minutes = [chi(2016, 3, 2, 15, 55), chi(2016, 3, 2, 15, 56), chi(2016, 3, 2, 15, 58), chi(2016, 3, 2, 15, 59),
               chi(2016, 3, 2, 17, 0), chi(2016, 3, 2, 17, 1)]
    assert find_gaps(_bars(minutes))["missing"].to_list() == [1]  # 15:57; the 60-min halt is excluded


# ── session-template rules ─────────────────────────────────────────────────

def _month(year: int, month: int, cut_1515: bool, friday_end: time, scatter: bool = False) -> pl.DataFrame:
    """Day sessions 08:00-15:59 CT on weekdays (enough to exercise the rules)."""
    minutes = []
    d = date(year, month, 1)
    while d.month == month:
        if d.weekday() < 5:
            for i in range(8 * 60):
                t = datetime.combine(d, time(8, 0), tzinfo=CHI) + timedelta(minutes=i)
                lt = t.timetz()
                if d.weekday() == 4 and lt.replace(tzinfo=None) > friday_end:
                    continue
                if cut_1515 and d.weekday() < 4 and time(15, 15) <= lt.replace(tzinfo=None) < time(15, 30):
                    continue
                if scatter and t.minute == (d.day * 7) % 60 and t.hour == 3 + d.day % 5 + 6:
                    continue  # one hole per day, never at the same time
                minutes.append(t.astimezone(timezone.utc))
        d += timedelta(days=1)
    return _bars(minutes)


def test_recurring_window_and_early_fridays_are_flagged():
    bars = _month(2021, 7, cut_1515=True, friday_end=time(15, 14))
    rec = recurring_gaps(bars)
    assert rec.select("month", "window_start_ct", "window_end_ct").rows() == [("2021-07", "15:15", "15:29")]
    row = rec.row(0, named=True)
    assert row["days_missing"] == 17 and row["trading_days"] == 22  # Mon-Thu of July 2021
    fri = early_fridays(bars)
    assert fri.rows() == [("2021-07", 5, 5, 1.0, "15:14")]


def test_correct_template_and_scattered_holes_pass():
    bars = _month(2021, 7, cut_1515=False, friday_end=time(15, 59), scatter=True)
    assert find_gaps(bars).height > 0  # there are holes...
    assert recurring_gaps(bars).is_empty()  # ...but never the same window
    assert early_fridays(bars).is_empty()


# ── multicharts.py: --full vs --replace ────────────────────────────────────

def _load_multicharts():
    path = Path(__file__).parents[1] / "applications" / "historical" / "multicharts.py"
    spec = importlib.util.spec_from_file_location("multicharts_script", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _export(path: Path, minutes: list[datetime], price) -> None:
    lines = ["date,time,open,high,low,close,volume,ticks,upticks,downticks"]
    for t in minutes:
        c = (t + timedelta(minutes=1)).astimezone(CHI)
        p = price(t)
        lines.append(f"{c:%Y%m%d},{c:%H%M},{p},{p + 0.25},{p - 0.25},{p},10,5,6,4")
    path.write_text("\n".join(lines) + "\n")


def test_reexport_needs_replace(lake, freeze_now, monkeypatch, tmp_path):
    import quantlake.storage as storage
    freeze_now(gold, utc(2026, 1, 1))
    folder = tmp_path / "multicharts"
    folder.mkdir()
    mod = _load_multicharts()
    for name in ("BRONZE_ROOT", "SILVER_ROOT", "GOLD_ROOT"):
        monkeypatch.setattr(mod, name, lake[name])
    sys.argv = ["multicharts.py"]

    day1 = [chi(2025, 6, 2, 14, 0) + timedelta(minutes=i) for i in range(120)]   # Mon 14:00-15:59
    day2 = [chi(2025, 6, 3, 14, 0) + timedelta(minutes=i) for i in range(120)]   # Tue
    hole = lambda t: time(15, 15) <= t.astimezone(CHI).time() < time(15, 30)  # noqa: E731
    _export(folder / "ES_1min.csv", [t for t in day1 + day2 if not hole(t)], lambda t: 5000.0)
    mod.main([], folder=folder)
    gold.update_ohlcv("multicharts_ohlcv", "multicharts_ohlcv", "1h", "ES")

    # new export: no 15:15 hole, history starts on day2, TradeStation re-adjusted prices (+10)
    _export(folder / "ES_1min.csv", day2, lambda t: 5010.0)

    def silver_es():
        return read_symbol(str(lake["SILVER_ROOT"] / "multicharts_ohlcv"), "ES").sort("timestamp")

    mod.main([], folder=folder)  # incremental: nothing after the last bar → the holes stay
    assert silver_es().height == 2 * 105

    mod.main(["--full"], folder=folder)  # holes filled, day2 re-priced, day1 left with old prices
    s = silver_es()
    assert s.height == 120 + 105
    assert s.filter(pl.col("timestamp") < chi(2025, 6, 3, 0, 0))["close"].unique().to_list() == [5000.0]

    mod.main(["--replace"], folder=folder)  # exactly the new export
    s = silver_es()
    assert s["timestamp"].to_list() == day2 and s["close"].unique().to_list() == [5010.0]
    b = read_symbol(str(lake["BRONZE_ROOT"] / "multicharts_ohlcv"), "ES")
    assert b.height == 120
    assert storage.read_symbol(str(lake["GOLD_ROOT"] / "multicharts_ohlcv" / "1h"), "ES").is_empty()

    gold.update_ohlcv("multicharts_ohlcv", "multicharts_ohlcv", "1h", "ES")  # rebuilt from scratch
    g = storage.read_symbol(str(lake["GOLD_ROOT"] / "multicharts_ohlcv" / "1h"), "ES").sort("timestamp")
    assert g["timestamp"].to_list() == [chi(2025, 6, 3, 14), chi(2025, 6, 3, 15)]
    assert g["close"].to_list() == [5010.0, 5010.0] and g["volume"].to_list() == [600.0, 600.0]


def test_short_exports_never_trigger_the_monthly_rules():
    bars = _month(2021, 7, cut_1515=True, friday_end=time(15, 14))
    five_days = bars.filter(pl.col("timestamp") < chi(2021, 7, 8, 0, 0))   # Thu 1 → Wed 7 July: 5 trading days
    assert recurring_gaps(five_days).is_empty()
    assert early_fridays(five_days).is_empty()                              # one Friday only
    assert not recurring_gaps(bars).is_empty()                              # the full month still fires


def test_history_plus_recent(lake, freeze_now, monkeypatch, tmp_path):
    freeze_now(gold, utc(2026, 1, 1))
    folder = tmp_path / "multicharts"
    folder.mkdir()
    mod = _load_multicharts()
    for name in ("BRONZE_ROOT", "SILVER_ROOT", "GOLD_ROOT"):
        monkeypatch.setattr(mod, name, lake[name])

    def day(d):  # 14:00-15:59 CT
        return [chi(2025, 6, d, 14, 0) + timedelta(minutes=i) for i in range(120)]

    def silver_es():
        return read_symbol(str(lake["SILVER_ROOT"] / "multicharts_ohlcv"), "ES").sort("timestamp")

    def bronze_es():
        return read_symbol(str(lake["BRONZE_ROOT"] / "multicharts_ohlcv"), "ES").sort("timestamp")

    # history Mon 2 → Wed 4, recent Wed 4 → Thu 5 on TradeStation's new adjustment (+1)
    _export(folder / "ES_1min.csv", day(2) + day(3) + day(4), lambda t: 5000.0)
    _export(folder / "ES_recent.csv", day(4) + day(5), lambda t: 5001.0)
    mod.main(["--replace"], folder=folder)
    s = silver_es()
    assert s["timestamp"].is_unique().all() and s.height == 4 * 120
    assert s.group_by(s["timestamp"].dt.day().alias("d")).agg(pl.col("close").unique()).sort("d").rows() == [
        (2, [5000.0]), (3, [5000.0]), (4, [5001.0]), (5, [5001.0])]
    assert bronze_es()["timestamp"].is_unique().all() and bronze_es().height == 4 * 120

    # next morning: a new recent, Thu 5 → Fri 6, re-adjusted again (+2)
    _export(folder / "ES_recent.csv", day(5) + day(6), lambda t: 5002.0)
    mod.main([], folder=folder)
    s = silver_es()
    assert s["timestamp"].is_unique().all() and s.height == 5 * 120
    assert s.group_by(s["timestamp"].dt.day().alias("d")).agg(pl.col("close").unique()).sort("d").rows() == [
        (2, [5000.0]), (3, [5000.0]), (4, [5001.0]), (5, [5002.0]), (6, [5002.0])]
    b = bronze_es()
    assert b["timestamp"].is_unique().all() and b.height == 5 * 120
    assert b.filter(pl.col("timestamp") >= chi(2025, 6, 5, 0, 0))["close"].unique().to_list() == [5002.0]
