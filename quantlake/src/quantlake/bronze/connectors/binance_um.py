"""Binance USDⓈ-M futures (perpetuals): OHLCV and funding rate.

OHLCV reuses the spot connectors with the futures endpoints:
  - REST  /fapi/v1/klines (same kline arrays as spot, up to 1500 per call)
  - bulk  data.binance.vision/data/futures/um/monthly/klines (CSV with a
          header row, handled by parse_kline_zip)
Both write bronze/binance_um_ohlcv; `symbol` is the exchange symbol
("BTCUSDT"), the table name tells it is the perpetual.

Funding: REST /fapi/v1/fundingRate, full history paginated by startTime
(up to 1000 rows per call, one row per settlement: every 8 h for BTCUSDT).
Columns returned: timestamp (fundingTime, UTC, as published: it can be a
few ms past the settlement), funding_rate, mark_price (null when Binance
has none, e.g. the oldest rows).
"""
import time
from datetime import datetime

import httpx
import polars as pl

from quantlake.bronze.base import HistoricalConnector
from quantlake.bronze.connectors.binance_spot_bulk import BinanceSpotOHLCVBulkConnector
from quantlake.bronze.connectors.binance_spot_rest import BinanceSpotOHLCVRestConnector
from quantlake.helper import to_utc


class BinanceUMOHLCVRestConnector(BinanceSpotOHLCVRestConnector):
    TABLE_NAME = "binance_um_ohlcv"
    _BASE_URL = "https://fapi.binance.com/fapi/v1/klines"
    _LIMIT = 1500


class BinanceUMOHLCVBulkConnector(BinanceSpotOHLCVBulkConnector):
    TABLE_NAME = "binance_um_ohlcv"
    _BASE_URL = "https://data.binance.vision/data/futures/um/monthly/klines"


FUNDING_SCHEMA = {
    "timestamp":    pl.Datetime("us", "UTC"),
    "funding_rate": pl.Float64,
    "mark_price":   pl.Float64,
}


class BinanceUMFundingRateConnector(HistoricalConnector):
    TABLE_NAME = "binance_um_funding"
    _BASE_URL = "https://fapi.binance.com/fapi/v1/fundingRate"
    _LIMIT = 1000

    def __init__(self, pause_s: float = 0.2):
        self.pause_s = pause_s

    def fetch(self, symbol: str, start: datetime, end: datetime) -> pl.DataFrame:
        start_ms = int(to_utc(start).timestamp() * 1000)
        end_ms = int(to_utc(end).timestamp() * 1000)
        rows: list[dict] = []
        with httpx.Client(timeout=30) as client:
            current = start_ms
            while current <= end_ms:
                resp = client.get(self._BASE_URL, params={
                    "symbol": symbol, "startTime": current, "endTime": end_ms, "limit": self._LIMIT,
                })
                resp.raise_for_status()
                batch = resp.json()
                if not batch:
                    break
                rows.extend(batch)
                if len(batch) < self._LIMIT:
                    break
                current = batch[-1]["fundingTime"] + 1
                time.sleep(self.pause_s)
        return parse_funding(rows)


def parse_funding(rows: list[dict]) -> pl.DataFrame:
    if not rows:
        return pl.DataFrame(schema=FUNDING_SCHEMA)
    return (
        pl.DataFrame({
            "timestamp":    [r["fundingTime"] for r in rows],
            "funding_rate": [r["fundingRate"] for r in rows],
            "mark_price":   [r.get("markPrice") or None for r in rows],
        }, schema={"timestamp": pl.Int64, "funding_rate": pl.String, "mark_price": pl.String})
        .with_columns(
            pl.from_epoch("timestamp", time_unit="ms").dt.replace_time_zone("UTC").cast(pl.Datetime("us", "UTC")),
            pl.col("funding_rate").cast(pl.Float64),
            pl.col("mark_price").cast(pl.Float64),
        )
        .unique(subset=["timestamp"], keep="last")
        .sort("timestamp")
    )
