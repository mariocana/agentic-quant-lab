"""Live satellite wheat NDVI - daily poll on top of the historical connector.

Same sources as applications/historical/wheat_ndvi.py, at their own pace:

  Sentinel-2   a scene every ~5 days per spot, on Planetary Computer
               1-5 days after acquisition
  NASS         Crop Progress every Monday 16:00 ET (growing season)
  USDA CDL     once a year, Jan-Feb of N+1

so this is a poll-based runner (no websocket): one tick per day.

Daily tick, in order:
  1. CDL     if a newer CDL got published, download it once and cut the
             AOI windows, so the NDVI step switches to it from today on.
             Rows already stored keep the mask they were computed with
             (their cdl_year): rewriting them would leak a mask that did
             not exist yet at their timestamp.
  2. NDVI    per AOI, search the last LOOKBACK_DAYS of scenes (not just
             "after the last stored date": a scene acquired on day 8 can
             show up after one acquired on day 10), compute NDVI on the
             cached crop mask, append only dates not in bronze yet.
             Idempotent on (bbox_id, date). First run of a season starts
             from Sept 1. Then silver/sentinel2_ndvi_anomaly is rebuilt.
  3. NASS    Crop Progress for the AOI states, only when bronze is older
             than the latest Monday 16:00 ET release.

Usage (from python/quantlake):
    .venv/bin/python applications/live/wheat_ndvi.py           # loop, ticks daily at RUN_AT_UTC
    .venv/bin/python applications/live/wheat_ndvi.py --once    # one tick, for cron/launchd

Run applications/historical/wheat_ndvi.py first for past seasons: this
runner only maintains the current one.
"""
import argparse
import os
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent.parent))

import polars as pl
from deltalake import DeltaTable
from dotenv import load_dotenv

import quantlake.bronze.ingest as bronze
import quantlake.poll as poll
import quantlake.silver.ndvi as silver_ndvi
from quantlake.bronze.connectors.cdl_rest import CDLConnector
from quantlake.bronze.connectors.nass_quickstats_rest import NASSQuickStatsConnector
from quantlake.bronze.connectors.sentinel2_ndvi_rest import CDL_FALLBACK_YEARS, Sentinel2NDVIConnector
from quantlake.config import BRONZE_ROOT
from symbols import NDVI_AOIS

load_dotenv()

TABLE = Sentinel2NDVIConnector.TABLE_NAME
PROGRESS_TABLE = NASSQuickStatsConnector.PROGRESS_TABLE
LOOKBACK_DAYS = 10      # > max Planetary Computer latency (~5 d), plus margin
RUN_AT_UTC = 7          # hour of the daily tick: after US-night processing
_ET = ZoneInfo("America/New_York")

cdl = CDLConnector()
CONNECTORS = {
    aoi.bbox_id: Sentinel2NDVIConnector(aoi.bbox, crop_class=aoi.crop_class, cdl=cdl)
    for aoi in NDVI_AOIS
}


def _read(table: str, columns: list[str], symbol: str | None = None) -> pl.DataFrame:
    path = str(BRONZE_ROOT / table)
    if not DeltaTable.is_deltatable(path):
        return pl.DataFrame()
    filters = [("symbol", "=", symbol)] if symbol else None
    return pl.from_arrow(DeltaTable(path).to_pyarrow_table(columns=columns, filters=filters))


# ── 1. CDL: pull a newly published year ────────────────────────────────────

def cdl_tick(today: date) -> None:
    """Make sure the newest published CDL a live season can use is cut for every AOI."""
    for year in range(today.year, today.year - CDL_FALLBACK_YEARS - 1, -1):
        try:
            if not cdl.is_published(year):
                continue
            for aoi in NDVI_AOIS:
                cdl.clip(aoi.bbox, year)      # downloads once, then clip cache
        except Exception as e:
            print(f"[cdl] {year}: {e}")
            continue
        print(f"[cdl] latest published: {year} (AOI windows cached)")
        return
    print("[cdl] no CDL published in the fallback window")


# ── 2. NDVI: new scenes per AOI ────────────────────────────────────────────

