"""Plain OHLCV gold tables read by alpha-quant.

    silver/multicharts_ohlcv   -> gold/multicharts_ohlcv/<tf>   (ES, NQ)
    silver/binance_spot_ohlcv  -> gold/binance_spot_ohlcv/<tf>  (every symbol in silver)

No features: resampled OHLCV only, one table per timeframe. Incremental
(gold.update_ohlcv): each run rebuilds the last stored bar and adds the
bars whose whole window is now in silver. Daily bars are UTC days.

Run after the silver backfills (historical/multicharts.py, historical/binance.py):
    .venv/bin/python applications/historical/ohlcv_gold.py
"""
import quantlake.gold.ingest as gold
from quantlake.config import SILVER_ROOT
from quantlake.storage import symbols

# (silver table, gold table)
TABLES = [
    ("multicharts_ohlcv", "multicharts_ohlcv"),
    ("binance_spot_ohlcv", "binance_spot_ohlcv"),
]
TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d"]


def main() -> None:
    for silver_table, gold_table in TABLES:
        syms = symbols(str(SILVER_ROOT / silver_table))
        if not syms:
            print(f"[{silver_table}] no silver table, skipped")
            continue
        for symbol in syms:
            for tf in TIMEFRAMES:
                df = gold.update_ohlcv(silver_table, gold_table, tf, symbol)
                last = df["timestamp"].max() if not df.is_empty() else "-"
                print(f"[{gold_table}/{tf}] {symbol}: {df.height:,} bars written, last {last}")


if __name__ == "__main__":
    main()
