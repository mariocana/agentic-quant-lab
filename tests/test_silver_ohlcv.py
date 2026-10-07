import math

import polars as pl

from quantlake.silver.ohlcv import clean_ohlcv


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
