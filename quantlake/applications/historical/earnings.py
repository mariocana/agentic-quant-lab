"""Earnings scanner data -> bronze (calendar, EPS surprises, stock prices) -> gold/earnings_screener.

    1. calendar for the weekdays from CAL_BACK days ago to CAL_AHEAD days ahead
       (every company); the time of day already stored is kept when Nasdaq
       no longer supplies it (it drops it once the day is past)
    2. daily prices for the companies in the screener windows (market cap
       >= gold.earnings.MIN_MARKET_CAP), only the missing days
    3. last-4-quarter EPS surprises for the upcoming ones, at most once a week
    4. gold/earnings_screener/1d rebuilt

A few hundred small requests in earnings season, 4 at a time (~1 minute).

Run:
    .venv/bin/python applications/historical/earnings.py
"""
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent.parent))

import polars as pl
from deltalake import DeltaTable

import quantlake.bronze.ingest as bronze
import quantlake.gold.earnings as gold
from quantlake.bronze.connectors.nasdaq_earnings import (
    NasdaqEarningsCalendarConnector, NasdaqEarningsSurpriseConnector, NasdaqStockDailyConnector)
from quantlake.config import BRONZE_ROOT

NY = ZoneInfo("America/New_York")
CAL_BACK, CAL_AHEAD = 10, 10      # calendar days fetched around today
PRICE_HISTORY = 160               # calendar days of prices for a new symbol (13-week return)
SURPRISE_EVERY = timedelta(days=7)
WORKERS = 4

CAL, SUR, PX = (NasdaqEarningsCalendarConnector.TABLE_NAME, NasdaqEarningsSurpriseConnector.TABLE_NAME,
                NasdaqStockDailyConnector.TABLE_NAME)


def table(name: str, columns: list[str] | None = None) -> pl.DataFrame:
    path = str(BRONZE_ROOT / name)
    if not DeltaTable.is_deltatable(path):
        return pl.DataFrame()
    return pl.from_arrow(DeltaTable(path).to_pyarrow_table(columns=columns))


def with_partitions(df: pl.DataFrame) -> pl.DataFrame:
    """symbol is already a column: add year / month / ingested_at like bronze.add_partition_columns."""
    return df.with_columns(
        pl.col("timestamp").dt.year().cast(pl.Int32).alias("year"),
        pl.col("timestamp").dt.month().cast(pl.Int8).alias("month"),
        pl.lit(datetime.now(timezone.utc)).cast(pl.Datetime("us", "UTC")).alias("ingested_at"),
    )


def pmap(fn, items):
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        return list(ex.map(fn, items))


today = datetime.now(NY).date()

# 1. calendar
days = [today + timedelta(days=i) for i in range(-CAL_BACK, CAL_AHEAD + 1)]
days = [d for d in days if d.weekday() < 5]
conn = NasdaqEarningsCalendarConnector()
frames = [f for f in pmap(conn.fetch_day, days) if not f.is_empty()]
cal_new = pl.concat(frames, how="diagonal_relaxed") if frames else pl.DataFrame()
if not cal_new.is_empty():
    old = table(CAL, ["timestamp", "symbol", "time"])
    if not old.is_empty():
        cal_new = cal_new.join(old.rename({"time": "time_old"}), on=["timestamp", "symbol"], how="left").with_columns(
            pl.when(pl.col("time") == "na").then(pl.col("time_old").fill_null("na")).otherwise(pl.col("time")).alias("time")
        ).drop("time_old")
    bronze.save(with_partitions(cal_new), CAL, update_matched=True)
print(f"[calendar] {cal_new.height} rows, {days[0]} -> {days[-1]}")

cal = table(CAL)
cal = cal.with_columns(pl.col("timestamp").dt.convert_time_zone("America/New_York").dt.date().alias("d"))
past, ahead = gold.weekdays(today, gold.LOOKBACK, -1), gold.weekdays(today, gold.LOOKAHEAD, 1)
big = cal.filter(pl.col("market_cap").fill_null(0) >= gold.MIN_MARKET_CAP)
reported = big.filter(pl.col("d").is_in(past) & pl.col("eps").is_not_null())["symbol"].unique().to_list()
upcoming = big.filter(pl.col("d").is_in(ahead) & pl.col("eps").is_null())["symbol"].unique().to_list()
symbols = sorted(set(reported) | set(upcoming))

# 2. prices: only what is missing
px_old = table(PX, ["symbol", "timestamp"])
last_px = dict(px_old.group_by("symbol").agg(pl.col("timestamp").max()).iter_rows()) if not px_old.is_empty() else {}
now = datetime.now(timezone.utc)


def session_close(d: date) -> datetime:
    return datetime.combine(d, datetime.min.time(), NY) + timedelta(hours=16, minutes=15)


# the last daily bar that can already exist: today's after 16:15 New York, else the previous weekday's
last_session = gold.weekdays(today, 1, -1)[0]
if now < session_close(last_session):
    last_session = gold.weekdays(last_session - timedelta(days=1), 1, -1)[0]
last_session_close = session_close(last_session).astimezone(timezone.utc)


def fetch_px(sym):
    last = last_px.get(sym)
    if last is not None and last >= last_session_close:   # already up to date
        return pl.DataFrame()
    start = (last + timedelta(hours=1)) if last else now - timedelta(days=PRICE_HISTORY)
    try:
        df = NasdaqStockDailyConnector().fetch(sym, start, now)
    except Exception as exc:
        print(f"  ! prices {sym}: {exc}")
        return pl.DataFrame()
    time.sleep(0.1)
    return df.with_columns(pl.lit(sym).alias("symbol")) if not df.is_empty() else df


frames = [f for f in pmap(fetch_px, symbols) if not f.is_empty()]
if frames:
    bronze.save(with_partitions(pl.concat(frames, how="diagonal_relaxed")), PX, update_matched=True)
print(f"[prices] {len(symbols)} symbols, {sum(f.height for f in frames)} new bars")

# 3. surprises for the upcoming ones, at most once a week per symbol
sur_old = table(SUR, ["symbol", "ingested_at"])
fresh = set(sur_old.filter(pl.col("ingested_at") > now - SURPRISE_EVERY)["symbol"].unique().to_list()) \
    if not sur_old.is_empty() else set()


def fetch_sur(sym):
    try:
        df = NasdaqEarningsSurpriseConnector().fetch(sym)
    except Exception as exc:
        print(f"  ! surprise {sym}: {exc}")
        return pl.DataFrame()
    time.sleep(0.1)
    return df.with_columns(pl.lit(sym).alias("symbol")) if not df.is_empty() else df


todo = [s for s in upcoming if s not in fresh]
frames = [f for f in pmap(fetch_sur, todo) if not f.is_empty()]
if frames:
    bronze.save(with_partitions(pl.concat(frames, how="diagonal_relaxed")), SUR, update_matched=True)
print(f"[surprise] {len(todo)} fetched, {len(upcoming) - len(todo)} still fresh")

# 4. gold
screen = gold.build(cal.drop("d"), table(SUR), table(PX), today)
gold.save(screen)
if screen.is_empty():
    print("[screener] nothing in the windows")
else:
    for lst in ("reported", "upcoming"):
        x = screen.filter(pl.col("list") == lst)
        top = ", ".join(f"{r['symbol']} {r['score']}" for r in x.filter("passes").head(8).iter_rows(named=True))
        print(f"[screener] {lst}: {x.height} in window, {x['passes'].sum()} pass  {top}")
