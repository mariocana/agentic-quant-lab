"""gold.ingest Delta round-trips (tmp dir, no network)."""
from datetime import timedelta

import polars as pl
import pytest

import quantlake.bronze.ingest as bronze
import quantlake.gold.ingest as gold
import quantlake.live as live
import quantlake.silver.ingest as silver
from helpers import minute_bars, utc

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


@pytest.fixture
def lake(tmp_path, monkeypatch):
    roots = {"BRONZE_ROOT": tmp_path / "bronze", "SILVER_ROOT": tmp_path / "silver", "GOLD_ROOT": tmp_path / "gold"}
    for mod in (bronze, silver, gold, live):
        for name, path in roots.items():
            if hasattr(mod, name):
                monkeypatch.setattr(mod, name, path)
    return roots


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
