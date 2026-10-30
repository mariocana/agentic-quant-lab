"""gold.ingest Delta round-trips (tmp dir, no network)."""
from datetime import datetime, timedelta, timezone

import polars as pl
from deltalake import DeltaTable

import quantlake.bronze.ingest as bronze
import quantlake.gold.ingest as gold
import quantlake.live as live
import quantlake.silver.ingest as silver
from helpers import minute_bars, utc
from quantlake.gold.ohlcv import resample

SYMBOL = "BTCUSDT"


class _EchoPipeline:
    """Oryon FeaturePipeline stand-in: one feature = close, warm-up of 2 bars."""

    def __init__(self):
        self.seen: list[list[float]] = []

    def input_names(self):
        return ["close"]

    def output_names(self):
        return ["f_close"]

    def warm_up_period(self):
        return 2

    def update(self, inputs):
        self.seen.append(list(inputs))
        return [inputs[0]]

    def run_research(self, data):
        self.seen = [list(r) for r in data]
        return [[r[0]] for r in data]


def _seed_silver(table: str, start, n: int, symbol: str = SYMBOL) -> pl.DataFrame:
    df = bronze.add_partition_columns(minute_bars(start, n, symbol=symbol).drop("symbol"), symbol)
    silver.ingest(df, table)
    return df


def test_rebuild_from_silver_matches_batch_ingest(lake, freeze_now):
    freeze_now(gold, utc(2024, 1, 2, 10, 0))
    df = _seed_silver("s", utc(2024, 1, 2, 9, 0), 32)  # 09:00..09:31

    built = gold.rebuild_from_silver("s", SYMBOL, "g", "5m", pipeline=_EchoPipeline())
    batch = gold.ingest(df, "g2", "5m", pipeline=_EchoPipeline())

    assert built["timestamp"].to_list() == [utc(2024, 1, 2, 9, m) for m in range(0, 31, 5)]
    drop = ["ingested_at"]
    assert built.drop(drop).equals(batch.drop(drop))
    assert built["f_close"].to_list() == built["close"].to_list()
    assert built["live"].to_list() == [False] * built.height
    assert (built["timestamp_close"] - built["timestamp"]).unique().to_list() == [timedelta(minutes=5)]


def test_rebuild_from_silver_applies_transform_before_features(lake, freeze_now):
    freeze_now(gold, utc(2024, 1, 2, 10, 0))
    _seed_silver("s", utc(2024, 1, 2, 9, 0), 10)

    def double_close(df, symbol):
        assert symbol == SYMBOL
        return df.with_columns(pl.col("close") * 2)

    built = gold.rebuild_from_silver("s", SYMBOL, "g", "5m", pipeline=_EchoPipeline(), transform_gold=double_close)
    assert built["f_close"].to_list() == built["close"].to_list()
    assert built["close"].to_list() == [2 * 104.25, 2 * 109.25]


def test_rebuild_from_silver_missing_or_empty_returns_none(lake, freeze_now):
    freeze_now(gold, utc(2024, 1, 2, 9, 3))
    assert gold.rebuild_from_silver("nope", SYMBOL, "g", "5m") is None
    _seed_silver("s", utc(2024, 1, 2, 9, 0), 3)  # only an incomplete 5m window
    assert gold.rebuild_from_silver("s", SYMBOL, "g", "5m") is None
    assert gold.rebuild_from_silver("s", "OTHER", "g", "5m") is None


def test_warmup_pipeline_feeds_last_n_gold_bars(lake, freeze_now):
    freeze_now(gold, utc(2024, 1, 2, 10, 0))
    _seed_silver("s", utc(2024, 1, 2, 9, 0), 20)
    gold.rebuild_from_silver("s", SYMBOL, "g", "5m")

    p = _EchoPipeline()
    gold.warmup_pipeline(p, "g", "5m", SYMBOL)
    assert p.seen == [[109.25 + 5], [109.25 + 10]]  # 09:10 and 09:15 closes

    p2 = _EchoPipeline()
    gold.warmup_pipeline(p2, "missing", "5m", SYMBOL)
    assert p2.seen == []


