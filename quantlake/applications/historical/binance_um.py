"""Binance USDⓈ-M perpetuals: OHLCV 1m + funding rate -> bronze + silver.

  bronze/binance_um_ohlcv   -> silver/binance_um_ohlcv   (align_to_minute + clean_ohlcv)
  bronze/binance_um_funding -> silver/binance_um_funding (silver.funding)

OHLCV: monthly ZIPs from data.binance.vision for every full month, then REST
from the last stored bar up to the last closed minute (covers the current
month and a previous month whose ZIP isn't published yet). Funding: REST, full history.
Resumable per symbol from the last bronze timestamp; re-running is safe.
Gold (plain OHLCV for alpha-quant) is built by historical/ohlcv_gold.py.

Run:
    .venv/bin/python applications/historical/binance_um.py
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import quantlake.bronze.ingest as bronze
import quantlake.silver.ingest as silver
from quantlake.bronze.connectors.binance_um import (
    BinanceUMFundingRateConnector, BinanceUMOHLCVBulkConnector, BinanceUMOHLCVRestConnector,
)
from quantlake.silver.funding import save_funding
from symbols import UM_PERPS

FIRST_MONTH = datetime(2019, 9, 1, tzinfo=timezone.utc)  # BTCUSDT perpetual listed 2019-09
OHLCV = BinanceUMOHLCVBulkConnector.TABLE_NAME
FUNDING = BinanceUMFundingRateConnector.TABLE_NAME


def _next_minute(ts: datetime) -> datetime:
    # bronze keeps raw open times, which can be a few seconds late (see
    # silver.ohlcv.align_to_minute): resume at the next whole minute.
    return ts.replace(second=0, microsecond=0) + timedelta(minutes=1)


def ingest_ohlcv(symbol: str, now: datetime) -> None:
    last = bronze.last_bronze_ts(OHLCV, symbol)
    start = _next_minute(last) if last else FIRST_MONTH
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # stop before the current minute: Binance would return the candle still open
    rest_end = now.replace(second=0, microsecond=0) - timedelta(milliseconds=1)

    if start < month_start:
        df = bronze.ingest(BinanceUMOHLCVBulkConnector(), symbol, start, month_start - timedelta(microseconds=1))
        silver.ingest(df, OHLCV, align_1m=True)
        print(f"[{symbol}] ohlcv bulk {start:%Y-%m} → {month_start:%Y-%m}: {len(df):,} bars")
        # REST continues from the last bar actually stored, not from month_start:
        # last month's ZIP is published a few days late and must not leave a hole.
        if not df.is_empty():
            start = _next_minute(df["timestamp"].max())
    if start < rest_end:
        df = bronze.ingest(BinanceUMOHLCVRestConnector(), symbol, start, rest_end)
        silver.ingest(df, OHLCV, align_1m=True)
        print(f"[{symbol}] ohlcv REST {start:%Y-%m-%d %H:%M} → {rest_end:%H:%M}: {len(df):,} bars")


def ingest_funding(symbol: str, now: datetime) -> None:
    last = bronze.last_bronze_ts(FUNDING, symbol)
    start = last + timedelta(milliseconds=1) if last else FIRST_MONTH
    df = bronze.ingest(BinanceUMFundingRateConnector(), symbol, start, now)
    if not df.is_empty():
        save_funding(df)
    print(f"[{symbol}] funding from {start:%Y-%m-%d}: {len(df):,} rows")


def main() -> None:
    now = datetime.now(timezone.utc)
    for symbol in UM_PERPS:
        try:
            ingest_ohlcv(symbol, now)
            ingest_funding(symbol, now)
        except Exception as e:  # keep going with the other symbols
            print(f"[{symbol}] ERROR: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
