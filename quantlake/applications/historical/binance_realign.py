"""Rewrite silver/binance_spot_ohlcv for a period from bronze, with 1m alignment.

Silver written before align_to_minute existed still holds the shifted open
times found in the Binance archives (e.g. BTCUSDT 2017-12-04 06:00 →
2018-02-10 05:59 UTC, +20.799 s / +14.789 s). An upsert alone would not fix
them: the merge key is the timestamp, so the shifted rows would stay next to
the aligned ones. For each symbol this script therefore:

  1. reads bronze for [start, end) (bronze keeps the raw rows),
  2. deletes silver rows in [start, end),
  3. writes the bronze rows through silver.ingest(..., align_1m=True),
  4. rebuilds the bars of [start, end) in every existing
     gold/binance_spot_ohlcv/<tf> (rows are overwritten, same labels).

start/end default to whole months so every 4h / 1d window is complete.
Re-running is safe (it always starts again from bronze).

Run:
    .venv/bin/python applications/historical/binance_realign.py --dry-run
    .venv/bin/python applications/historical/binance_realign.py
    .venv/bin/python applications/historical/binance_realign.py --symbol ETHUSDT --start 2017-12-01 --end 2018-03-01
"""
import argparse
from datetime import datetime, timezone

import polars as pl

import quantlake.gold.ingest as gold
import quantlake.silver.ingest as silver
from quantlake.config import BRONZE_ROOT, GOLD_ROOT, SILVER_ROOT
from quantlake.maintenance import find_tables
from quantlake.storage import delete_range, read_symbol

TABLE = "binance_spot_ohlcv"


def _utc(day: str) -> datetime:
    return datetime.fromisoformat(day).replace(tzinfo=timezone.utc)


def misaligned(df: pl.DataFrame) -> int:
    return df.filter(pl.col("timestamp") != pl.col("timestamp").dt.truncate("1m")).height


def realign(symbol: str, start: datetime, end: datetime, dry_run: bool = False) -> dict:
    raw = read_symbol(str(BRONZE_ROOT / TABLE), symbol, since=start)
    if raw is None:
        raise SystemExit(f"no bronze table at {BRONZE_ROOT / TABLE}")
    raw = raw.filter(pl.col("timestamp") < end).sort("timestamp")
    old = read_symbol(str(SILVER_ROOT / TABLE), symbol, since=start)
    old = old.filter(pl.col("timestamp") < end) if old is not None else pl.DataFrame()

    stats = {
        "bronze_rows": raw.height,
        "bronze_misaligned": misaligned(raw) if raw.height else 0,
        "silver_rows_before": old.height,
        "silver_misaligned_before": misaligned(old) if old.height else 0,
    }
    if dry_run or raw.is_empty():
        return stats

    stats["silver_deleted"] = delete_range(str(SILVER_ROOT / TABLE), symbol, start, end)
    clean = silver.ingest(raw, TABLE, align_1m=True)
    stats["silver_rows_after"] = clean.height

    gold_root = GOLD_ROOT / TABLE
    for path in find_tables(gold_root):
        tf = path.relative_to(gold_root).as_posix()
        stats[f"gold_{tf}"] = gold.ingest(clean, TABLE, tf).height
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--symbol", action="append", help="repeatable; default BTCUSDT")
    parser.add_argument("--start", default="2017-12-01", help="UTC date, inclusive (default 2017-12-01)")
    parser.add_argument("--end", default="2018-03-01", help="UTC date, exclusive (default 2018-03-01)")
    parser.add_argument("--dry-run", action="store_true", help="only count rows, change nothing")
    args = parser.parse_args()

    for symbol in args.symbol or ["BTCUSDT"]:
        stats = realign(symbol, _utc(args.start), _utc(args.end), args.dry_run)
        print(f"[{symbol}] " + ", ".join(f"{k}={v:,}" for k, v in stats.items()))


if __name__ == "__main__":
    main()
