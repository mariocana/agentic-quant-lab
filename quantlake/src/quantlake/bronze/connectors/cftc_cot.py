"""CFTC Commitments of Traders — Legacy, Futures Only (weekly).

Official CFTC Public Reporting API (Socrata), dataset 6dca-aqww:
https://publicreporting.cftc.gov/resource/6dca-aqww.json

One request per contract (cftc_contract_market_code, e.g. "099741" =
EURO FX), paginated with $limit/$offset. History goes back to 1986.

Vintage. Each report reflects positions as of Tuesday close but is only
published the following Friday at 15:30 US Eastern. Stamping the row on
the Tuesday would leak three days of future information into any join,
so `timestamp` is the Friday release (Tuesday + 3 days, 15:30 ET,
DST-aware, converted to UTC). The Tuesday is kept in `report_date`.
Holiday weeks (and government shutdowns) delay the release: those rows
are stamped earlier than the real publication. Close enough for weekly
features, but worth knowing.

Socrata rejects anonymous bot-looking traffic (403), so requests carry a
browser User-Agent and, if set in .env, CFTC_APP_TOKEN as X-App-Token
(free: https://publicreporting.cftc.gov/profile/edit/developer_settings).

Columns returned: timestamp (release UTC), report_date, cftc_code,
market_name, open_interest, nc_long, nc_short, nc_spread, comm_long,
comm_short, nonrept_long, nonrept_short.
"""
import os
import time
from datetime import datetime, timedelta

import httpx
import polars as pl

from quantlake.bronze.base import HistoricalConnector
from quantlake.helper import to_utc

_URL = "https://publicreporting.cftc.gov/resource/6dca-aqww.json"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36",
    "Accept": "application/json",
}
_PAGE_LIMIT = 5000

# output column -> Socrata field(s). Several names per column because the
# dataset carries a historic typo ("postions") on the spreading field.
_FIELDS = {
    "open_interest": ["open_interest_all"],
    "nc_long":       ["noncomm_positions_long_all"],
    "nc_short":      ["noncomm_positions_short_all"],
    "nc_spread":     ["noncomm_postions_spread_all", "noncomm_positions_spread_all"],
    "comm_long":     ["comm_positions_long_all"],
    "comm_short":    ["comm_positions_short_all"],
    "nonrept_long":  ["nonrept_positions_long_all"],
    "nonrept_short": ["nonrept_positions_short_all"],
}

SCHEMA = {
    "timestamp":   pl.Datetime("us", "UTC"),
    "report_date": pl.Date,
    "cftc_code":   pl.Utf8,
    "market_name": pl.Utf8,
    **{col: pl.Int64 for col in _FIELDS},
}


class CFTCCOTConnector(HistoricalConnector):

    TABLE_NAME = "cftc_cot"
    RELEASE_TIME_ET = "15:30"
    RELEASE_LAG_DAYS = 3  # Tuesday as-of -> Friday release

    def __init__(self, app_token: str | None = None, pause_s: float = 0.4):
        self.app_token = app_token or os.getenv("CFTC_APP_TOKEN")
        self.pause_s = pause_s

    def fetch(self, symbol: str, start: datetime, end: datetime) -> pl.DataFrame:
        """symbol is the CFTC contract market code (e.g. "099741").

        start/end bound the release timestamp, so incremental callers can
        pass last_bronze_ts(...) directly.
        """
        start, end = to_utc(start), to_utc(end)
        # Server-side filter on report_date (Tuesday); widen by the release
        # lag and trim precisely on `timestamp` below.
        since = (start - timedelta(days=self.RELEASE_LAG_DAYS + 1)).date()
        until = end.date()
        where = (
            f"cftc_contract_market_code='{symbol}' AND "
            f"report_date_as_yyyy_mm_dd >= '{since.isoformat()}T00:00:00.000' AND "
            f"report_date_as_yyyy_mm_dd <= '{until.isoformat()}T00:00:00.000'"
        )
        rows: list[dict] = []
        offset = 0
        while True:
            page = self._get({
                "$where":  where,
                "$order":  "report_date_as_yyyy_mm_dd ASC",
                "$limit":  _PAGE_LIMIT,
                "$offset": offset,
            })
            rows.extend(page)
            if len(page) < _PAGE_LIMIT:
                break
            offset += _PAGE_LIMIT
            time.sleep(self.pause_s)

        if not rows:
            return pl.DataFrame(schema=SCHEMA)

        df = pl.DataFrame(
            {
                "report_date": [r["report_date_as_yyyy_mm_dd"][:10] for r in rows],
                "cftc_code":   [r.get("cftc_contract_market_code", symbol) for r in rows],
                "market_name": [r.get("market_and_exchange_names") for r in rows],
                **{col: [_pick_int(r, names) for r in rows] for col, names in _FIELDS.items()},
            },
            schema_overrides={col: pl.Int64 for col in _FIELDS},
        ).with_columns(pl.col("report_date").str.to_date("%Y-%m-%d"))

        df = df.with_columns(
            (
                (pl.col("report_date") + pl.duration(days=self.RELEASE_LAG_DAYS)).cast(pl.Utf8)
                + f" {self.RELEASE_TIME_ET}"
            )
            .str.to_datetime(format="%Y-%m-%d %H:%M", time_zone="America/New_York")
            .dt.convert_time_zone("UTC")
            .cast(pl.Datetime("us", "UTC"))
            .alias("timestamp")
        )
        return (
            df.filter(pl.col("timestamp").is_between(start, end))
            .unique(subset="report_date", keep="last")
            .select(list(SCHEMA))
            .sort("timestamp")
        )

    def _get(self, params: dict, max_attempts: int = 4) -> list[dict]:
        headers = dict(_HEADERS)
        if self.app_token:
            headers["X-App-Token"] = self.app_token
        last_err: Exception | None = None
        with httpx.Client(timeout=30, headers=headers, follow_redirects=True) as client:
            for attempt in range(1, max_attempts + 1):
                try:
                    resp = client.get(_URL, params=params)
                    resp.raise_for_status()
                    return resp.json()
                except httpx.HTTPStatusError as e:
                    last_err = e
                    # 403/429 = Socrata throttling: back off harder.
                    throttled = e.response.status_code in (403, 429)
                    if attempt < max_attempts:
                        time.sleep(3 * attempt if throttled else 2 ** attempt)
                except (httpx.TransportError, ValueError) as e:
                    last_err = e
                    if attempt < max_attempts:
                        time.sleep(2 ** attempt)
        raise RuntimeError(f"CFTC API failed after {max_attempts} attempts: {last_err}")


def _pick_int(row: dict, names: list[str]) -> int | None:
    for name in names:
        v = row.get(name)
        if v not in (None, ""):
            return int(float(v))
    return None
