"""Read-only loader for quantlake gold bars.

Reads gold/<gold_table>/<timeframe> for one instrument, checks the schema,
records the Delta version read (so a run can be repeated exactly with
version=...) and reports data quality without dropping anything.

Convention inherited from quantlake: 'timestamp' is the bar open, in UTC.

Timeframes are UTC-aligned ('15m', '1d'), or anchored to the CME trading day
with a '_cme' suffix ('1d_cme': one bar per Globex session, opening 17:00
America/Chicago). quantlake writes '_cme' tables for CME futures only.
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
from alphaquant.instruments.sessions import ExchangeSession

PRICE_COLUMNS = ("open", "high", "low", "close")
PARTITION_COLUMNS = ("year", "month")
_MISSING_SAMPLE = 10

_TF_PATTERN = re.compile(r"^(\d+)(m|h|d)(_cme)?$")
CME_CALENDAR = "CMES"
_TF_UNITS = {"m": "minutes", "h": "hours", "d": "days"}


def parse_timeframe(timeframe: str) -> timedelta:
    """'1m', '15m', '4h', '1d', '1d_cme' -> nominal bar length (same names as quantlake's gold tables).

    A '_cme' bar is anchored to the CME session: '1d_cme' lasts 23 or 25 hours
    on DST changes, so the nominal length is not a fixed step between bars.
    """
    match = _TF_PATTERN.match(timeframe)
    if match is None:
        raise ValueError(f"Invalid timeframe {timeframe!r}: expected e.g. '1m', '15m', '4h', '1d', '1d_cme'")
    return timedelta(**{_TF_UNITS[match.group(2)]: int(match.group(1))})


def is_session_anchored(timeframe: str) -> bool:
    match = _TF_PATTERN.match(timeframe)
    return match is not None and match.group(3) is not None


@dataclass(frozen=True)
class QualityReport:
    rows: int
    start: datetime
    end: datetime
    nan_price_rows: int                 # rows with a NaN in open/high/low/close (quantlake marks bad bars so)
    missing_bars: int | None            # expected bars (market open) not in the table; None if not checked
    missing_sample: tuple[datetime, ...]
    off_calendar_bars: int = 0          # '1d_cme' bars on days the calendar has closed (e.g. Good Friday short sessions)

    @property
    def clean(self) -> bool:
        return self.nan_price_rows == 0 and not self.missing_bars

    def summary(self) -> str:
        missing = "n/a" if self.missing_bars is None else str(self.missing_bars)
        text = (
            f"{self.rows} bars {self.start:%Y-%m-%d %H:%M} -> {self.end:%Y-%m-%d %H:%M} UTC, "
            f"NaN rows: {self.nan_price_rows}, missing bars: {missing}"
        )
        if self.off_calendar_bars:
            text += f", off-calendar bars: {self.off_calendar_bars}"
        return text


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
    anchored = is_session_anchored(timeframe)
    if anchored and not (isinstance(instrument.session, ExchangeSession) and instrument.session.calendar == CME_CALENDAR):
        raise ValueError(f"{instrument.symbol}: timeframe {timeframe!r} is anchored to the CME session, "
                         f"but the instrument trades on calendar {instrument.session.name!r}")
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
        quality=_quality(df, instrument, step, anchored),
    )


def _quality(df: pl.DataFrame, instrument: Instrument, step: timedelta, anchored: bool) -> QualityReport:
    ts = df["timestamp"]
    nan_rows = df.select(
        pl.any_horizontal([pl.col(c).is_nan() | pl.col(c).is_null() for c in PRICE_COLUMNS]).sum()
    ).item()

    missing_bars, sample, off_calendar = None, (), 0
    if anchored and step == timedelta(days=1):
        # One bar per session, keyed by the session open. Bars the calendar does not know
        # (short sessions CME opens on days exchange_calendars marks closed) are kept and counted.
        expected = instrument.session.session_opens(ts.min(), ts.max()).to_frame()
        missing = expected.join(df.select("timestamp"), on="timestamp", how="anti")["timestamp"]
        missing_bars = len(missing)
        sample = tuple(missing.head(_MISSING_SAMPLE).to_list())
        off_calendar = df.select("timestamp").join(expected, on="timestamp", how="anti").height
    elif not anchored and step < timedelta(days=1):
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
        off_calendar_bars=off_calendar,
    )


def _to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