def test_build_live_bar_builds_last_closed_window_once(lake, freeze_now):
    _seed_silver("s", utc(2024, 1, 2, 9, 0), 12)  # 09:00..09:11
    freeze_now(gold, utc(2024, 1, 2, 9, 10, 20))

    p = _EchoPipeline()
    bar = gold.build_live_bar("s", SYMBOL, "g", "5m", pipeline=p)
    assert bar["timestamp"].to_list() == [utc(2024, 1, 2, 9, 5)]
    assert bar["close"].to_list() == [109.25]
    assert bar["f_close"].to_list() == [109.25]
    assert bar["live"].to_list() == [True]
    assert bar["latency_ms"].to_list() == [20_000]
    assert p.seen == [[109.25]]

    # already in gold → no second build
    assert gold.build_live_bar("s", SYMBOL, "g", "5m", pipeline=p) is None
    assert p.seen == [[109.25]]


def test_last_timestamps(lake):
    assert bronze.last_bronze_ts("b", SYMBOL) is None
    df = bronze.add_partition_columns(minute_bars(utc(2024, 1, 2, 9, 0), 3).drop("symbol"), SYMBOL)
    bronze.save(df, "b")
    silver.ingest(df, "s")
    assert bronze.last_bronze_ts("b", SYMBOL) == utc(2024, 1, 2, 9, 2)
    assert bronze.last_bronze_ts("b", "OTHER") is None
    assert live._last_silver_ts("s", SYMBOL) == utc(2024, 1, 2, 9, 2)
    assert live._last_silver_ts("missing", SYMBOL) is None


def test_reconstitute_buffer_reloads_current_window(lake):
    # 09:00..09:07 with timestamp_close, like the WS path stores it; 09:05 window still open
    src = bronze.add_partition_columns(minute_bars(utc(2024, 1, 2, 9, 0), 8).drop("symbol"), SYMBOL)
    silver.ingest(src.with_columns((pl.col("timestamp") + pl.duration(minutes=1)).alias("timestamp_close")), "s")

    buffers = {SYMBOL: []}
    live._reconstitute_buffer(SYMBOL, "s", "5m", utc(2024, 1, 2, 9, 7), buffers)
    got = pl.concat(buffers[SYMBOL])
    assert got.columns == live._BUFFER_COLS
    assert got["timestamp"].to_list() == [utc(2024, 1, 2, 9, m) for m in (5, 6, 7)]

    empty = {SYMBOL: []}
    live._reconstitute_buffer(SYMBOL, "s", "5m", utc(2024, 1, 2, 9, 4), empty)  # window complete
    assert empty[SYMBOL] == []


# ── plain OHLCV gold (update_ohlcv) ────────────────────────────────────────

def _gold(table: str, tf: str, symbol: str = SYMBOL) -> pl.DataFrame:
    from quantlake.storage import read_symbol
    return read_symbol(str(gold.GOLD_ROOT / table / tf), symbol).sort("timestamp")


def test_read_symbol_since_and_symbols(lake):
    from quantlake.storage import read_symbol, symbols
    _seed_silver("s", utc(2023, 12, 31, 23, 58), 4)
    _seed_silver("s", utc(2024, 1, 2, 9, 0), 2, symbol="ETHUSDT")
    path = str(lake["SILVER_ROOT"] / "s")
    got = read_symbol(path, SYMBOL, since=utc(2024, 1, 1, 0, 0))
    assert got["timestamp"].to_list() == [utc(2024, 1, 1, 0, 0), utc(2024, 1, 1, 0, 1)]
    assert symbols(path) == ["BTCUSDT", "ETHUSDT"]
    assert symbols(str(lake["SILVER_ROOT"] / "missing")) == []


