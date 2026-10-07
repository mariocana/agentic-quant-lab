from datetime import datetime, timezone

import polars as pl
import pytest
from deltalake import DeltaTable

import quantlake.reference.instruments as ref
from quantlake.reference.instruments import (
    DEFAULT_INSTRUMENTS, SCHEMA, InstrumentsError, instruments_frame,
    read_instruments, seed_default, upsert_instruments, validate_instruments,
)

T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def reference_root(tmp_path, monkeypatch):
    monkeypatch.setattr(ref, "REFERENCE_ROOT", tmp_path / "reference")
    return tmp_path / "reference"


def _row(**overrides) -> dict:
    row = dict(DEFAULT_INSTRUMENTS[0])
    row.update(overrides)
    return row


def _frame(*rows: dict) -> pl.DataFrame:
    return instruments_frame(list(rows) or [_row()], updated_at=T0)


def _error(df: pl.DataFrame) -> str:
    with pytest.raises(InstrumentsError) as exc:
        validate_instruments(df)
    return str(exc.value)


# ── validation ─────────────────────────────────────────────────────────────

def test_defaults_are_valid():
    validate_instruments(_frame(*DEFAULT_INSTRUMENTS))


def test_missing_wrong_type_and_extra_columns():
    df = _frame().drop("min_qty").with_columns(
        pl.col("tick_size").cast(pl.Float32),
        pl.lit(1.0).alias("fee"),
    )
    msg = _error(df)
    assert "missing column 'min_qty'" in msg
    assert "column 'tick_size' is Float32" in msg
    assert "unexpected columns ['fee']" in msg


def test_naive_updated_at_is_rejected():
    df = _frame().with_columns(pl.col("updated_at").dt.replace_time_zone(None))
    assert "updated_at" in _error(df)


def test_duplicated_and_empty_symbols():
    assert "duplicated symbols ['ES']" in _error(_frame(_row(), _row()))
    assert "empty symbol" in _error(_frame(_row(symbol=" ")))
    assert "empty symbol" in _error(_frame(_row(symbol=None)))


def test_unknown_asset_class():
    assert "unknown asset_class for ['ES']" in _error(_frame(_row(asset_class="futures")))


@pytest.mark.parametrize("column", ["tick_size", "multiplier", "qty_step", "min_qty"])
@pytest.mark.parametrize("value", [0.0, -1.0, float("nan"), float("inf"), None])
def test_numbers_must_be_positive_and_finite(column, value):
    assert f"{column} must be a finite number > 0 for ['ES']" in _error(_frame(_row(**{column: value})))


def test_required_text_columns():
    msg = _error(_frame(_row(exchange="", gold_table=None)))
    assert "empty exchange for ['ES']" in msg
    assert "empty gold_table for ['ES']" in msg


def test_break_must_be_complete():
    assert "both set or both null" in _error(_frame(_row(break_end=None)))
    assert "both set or both null" in _error(_frame(_row(break_start=None)))


@pytest.mark.parametrize("bad", ["16:0", "4pm", "24:00", "16:60", "16:00:00", "1600"])
def test_break_format(bad):
    assert "break_start must be HH:MM for ['ES']" in _error(_frame(_row(break_start=bad)))


def test_every_problem_is_reported_at_once():
    msg = _error(_frame(_row(asset_class="x", tick_size=0.0, break_end=None)))
    assert "asset_class" in msg and "tick_size" in msg and "break_start and break_end" in msg


def test_invalid_frame_is_never_written(reference_root):
    with pytest.raises(InstrumentsError):
        upsert_instruments(_frame(_row(tick_size=-1.0)))
    assert not DeltaTable.is_deltatable(str(reference_root / "instruments"))


# ── Delta round-trip ───────────────────────────────────────────────────────

def test_seed_default_creates_table_with_exact_schema(reference_root):
    df = seed_default()
    path = reference_root / "instruments"
    assert DeltaTable.is_deltatable(str(path))
    assert DeltaTable(str(path)).metadata().partition_columns == []

    raw = pl.from_arrow(DeltaTable(str(path)).to_pyarrow_table())
    assert dict(raw.schema) == SCHEMA
    assert list(read_instruments().schema.items()) == list(SCHEMA.items())
    assert df.height == 4
    assert df["symbol"].to_list() == ["BTCUSDT", "ES", "ETHUSDT", "NQ"]


def test_seed_values(reference_root):
    df = seed_default()
    es = df.row(by_predicate=pl.col("symbol") == "ES", named=True)
    assert (es["tick_size"], es["multiplier"], es["calendar"]) == (0.25, 50.0, "CMES")
    assert (es["break_start"], es["break_end"]) == ("16:00", "17:00")
    assert (es["gold_table"], es["data_symbol"]) == ("multicharts_ohlcv", "ES")
    nq = df.row(by_predicate=pl.col("symbol") == "NQ", named=True)
    assert nq["multiplier"] == 20.0
    eth = df.row(by_predicate=pl.col("symbol") == "ETHUSDT", named=True)
    assert (eth["qty_step"], eth["min_qty"], eth["calendar"]) == (0.0001, 0.0001, "24/7")
    assert eth["break_start"] is None and eth["break_end"] is None


def test_merge_is_idempotent():
    seed_default()
    seed_default()
    df = read_instruments()
    assert df.height == 4
    assert df["symbol"].is_unique().all()


def test_merge_updates_existing_and_inserts_new():
    upsert_instruments(_frame(_row(), _row(symbol="NQ", multiplier=20.0)))
    v_first = DeltaTable(ref.table_path()).version()

    later = datetime(2026, 2, 1, tzinfo=timezone.utc)
    upsert_instruments(instruments_frame(
        [_row(tick_size=0.5), _row(symbol="RTY", multiplier=50.0, tick_size=0.1)], updated_at=later,
    ))
    df = read_instruments()
    assert df["symbol"].to_list() == ["ES", "NQ", "RTY"]
    es = df.row(by_predicate=pl.col("symbol") == "ES", named=True)
    assert es["tick_size"] == 0.5 and es["updated_at"] == later
    nq = df.row(by_predicate=pl.col("symbol") == "NQ", named=True)
    assert nq["updated_at"] == T0  # untouched

    # older versions stay readable (alpha-quant pins the version it used)
    old = read_instruments(version=v_first)
    assert old["symbol"].to_list() == ["ES", "NQ"]
    assert old.row(by_predicate=pl.col("symbol") == "ES", named=True)["tick_size"] == 0.25


def test_read_missing_table():
    with pytest.raises(FileNotFoundError):
        read_instruments()
