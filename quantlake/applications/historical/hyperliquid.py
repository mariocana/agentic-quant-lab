"""Hyperliquid perps, main dex and HIP-3: daily and hourly bars, hourly funding,
and the listing table that makes a point-in-time universe possible.

  bronze/hyperliquid_ohlcv_1d      whole history, delisted perps included
  bronze/hyperliquid_ohlcv_1h      only the latest ~5000 bars exist upstream:
                                   run this at least every few months
  bronze/hyperliquid_funding       hourly, from 2023-05-12
  reference/hyperliquid_listings   first/last daily bar per perp, delisting day

Resumable per symbol from the last bronze timestamp; re-running is safe. A
delisted perp whose history is already stored is skipped: it cannot grow.
At about one API call a second, the first full funding backfill takes hours;
interrupt it whenever, the next run continues.

Run:
    poetry run python applications/historical/hyperliquid.py                 # everything
    poetry run python applications/historical/hyperliquid.py --dex main --limit 20
    poetry run python applications/historical/hyperliquid.py --no-funding --intervals 1d
"""
import argparse
from datetime import datetime, timedelta, timezone

import polars as pl
from deltalake import DeltaTable, write_deltalake

import quantlake.bronze.ingest as bronze
from quantlake.bronze.connectors import hyperliquid as hl
from quantlake.config import BRONZE_ROOT, REFERENCE_ROOT

STEP = {"1h": timedelta(hours=1), "1d": timedelta(days=1)}
EPOCH = datetime(2020, 1, 1, tzinfo=timezone.utc)


def ingest_bars(conn, sym, delisted, now):
    last = bronze.last_bronze_ts(conn.TABLE_NAME, sym)
    if last and delisted:
        return 0
    df = bronze.ingest(conn, sym, (last + STEP[conn.interval]) if last else EPOCH, now)
    return len(df)


def ingest_funding(conn, sym, delisted, now):
    last = bronze.last_bronze_ts(conn.TABLE_NAME, sym)
    if last and delisted:
        return 0
    end = hl.funding_end(now, delisted, bronze.last_bronze_ts("hyperliquid_ohlcv_1d", sym))
    if end is None:
        return 0
    df = bronze.ingest(conn, sym, (last + timedelta(milliseconds=1)) if last else hl.FUNDING_START, end)
    return len(df)


def write_listings(uni):
    path = str(BRONZE_ROOT / "hyperliquid_ohlcv_1d")
    if not DeltaTable.is_deltatable(path):
        return 0
    daily = pl.from_arrow(DeltaTable(path).to_pyarrow_table(columns=["symbol", "timestamp"]))
    fl = daily.group_by("symbol").agg(pl.col("timestamp").min().dt.date().alias("first_bar"),
                                      pl.col("timestamp").max().dt.date().alias("last_bar"))
    df = hl.listings(fl, uni)
    write_deltalake(str(REFERENCE_ROOT / "hyperliquid_listings"), df, mode="overwrite",
                    schema_mode="overwrite")
    return df.height


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--intervals", default="1d,1h")
    ap.add_argument("--no-funding", action="store_true")
    ap.add_argument("--dex", help="only this dex (main, xyz, ...)")
    ap.add_argument("--symbols", help="comma-separated, e.g. BTC,ETH,xyz:TSLA")
    ap.add_argument("--limit", type=int, help="first N symbols only (a trial run)")
    a = ap.parse_args()

    now = datetime.now(timezone.utc)
    uni = hl.universe()
    todo = [u for u in uni
            if (not a.dex or u["dex"] == a.dex) and (not a.symbols or u["symbol"] in a.symbols.split(","))]
    todo = todo[: a.limit] if a.limit else todo
    print(f"{len(uni)} perps on {len({u['dex'] for u in uni})} dexs; {len(todo)} to visit")

    api = hl._Client()
    bars = [hl.HyperliquidOHLCVConnector(i, client=api) for i in a.intervals.split(",") if i]
    funding = None if a.no_funding else hl.HyperliquidFundingConnector(client=api)

    for n, u in enumerate(todo, 1):
        sym, dead = u["symbol"], u["is_delisted"]
        try:
            got = {c.interval: ingest_bars(c, sym, dead, now) for c in bars}
            if funding:
                got["funding"] = ingest_funding(funding, sym, dead, now)
        except Exception as e:                    # noqa: BLE001 - one bad perp must not stop the run
            print(f"[{n}/{len(todo)}] {sym}: FAILED {e!r}")
            continue
        if any(got.values()):
            print(f"[{n}/{len(todo)}] {sym}{' (delisted)' if dead else ''}: "
                  + ", ".join(f"{k} {v:,}" for k, v in got.items()))

    print(f"reference/hyperliquid_listings: {write_listings(uni)} perps")


if __name__ == "__main__":
    main()
