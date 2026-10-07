import polars as pl

from quantlake.silver.merge import _MACRO_SCHEMA, _project


def test_project_casts_drops_and_fills():
    df = pl.DataFrame({
        "close":       [1],              # Int64 → cast to Float64
        "spread_open": [0.1],            # not in schema → dropped
        "symbol":      ["EURUSD"],
    })
    schema = {"symbol": pl.Utf8, "close": pl.Float64, "avg_gas": pl.Float64}
    out = _project(df, schema)
    assert out.columns == ["symbol", "close", "avg_gas"]
    assert dict(out.schema) == schema
    assert out["close"][0] == 1.0
    assert out["avg_gas"][0] is None


def test_macro_schema_has_no_volume():
    df = pl.DataFrame({"volume": [5.0], "close": [1.0]})
    out = _project(df, _MACRO_SCHEMA)
    assert "volume" not in out.columns
    assert list(out.columns) == list(_MACRO_SCHEMA)