def test_update_ohlcv_writes_only_fully_covered_windows(lake, freeze_now):
    freeze_now(gold, utc(2024, 1, 2, 12, 0))
    _seed_silver("s", utc(2024, 1, 2, 9, 0), 13)  # 09:00..09:12 → 09:10 window incomplete

    out = gold.update_ohlcv("s", "g", "5m", SYMBOL)
    assert out["timestamp"].to_list() == [utc(2024, 1, 2, 9, 0), utc(2024, 1, 2, 9, 5)]

    # 09:13..09:14 arrive: the 09:10 bar is now complete; 09:05 is rebuilt, not duplicated
    _seed_silver("s", utc(2024, 1, 2, 9, 13), 2)
    out = gold.update_ohlcv("s", "g", "5m", SYMBOL)
    assert out["timestamp"].to_list() == [utc(2024, 1, 2, 9, 5), utc(2024, 1, 2, 9, 10)]

    g = _gold("g", "5m")
    assert g["timestamp"].to_list() == [utc(2024, 1, 2, 9, m) for m in (0, 5, 10)]
    assert g["volume"].to_list() == [1 + 2 + 3 + 4 + 5, 6 + 7 + 8 + 9 + 10, 11 + 12 + 13 + 1 + 2]

    # nothing new → nothing but the last bar rewritten, still 3 rows
    gold.update_ohlcv("s", "g", "5m", SYMBOL)
    assert _gold("g", "5m").height == 3


def test_update_ohlcv_matches_batch_resample(lake, freeze_now):
    freeze_now(gold, utc(2024, 1, 3, 12, 0))
    df = _seed_silver("s", utc(2024, 1, 2, 0, 0), 24 * 60)  # one full UTC day
    for tf in ("1m", "15m", "4h", "1d"):
        gold.update_ohlcv("s", "g", tf, SYMBOL)
        got = _gold("g", tf).select("timestamp", "open", "high", "low", "close", "volume")
        want = resample(df, tf).select("timestamp", "open", "high", "low", "close", "volume")
        assert got.equals(want), tf


def test_update_ohlcv_output_fits_alpha_quant_loader(lake, freeze_now):
    freeze_now(gold, utc(2024, 1, 2, 12, 0))
    _seed_silver("s", utc(2024, 1, 2, 9, 0), 30)
    _seed_silver("s", utc(2024, 1, 2, 9, 0), 30, symbol="ETHUSDT")
    gold.update_ohlcv("s", "g", "5m", SYMBOL)
    gold.update_ohlcv("s", "g", "5m", "ETHUSDT")
    g = pl.from_arrow(DeltaTable(str(gold.GOLD_ROOT / "g" / "5m")).to_pyarrow_table())
    assert g.schema["timestamp"] == pl.Datetime("us", "UTC")
    assert g.schema["symbol"] == pl.String
    for c in ("open", "high", "low", "close"):
        assert g.schema[c] == pl.Float64
    assert g.group_by("symbol").agg(pl.col("timestamp").is_duplicated().any())["timestamp"].to_list() == [False, False]
    assert g["live"].unique().to_list() == [False]


def test_update_ohlcv_without_silver(lake):
    assert gold.update_ohlcv("missing", "g", "5m", SYMBOL).is_empty()


