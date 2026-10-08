"""MultiCharts CSV export (ExportBars indicator) as a bronze source.

The PowerLanguage indicator ExportBars writes one line per closed bar:
    date,time,open,high,low,close,volume,ticks,upticks,downticks
with date = YYYYMMDD and time = HHMM of the bar *close*, in the
chart's time zone. MultiCharts runs on a separate Windows PC: the
indicator writes into this project's data/multicharts folder shared from
the Mac over SMB (or the CSV is copied here by hand).

Quantlake convention: `timestamp` is the bar *open* (UTC), plus
`timestamp_close`. On intraday bars MultiCharts' `Volume` is the up-tick
volume only and `Ticks` is the total, so `volume` is rebuilt here as
upticks + downticks. upticks/downticks give an approximate delta
(volume traded on up-ticks vs down-ticks), not the true aggressor side.
"""
from datetime import datetime, timedelta
from pathlib import Path

import polars as pl

from quantlake.bronze.base import HistoricalConnector
from quantlake.config import DATA_ROOT
from quantlake.helper import to_utc

MC_DIR = DATA_ROOT / "multicharts"


class MultiChartsCSVConnector(HistoricalConnector):
    """symbol = file stem in data/multicharts/, e.g. 'ES_1min' -> ES_1min.csv."""

    TABLE_NAME = "multicharts_ohlcv"

    def __init__(self, chart_tz: str = "America/Chicago", bar_minutes: int = 1, folder: Path = MC_DIR):
        self.chart_tz = chart_tz
        self.bar = timedelta(minutes=bar_minutes)
        self.folder = Path(folder)

    def fetch(self, symbol: str, start: datetime | None = None, end: datetime | None = None) -> pl.DataFrame:
        path = self.folder / f"{symbol}.csv"
        raw = pl.read_csv(path, infer_schema_length=0)
        raw = raw.rename({c: c.strip().lower() for c in raw.columns})
        df = raw.select(
            (pl.col("date") + pl.col("time").str.zfill(4))
            .str.to_datetime(format="%Y%m%d%H%M", time_zone=self.chart_tz, ambiguous="earliest")
            .dt.convert_time_zone("UTC")
            .cast(pl.Datetime("us", "UTC"))
            .alias("timestamp_close"),
            *[pl.col(c).cast(pl.Float64) for c in ("open", "high", "low", "close")],
            *[pl.col(c).cast(pl.Float64) for c in ("volume", "ticks", "upticks", "downticks") if c in raw.columns],
        ).with_columns(
            (pl.col("timestamp_close") - self.bar).alias("timestamp"),
        )
        if {"upticks", "downticks"} <= set(df.columns):
            df = df.with_columns((pl.col("upticks") + pl.col("downticks")).alias("volume"))
        df = df.unique(subset=["timestamp"], keep="last").sort("timestamp")
        if start is not None:
            df = df.filter(pl.col("timestamp") >= to_utc(start))
        if end is not None:
            df = df.filter(pl.col("timestamp") <= to_utc(end))
        return df.select("timestamp", "timestamp_close", *[c for c in df.columns if c not in ("timestamp", "timestamp_close")])
