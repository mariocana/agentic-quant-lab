"""SEC Form 4 -> bronze/sec_form4 -> gold/insider_activity (+ prices of the buys).

    1. EDGAR daily index for every weekday not yet stored (first run:
       BACKFILL weekdays; later only the new ones, up to today)
    2. each Form 4 / 4/A of the day (full submission .txt), parsed into one
       row per non-derivative transaction; a day is rewritten as a whole, so
       re-running it is safe
    3. Nasdaq daily prices for the symbols bought in the window
    4. gold/insider_activity/1d rebuilt

~1,000-2,000 Form 4 per day at <= 8 requests/second: about 3-4 minutes per
day, so the first run (BACKFILL days) takes ~20-30 minutes, then a few minutes.
Needs SEC_USER_AGENT in .env (the SEC requires a declared contact).

Run:
    .venv/bin/python applications/historical/insiders.py [--days N]
"""
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent.parent))

import polars as pl
from deltalake import DeltaTable, write_deltalake

import quantlake.bronze.ingest as bronze
import quantlake.gold.insiders as gold
from quantlake.bronze.connectors.nasdaq_earnings import NasdaqStockDailyConnector
from quantlake.bronze.connectors.sec_form4 import (ARCHIVES, SECClient, daily_index_url, parse_daily_index,
                                                    parse_form4)
from quantlake.config import BRONZE_ROOT

NY = ZoneInfo("America/New_York")
TABLE = "sec_form4"
PATH = str(BRONZE_ROOT / TABLE)
BACKFILL = 7
WORKERS = 8
PRICE_HISTORY = 60


def weekdays_back(end: date, n: int) -> list[date]:
    out, d = [], end
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d -= timedelta(days=1)
    return sorted(out)


def stored_days() -> set[date]:
    if not DeltaTable.is_deltatable(PATH):
        return set()
    return set(pl.from_arrow(DeltaTable(PATH).to_pyarrow_table(columns=["filed_date"]))["filed_date"].unique().to_list())


def write_day(day: date, rows: list[dict]) -> None:
    df = pl.DataFrame(rows, infer_schema_length=None).with_columns(
        pl.lit(day).alias("filed_date"),
        pl.lit(datetime.combine(day, datetime.min.time(), NY)).cast(pl.Datetime("us", "UTC")).alias("timestamp"),
        pl.lit(day.year).cast(pl.Int32).alias("year"), pl.lit(day.month).cast(pl.Int8).alias("month"),
        pl.lit(datetime.now(timezone.utc)).cast(pl.Datetime("us", "UTC")).alias("ingested_at"),
    )
    if DeltaTable.is_deltatable(PATH):
        DeltaTable(PATH).delete(f"filed_date = '{day.isoformat()}'")
        write_deltalake(PATH, df.to_arrow(), mode="append", partition_by=["year", "month"], schema_mode="merge")
    else:
        write_deltalake(PATH, df.to_arrow(), mode="overwrite", partition_by=["year", "month"])


def main() -> None:
    days_arg = int(sys.argv[sys.argv.index("--days") + 1]) if "--days" in sys.argv else None
    sec = SECClient()
    today = datetime.now(NY).date()
    have = stored_days()
    if days_arg:
        todo = weekdays_back(today, days_arg)
    elif have:
        todo = [d for d in weekdays_back(today, (today - max(have)).days + 1) if d > max(have)]
        todo.append(max(have))   # the last stored day may have been read before it was complete
    else:
        todo = weekdays_back(today, BACKFILL)

    for day in sorted(set(todo)):
        r = sec.get(daily_index_url(day), missing=(403, 404))
        if r is None:
            print(f"[{day}] no daily index yet (holiday or not published)")
            continue
        filings = parse_daily_index(r.text)
        t0 = time.monotonic()

        def fetch(f):
            resp = sec.get(f"{ARCHIVES}/{f['path']}")
            if resp is None:
                return []
            return [{**row, "accession": f["accession"], "form": f["form"]} for row in parse_form4(resp.text)]

        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            rows = [row for part in ex.map(fetch, filings) for row in part]
        if rows:
            write_day(day, rows)
        buys = sum(1 for x in rows if x["code"] == "P")
        print(f"[{day}] {len(filings)} Form 4, {len(rows)} transactions ({buys} purchases), {time.monotonic() - t0:.0f}s")

    form4 = pl.from_arrow(DeltaTable(PATH).to_pyarrow_table()) if DeltaTable.is_deltatable(PATH) else pl.DataFrame()
    if form4.is_empty():
        print("[insiders] nothing stored")
        return

    # prices for the symbols bought in the window (since-purchase return)
    window = form4.filter((pl.col("filed_date") >= today - timedelta(days=gold.WINDOW_DAYS)) & (pl.col("code") == "P"))
    symbols = sorted(s for s in window["symbol"].drop_nulls().unique().to_list() if s.isalpha())
    now = datetime.now(timezone.utc)

    def fetch_px(sym):
        try:
            df = NasdaqStockDailyConnector().fetch(sym, now - timedelta(days=PRICE_HISTORY), now)
        except Exception:
            return pl.DataFrame()
        return df.with_columns(pl.lit(sym).alias("symbol")) if not df.is_empty() else df

    with ThreadPoolExecutor(max_workers=4) as ex:
        frames = [f for f in ex.map(fetch_px, symbols) if not f.is_empty()]
    if frames:
        px = pl.concat(frames, how="diagonal_relaxed")
        px = px.with_columns(pl.col("timestamp").dt.year().cast(pl.Int32).alias("year"),
                             pl.col("timestamp").dt.month().cast(pl.Int8).alias("month"),
                             pl.lit(now).cast(pl.Datetime("us", "UTC")).alias("ingested_at"))
        bronze.save(px, "nasdaq_stock_daily", update_matched=True)
    print(f"[prices] {len(frames)}/{len(symbols)} symbols bought in the window")

    prices = pl.from_arrow(DeltaTable(str(BRONZE_ROOT / "nasdaq_stock_daily")).to_pyarrow_table(
        columns=["symbol", "timestamp", "close"])) if frames or DeltaTable.is_deltatable(
        str(BRONZE_ROOT / "nasdaq_stock_daily")) else pl.DataFrame()
    act = gold.build(form4, prices.filter(pl.col("symbol").is_in(symbols)) if not prices.is_empty() else prices, today)
    gold.save(act)
    if not act.is_empty():
        buys = act.filter(pl.col("list") == "buy")
        clusters = buys.filter(pl.col("cluster_buyers") >= 2)["symbol"].unique().to_list()
        print(f"[insiders] {buys.height} purchases >= ${gold.MIN_BUY:,}, "
              f"{act.filter(pl.col('list') == 'sell').height} sales >= ${gold.MIN_SELL:,}, "
              f"clusters: {', '.join(sorted(clusters)) or '-'}")


if __name__ == "__main__":
    main()
