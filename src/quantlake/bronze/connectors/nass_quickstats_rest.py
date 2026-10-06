"""USDA NASS QuickStats - county yields and weekly Crop Progress.

Ground truth for the satellite NDVI pipeline (02/03 notebooks). Same API
and key as usda_nass.py (NASS_API_KEY in .env), different statistics:

  county_yields(state, county, ...)  annual yield, bu/acre, per county
      symbol suggestion: f"{STATE}_{COUNTY}"   e.g. KS_SUMNER
  crop_progress(state, ...)          % of the crop at each stage, weekly
      symbol suggestion: f"{STATE}_{STAGE}"    e.g. KS_HEADED
      (one symbol per stage, so (symbol, timestamp) stays unique)

Vintage:
  - Crop Progress covers the week ending Sunday and is released Monday
    16:00 ET (Tuesday after a federal holiday - not modelled).
  - County estimates for small grains come out the following winter;
    rows are stamped conservatively at Mar 1 of year+1, 16:00 ET.
    Later than the real release rather than earlier: no look-ahead.

Columns:
  county_yields: timestamp, crop_year, state, county, commodity, class_desc, yield_bu_acre
  crop_progress: timestamp, week_ending, crop_year, state, commodity, class_desc, stage, pct
(`crop_year`, not `year`: bronze adds `year`/`month` partition columns
from the timestamp, which would silently overwrite it.)
"""
import os
import re
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import httpx
import polars as pl

from quantlake.bronze.connectors.usda_nass import _parse_value

_QUICKSTATS_URL = "https://quickstats.nass.usda.gov/api/api_GET/"
_ET = ZoneInfo("America/New_York")
_STAGE_RE = re.compile(r"MEASURED IN PCT (.+)$")

YIELD_RELEASE = (3, 1)  # (month, day) of year + 1


def _et_to_utc(d: date, hh: int = 16) -> datetime:
    return datetime.combine(d, time(hh, 0), tzinfo=_ET).astimezone(ZoneInfo("UTC"))


class NASSQuickStatsConnector:

    YIELD_TABLE = "nass_county_yield"
    PROGRESS_TABLE = "nass_crop_progress"

    def __init__(self, api_key: str | None = None, timeout: float = 60.0):
        self.api_key = api_key or os.getenv("NASS_API_KEY")
        if not self.api_key:
            raise ValueError("NASS_API_KEY missing - set it in .env")
        self._timeout = timeout

    def query(self, params: dict) -> list[dict]:
        """Raw QuickStats rows. NASS answers 400 when nothing matches."""
        p = {"key": self.api_key, "format": "JSON", **params}
        with httpx.Client(timeout=self._timeout) as client:
            resp = client.get(_QUICKSTATS_URL, params=p)
        if resp.status_code == 400 and "no data" in resp.text.lower():
            return []
        resp.raise_for_status()
        return resp.json().get("data") or []

    def county_yields(
        self,
        state: str,
        county: str,
        commodity: str = "WHEAT",
        class_desc: str = "WINTER",
        year_start: int = 2000,
        year_end: int | None = None,
    ) -> pl.DataFrame:
        params = {
            "source_desc":       "SURVEY",
            "commodity_desc":    commodity,
            "statisticcat_desc": "YIELD",
            "unit_desc":         "BU / ACRE",
            "agg_level_desc":    "COUNTY",
            "state_alpha":       state,
            "county_name":       county,
            "year__GE":          year_start,
        }
        if year_end is not None:
            params["year__LE"] = year_end
        rows = [
            r for r in self.query(params)
            if (r.get("class_desc") or "").upper() == class_desc
            and (r.get("prodn_practice_desc") or "ALL PRODUCTION PRACTICES") == "ALL PRODUCTION PRACTICES"
            and (r.get("reference_period_desc") or "YEAR") == "YEAR"
        ]
        if not rows:
            return pl.DataFrame(schema=_YIELD_SCHEMA)
        m, d = YIELD_RELEASE
        return pl.DataFrame(
            {
                "timestamp":     [_et_to_utc(date(int(r["year"]) + 1, m, d)) for r in rows],
                "crop_year":     [int(r["year"]) for r in rows],
                "state":         state,
                "county":        county,
                "commodity":     commodity,
                "class_desc":    class_desc,
                "yield_bu_acre": [_parse_value(r.get("Value")) for r in rows],
            },
            schema=_YIELD_SCHEMA,
        ).unique(subset="crop_year", keep="last").sort("crop_year")

    def crop_progress(
        self,
        state: str,
        commodity: str = "WHEAT",
        class_desc: str = "WINTER",
        year_start: int = 2000,
        year_end: int | None = None,
    ) -> pl.DataFrame:
        params = {
            "source_desc":       "SURVEY",
            "commodity_desc":    commodity,
            "statisticcat_desc": "PROGRESS",
            "agg_level_desc":    "STATE",
            "state_alpha":       state,
            "year__GE":          year_start,
        }
        if year_end is not None:
            params["year__LE"] = year_end
        parsed = []
        for r in self.query(params):
            short = r.get("short_desc") or ""
            stage = _STAGE_RE.search(short)
            if class_desc not in short or not stage or not r.get("week_ending"):
                continue
            week_ending = date.fromisoformat(r["week_ending"][:10])
            parsed.append({
                "timestamp":   _et_to_utc(week_ending + timedelta(days=1)),
                "week_ending": week_ending,
                "crop_year":   int(r["year"]),
                "state":       state,
                "commodity":   commodity,
                "class_desc":  class_desc,
                "stage":       stage.group(1).strip(),
                "pct":         _parse_value(r.get("Value")),
            })
        if not parsed:
            return pl.DataFrame(schema=_PROGRESS_SCHEMA)
        return (
            pl.DataFrame(parsed, schema=_PROGRESS_SCHEMA)
            .unique(subset=["stage", "week_ending"], keep="last")
            .sort(["stage", "week_ending"])
        )


_YIELD_SCHEMA = {
    "timestamp":     pl.Datetime("us", "UTC"),
    "crop_year":     pl.Int32,
    "state":         pl.Utf8,
    "county":        pl.Utf8,
    "commodity":     pl.Utf8,
    "class_desc":    pl.Utf8,
    "yield_bu_acre": pl.Float64,
}

_PROGRESS_SCHEMA = {
    "timestamp":   pl.Datetime("us", "UTC"),
    "week_ending": pl.Date,
    "crop_year":   pl.Int32,
    "state":       pl.Utf8,
    "commodity":   pl.Utf8,
    "class_desc":  pl.Utf8,
    "stage":       pl.Utf8,
    "pct":         pl.Float64,
}
