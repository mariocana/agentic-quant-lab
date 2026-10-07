import math
from datetime import datetime, timedelta, timezone

import polars as pl

from quantlake.silver.ohlcv import align_to_minute, clean_ohlcv


def _bars(**cols) -> pl.DataFrame:
    base = {
        "open":   [1.0, 2.0],
        "high":   [1.5, 2.5],
        "low":    [0.5, 1.5],
        "close":  [1.2, 2.2],
        "volume": [10.0, 20.0],
    }
    base.update(cols)
    return pl.DataFrame(base, schema={k: pl.Float64 for k in base})


def _isnan(v) -> bool:
    return v is not None and math.isnan(v)


def test_valid_bars_are_unchanged():
    df = _bars()
    assert clean_ohlcv(df).equals(df)


def test_empty_df_is_returned_as_is():
    df = _bars().clear()
    assert clean_ohlcv(df).is_empty()


def test_infinite_values_become_nan():
    out = clean_ohlcv(_bars(close=[float("inf"), float("-inf")]))
    assert _isnan(out["close"][0]) and _isnan(out["close"][1])


def test_nulls_become_nan_not_null():
    out = clean_ohlcv(_bars(volume=[None, 20.0]))
    assert out["volume"].null_count() == 0
    assert _isnan(out["volume"][0])
    assert out["volume"][1] == 20.0


def test_high_below_low_invalidates_all_price_columns():
    out = clean_ohlcv(_bars(high=[0.4, 2.5]))  # row 0: high < low
    for c in ("open", "high", "low", "close"):
        assert _isnan(out[c][0]), c
        assert not _isnan(out[c][1]), c
    assert out["volume"][0] == 10.0  # volume is not a price column


def test_negative_low_invalidates_all_price_columns():
    out = clean_ohlcv(_bars(low=[-0.1, 1.5]))
    for c in ("open", "high", "low", "close"):
        assert _isnan(out[c][0]), c


def test_negative_volume_becomes_nan_and_prices_survive():
    out = clean_ohlcv(_bars(volume=[-5.0, 20.0]))
    assert _isnan(out["volume"][0])
    assert out["close"][0] == 1.2


def test_rows_are_never_dropped():
    df = _bars(high=[0.1, float("inf")], volume=[-1.0, None])
    out = clean_ohlcv(df)
    assert out.height == df.height
    assert out.columns == df.columns


def test_non_float_columns_and_extras_are_preserved():
    df = _bars().with_columns(
        pl.lit("ETHUSDT").alias("symbol"),
        pl.Series("spread_open", [float("inf"), 0.1]),
    )
    out = clean_ohlcv(df)
    assert out["symbol"].to_list() == ["ETHUSDT", "ETHUSDT"]
    assert _isnan(out["spread_open"][0])  # extra Float64 columns get rules 1-2 too


def test_works_without_volume_column():
    df = _bars().drop("volume")
    out = clean_ohlcv(df)
    assert "volume" not in out.columns
    assert out.equals(df)


# ── align_to_minute ────────────────────────────────────────────────────────

def _ts(h, m, s=0, us=0):
    return datetime(2017, 12, 4, h, m, s, us, tzinfo=timezone.utc)


def _shifted(rows):
    """rows: (open_ts, volume, close) → binance-like 1m bars."""
    ts = [r[0] for r in rows]
    return pl.DataFrame({
        "timestamp": pl.Series(ts, dtype=pl.Datetime("us", "UTC")),
        "timestamp_close": pl.Series([t + timedelta(seconds=59, milliseconds=999) for t in ts],
                                     dtype=pl.Datetime("us", "UTC")),
        "symbol": ["BTCUSDT"] * len(rows),
        "open":  [r[2] for r in rows],
        "high":  [r[2] for r in rows],
        "low":   [r[2] for r in rows],
        "close": [r[2] for r in rows],
        "volume": [r[1] for r in rows],
    })


def test_shifted_open_times_are_truncated_to_the_minute():
    df = _shifted([
        (_ts(6, 0), 0.0, 100.0),                       # halt filler bar, already aligned
        (_ts(6, 1, 20, 799_000), 3.0, 101.0),          # +20.799 s
        (_ts(6, 2, 14, 789_000), 4.0, 102.0),          # +14.789 s
    ])
    out = align_to_minute(df)
    assert out["timestamp"].to_list() == [_ts(6, 0), _ts(6, 1), _ts(6, 2)]
    assert out["timestamp_close"].to_list() == [
        _ts(6, m) + timedelta(seconds=59, milliseconds=999) for m in (0, 1, 2)
    ]
    assert out["close"].to_list() == [100.0, 101.0, 102.0]
    assert out.row(0, named=True)["volume"] == 0.0  # filler bar kept as is


def test_collision_keeps_the_row_with_larger_volume():
    df = _shifted([
        (_ts(6, 5), 2.0, 105.0),
        (_ts(6, 5, 20, 799_000), 7.0, 106.0),   # truncates onto 06:05, larger volume → wins
        (_ts(6, 6, 14, 789_000), 1.0, 107.0),
    ])
    out = align_to_minute(df)
    assert out["timestamp"].to_list() == [_ts(6, 5), _ts(6, 6)]
    assert out["close"].to_list() == [106.0, 107.0]
    assert out["volume"].to_list() == [7.0, 1.0]


def test_collision_tie_keeps_earliest_original_timestamp():
    df = _shifted([(_ts(6, 5, 20, 799_000), 5.0, 106.0), (_ts(6, 5), 5.0, 105.0)])
    assert align_to_minute(df)["close"].to_list() == [105.0]


def test_collisions_are_per_symbol():
    a = _shifted([(_ts(6, 5), 1.0, 1.0)])
    b = _shifted([(_ts(6, 5, 20, 799_000), 2.0, 2.0)]).with_columns(pl.lit("ETHUSDT").alias("symbol"))
    out = align_to_minute(pl.concat([a, b]))
    assert out.height == 2
    assert out["timestamp"].to_list() == [_ts(6, 5), _ts(6, 5)]


def test_aligned_input_is_unchanged():
    df = _shifted([(_ts(6, m), float(m), float(m)) for m in range(5)])
    assert align_to_minute(df).equals(df)
