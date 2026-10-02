"""CBOE public data: volatility indices (daily) and SPX option chain snapshots.

Two connectors, same free CDN (cdn.cboe.com), which rejects requests
without a browser User-Agent.

CBOEIndexDailyConnector
    Daily OHLC history of CBOE indices (VIX, VIX9D, VIX1D, VIX3M...).
    One CSV per index: {BASE}/us_indices/daily_prices/{SYMBOL}_History.csv
    Each row is stamped at 16:15 US Eastern (index settlement, DST-aware)
    and converted to UTC, so a daily value is never visible before the
    close that produced it.

CBOEOptionChainConnector
    Snapshot of the full option chain of an index (SPX), 15-minute delayed:
    {BASE}/delayed_quotes/options/_{SYMBOL}.json
    The CDN only serves the current chain: history exists only for the
    snapshots we save. Every row of one snapshot shares the same
    timestamp (the moment we downloaded it, UTC). Expiries and strikes
    are filtered to keep the table small.
"""
import re
from datetime import datetime, timezone

import httpx
import polars as pl

from quantlake.bronze.base import HistoricalConnector
from quantlake.helper import to_utc

_BASE = "https://cdn.cboe.com/api/global"
_HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"}
_OPTION_RE = re.compile(r"^([A-Z]+)(\d{6})([CP])(\d{8})$")


def _get(url: str, timeout: float = 60) -> httpx.Response:
    with httpx.Client(timeout=timeout, headers=_HEADERS, follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return resp


class CBOEIndexDailyConnector(HistoricalConnector):
    """Daily OHLC of a CBOE index. symbol = 'VIX', 'VIX9D', 'VIX1D', 'VIX3M'."""

    TABLE_NAME = "cboe_index_daily"
    SETTLE_TIME_ET = "16:15"

    def fetch(self, symbol: str, start: datetime, end: datetime) -> pl.DataFrame:
        text = _get(f"{_BASE}/us_indices/daily_prices/{symbol}_History.csv").text
        df = pl.read_csv(text.encode(), infer_schema_length=0)
        df = df.rename({c: c.strip().lower() for c in df.columns})
        df = df.select(
            (pl.col("date") + f" {self.SETTLE_TIME_ET}")
            .str.to_datetime(format="%m/%d/%Y %H:%M", time_zone="America/New_York")
            .dt.convert_time_zone("UTC")
            .cast(pl.Datetime("us", "UTC"))
            .alias("timestamp"),
            *[pl.col(c).cast(pl.Float64) for c in ("open", "high", "low", "close")],
        )
        return df.filter(
            (pl.col("timestamp") >= to_utc(start)) & (pl.col("timestamp") <= to_utc(end))
        ).sort("timestamp")


class CBOEOptionChainConnector(HistoricalConnector):
    """Delayed option chain snapshot. symbol = 'SPX' (also 'NDX', 'RUT', 'XSP'...).

    start/end are ignored: the endpoint only serves the current chain.
    """

    TABLE_NAME = "cboe_option_chain"

    def __init__(self, max_dte: int = 90, strike_band: float = 0.20):
        self.max_dte = max_dte          # keep expiries within N calendar days
        self.strike_band = strike_band  # keep strikes within +-band of spot

    def fetch(self, symbol: str, start: datetime | None = None, end: datetime | None = None) -> pl.DataFrame:
        payload = _get(f"{_BASE}/delayed_quotes/options/_{symbol}.json").json()
        data = payload["data"]
        spot = float(data["current_price"])
        now = datetime.now(timezone.utc).replace(microsecond=0)

        rows = []
        for o in data["options"]:
            m = _OPTION_RE.match(o["option"])
            if not m:
                continue
            root, ymd, right, strike = m.groups()
            rows.append({
                "option": o["option"],
                "root": root,
                "expiry": datetime.strptime(ymd, "%y%m%d").date(),
                "right": right,
                "strike": int(strike) / 1000,
                **{k: _f(o.get(k)) for k in (
                    "bid", "ask", "iv", "open_interest", "volume",
                    "delta", "gamma", "vega", "theta", "last_trade_price", "prev_day_close",
                )},
            })
        if not rows:
            return pl.DataFrame()

        df = pl.DataFrame(rows)
        dte = (pl.col("expiry") - pl.lit(now.date())).dt.total_days()
        df = df.filter(
            (dte >= 0) & (dte <= self.max_dte)
            & (pl.col("strike") >= spot * (1 - self.strike_band))
            & (pl.col("strike") <= spot * (1 + self.strike_band))
        )
        return df.with_columns(
            pl.lit(now).cast(pl.Datetime("us", "UTC")).alias("timestamp"),
            pl.lit(spot).alias("spot"),
            pl.lit(str(payload.get("timestamp", ""))).alias("cboe_timestamp"),
        ).sort(["expiry", "strike", "right"])


def _f(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return float("nan")
