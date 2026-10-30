"""Plain OHLCV gold tables read by alpha-quant.

    silver/multicharts_ohlcv   -> gold/multicharts_ohlcv/<tf>   (ES, NQ)
    silver/binance_spot_ohlcv  -> gold/binance_spot_ohlcv/<tf>  (every symbol in silver)
    silver/binance_um_ohlcv    -> gold/binance_um_ohlcv/<tf>    (USDⓈ-M perpetuals)

No features: resampled OHLCV only, one table per timeframe. Incremental
(gold.update_ohlcv): each run rebuilds the last stored bar and adds the
bars whose whole window is now in silver. '1d' / '4h' are UTC-aligned;
the futures also get '1d_cme' / '4h_cme', anchored to the CME trading day
(17:00 America/Chicago, see gold.ohlcv.SESSION_ANCHORS).

multicharts_ohlcv is rebuilt over the last REBUILD_LOOKBACK too: the daily
ES_recent / NQ_recent export rewrites the last 5 days of silver (after a
roll on TradeStation's new back-adjustment), and the gold must follow.

Run after the silver backfills (historical/multicharts.py, historical/binance.py):
    .venv/bin/python applications/historical/ohlcv_gold.py
"""
from datetime import timedelta

import quantlake.gold.ingest as gold
from quantlake.config import SILVER_ROOT
from quantlake.storage import symbols

TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d"]

# silver table -> (gold table, timeframes)
TABLES = {
    "multicharts_ohlcv":  ("multicharts_ohlcv", TIMEFRAMES + ["4h_cme", "1d_cme"]),
    "binance_spot_ohlcv": ("binance_spot_ohlcv", TIMEFRAMES),
    "binance_um_ohlcv":   ("binance_um_ohlcv", TIMEFRAMES),
}

# silver tables whose last days are rewritten in place (recent export)
REBUILD_LOOKBACK = {"multicharts_ohlcv": timedelta(days=7)}


def main() -> None:
    for silver_table, (gold_table, timeframes) in TABLES.items():
        syms = symbols(str(SILVER_ROOT / silver_table))
        if not syms:
            print(f"[{silver_table}] no silver table, skipped")
            continue
        for symbol in syms:
            for tf in timeframes:
                df = gold.update_ohlcv(silver_table, gold_table, tf, symbol,
                                       lookback=REBUILD_LOOKBACK.get(silver_table))
                last = df["timestamp"].max() if not df.is_empty() else "-"
                print(f"[{gold_table}/{tf}] {symbol}: {df.height:,} bars written, last {last}")


if __name__ == "__main__":
    main()
