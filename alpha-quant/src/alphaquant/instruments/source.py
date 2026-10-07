"""InstrumentSource: builds Instrument objects.

QuantlakeInstrumentSource reads market specs from quantlake's
reference/instruments Delta table (read-only) and joins them with the cost
profile from config/costs.yaml. Expected table columns are in
REFERENCE_COLUMNS; quantlake owns and writes that table.
"""
from pathlib import Path
from typing import Protocol

import polars as pl
from deltalake import DeltaTable

from alphaquant.config import QUANTLAKE_DATA_ROOT
from alphaquant.data.schema import SchemaError, require_columns
from alphaquant.instruments.fees import Costs, load_costs
from alphaquant.instruments.instrument import AssetClass, DataRef, Instrument
from alphaquant.instruments.sessions import make_session

REFERENCE_TABLE = Path("reference") / "instruments"

REFERENCE_COLUMNS: dict[str, pl.DataType] = {
    "symbol": pl.String(),
    "asset_class": pl.String(),
    "exchange": pl.String(),
    "quote_ccy": pl.String(),
    "tick_size": pl.Float64(),
    "multiplier": pl.Float64(),
    "qty_step": pl.Float64(),
    "min_qty": pl.Float64(),
    "calendar": pl.String(),
    "break_start": pl.String(),
    "break_end": pl.String(),
    "gold_table": pl.String(),
    "data_symbol": pl.String(),
}


class InstrumentSource(Protocol):
    def symbols(self) -> list[str]: ...

    def get(self, symbol: str) -> Instrument: ...


class QuantlakeInstrumentSource:
    """Instruments from quantlake's reference/instruments table + alphaquant's cost profile."""

    def __init__(
        self,
        data_root: Path = QUANTLAKE_DATA_ROOT,
        costs: dict[str, Costs] | None = None,
        version: int | None = None,
    ):
        path = Path(data_root) / REFERENCE_TABLE
        self.table_path = str(path)
        if not DeltaTable.is_deltatable(self.table_path):
            raise FileNotFoundError(
                f"No Delta table at {path}: quantlake must create reference/instruments "
                "(check QUANTLAKE_DATA_ROOT)"
            )
        table = DeltaTable(self.table_path, version=version)
        self.version = table.version()

        df = pl.from_arrow(table.to_pyarrow_table())
        require_columns(df.schema, REFERENCE_COLUMNS, table="reference/instruments")
        duplicates = df.filter(pl.col("symbol").is_duplicated())["symbol"].unique().to_list()
        if duplicates:
            raise SchemaError(f"reference/instruments: duplicated symbols {sorted(duplicates)}")

        self._rows = {row["symbol"]: row for row in df.iter_rows(named=True)}
        self._costs = load_costs() if costs is None else costs

    def symbols(self) -> list[str]:
        return sorted(self._rows)

    def get(self, symbol: str) -> Instrument:
        row = self._rows.get(symbol)
        if row is None:
            raise KeyError(f"{symbol} is not in reference/instruments; available: {self.symbols()}")
        costs = self._costs.get(symbol)
        if costs is None:
            raise KeyError(f"No costs for {symbol}: add it to config/costs.yaml")

        return Instrument(
            symbol=symbol,
            asset_class=AssetClass(row["asset_class"]),
            exchange=row["exchange"],
            quote_ccy=row["quote_ccy"],
            tick_size=row["tick_size"],
            multiplier=row["multiplier"],
            qty_step=row["qty_step"],
            min_qty=row["min_qty"],
            session=make_session(row["calendar"], row["break_start"], row["break_end"]),
            data=DataRef(gold_table=row["gold_table"], symbol=row["data_symbol"]),
            costs=costs,
        )
