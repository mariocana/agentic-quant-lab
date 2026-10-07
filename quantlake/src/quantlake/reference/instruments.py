"""reference/instruments: market specs of the traded instruments.

One row per instrument, keyed by `symbol`. alpha-quant reads this table
read-only (QuantlakeInstrumentSource), so SCHEMA is a contract: column
names and dtypes must not change without changing the reader too. Costs
(fees, slippage) live in alpha-quant, not here.

`gold_table` / `data_symbol` point at the bars: gold/<gold_table>/<tf>,
rows where symbol == data_symbol.

The table is small and unpartitioned; writes merge on `symbol`. It is not
vacuumed by quantlake.maintenance, so alpha-quant can always reopen the
exact version it recorded.
"""
import re
from datetime import datetime, timezone

import polars as pl
from deltalake import DeltaTable, write_deltalake

from quantlake.config import REFERENCE_ROOT

TABLE_NAME = "instruments"

SCHEMA: dict[str, pl.DataType] = {
    "symbol":      pl.String(),
    "asset_class": pl.String(),
    "exchange":    pl.String(),
    "quote_ccy":   pl.String(),
    "tick_size":   pl.Float64(),
    "multiplier":  pl.Float64(),
    "qty_step":    pl.Float64(),
    "min_qty":     pl.Float64(),
    "calendar":    pl.String(),
    "break_start": pl.String(),
    "break_end":   pl.String(),
    "gold_table":  pl.String(),
    "data_symbol": pl.String(),
    "updated_at":  pl.Datetime("us", "UTC"),
    "description": pl.String(),
}

ASSET_CLASSES = ("future", "crypto_spot", "crypto_perp", "fx", "equity")
ALWAYS_OPEN = "24/7"

_REQUIRED_TEXT = ("symbol", "asset_class", "exchange", "quote_ccy", "calendar", "gold_table", "data_symbol")
_POSITIVE = ("tick_size", "multiplier", "qty_step", "min_qty")
_HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")

# Sources: CME contract specs (ES $50 x index, NQ $20 x index, tick 0.25,
# daily halt 16:00-17:00 America/Chicago); Binance spot exchangeInfo
# (PRICE_FILTER.tickSize, LOT_SIZE.stepSize / minQty).
# MultiCharts bars are stored with symbol "ES"/"NQ" (applications/symbols.py
# MC_FILES); "ES_1min" is only the CSV file name.
DEFAULT_INSTRUMENTS: list[dict] = [
    {
        "symbol": "ES", "asset_class": "future", "exchange": "CME", "quote_ccy": "USD",
        "tick_size": 0.25, "multiplier": 50.0, "qty_step": 1.0, "min_qty": 1.0,
        "calendar": "CMES", "break_start": "16:00", "break_end": "17:00",
        "gold_table": "multicharts_ohlcv", "data_symbol": "ES",
        "description": "E-mini S&P 500, continuous (MultiCharts @ES)",
    },
    {
        "symbol": "NQ", "asset_class": "future", "exchange": "CME", "quote_ccy": "USD",
        "tick_size": 0.25, "multiplier": 20.0, "qty_step": 1.0, "min_qty": 1.0,
        "calendar": "CMES", "break_start": "16:00", "break_end": "17:00",
        "gold_table": "multicharts_ohlcv", "data_symbol": "NQ",
        "description": "E-mini Nasdaq-100, continuous (MultiCharts @NQ)",
    },
    {
        "symbol": "BTCUSDT", "asset_class": "crypto_spot", "exchange": "BINANCE", "quote_ccy": "USDT",
        "tick_size": 0.01, "multiplier": 1.0, "qty_step": 0.00001, "min_qty": 0.00001,
        "calendar": ALWAYS_OPEN, "break_start": None, "break_end": None,
        "gold_table": "binance_spot_ohlcv", "data_symbol": "BTCUSDT",
        "description": "Bitcoin / Tether, Binance spot",
    },
    {
        "symbol": "ETHUSDT", "asset_class": "crypto_spot", "exchange": "BINANCE", "quote_ccy": "USDT",
        "tick_size": 0.01, "multiplier": 1.0, "qty_step": 0.0001, "min_qty": 0.0001,
        "calendar": ALWAYS_OPEN, "break_start": None, "break_end": None,
        "gold_table": "binance_spot_ohlcv", "data_symbol": "ETHUSDT",
        "description": "Ether / Tether, Binance spot",
    },
]


