"""Sentinel-2 NDVI over the pixels of one crop, per acquisition date.

Wraps the 02/03 satellite notebooks in a HistoricalConnector:

    Planetary Computer STAC (sentinel-2-l2a, free, no auth)
      -> lazy (time, y, x) cube of B04 / B08 / SCL at 10 m   (odc.stac + dask)
      -> NDVI = (NIR - RED) / (NIR + RED), cloud pixels dropped via SCL
      -> USDA CDL crop mask (30 m Albers) reprojected onto the S2 UTM grid,
         eroded to drop mixed field-edge pixels
      -> one row per acquisition date: mean / std NDVI over the crop pixels

symbol is the AOI id (e.g. "KS_SUMNER_5KM"); the bbox and crop class are
connector parameters, like the lat/lon of OpenMeteoConnector.

Seasons. Winter wheat is sown in September of N-1 and harvested in June-
July of N: "season N" runs from Sept 1 of N-1 to Aug 31 of N. fetch()
splits [start, end] by season because the crop mask comes from the CDL
of the harvest year (wheat fields move between years). If that CDL is
not published yet (the current season), the most recent published one
among the CDL_FALLBACK_YEARS before it is used and `cdl_year` says so.
Between Sept and Jan of a live season even N-1 is not out yet (CDL N-1
lands in Jan-Feb of N), hence the 2-year fallback.

Two fixes vs the notebooks:

1. Processing baseline 04.00. Since 2022-01-25 ESA adds +1000 to L2A
   reflectances (BOA_ADD_OFFSET). Raw digital numbers from 2021 and 2023
   are on different scales, and NDVI on the shifted ones is biased low
   (e.g. red 500 / nir 3000: 0.71 true vs 0.45 unshifted). harmonize()
   removes the offset after the cutoff, as in Planetary Computer's own
   "harmonize_to_old" recipe, so multi-year anomalies compare like with
   like.
2. SCL 0 (no data) and 1 (saturated/defective) are masked too. Pixels
   outside the swath are 0 in every band and would count as NDVI = 0.

Vintage. An L2A scene is processed and published within about a day,
so `timestamp` = acquisition date + 1 day (00:00 UTC). `acq_date` keeps
the real date.

Columns: timestamp, acq_date, season, doy_season, cdl_year, crop_class,
ndvi_mean, ndvi_std, n_valid, n_mask, valid_frac.
"""
from datetime import date, datetime, timedelta

import numpy as np
import polars as pl
import xarray as xr
from rasterio.enums import Resampling
from scipy.ndimage import binary_erosion

from quantlake.bronze.base import HistoricalConnector
from quantlake.bronze.connectors.cdl_rest import WINTER_WHEAT, CDLConnector, CDLNotPublished
from quantlake.helper import to_utc

_STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
_COLLECTION = "sentinel-2-l2a"
_BANDS = ["B04", "B08", "SCL"]

# SCL: 0 no data, 1 saturated/defective, 3 cloud shadow, 8/9 cloud medium/high,
# 10 thin cirrus, 11 snow.
BAD_SCL = [0, 1, 3, 8, 9, 10, 11]

CDL_FALLBACK_YEARS = 2

BASELINE_0400_CUTOFF = np.datetime64("2022-01-25")
BOA_OFFSET = 1000

SCHEMA = {
    "timestamp":  pl.Datetime("us", "UTC"),
    "acq_date":   pl.Date,
    "season":     pl.Int32,
    "doy_season": pl.Int32,
    "cdl_year":   pl.Int32,
    "crop_class": pl.Int32,
    "ndvi_mean":  pl.Float64,
    "ndvi_std":   pl.Float64,
    "n_valid":    pl.Int64,
    "n_mask":     pl.Int64,
    "valid_frac": pl.Float64,
}


