"""CUSIP -> ticker via OpenFIGI, cached in data/reference/cusip_ticker (parquet).

13F filings identify securities by CUSIP only. OpenFIGI (Bloomberg, free)
maps them: without a key 25 requests/minute of 10 CUSIPs each; with
OPENFIGI_API_KEY in .env 100 per request. The US composite listing
(exchCode "US") is preferred; "BRK/B" becomes "BRK.B". CUSIPs OpenFIGI does
not know are cached as null too, so each code is asked once.
"""
import os
import time

import httpx
import polars as pl

from quantlake.config import REFERENCE_ROOT

PATH = REFERENCE_ROOT / "cusip_ticker.parquet"
URL = "https://api.openfigi.com/v3/mapping"


def load() -> pl.DataFrame:
    if PATH.exists():
        return pl.read_parquet(PATH)
    return pl.DataFrame(schema={"cusip": pl.String, "ticker": pl.String, "figi_name": pl.String})


def _pick(data: list[dict]) -> tuple[str | None, str | None]:
    if not data:
        return None, None
    best = next((d for d in data if d.get("exchCode") == "US"), data[0])
    t = best.get("ticker")
    return (t.replace("/", ".") if t else None), best.get("name")


def resolve(cusips: list[str], log=print) -> pl.DataFrame:
    """Mapping for every CUSIP asked (from the cache, missing ones fetched)."""
    cache = load()
    known = set(cache["cusip"].to_list())
    todo = sorted({c for c in cusips if c and c not in known})
    key = os.getenv("OPENFIGI_API_KEY")
    batch, pause = (100, 0.25) if key else (10, 2.5)
    headers = {"Content-Type": "application/json", **({"X-OPENFIGI-APIKEY": key} if key else {})}
    new = []
    with httpx.Client(timeout=30, headers=headers) as client:
        for i in range(0, len(todo), batch):
            chunk = todo[i:i + batch]
            for attempt in range(5):
                r = client.post(URL, json=[{"idType": "ID_CUSIP", "idValue": c} for c in chunk])
                if r.status_code == 429:
                    time.sleep(10 * (attempt + 1))
                    continue
                r.raise_for_status()
                break
            for c, res in zip(chunk, r.json()):
                t, name = _pick(res.get("data") or [])
                new.append({"cusip": c, "ticker": t, "figi_name": name})
            if i // batch % 20 == 0 and len(todo) > batch:
                log(f"  openfigi {min(i + batch, len(todo))}/{len(todo)}")
            time.sleep(pause)
    if new:
        cache = pl.concat([cache, pl.DataFrame(new, schema=cache.schema)]).unique("cusip", keep="last")
        PATH.parent.mkdir(parents=True, exist_ok=True)
        cache.write_parquet(PATH)
    return cache.filter(pl.col("cusip").is_in(cusips))