class InstrumentsError(ValueError):
    """reference/instruments rows break the schema or the value rules."""


def table_path() -> str:
    return str(REFERENCE_ROOT / TABLE_NAME)


def instruments_frame(rows: list[dict], updated_at: datetime | None = None) -> pl.DataFrame:
    """Build a SCHEMA-typed frame from dicts; fills updated_at (now) and description (null) if absent."""
    now = updated_at or datetime.now(timezone.utc)
    full = [{"updated_at": now, "description": None, **row} for row in rows]
    return pl.DataFrame(full, schema=SCHEMA)


def validate_instruments(df: pl.DataFrame) -> None:
    """Raise InstrumentsError listing every schema or value problem in df."""
    problems = []
    for name, dtype in SCHEMA.items():
        if name not in df.columns:
            problems.append(f"missing column '{name}'")
        elif df.schema[name] != dtype:
            problems.append(f"column '{name}' is {df.schema[name]}, expected {dtype}")
    extra = [c for c in df.columns if c not in SCHEMA]
    if extra:
        problems.append(f"unexpected columns {extra}")
    if problems:
        raise InstrumentsError("reference/instruments: " + "; ".join(problems))

    def rows_where(mask: pl.Expr) -> list:
        return df.filter(mask)["symbol"].to_list()

    for c in _REQUIRED_TEXT:
        bad = rows_where(pl.col(c).is_null() | (pl.col(c).str.strip_chars() == ""))
        if bad:
            problems.append(f"empty {c} for {bad}")

    dupes = sorted(df.filter(pl.col("symbol").is_duplicated() & pl.col("symbol").is_not_null())["symbol"].unique())
    if dupes:
        problems.append(f"duplicated symbols {dupes}")

    bad = rows_where(pl.col("asset_class").is_not_null() & ~pl.col("asset_class").is_in(ASSET_CLASSES))
    if bad:
        problems.append(f"unknown asset_class for {bad} (allowed: {', '.join(ASSET_CLASSES)})")

    for c in _POSITIVE:
        col = pl.col(c)
        bad = rows_where(col.is_null() | col.is_nan() | col.is_infinite() | (col <= 0))
        if bad:
            problems.append(f"{c} must be a finite number > 0 for {bad}")

    bad = rows_where(pl.col("break_start").is_null() != pl.col("break_end").is_null())
    if bad:
        problems.append(f"break_start and break_end must be both set or both null for {bad}")
    for c in ("break_start", "break_end"):
        bad = rows_where(pl.col(c).is_not_null() & ~pl.col(c).str.contains(_HHMM.pattern))
        if bad:
            problems.append(f"{c} must be HH:MM for {bad}")

    bad = rows_where(pl.col("updated_at").is_null())
    if bad:
        problems.append(f"updated_at is null for {bad}")

    if problems:
        raise InstrumentsError("reference/instruments: " + "; ".join(problems))


def upsert_instruments(df: pl.DataFrame) -> None:
    """Validate, then merge on symbol (update existing, insert new); create the table on first write."""
    validate_instruments(df)
    data = df.select(list(SCHEMA)).to_arrow()
    path = table_path()
    if DeltaTable.is_deltatable(path):
        (
            DeltaTable(path)
            .merge(data, predicate="t.symbol = s.symbol", source_alias="s", target_alias="t")
            .when_matched_update_all()
            .when_not_matched_insert_all()
            .execute()
        )
    else:
        write_deltalake(path, data, mode="overwrite")


def read_instruments(version: int | None = None) -> pl.DataFrame:
    """The whole table (or the given Delta version), columns in SCHEMA order, sorted by symbol."""
    path = table_path()
    if not DeltaTable.is_deltatable(path):
        raise FileNotFoundError(f"No Delta table at {path}: run seed_default() or upsert_instruments() first")
    df = pl.from_arrow(DeltaTable(path, version=version).to_pyarrow_table())
    return df.select(list(SCHEMA)).sort("symbol")


def seed_default() -> pl.DataFrame:
    """Write DEFAULT_INSTRUMENTS (idempotent) and return the table."""
    upsert_instruments(instruments_frame(DEFAULT_INSTRUMENTS))
    return read_instruments()