def test_ohlcv_gold_script_builds_every_table_and_timeframe(lake, freeze_now, monkeypatch):
    import importlib.util
    from pathlib import Path

    freeze_now(gold, utc(2024, 1, 3, 0, 0))
    _seed_silver("binance_spot_ohlcv", utc(2024, 1, 2, 0, 0), 60)
    _seed_silver("multicharts_ohlcv", utc(2024, 1, 2, 0, 0), 5 * 60, symbol="ES")

    script = Path(__file__).parents[1] / "applications" / "historical" / "ohlcv_gold.py"
    spec = importlib.util.spec_from_file_location("ohlcv_gold", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "SILVER_ROOT", lake["SILVER_ROOT"])
    monkeypatch.setattr(mod, "TABLES", {
        "multicharts_ohlcv": ("multicharts_ohlcv", ["1h", "4h_cme"]),
        "binance_spot_ohlcv": ("binance_spot_ohlcv", ["1m", "1h"]),
    })
    mod.main()

    assert _gold("binance_spot_ohlcv", "1m").height == 60
    assert _gold("binance_spot_ohlcv", "1h").height == 1
    assert _gold("multicharts_ohlcv", "1h", symbol="ES")["timestamp"].to_list() == [utc(2024, 1, 2, h) for h in range(5)]
    # data 00:00-05:00 UTC = 18:00-23:00 CST: the 17:00-21:00 CST window (23:00-03:00 UTC) is written,
    # the 21:00-01:00 CST one (03:00-07:00 UTC) is not complete yet
    assert _gold("multicharts_ohlcv", "4h_cme", symbol="ES")["timestamp"].to_list() == [utc(2024, 1, 1, 23, 0)]


# ── binance_realign.py ─────────────────────────────────────────────────────

def _load_script(name: str):
    import importlib.util
    from pathlib import Path

    path = Path(__file__).parents[1] / "applications" / "historical" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_binance_realign_rewrites_silver_and_gold(lake, freeze_now, monkeypatch):
    freeze_now(gold, utc(2018, 3, 1))
    shift = timedelta(seconds=20, milliseconds=799)
    raw = minute_bars(utc(2017, 12, 4, 6, 0), 10).drop("symbol")
    # minutes 1..9 shifted; minute 2 also present aligned with lower volume → collision
    raw = raw.with_columns(
        pl.when(pl.int_range(pl.len()) > 0).then(pl.col("timestamp") + shift).otherwise(pl.col("timestamp"))
    )
    dup = minute_bars(utc(2017, 12, 4, 6, 2), 1).drop("symbol").with_columns(pl.lit(0.5).alias("volume"))
    raw = bronze.add_partition_columns(pl.concat([raw, dup]), SYMBOL)
    bronze.save(raw, "binance_spot_ohlcv")
    # silver as written before the fix: shifted timestamps
    silver.ingest(raw, "binance_spot_ohlcv")
    gold.update_ohlcv("binance_spot_ohlcv", "binance_spot_ohlcv", "5m", SYMBOL)

    mod = _load_script("binance_realign")
    for name, path in (("BRONZE_ROOT", lake["BRONZE_ROOT"]), ("SILVER_ROOT", lake["SILVER_ROOT"]),
                       ("GOLD_ROOT", lake["GOLD_ROOT"])):
        monkeypatch.setattr(mod, name, path)

    dry = mod.realign(SYMBOL, utc(2017, 12, 1), utc(2018, 3, 1), dry_run=True)
    assert dry == {"bronze_rows": 11, "bronze_misaligned": 9,
                   "silver_rows_before": 11, "silver_misaligned_before": 9}

    stats = mod.realign(SYMBOL, utc(2017, 12, 1), utc(2018, 3, 1))
    assert stats["silver_deleted"] == 11 and stats["silver_rows_after"] == 10
    assert stats["gold_5m"] == 2

    from quantlake.storage import read_symbol
    s = read_symbol(str(lake["SILVER_ROOT"] / "binance_spot_ohlcv"), SYMBOL).sort("timestamp")
    assert s["timestamp"].to_list() == [utc(2017, 12, 4, 6, m) for m in range(10)]
    assert s.filter(pl.col("timestamp") == utc(2017, 12, 4, 6, 2))["volume"].to_list() == [3.0]

    g = _gold("binance_spot_ohlcv", "5m")
    assert g["timestamp"].to_list() == [utc(2017, 12, 4, 6, 0), utc(2017, 12, 4, 6, 5)]
    assert g["volume"].to_list() == [1 + 2 + 3 + 4 + 5, 6 + 7 + 8 + 9 + 10]  # duplicate no longer summed

    # second run: nothing misaligned left, same result
    again = mod.realign(SYMBOL, utc(2017, 12, 1), utc(2018, 3, 1))
    assert again["silver_misaligned_before"] == 0 and again["silver_rows_after"] == 10