class Sentinel2NDVIConnector(HistoricalConnector):

    TABLE_NAME = "sentinel2_ndvi"

    def __init__(
        self,
        bbox: tuple[float, float, float, float],
        crop_class: int = WINTER_WHEAT,
        erode_iterations: int = 3,
        max_cloud: float = 30,
        season_start_month: int = 9,
        resolution: int = 10,
        chunk: int = 2048,
        cdl: CDLConnector | None = None,
    ):
        self.bbox = tuple(bbox)
        self.crop_class = crop_class
        self.erode_iterations = erode_iterations
        self.max_cloud = max_cloud
        self.season_start_month = season_start_month
        self.resolution = resolution
        self.chunk = chunk
        self.cdl = cdl or CDLConnector()
        self._catalog = None

    # ── Public API ────────────────────────────────────────────────────────

    def fetch(self, symbol: str, start: datetime, end: datetime) -> pl.DataFrame:
        frames = [
            self.fetch_season(season, s_start, s_end)
            for season, s_start, s_end in self.seasons(to_utc(start).date(), to_utc(end).date())
        ]
        frames = [f for f in frames if not f.is_empty()]
        if not frames:
            return pl.DataFrame(schema=SCHEMA)
        return pl.concat(frames).sort("timestamp")

    def fetch_season(self, season: int, start: date | None = None, end: date | None = None) -> pl.DataFrame:
        """NDVI rows for one season, optionally restricted to [start, end]."""
        s_start, s_end = self.season_bounds(season)
        start, end = max(start or s_start, s_start), min(end or s_end, s_end)

        items = self._search(start, end)
        print(f"  season {season}: {len(items)} S2 scenes {start} -> {end}")
        if not items:
            return pl.DataFrame(schema=SCHEMA)

        s2 = harmonize(self._load(items))
        ndvi = compute_ndvi(s2)
        cdl_mask, cdl_year = self._cdl_mask(season)
        mask = crop_mask_on_grid(cdl_mask, s2, self.erode_iterations)
        n_mask = int(mask.sum())
        print(f"  season {season}: {n_mask} crop pixels on the S2 grid (CDL {cdl_year})")
        if n_mask == 0:
            return pl.DataFrame(schema=SCHEMA)

        df = aggregate(ndvi, mask)
        return df.with_columns(
            (pl.col("acq_date").cast(pl.Datetime("us")) + pl.duration(days=1))
            .dt.replace_time_zone("UTC").alias("timestamp"),
            pl.lit(season, pl.Int32).alias("season"),
            (pl.col("acq_date") - pl.lit(s_start)).dt.total_days().cast(pl.Int32).alias("doy_season"),
            pl.lit(cdl_year, pl.Int32).alias("cdl_year"),
            pl.lit(self.crop_class, pl.Int32).alias("crop_class"),
            pl.lit(n_mask, pl.Int64).alias("n_mask"),
        ).with_columns(
            (pl.col("n_valid") / pl.col("n_mask")).alias("valid_frac"),
        ).select(list(SCHEMA))

    def season_bounds(self, season: int) -> tuple[date, date]:
        start = date(season - 1, self.season_start_month, 1)
        return start, date(season, self.season_start_month, 1) - timedelta(days=1)

    def season_of(self, d: date) -> int:
        return d.year + 1 if d.month >= self.season_start_month else d.year

    def seasons(self, start: date, end: date) -> list[tuple[int, date, date]]:
        out = []
        for season in range(self.season_of(start), self.season_of(end) + 1):
            s_start, s_end = self.season_bounds(season)
            out.append((season, max(start, s_start), min(end, s_end)))
        return out

    # ── Sources (overridable in tests) ────────────────────────────────────

    def _search(self, start: date, end: date) -> list:
        if self._catalog is None:
            import planetary_computer
            from pystac_client import Client
            self._catalog = Client.open(_STAC_URL, modifier=planetary_computer.sign_inplace)
        search = self._catalog.search(
            collections=[_COLLECTION],
            bbox=self.bbox,
            datetime=f"{start.isoformat()}/{end.isoformat()}",
            query={"eo:cloud_cover": {"lt": self.max_cloud}},
        )
        return list(search.items())

    def _load(self, items: list) -> xr.Dataset:
        import odc.stac
        return odc.stac.load(
            items,
            bands=_BANDS,
            bbox=self.bbox,
            resolution=self.resolution,
            groupby="solar_day",            # merge tiles acquired the same day
            chunks={"x": self.chunk, "y": self.chunk},  # lazy (dask)
        )

    def _cdl_mask(self, season: int) -> tuple[xr.DataArray, int]:
        """Crop mask from the harvest-year CDL, else the latest published before it."""
        for year in range(season, season - CDL_FALLBACK_YEARS - 1, -1):
            try:
                return self.cdl.crop_mask(self.bbox, year, self.crop_class), year
            except CDLNotPublished:
                print(f"  CDL {year} not published, trying {year - 1}")
        raise CDLNotPublished(f"no CDL for {season} or the {CDL_FALLBACK_YEARS} years before")


# ── Pure raster steps (no network) ────────────────────────────────────────

def harmonize(s2: xr.Dataset) -> xr.Dataset:
    """Remove the +1000 BOA offset from reflectances acquired since baseline 04.00."""
    new = s2["time"] >= BASELINE_0400_CUTOFF
    out = s2.copy()
    for band in ("B04", "B08"):
        shifted = out[band].clip(min=BOA_OFFSET) - BOA_OFFSET
        out[band] = xr.where(new, shifted, out[band]).astype(out[band].dtype)
    return out


def compute_ndvi(s2: xr.Dataset) -> xr.DataArray:
    """Per-pixel NDVI, NaN where SCL flags the pixel or reflectance is zero."""
    valid = ~s2["SCL"].isin(BAD_SCL)
    red = s2["B04"].where(valid).astype("float32")
    nir = s2["B08"].where(valid).astype("float32")
    denom = nir + red
    return ((nir - red) / denom).where(denom > 0)


def crop_mask_on_grid(cdl_mask: xr.DataArray, s2: xr.Dataset, erode_iterations: int) -> xr.DataArray:
    """Reproject the 30 m CDL mask onto the 10 m S2 grid, then erode it.

    Nearest neighbour: class codes are categorical, interpolating would
    invent values. Erosion by k pixels drops the outer k*10 m of each
    field, where pixels mix wheat with roads and fence rows.
    """
    target = s2["SCL"].isel(time=0).rio.write_crs(s2.odc.crs.to_wkt())
    mask = cdl_mask.rio.reproject_match(target, resampling=Resampling.nearest) > 0
    values = mask.values
    if erode_iterations:
        values = binary_erosion(values, iterations=erode_iterations)
    return xr.DataArray(values, dims=("y", "x"), coords={"y": s2["y"], "x": s2["x"]})


def aggregate(ndvi: xr.DataArray, mask: xr.DataArray) -> pl.DataFrame:
    """One row per date: mean / std NDVI and count of valid crop pixels."""
    masked = ndvi.where(mask)
    stats = xr.Dataset({
        "ndvi_mean": masked.mean(dim=["y", "x"]),
        "ndvi_std":  masked.std(dim=["y", "x"]),
        "n_valid":   masked.notnull().sum(dim=["y", "x"]),
    }).compute()
    df = pl.DataFrame({
        "acq_date":  [np.datetime64(t, "D").astype(date) for t in stats["time"].values],
        "ndvi_mean": stats["ndvi_mean"].values.astype("float64"),
        "ndvi_std":  stats["ndvi_std"].values.astype("float64"),
        "n_valid":   stats["n_valid"].values.astype("int64"),
    })
    return df.filter(pl.col("n_valid") > 0)
