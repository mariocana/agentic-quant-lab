"""Hyperliquid perpetuals, main dex and HIP-3: OHLCV and hourly funding.

What the API keeps, measured on 09/11/2026:

  candles 1d   the whole life of every perp, delisted ones included: MATIC runs
               2020-10-22 -> 2024-09-09, its last bar is the delisting. So the
               daily table gives a historical listing and delisting date for
               every asset, which no other endpoint does.
  candles 1h   only the latest ~5000 bars (about seven months). Older ones are
               gone: asking for January 2024 returns nothing. The intraday
               table is therefore built forward, and the ingest must run at
               least every few months or a hole opens that cannot be filled.
  funding      hourly, from 2023-05-12 (the start of Hyperliquid's history),
               500 rows per call.

`symbol` is the API coin: "BTC" on the main dex, "xyz:TSLA" on a HIP-3 dex.
One table per interval, because a 1h and a 1d bar both open at 00:00 and the
merge key is (symbol, timestamp).

The bar still open is never stored: its close is a price nobody could have
known at the bar's close time.
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

import httpx
import polars as pl

from quantlake.bronze.base import HistoricalConnector
from quantlake.helper import to_utc

API = "https://api.hyperliquid.xyz/info"
FUNDING_START = datetime(2023, 5, 12, tzinfo=timezone.utc)
_INTERVAL_MS = {"1h": 3_600_000, "4h": 14_400_000, "1d": 86_400_000}

OHLCV_SCHEMA = {
    "timestamp": pl.Datetime("us", "UTC"), "timestamp_close": pl.Datetime("us", "UTC"),
    "open": pl.Float64, "high": pl.Float64, "low": pl.Float64, "close": pl.Float64,
    "volume": pl.Float64, "trades": pl.Int64,
}
FUNDING_SCHEMA = {"timestamp": pl.Datetime("us", "UTC"), "funding_rate": pl.Float64, "premium": pl.Float64}


class _Client:
    """Info endpoint with a pause between calls. Hyperliquid allows ~1200 weight a
    minute per IP and a history call weighs 20 or more: about one call a second."""

    def __init__(self, pause_s: float = 1.2, client: httpx.Client | None = None):
        self.pause_s, self.client, self._last = pause_s, client or httpx.Client(timeout=30), 0.0

    def post(self, body: dict):
        wait = self.pause_s - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        for attempt in range(4):
            self._last = time.monotonic()
            r = self.client.post(API, json=body)
            if r.status_code == 429 or r.status_code >= 500:
                time.sleep(2 ** attempt * 5)
                continue
            r.raise_for_status()
            return r.json()
        r.raise_for_status()


def _ts(col: str) -> pl.Expr:
    return pl.from_epoch(col, time_unit="ms").dt.replace_time_zone("UTC").cast(pl.Datetime("us", "UTC"))


def parse_candles(rows: list[dict], now: datetime) -> pl.DataFrame:
    """Closed bars only: a bar whose close time is after `now` is still moving."""
    if not rows:
        return pl.DataFrame(schema=OHLCV_SCHEMA)
    now_ms = int(to_utc(now).timestamp() * 1000)
    rows = [r for r in rows if r["T"] < now_ms]
    if not rows:
        return pl.DataFrame(schema=OHLCV_SCHEMA)
    return (
        pl.DataFrame({
            "timestamp": [r["t"] for r in rows], "timestamp_close": [r["T"] for r in rows],
            "open": [float(r["o"]) for r in rows], "high": [float(r["h"]) for r in rows],
            "low": [float(r["l"]) for r in rows], "close": [float(r["c"]) for r in rows],
            "volume": [float(r["v"]) for r in rows], "trades": [int(r["n"]) for r in rows],
        })
        .with_columns(_ts("timestamp"), _ts("timestamp_close"))
        .unique(subset=["timestamp"], keep="last").sort("timestamp")
        .cast(OHLCV_SCHEMA)
    )


def parse_funding(rows: list[dict]) -> pl.DataFrame:
    if not rows:
        return pl.DataFrame(schema=FUNDING_SCHEMA)
    return (
        pl.DataFrame({
            "timestamp": [r["time"] for r in rows],
            "funding_rate": [float(r["fundingRate"]) for r in rows],
            "premium": [float(r["premium"]) if r.get("premium") is not None else None for r in rows],
        })
        .with_columns(_ts("timestamp"))
        .unique(subset=["timestamp"], keep="last").sort("timestamp")
        .cast(FUNDING_SCHEMA)
    )


class HyperliquidOHLCVConnector(HistoricalConnector):
    def __init__(self, interval: str = "1d", client: _Client | None = None):
        if interval not in _INTERVAL_MS:
            raise ValueError(f"interval {interval!r} not in {sorted(_INTERVAL_MS)}")
        self.interval, self.api = interval, client or _Client()
        self.TABLE_NAME = f"hyperliquid_ohlcv_{interval}"

    def fetch(self, symbol: str, start: datetime, end: datetime) -> pl.DataFrame:
        """At most ~5000 bars come back per call, the latest ones in the window,
        so the window is walked forward until it is exhausted."""
        start_ms, end_ms = int(to_utc(start).timestamp() * 1000), int(to_utc(end).timestamp() * 1000)
        rows: list[dict] = []
        while start_ms <= end_ms:
            batch = self.api.post({"type": "candleSnapshot", "req": {
                "coin": symbol, "interval": self.interval, "startTime": start_ms, "endTime": end_ms}})
            if not batch:
                break
            rows.extend(batch)
            nxt = batch[-1]["t"] + _INTERVAL_MS[self.interval]
            if nxt <= start_ms or len(batch) < 4000:
                break
            start_ms = nxt
        return parse_candles(rows, now=end)


class HyperliquidFundingConnector(HistoricalConnector):
    TABLE_NAME = "hyperliquid_funding"
    _PAGE = 500

    def __init__(self, client: _Client | None = None):
        self.api = client or _Client()

    def fetch(self, symbol: str, start: datetime, end: datetime) -> pl.DataFrame:
        start_ms = int(to_utc(max(start, FUNDING_START)).timestamp() * 1000)
        end_ms = int(to_utc(end).timestamp() * 1000)
        rows: list[dict] = []
        while start_ms <= end_ms:
            batch = self.api.post({"type": "fundingHistory", "coin": symbol,
                                   "startTime": start_ms, "endTime": end_ms})
            if not batch:
                break
            rows.extend(batch)
            if len(batch) < self._PAGE:
                break
            start_ms = batch[-1]["time"] + 1
        return parse_funding(rows)


def universe(client: _Client | None = None) -> list[dict]:
    """Every perp on every dex, delisted ones included: {symbol, dex, is_delisted}."""
    api = client or _Client(pause_s=0.2)
    out = []
    meta = api.post({"type": "meta"})
    out += [{"symbol": u["name"], "dex": "main", "is_delisted": bool(u.get("isDelisted"))}
            for u in meta["universe"]]
    for d in api.post({"type": "perpDexs"}):
        if not d:
            continue
        m = api.post({"type": "meta", "dex": d["name"]})
        out += [{"symbol": u["name"], "dex": d["name"], "is_delisted": bool(u.get("isDelisted"))}
                for u in m["universe"]]
    return out


LISTINGS_SCHEMA = {
    "symbol": pl.String, "dex": pl.String, "is_delisted": pl.Boolean,
    "first_bar": pl.Date, "last_bar": pl.Date, "delisted_after": pl.Date,
}


def listings(daily_first_last: pl.DataFrame, uni: list[dict]) -> pl.DataFrame:
    """When each perp traded: first and last daily bar, and for a delisted one the
    last day it traded. `daily_first_last` has symbol, first_bar, last_bar.

    The first daily bar is the listing as far as prices can tell. The last bar of
    a delisted perp is the day it stopped: this is what keeps a backtest from
    choosing, on a past date, among assets that were not yet listed or had
    already died. A perp with no bars at all (listed and delisted before
    trading, common on HIP-3 dexs) keeps null dates and is never in a universe.
    """
    u = pl.DataFrame(uni, schema={"symbol": pl.String, "dex": pl.String, "is_delisted": pl.Boolean})
    return (
        u.join(daily_first_last, on="symbol", how="left")
        .with_columns(pl.when(pl.col("is_delisted")).then(pl.col("last_bar")).alias("delisted_after"))
        .select(list(LISTINGS_SCHEMA))
        .cast(LISTINGS_SCHEMA)
        .sort("dex", "symbol")
    )


def universe_on(listings_df: pl.DataFrame, day) -> list[str]:
    """The perps that were trading on `day`, as known from the bars: listed on or
    before it, and if delisted, not before it."""
    return (
        listings_df.filter(
            pl.col("first_bar").is_not_null()
            & (pl.col("first_bar") <= day)
            & (pl.col("delisted_after").is_null() | (pl.col("delisted_after") >= day))
        )["symbol"].sort().to_list()
    )


def funding_end(now: datetime, is_delisted: bool, last_daily_bar: datetime | None) -> datetime | None:
    """Where to stop asking for funding. After a delisting the API keeps answering
    with a zero rate every hour, for years: MATIC, delisted 2024-09-09, came back
    with 30,098 rows running to today. Those zeros are not funding, they are the
    absence of a market, and a carry backtest would read them as free holding.
    A delisted perp stops the day after its last bar; one that never traded has
    no funding at all (None)."""
    if not is_delisted:
        return now
    if last_daily_bar is None:
        return None
    return min(now, last_daily_bar + timedelta(days=1))