def ndvi_tick(today: date) -> int:
    added = 0
    for aoi in NDVI_AOIS:
        conn = CONNECTORS[aoi.bbox_id]
        try:
            stored = _read(TABLE, ["acq_date"], aoi.bbox_id)
            have = set(stored["acq_date"].to_list()) if not stored.is_empty() else set()
            season_start, _ = conn.season_bounds(conn.season_of(today))
            in_season = any(d >= season_start for d in have)
            start = max(today - timedelta(days=LOOKBACK_DAYS), season_start) if in_season else season_start
            df = conn.fetch(aoi.bbox_id,
                            datetime.combine(start, time(), timezone.utc),
                            datetime.combine(today, time(), timezone.utc))
            new = df.filter(~pl.col("acq_date").is_in(list(have))) if have else df
        except Exception as e:
            print(f"[{aoi.bbox_id}] ndvi error: {e}")
            continue
        if new.is_empty():
            print(f"[{aoi.bbox_id}] no new scenes since {start}")
            continue
        bronze.save(bronze.add_partition_columns(new, symbol=aoi.bbox_id), TABLE)
        added += len(new)
        last = new.sort("acq_date").tail(1).row(0, named=True)
        print(f"[{aoi.bbox_id}] +{len(new)} dates, last {last['acq_date']} "
              f"NDVI {last['ndvi_mean']:.3f} (valid {last['valid_frac']:.0%}, CDL {last['cdl_year']})")
    return added


def silver_tick() -> None:
    df = _read(TABLE, None)
    if df.is_empty():
        return
    out = silver_ndvi.rebuild(df)
    latest = out.sort("acq_date").group_by("symbol").agg(pl.all().last())
    for r in latest.iter_rows(named=True):
        anomaly = "n/a" if r["anomaly"] is None else f"{r['anomaly']:+.3f}"
        print(f"[{r['symbol']}] silver: {r['acq_date']} NDVI {r['ndvi_mean']:.3f} anomaly {anomaly} "
              f"({r['n_baseline']} prior seasons)")


# ── 3. NASS Crop Progress: weekly ──────────────────────────────────────────

def last_progress_release(now: datetime) -> datetime:
    """Most recent Monday 16:00 ET at or before `now` (holiday shifts ignored)."""
    et = now.astimezone(_ET)
    monday = et.date() - timedelta(days=et.weekday())
    release = datetime.combine(monday, time(16, 0), tzinfo=_ET)
    if release > et:
        release -= timedelta(days=7)
    return release.astimezone(timezone.utc)


def progress_tick(now: datetime) -> None:
    if not os.getenv("NASS_API_KEY"):
        print("[nass] NASS_API_KEY missing, skip")
        return
    nass = NASSQuickStatsConnector()
    expected = last_progress_release(now)
    stored = _read(PROGRESS_TABLE, ["symbol", "timestamp"])
    for state in sorted({a.state for a in NDVI_AOIS}):
        mine = stored.filter(pl.col("symbol").str.starts_with(f"{state}_")) if not stored.is_empty() else stored
        if not mine.is_empty() and mine["timestamp"].max() >= expected:
            print(f"[{state}] crop progress up to date ({expected:%Y-%m-%d})")
            continue
        try:
            df = nass.crop_progress(state, year_start=now.year)
        except Exception as e:
            print(f"[{state}] nass error: {e}")
            continue
        for (stage,), g in df.group_by("stage"):
            bronze.save(bronze.add_partition_columns(g, symbol=f"{state}_{stage}"), PROGRESS_TABLE)
        last = df["week_ending"].max() if not df.is_empty() else None
        print(f"[{state}] crop progress: {len(df)} rows this year, last week {last}")


# ── Tick ───────────────────────────────────────────────────────────────────

def daily_tick(now: datetime | None = None) -> None:
    now = now or datetime.now(timezone.utc)
    today = now.date()
    print(f"=== wheat_ndvi tick {now:%Y-%m-%d %H:%M} UTC")
    cdl_tick(today)
    if ndvi_tick(today):
        silver_tick()
    progress_tick(now)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Live satellite wheat NDVI (daily poll)")
    p.add_argument("--once", action="store_true", help="run one tick and exit (cron / launchd)")
    args = p.parse_args()
    if args.once:
        daily_tick()
    else:
        poll.run(task=daily_tick, interval="1d", offset_ms=RUN_AT_UTC * 3600 * 1000)