def test_update_ohlcv_1d_cme_waits_for_the_session_close(lake, freeze_now):
    from zoneinfo import ZoneInfo
    chi = lambda *a: datetime(*a, tzinfo=ZoneInfo("America/Chicago")).astimezone(timezone.utc)  # noqa: E731

    freeze_now(gold, chi(2026, 10, 3, 12, 0))
    # Wed 17:00 → Thu 15:59 CT (session not over) then Thu 16:00 → 16:59 (last hour)
    _seed_silver("s", chi(2026, 9, 30, 17, 0), 23 * 60, symbol="ES")
    assert gold.update_ohlcv("s", "g", "1d_cme", "ES").is_empty()

    _seed_silver("s", chi(2026, 10, 1, 16, 0), 61, symbol="ES")  # 16:00 → 17:00, opens Thu's session
    out = gold.update_ohlcv("s", "g", "1d_cme", "ES")
    assert out["timestamp"].to_list() == [chi(2026, 9, 30, 17)]
    assert out["timestamp_close"].to_list() == [chi(2026, 10, 1, 17)]
    assert out["volume"].item() > 0


def test_update_ohlcv_also_fills_history_added_before_the_first_gold_bar(lake, freeze_now):
    freeze_now(gold, utc(2020, 1, 2, 12, 0))
    _seed_silver("s", utc(2020, 1, 1, 0, 0), 60)            # gold built first from 2020-01-01
    out = gold.update_ohlcv("s", "g", "15m", SYMBOL)
    assert out["timestamp"].min() == utc(2020, 1, 1, 0, 0)

    _seed_silver("s", utc(2019, 12, 31, 23, 0), 60)        # head added later (binance_um 2019 via REST)
    out = gold.update_ohlcv("s", "g", "15m", SYMBOL)
    head = [utc(2019, 12, 31, 23, m) for m in (0, 15, 30, 45)]
    assert out["timestamp"].to_list() == head + [utc(2020, 1, 1, 0, 45)]  # head + rebuilt last bar

    g = _gold("g", "15m")
    assert g["timestamp"].to_list() == head + [utc(2020, 1, 1, 0, m) for m in (0, 15, 30, 45)]
    assert g["timestamp"].is_unique().all()
    assert g["year"].to_list()[:4] == [2019] * 4

    # nothing new at either end: only the last bar is rewritten
    assert gold.update_ohlcv("s", "g", "15m", SYMBOL)["timestamp"].to_list() == [utc(2020, 1, 1, 0, 45)]


def test_update_ohlcv_head_with_session_timeframe(lake, freeze_now):
    from zoneinfo import ZoneInfo
    chi = lambda *a: datetime(*a, tzinfo=ZoneInfo("America/Chicago")).astimezone(timezone.utc)  # noqa: E731
    freeze_now(gold, chi(2026, 10, 3, 12, 0))
    _seed_silver("s", chi(2026, 10, 1, 17, 0), 24 * 60, symbol="ES")   # Thu 17:00 → Fri 17:00 session
    assert gold.update_ohlcv("s", "g", "1d_cme", "ES")["timestamp"].to_list() == [chi(2026, 10, 1, 17)]
    _seed_silver("s", chi(2026, 9, 30, 17, 0), 24 * 60, symbol="ES")   # the session before, added later
    out = gold.update_ohlcv("s", "g", "1d_cme", "ES")
    assert out["timestamp"].to_list() == [chi(2026, 9, 30, 17), chi(2026, 10, 1, 17)]
    assert _gold("g", "1d_cme", "ES")["timestamp"].to_list() == [chi(2026, 9, 30, 17), chi(2026, 10, 1, 17)]
