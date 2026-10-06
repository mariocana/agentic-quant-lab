"""USDA Cropland Data Layer (CDL) - annual national crop classification raster.

https://www.nass.usda.gov/Research_and_Science/Cropland/Release/
One GeoTIFF per year, 30 m pixels over the lower 48, in the CDL's own
Albers equal-area CRS (EPSG:5070). Each pixel holds a crop class code
(24 = winter wheat, 1 = corn, 5 = soybeans, ...).

Not a HistoricalConnector: the natural grain is one raster per year, and
nothing goes to Delta. The raster is the cache:

    fetch(year)  -> Path of {BRONZE_ROOT}/usda_cdl/{year}_30m_cdls.tif
                    first call downloads the ~3 GB zip and unzips it
                    (~10 GB), later calls are a file lookup.
    clip(bbox, year)            -> CDL classes inside a lon/lat bbox
    crop_mask(bbox, year, cls)  -> boolean DataArray (True = that crop)

Two cache levels:
  1. the national raster per year (~10 GB unzipped), needed only to cut
     new windows;
  2. the clipped window per (year, bbox) in usda_cdl/clips/ (KB-MB).
     Once an AOI is clipped, drop_national(year) frees the 10 GB and
     re-runs over the same AOI never touch the national file again.
clip() never loads the national raster: rioxarray opens it lazily and
reads only the window that covers the bbox.

Publication: the CDL for year N is released around Jan-Feb of N+1.
Asking for a year not yet published raises CDLNotPublished, so callers
can fall back to the previous year (see sentinel2_ndvi_rest).
"""
import shutil
import zipfile
from pathlib import Path

import httpx
import rioxarray
import xarray as xr
from rasterio.warp import transform_bounds

from quantlake.config import BRONZE_ROOT

_URL = "https://www.nass.usda.gov/Research_and_Science/Cropland/Release/datasets/{year}_30m_cdls.zip"

WINTER_WHEAT = 24


class CDLNotPublished(Exception):
    """USDA has no CDL for this year (yet)."""


class CDLConnector:

    def __init__(self, cache_dir: Path | None = None, timeout: float = 600.0):
        self.cache_dir = Path(cache_dir or BRONZE_ROOT / "usda_cdl")
        self._timeout = timeout

    # ── Download + cache ──────────────────────────────────────────────────

    def cached(self, year: int) -> Path | None:
        """Path of the national GeoTIFF if already on disk, else None."""
        if not self.cache_dir.exists():
            return None
        return next(self.cache_dir.rglob(f"{year}_30m_cdls.tif"), None)

    def is_published(self, year: int) -> bool:
        """True if USDA serves the CDL zip for `year`. Reads headers only."""
        if self.cached(year) is not None:
            return True
        with httpx.stream("GET", _URL.format(year=year), timeout=60, follow_redirects=True) as r:
            return r.status_code == 200

    def fetch(self, year: int) -> Path:
        """Return the national CDL GeoTIFF for `year`, downloading it once."""
        hit = self.cached(year)
        if hit is not None:
            return hit

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        zip_path = self.cache_dir / f"{year}_30m_cdls.zip"
        part = zip_path.with_suffix(".zip.part")
        url = _URL.format(year=year)
        print(f"  CDL {year}: downloading {url} (~3 GB, one-time)")
        with httpx.stream("GET", url, timeout=self._timeout, follow_redirects=True) as r:
            if r.status_code == 404:
                raise CDLNotPublished(f"no CDL for {year} at {url}")
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            done = 0
            with open(part, "wb") as f:
                for chunk in r.iter_bytes(chunk_size=16 * 1024 * 1024):
                    f.write(chunk)
                    done += len(chunk)
                    if total:
                        print(f"\r    {100 * done / total:5.1f}%", end="", flush=True)
            print()
        # Rename only once complete: an interrupted download never looks cached.
        part.rename(zip_path)

        print(f"  CDL {year}: unzipping (~10 GB)")
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(self.cache_dir / str(year))
        zip_path.unlink()

        tif = self.cached(year)
        if tif is None:
            raise FileNotFoundError(f"{year}_30m_cdls.tif not found in the CDL zip")
        return tif

    # ── Read a window ─────────────────────────────────────────────────────

    def clip(self, bbox_lonlat: tuple[float, float, float, float], year: int) -> xr.DataArray:
        """CDL classes inside a [min_lon, min_lat, max_lon, max_lat] bbox.

        Stays in the CDL's native CRS (written on the DataArray via rioxarray),
        so it can be reprojected onto any other grid later.
        """
        clip_path = self.cache_dir / "clips" / f"{year}_{_bbox_key(bbox_lonlat)}.tif"
        if clip_path.exists():
            return rioxarray.open_rasterio(clip_path).squeeze("band", drop=True).load()

        cdl = rioxarray.open_rasterio(self.fetch(year)).squeeze("band", drop=True)
        bbox_proj = transform_bounds("EPSG:4326", cdl.rio.crs, *bbox_lonlat)
        window = cdl.rio.clip_box(*bbox_proj).load()
        clip_path.parent.mkdir(parents=True, exist_ok=True)
        window.rio.to_raster(clip_path, compress="deflate")
        return window

    def drop_national(self, year: int) -> None:
        """Delete the national raster of `year` (clipped windows are kept)."""
        tif = self.cached(year)
        if tif is None:
            return
        year_dir = self.cache_dir / str(year)
        if year_dir in tif.parents:
            shutil.rmtree(year_dir)
        else:
            tif.unlink()

    def crop_mask(self, bbox_lonlat, year: int, crop_class: int = WINTER_WHEAT) -> xr.DataArray:
        """uint8 DataArray, 1 where the CDL says `crop_class`, CRS preserved."""
        cdl = self.clip(bbox_lonlat, year)
        return (cdl == crop_class).astype("uint8").rio.write_crs(cdl.rio.crs)


def _bbox_key(bbox) -> str:
    return "_".join(f"{v:.5f}" for v in bbox).replace("-", "m")
