"""Read-only loader for quantlake gold bars.

Reads gold/<gold_table>/<timeframe> for one instrument, checks the schema,
records the Delta version read (so a run can be repeated exactly with
version=...) and reports data quality without dropping anything.

Convention inherited from quantlake: 'timestamp' is the bar open, in UTC.
"""
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import polars as pl
from deltalake import DeltaTable

from alphaquant.config import QUANTLAKE_DATA_ROOT
from alphaquant.data.schema import SchemaError, require_columns, require_utc_datetime
from alphaquant.instruments.instrument import Instrument

PRICE_COLUMNS = ("open", "high", "low", "close")
PARTITION_COLUMNS = ("year", "month")
_MISSING_SAMPLE = 10

_TF_PATTERN = re.compile(r"^(\d+)(m|h|d)$")
_TF_UNITS = {"m": "minutes", "h": "hours", "d": "days"}


def parse_timeframe(timeframe: str) -> timedelta:
    """'1m', '15m', '4h', '1d' -> timedelta (same names as quantlake's gold tables)."""
    match = _TF_PATTERN.match(timeframe)
    if match is None:
        raise ValueError(f"Invalid timeframe {timeframe!r}: expected e.g. '1m', '15m', '4h', '1d'")
    return timedelta(**{_TF_UNITS[match.group(2)]: int(match.group(1))})


@dataclass(frozen=True)
class QualityReport:
    rows: int
    start: datetime
    end: datetime
    nan_price_rows: int                 # rows with a NaN in open/high/low/close (quantlake marks bad bars so)
    missing_bars: int | None            # expected bars (market open) not in the table; None for >= 1d
    missing_sample: tuple[datetime, ...]

    @property
    def clean(self) -> bool:
        return self.nan_price_rows == 0 and not self.missing_bars

    def summary(self) -> str:
        missing = "n/a" if self.missing_bars is None else str(self.missing_bars)
        return (
            f"{self.rows} bars {self.start:%Y-%m-%d %H:%M} -> {self.end:%Y-%m-%d %H:%M} UTC, "
            f"NaN rows: {self.nan_price_rows}, missing bars: {missing}"
        )


@dataclass(frozen=True)
class Bars:
    df: pl.DataFrame
    instrument: Instrument
    timeframe: str
    table_path: str
    delta_version: int
    quality: QualityReport


def load_bars(
    instrument: Instrument,
    timeframe: str,
    start: datetime | None = None,
    end: datetime | None = None,
    version: int | None = None,
    data_root: Path = QUANTLAKE_DATA_ROOT,
) -> Bars:
    """Load gold bars for an instrument in [start, end) (UTC; naive datetimes are taken as UTC)."""
    step = parse_timeframe(timeframe)
    path = Path(data_root) / "gold" / instrument.data.gold_table / timeframe
    table_name = f"gold/{instrument.data.gold_table}/{timeframe}"
    if not DeltaTable.is_deltatable(str(path)):
        raise FileNotFoundError(
            f"No Delta table at {path}: build {table_name} in quantlake (gold.ingest) "
            "or check QUANTLAKE_DATA_ROOT"
        )

    delta_version = DeltaTable(str(path), version=version).version()
    lf = pl.scan_delta(str(path), version=delta_version)

    schema = lf.collect_schema()
    require_utc_datetime(schema, "timestamp", table_name)
    require_columns(schema, {"symbol": pl.String(), **{c: pl.Float64() for c in PRICE_COLUMNS}}, table_name)

    lf = lf.filter(pl.col("symbol") == instrument.data.symbol)
    if start is not None:
        start = _to_utc(start)
        lf = lf.filter(pl.col("timestamp") >= start)
        if "year" in schema:
            lf = lf.filter(pl.col("year") >= start.year)  # partition pruning
    if end is not None:
        end = _to_utc(end)
        lf = lf.filter(pl.col("timestamp") < end)
        if "year" in schema:
            lf = lf.filter(pl.col("year") <= end.year)

    df = (
        lf.drop([c for c in PARTITION_COLUMNS if c in schema])
        .with_columns(pl.col("timestamp").cast(pl.Datetime("us", "UTC")))
        .sort("timestamp")
        .collect()
    )
    if df.is_empty():
        raise ValueError(
            f"{table_name}: no rows for symbol '{instrument.data.symbol}' in the requested range"
        )

    duplicated = df.filter(pl.col("timestamp").is_duplicated())["timestamp"]
    if len(duplicated) > 0:
        raise SchemaError(f"{table_name}: {duplicated.n_unique()} duplicated timestamps, first {duplicated.min()}")

    return Bars(
        df=df,
        instrument=instrument,
        timeframe=timeframe,
        table_path=str(path),
        delta_version=delta_version,
        quality=_quality(df, instrument, step),
    )


def _quality(df: pl.DataFrame, instrument: Instrument, step: timedelta) -> QualityReport:
    ts = df["timestamp"]
    nan_rows = df.select(
        pl.any_horizontal([pl.col(c).is_nan() | pl.col(c).is_null() for c in PRICE_COLUMNS]).sum()
    ).item()

    missing_bars, sample = None, ()
    if step < timedelta(days=1):
        # Expected grid = every step between first and last bar when the market is open
        grid = pl.datetime_range(ts.min(), ts.max(), interval=step, time_zone="UTC", eager=True).alias("timestamp")
        expected = grid.filter(instrument.session.open_mask(grid))
        missing = expected.to_frame().join(df.select("timestamp"), on="timestamp", how="anti")["timestamp"]
        missing_bars = len(missing)
        sample = tuple(missing.head(_MISSING_SAMPLE).to_list())

    return QualityReport(
        rows=len(df),
        start=ts.min(),
        end=ts.max(),
        nan_price_rows=nan_rows,
        missing_bars=missing_bars,
        missing_sample=sample,
    )


def _to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
