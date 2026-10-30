"""Nasdaq.com public API: earnings calendar, EPS surprises, stock daily prices.

Free, no key, needs a browser User-Agent (same API as connectors/nasdaq.py).

NasdaqEarningsCalendarConnector   TABLE nasdaq_earnings_calendar
    /api/calendar/earnings?date=YYYY-MM-DD, one row per company reporting
    that day: time (bmo / amc / na), EPS consensus and number of estimates,
    and, once reported, actual EPS and % surprise. `timestamp` is the report
    date at 00:00 New York (stable key: the time of day can still change
    before the report). Re-fetching a past day fills in the actual EPS, so
    the loader merges with update_matched=True.

NasdaqEarningsSurpriseConnector   TABLE nasdaq_earnings_surprise
    /api/company/{SYMBOL}/earnings-surprise: last 4 reported quarters
    (actual EPS, consensus, % surprise). `timestamp` = date reported, 00:00 NY.

NasdaqStockDailyConnector         TABLE nasdaq_stock_daily
    /api/quote/{SYMBOL}/historical?assetclass=stocks: daily OHLCV, stamped
    16:15 New York like the index connector (no look-ahead on the close).

Not available for free here: consensus revenue estimates.
"""
import time as _time
from datetime import date, datetime

import httpx
import polars as pl

from quantlake.bronze.base import HistoricalConnector
from quantlake.helper import to_utc

_BASE = "https://api.nasdaq.com/api"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36",
    "Accept": "application/json",
}
_TIME = {"time-pre-market": "bmo", "time-after-hours": "amc"}
NY = "America/New_York"


def _get(path: str, params: dict | None = None, retries: int = 3) -> dict:
    for attempt in range(retries):
        try:
            with httpx.Client(timeout=30, headers=_HEADERS, follow_redirects=True) as client:
                r = client.get(f"{_BASE}/{path}", params=params)
                r.raise_for_status()
                return r.json().get("data") or {}
        except (httpx.HTTPError, ValueError):
            if attempt == retries - 1:
                raise
            _time.sleep(1.5 * (attempt + 1))
    return {}


def _money(col: str) -> pl.Expr:
    """'$1,234.5' / '($0.12)' / 'N/A' -> float."""
    s = pl.col(col).cast(pl.String).str.replace_all(r"[$,\s]", "")
    neg = s.str.starts_with("(")
    v = s.str.replace_all(r"[()]", "").cast(pl.Float64, strict=False)
    return pl.when(neg).then(-v).otherwise(v).alias(col)


def _ny_midnight(col: str, fmt: str) -> pl.Expr:
    return (pl.col(col).str.to_datetime(fmt, time_zone=NY, strict=False)
            .dt.convert_time_zone("UTC").cast(pl.Datetime("us", "UTC")).alias("timestamp"))


class NasdaqEarningsCalendarConnector(HistoricalConnector):
    """symbol is ignored: one call returns every company reporting on `start`."""

    TABLE_NAME = "nasdaq_earnings_calendar"

    def fetch_day(self, day: date) -> pl.DataFrame:
        rows = _get("calendar/earnings", {"date": day.isoformat()}).get("rows") or []
        if not rows:
            return pl.DataFrame()
        df = pl.DataFrame(rows, infer_schema_length=None)
        for c in ("eps", "surprise", "lastYearEPS", "lastYearRptDt"):
            if c not in df.columns:
                df = df.with_columns(pl.lit(None, pl.String).alias(c))
        return df.select(
            pl.lit(day.isoformat()).str.to_datetime("%Y-%m-%d", time_zone=NY)
              .dt.convert_time_zone("UTC").cast(pl.Datetime("us", "UTC")).alias("timestamp"),
            pl.col("symbol").str.strip_chars().str.to_uppercase(),
            pl.col("name").str.strip_chars(),
            pl.col("time").replace_strict(_TIME, default="na").alias("time"),
            _money("eps").alias("eps"),
            _money("epsForecast").alias("eps_forecast"),
            pl.col("surprise").cast(pl.Float64, strict=False).alias("surprise_pct"),
            pl.col("noOfEsts").cast(pl.Int32, strict=False).alias("n_estimates"),
            _money("marketCap").alias("market_cap"),
            pl.col("fiscalQuarterEnding").alias("fiscal_quarter"),
            _money("lastYearEPS").alias("last_year_eps"),
        ).filter(pl.col("symbol").str.len_chars() > 0).unique("symbol", keep="first")

    def fetch(self, symbol: str, start: datetime, end: datetime) -> pl.DataFrame:
        return self.fetch_day(start.date())


class NasdaqEarningsSurpriseConnector(HistoricalConnector):
    TABLE_NAME = "nasdaq_earnings_surprise"

    def fetch(self, symbol: str, start: datetime | None = None, end: datetime | None = None) -> pl.DataFrame:
        table = _get(f"company/{symbol}/earnings-surprise").get("earningsSurpriseTable") or {}
        rows = table.get("rows") or []
        if not rows:
            return pl.DataFrame()
        df = pl.DataFrame(rows, infer_schema_length=None).with_columns(pl.all().cast(pl.String))
        return df.select(
            _ny_midnight("dateReported", "%m/%d/%Y"),
            pl.col("fiscalQtrEnd").alias("fiscal_quarter"),
            pl.col("eps").cast(pl.Float64, strict=False).alias("eps"),
            pl.col("consensusForecast").cast(pl.Float64, strict=False).alias("eps_forecast"),
            pl.col("percentageSurprise").cast(pl.Float64, strict=False).alias("surprise_pct"),
        ).drop_nulls("timestamp").unique("timestamp").sort("timestamp")


class NasdaqStockDailyConnector(HistoricalConnector):
    TABLE_NAME = "nasdaq_stock_daily"
    SETTLE_TIME_ET = "16:15"

    def fetch(self, symbol: str, start: datetime, end: datetime) -> pl.DataFrame:
        params = {"assetclass": "stocks", "fromdate": start.strftime("%Y-%m-%d"),
                  "todate": end.strftime("%Y-%m-%d"), "limit": 9999}
        rows = ((_get(f"quote/{symbol}/historical", params).get("tradesTable") or {}).get("rows")) or []
        if not rows:
            return pl.DataFrame()
        df = pl.DataFrame(rows, infer_schema_length=None)
        return df.select(
            (pl.col("date") + f" {self.SETTLE_TIME_ET}")
            .str.to_datetime("%m/%d/%Y %H:%M", time_zone=NY)
            .dt.convert_time_zone("UTC").cast(pl.Datetime("us", "UTC")).alias("timestamp"),
            *[_money(c) for c in ("open", "high", "low", "close")],
            pl.col("volume").str.replace_all(",", "").cast(pl.Float64, strict=False).alias("volume"),
        ).filter(
            (pl.col("timestamp") >= to_utc(start)) & (pl.col("open") > 0)
        ).unique("timestamp").sort("timestamp")
