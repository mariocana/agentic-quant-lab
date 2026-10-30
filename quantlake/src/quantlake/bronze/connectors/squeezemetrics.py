"""SqueezeMetrics DIX / GEX daily history (free CSV, since 2011).

https://squeezemetrics.com/monitor/static/DIX.csv
Columns: date, price (SPX close), dix, gex (dollar gamma exposure).

The file is updated in the evening after the US close. Each row is
stamped at 18:00 US Eastern (DST-aware) and converted to UTC, so the
value is only available to the next session, as it would be live.
"""
from datetime import datetime

import httpx
import polars as pl

from quantlake.bronze.base import HistoricalConnector
from quantlake.helper import to_utc

_URL = "https://squeezemetrics.com/monitor/static/DIX.csv"


class SqueezeMetricsConnector(HistoricalConnector):

    TABLE_NAME = "squeezemetrics"
    PUBLISH_TIME_ET = "18:00"

    def fetch(self, symbol: str = "SPX", start: datetime | None = None, end: datetime | None = None) -> pl.DataFrame:
        with httpx.Client(timeout=60, follow_redirects=True) as client:
            resp = client.get(_URL)
            resp.raise_for_status()
        df = pl.read_csv(resp.content).select(
            (pl.col("date").cast(pl.Utf8) + f" {self.PUBLISH_TIME_ET}")
            .str.to_datetime(format="%Y-%m-%d %H:%M", time_zone="America/New_York")
            .dt.convert_time_zone("UTC")
            .cast(pl.Datetime("us", "UTC"))
            .alias("timestamp"),
            pl.col("price").cast(pl.Float64).alias("spx_close"),
            pl.col("dix").cast(pl.Float64),
            pl.col("gex").cast(pl.Float64),
        )
        if start is not None:
            df = df.filter(pl.col("timestamp") >= to_utc(start))
        if end is not None:
            df = df.filter(pl.col("timestamp") <= to_utc(end))
        return df.sort("timestamp")
