"""Nasdaq.com public API: daily OHLC history of cash indices (NDX).

    https://api.nasdaq.com/api/quote/{SYMBOL}/historical?assetclass=index

Free, no key, needs a browser User-Agent. History starts ~10 years back.
Used for the *real* index level: the MultiCharts @ES / @NQ continuous
contracts are back-adjusted (2016 ES sits ~800 points above SPX), so
percentage measures (Expected Move = level x IV) need the cash index.

Each row is stamped at 16:15 US Eastern like CBOEIndexDailyConnector, so a
daily value is never visible before the close that produced it.
"""
from datetime import datetime

import httpx
import polars as pl

from quantlake.bronze.base import HistoricalConnector
from quantlake.helper import to_utc

_URL = "https://api.nasdaq.com/api/quote/{symbol}/historical"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36",
    "Accept": "application/json",
}


class NasdaqIndexDailyConnector(HistoricalConnector):
    """Daily OHLC of a cash index. symbol = 'NDX' (SPX is not served)."""

    TABLE_NAME = "nasdaq_index_daily"
    SETTLE_TIME_ET = "16:15"

    def fetch(self, symbol: str, start: datetime, end: datetime) -> pl.DataFrame:
        params = {
            "assetclass": "index",
            "fromdate": start.strftime("%Y-%m-%d"),
            "todate": end.strftime("%Y-%m-%d"),
            "limit": 9999,
        }
        with httpx.Client(timeout=60, headers=_HEADERS, follow_redirects=True) as client:
            resp = client.get(_URL.format(symbol=symbol), params=params)
            resp.raise_for_status()
        rows = ((resp.json().get("data") or {}).get("tradesTable") or {}).get("rows") or []
        if not rows:
            return pl.DataFrame()
        df = pl.DataFrame(rows).select("date", "open", "high", "low", "close")
        return df.select(
            (pl.col("date") + f" {self.SETTLE_TIME_ET}")
            .str.to_datetime(format="%m/%d/%Y %H:%M", time_zone="America/New_York")
            .dt.convert_time_zone("UTC")
            .cast(pl.Datetime("us", "UTC"))
            .alias("timestamp"),
            *[pl.col(c).str.replace_all(",", "").cast(pl.Float64, strict=False) for c in ("open", "high", "low", "close")],
        ).filter(
            (pl.col("timestamp") >= to_utc(start)) & (pl.col("timestamp") <= to_utc(end))
            & (pl.col("open") > 0)  # holidays come back as 0/0/0 + the previous close
        ).unique("timestamp").sort("timestamp")
