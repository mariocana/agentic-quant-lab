"""Satellite wheat NDVI backfill -> bronze + silver.

For every AOI in symbols.NDVI_AOIS and every season:
    bronze/sentinel2_ndvi       per-date NDVI on eroded crop pixels
                                partitioned (bbox_id, year, month),
                                idempotent on (bbox_id, date)
    bronze/nass_county_yield    county yields (symbol STATE_COUNTY)
    bronze/nass_crop_progress   weekly stage % (symbol STATE_STAGE)
    silver/sentinel2_ndvi_anomaly   anomaly vs prior seasons

Resumable: a finished season already in bronze is skipped; the season in
progress resumes from its last acquisition date.

Run:
    .venv/bin/python applications/historical/wheat_ndvi.py                 # NDVI_SEASONS
    .venv/bin/python applications/historical/wheat_ndvi.py 2019 2020 2022  # other seasons
    .venv/bin/python applications/historical/wheat_ndvi.py --drop-cdl      # free the 10 GB rasters after clipping
"""
import argparse
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import polars as pl
from deltalake import DeltaTable
from dotenv import load_dotenv

import quantlake.bronze.ingest as bronze
import quantlake.silver.ndvi as silver_ndvi
from quantlake.bronze.connectors.cdl_rest import CDLConnector
from quantlake.bronze.connectors.nass_quickstats_rest import NASSQuickStatsConnector
from quantlake.bronze.connectors.sentinel2_ndvi_rest import Sentinel2NDVIConnector
from quantlake.config import BRONZE_ROOT
from symbols import NDVI_AOIS, NDVI_SEASONS

load_dotenv()

TABLE = Sentinel2NDVIConnector.TABLE_NAME
BRONZE_PATH = str(BRONZE_ROOT / TABLE)


def last_acq_by_season(bbox_id: str) -> dict[int, date]:
    if not DeltaTable.is_deltatable(BRONZE_PATH):
        return {}
    df = pl.from_arrow(DeltaTable(BRONZE_PATH).to_pyarrow_table(
        columns=["season", "acq_date"], filters=[("symbol", "=", bbox_id)]))
    if df.is_empty():
        return {}
    return dict(df.group_by("season").agg(pl.col("acq_date").max()).iter_rows())


def backfill_ndvi(seasons: list[int], drop_cdl: bool) -> None:
    cdl = CDLConnector()
    today = datetime.now(timezone.utc).date()
    for aoi in NDVI_AOIS:
        connector = Sentinel2NDVIConnector(aoi.bbox, crop_class=aoi.crop_class, cdl=cdl)
        done = last_acq_by_season(aoi.bbox_id)
        for season in seasons:
            s_start, s_end = connector.season_bounds(season)
            if s_start > today:
                print(f"[{aoi.bbox_id}] season {season} not started")
                continue
            last = done.get(season)
            if last is not None and s_end < today:
                print(f"[{aoi.bbox_id}] season {season} complete in bronze, skip")
                continue
            start = last + timedelta(days=1) if last else s_start
            df = connector.fetch_season(season, start, min(s_end, today))
            if df.is_empty():
                print(f"[{aoi.bbox_id}] season {season}: no new dates")
                continue
            bronze.save(bronze.add_partition_columns(df, symbol=aoi.bbox_id), TABLE)
            print(f"[{aoi.bbox_id}] season {season}: {len(df)} dates, "
                  f"peak NDVI {df['ndvi_mean'].max():.2f} (CDL {df['cdl_year'][0]})")
    if drop_cdl:  # after every AOI: they may share the same national rasters
        for year in sorted({y for s in seasons for y in (s, s - 1)}):
            cdl.drop_national(year)


def backfill_nass(seasons: list[int]) -> None:
    if not os.getenv("NASS_API_KEY"):
        print("NASS_API_KEY missing - skipping yields and crop progress")
        return
    nass = NASSQuickStatsConnector()
    first = min(seasons) - 1
    for state, county in sorted({(a.state, a.county) for a in NDVI_AOIS}):
        df = nass.county_yields(state, county, year_start=first)
        if not df.is_empty():
            bronze.save(bronze.add_partition_columns(df, symbol=f"{state}_{county}"), nass.YIELD_TABLE)
        print(f"[{state}_{county}] {len(df)} yearly yields")
    for state in sorted({a.state for a in NDVI_AOIS}):
        df = nass.crop_progress(state, year_start=first)
        for (stage,), g in df.group_by("stage"):
            bronze.save(bronze.add_partition_columns(g, symbol=f"{state}_{stage}"), nass.PROGRESS_TABLE)
        print(f"[{state}] crop progress: {len(df)} rows, stages {sorted(df['stage'].unique().to_list())}")


def rebuild_silver() -> None:
    if not DeltaTable.is_deltatable(BRONZE_PATH):
        return
    df = silver_ndvi.rebuild(pl.from_arrow(DeltaTable(BRONZE_PATH).to_pyarrow_table()))
    print(f"silver/{silver_ndvi.TABLE}: {len(df)} rows")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Sentinel-2 crop NDVI backfill")
    p.add_argument("seasons", nargs="*", type=int, help="harvest years (default: symbols.NDVI_SEASONS)")
    p.add_argument("--drop-cdl", action="store_true",
                   help="delete national CDL rasters once the AOI windows are cached")
    args = p.parse_args()
    seasons = sorted(args.seasons or NDVI_SEASONS)
    backfill_ndvi(seasons, args.drop_cdl)
    backfill_nass(seasons)
    rebuild_silver()
