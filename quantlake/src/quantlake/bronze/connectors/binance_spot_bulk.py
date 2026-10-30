import io
import zipfile
from datetime import datetime

import httpx
import polars as pl

from quantlake.bronze.base import HistoricalConnector
from quantlake.helper import empty_ohlcv_df, to_utc


class BinanceSpotOHLCVBulkConnector(HistoricalConnector):
    """Fetches spot OHLCV from Binance public S3 bucket (no API key, no rate limit).

    Downloads monthly ZIP files and returns a single concatenated DataFrame.
    Columns returned: timestamp, open, high, low, close, volume
    """

    TABLE_NAME = "binance_spot_ohlcv"
    _BASE_URL = "https://data.binance.vision/data/spot/monthly/klines"

    def __init__(self, timeframe: str = "1m"):
        self.timeframe = timeframe

    def fetch(self, symbol: str, start: datetime, end: datetime) -> pl.DataFrame:
        start_utc = to_utc(start)
        end_utc = to_utc(end)
        months = _month_range(start_utc, end_utc)
        parts = []

        with httpx.Client(timeout=60) as client:
            for year, month in months:
                url = f"{self._BASE_URL}/{symbol}/{self.timeframe}/{symbol}-{self.timeframe}-{year}-{month:02d}.zip"
                resp = client.get(url)
                if resp.status_code == 404:
                    continue  # symbol not listed yet for this month
                resp.raise_for_status()

                parts.append(parse_kline_zip(resp.content))

        if not parts:
            return empty_ohlcv_df()

        return (
            pl.concat(parts)
            .filter(pl.col("timestamp").is_between(pl.lit(start_utc), pl.lit(end_utc)))
            .sort("timestamp")
        )


_KLINE_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume",
                  "close_time", "quote_volume", "trades",
                  "taker_buy_volume", "taker_buy_quote_volume", "ignore"]


def parse_kline_zip(content: bytes) -> pl.DataFrame:
    """Parse one data.binance.vision kline ZIP (spot or futures).

    Spot CSVs have no header; USD-M futures CSVs start with one
    (open_time,open,...). Rows whose first field isn't a number are dropped.
    Binance changed the timestamp unit over time: old files use ms
    (13 digits), recent spot files us (16 digits).
    """
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        with zf.open(zf.namelist()[0]) as f:
            raw = pl.read_csv(f.read(), has_header=False, new_columns=_KLINE_COLUMNS, infer_schema=False)
    df = raw.filter(pl.col("timestamp").str.contains(r"^\d+$")).select(
        pl.col("timestamp").cast(pl.Int64),
        pl.col("close_time").cast(pl.Int64).alias("timestamp_close"),
        *[pl.col(c).cast(pl.Float64) for c in ("open", "high", "low", "close", "volume")],
    )
    if df.is_empty():
        return empty_ohlcv_df()
    time_unit = "us" if df["timestamp"].max() > 10 ** 15 else "ms"
    return df.with_columns(
        pl.from_epoch(c, time_unit=time_unit).dt.replace_time_zone("UTC").cast(pl.Datetime("us", "UTC"))
        for c in ("timestamp", "timestamp_close")
    )


def _month_range(start: datetime, end: datetime) -> list[tuple[int, int]]:
    months = []
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        months.append((year, month))
        month += 1
        if month > 12:
            month = 1
            year += 1
    return months
