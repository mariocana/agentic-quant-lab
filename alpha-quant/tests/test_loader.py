from datetime import datetime, timedelta, timezone

import polars as pl
import pytest

from alphaquant.data import SchemaError, load_bars, parse_timeframe
from alphaquant.instruments import QuantlakeInstrumentSource

from conftest import gold_bars, write_delta

UTC = timezone.utc
PARTITIONS = ["symbol", "year", "month"]


@pytest.fixture
def btc(data_root, costs):
    return QuantlakeInstrumentSource(data_root, costs=costs).get("BTCUSDT")


@pytest.fixture
def gold_15m(data_root):
    path = data_root / "gold" / "binance_spot_ohlcv" / "15m"
    start = datetime(2025, 12, 31, 20, tzinfo=UTC)  # crosses a year/month partition boundary
    bars = pl.concat([
        gold_bars("BTCUSDT", start, 40, timedelta(minutes=15)),
        gold_bars("ETHUSDT", start, 40, timedelta(minutes=15), base=10.0),
    ])
    write_delta(bars, path, partition_by=PARTITIONS)
    return path


def test_parse_timeframe():
    assert parse_timeframe("15m") == timedelta(minutes=15)
    assert parse_timeframe("4h") == timedelta(hours=4)
    assert parse_timeframe("1d") == timedelta(days=1)
    with pytest.raises(ValueError):
        parse_timeframe("15min")


def test_loads_one_symbol_with_version_and_quality(data_root, btc, gold_15m):
    bars = load_bars(btc, "15m", data_root=data_root)

    assert bars.delta_version == 0
    assert bars.df["symbol"].unique().to_list() == ["BTCUSDT"]
    assert len(bars.df) == 40
    assert bars.df["timestamp"].is_sorted()
    assert bars.df.schema["timestamp"] == pl.Datetime("us", "UTC")
    assert "year" not in bars.df.columns and "volume" in bars.df.columns
    assert bars.quality.clean and bars.quality.missing_bars == 0


def test_range_filter_naive_is_utc(data_root, btc, gold_15m):
    bars = load_bars(btc, "15m", start=datetime(2026, 1, 1), end=datetime(2026, 1, 1, 1), data_root=data_root)
    assert bars.df["timestamp"].to_list() == [datetime(2026, 1, 1, 0, 15 * i, tzinfo=UTC) for i in range(4)]


def test_quality_reports_missing_and_nan_bars(data_root, btc):
    path = data_root / "gold" / "binance_spot_ohlcv" / "15m"
    bars = gold_bars("BTCUSDT", datetime(2026, 1, 1, tzinfo=UTC), 10, timedelta(minutes=15))
    bars = bars.filter(pl.int_range(pl.len()).is_in([3, 4]).not_())  # two missing bars
    bars = bars.with_columns(pl.when(pl.int_range(pl.len()) == 0).then(float("nan")).otherwise(pl.col("high")).alias("high"))
    write_delta(bars, path, partition_by=PARTITIONS)

    quality = load_bars(btc, "15m", data_root=data_root).quality
    assert quality.nan_price_rows == 1
    assert quality.missing_bars == 2
    assert quality.missing_sample == (datetime(2026, 1, 1, 0, 45, tzinfo=UTC), datetime(2026, 1, 1, 1, 0, tzinfo=UTC))
    assert not quality.clean


def test_pinned_version_reads_old_data(data_root, btc, gold_15m):
    extra = gold_bars("BTCUSDT", datetime(2026, 1, 1, 6, tzinfo=UTC), 4, timedelta(minutes=15))
    write_delta(extra, gold_15m, mode="append")

    assert len(load_bars(btc, "15m", data_root=data_root).df) == 44
    old = load_bars(btc, "15m", version=0, data_root=data_root)
    assert old.delta_version == 0 and len(old.df) == 40


def test_missing_table_and_empty_range(data_root, btc, gold_15m):
    with pytest.raises(FileNotFoundError, match="gold/binance_spot_ohlcv/1h"):
        load_bars(btc, "1h", data_root=data_root)
    with pytest.raises(ValueError, match="no rows"):
        load_bars(btc, "15m", start=datetime(2030, 1, 1), data_root=data_root)


def test_schema_errors(data_root, btc):
    path = data_root / "gold" / "binance_spot_ohlcv" / "15m"
    naive = gold_bars("BTCUSDT", datetime(2026, 1, 1, tzinfo=UTC), 4, timedelta(minutes=15)).with_columns(
        pl.col("timestamp").dt.replace_time_zone(None)
    )
    write_delta(naive, path, partition_by=PARTITIONS)
    with pytest.raises(SchemaError, match="time_zone='UTC'"):
        load_bars(btc, "15m", data_root=data_root)

    no_close = gold_bars("BTCUSDT", datetime(2026, 1, 1, tzinfo=UTC), 4, timedelta(minutes=15)).drop("close")
    write_delta(no_close, path, partition_by=PARTITIONS, mode="overwrite")
    with pytest.raises(SchemaError, match="close"):
        load_bars(btc, "15m", data_root=data_root)


def test_duplicate_timestamps_are_an_error(data_root, btc):
    path = data_root / "gold" / "binance_spot_ohlcv" / "15m"
    bars = gold_bars("BTCUSDT", datetime(2026, 1, 1, tzinfo=UTC), 4, timedelta(minutes=15))
    write_delta(pl.concat([bars, bars.head(1)]), path, partition_by=PARTITIONS)
    with pytest.raises(SchemaError, match="duplicated timestamps"):
        load_bars(btc, "15m", data_root=data_root)


def test_cme_missing_bars_ignore_closed_market(data_root, costs):
    es = QuantlakeInstrumentSource(data_root, costs=costs).get("ES")
    path = data_root / "gold" / "multicharts_ohlcv" / "1h"
    # Friday 2026-03-13 18:00 UTC (13:00 CDT) -> Sunday 23:00 UTC: only the hours the market is open
    hours = pl.datetime_range(datetime(2026, 3, 13, 18, tzinfo=UTC), datetime(2026, 3, 15, 23, tzinfo=UTC), "1h", time_zone="UTC", eager=True)
    open_hours = hours.filter(es.session.open_mask(hours))
    bars = gold_bars("ES", datetime(2026, 1, 1, tzinfo=UTC), len(open_hours), timedelta(hours=1)).with_columns(
        open_hours.alias("timestamp")
    )
    write_delta(bars, path, partition_by=PARTITIONS)

    quality = load_bars(es, "1h", data_root=data_root).quality
    assert quality.missing_bars == 0
    # Fri 18:00, 19:00, 20:00 UTC (break from 16:00 CDT) + Sun 22:00, 23:00 UTC after the reopen
    assert len(open_hours) == 5
