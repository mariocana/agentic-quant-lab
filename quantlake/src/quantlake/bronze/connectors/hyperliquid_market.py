"""Hyperliquid market state, as the Hyperliquid bridge (formerly trading-desk) recorded it.

The desk samples `metaAndAssetCtxs` every hour for the main dex and every HIP-3
dex, and serves one gzip file per UTC day at /api/market/{day}. It is the only
source of the point-in-time universe: the API says what is listed now, never what
was listed on a past date, and never when `isDelisted` flipped. Open interest has
no history endpoint either.

Two layers, both bronze:

  _raw/hyperliquid_market/<day>.jsonl.gz   the desk's files, byte for byte. The
                                           archive: a field nobody parses today
                                           is still there tomorrow.
  hyperliquid_market                       one row per (sample, dex, asset),
                                           typed, delisted assets included.

The table is partitioned by (dex, year, month), not by symbol like the other
bronze tables: ~560 assets sampled hourly would write one tiny file per asset per
run. The merge key is (timestamp, dex, asset), so re-ingesting a day never
duplicates a row.

The desk's reader is not imported: the desk depends on nothing in the lab and the
lab does not reach into the desk's package. The twenty lines are copied.
"""
from __future__ import annotations

import base64
import json
import zlib
from datetime import datetime
from pathlib import Path

import httpx
import polars as pl
from deltalake import DeltaTable, write_deltalake

TABLE_NAME = "hyperliquid_market"
RAW_DIR_NAME = "_raw/hyperliquid_market"
PARTITION_BY = ["dex", "year", "month"]
MERGE_PREDICATE = ("s.timestamp = t.timestamp AND s.dex = t.dex AND s.asset = t.asset "
                   "AND s.year = t.year AND s.month = t.month")

# ctx fields that are numbers sent as strings
_NUM = {"markPx": "mark_px", "midPx": "mid_px", "oraclePx": "oracle_px", "prevDayPx": "prev_day_px",
        "funding": "funding", "premium": "premium", "openInterest": "open_interest",
        "dayNtlVlm": "day_ntl_vlm", "dayBaseVlm": "day_base_vlm"}

SCHEMA = {
    "timestamp": pl.Datetime("us", "UTC"), "dex": pl.String, "asset": pl.String,
    "is_delisted": pl.Boolean, "only_isolated": pl.Boolean,
    "sz_decimals": pl.Int32, "max_leverage": pl.Int32, "margin_table_id": pl.Int32,
    **{v: pl.Float64 for v in _NUM.values()},
    "impact_bid_px": pl.Float64, "impact_ask_px": pl.Float64,
    "year": pl.Int32, "month": pl.Int8,
}


def _f(x) -> float | None:
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def read_samples(blob: bytes) -> list[dict]:
    """Every complete sample in a day file. A truncated last member is dropped."""
    out: list[dict] = []
    while blob:
        d = zlib.decompressobj(wbits=31)
        try:
            chunk = d.decompress(blob)
        except zlib.error:
            break
        if not d.eof:
            break
        out.extend(json.loads(x) for x in chunk.decode().splitlines() if x)
        blob = d.unused_data
    return out


def parse_sample(sample: dict) -> pl.DataFrame:
    """One sample -> one row per (dex, asset). Delisted assets are kept: when they
    stop being listed is the information."""
    ts = datetime.fromisoformat(sample["ts"])
    rows = []
    for block in sample.get("dexs", []):
        dex = block["dex"] or "main"
        meta, ctxs = block["data"]
        for u, c in zip(meta["universe"], ctxs):
            impact = c.get("impactPxs") or [None, None]
            rows.append({
                "timestamp": ts, "dex": dex, "asset": u["name"],
                "is_delisted": bool(u.get("isDelisted", False)),
                "only_isolated": bool(u.get("onlyIsolated", False)),
                "sz_decimals": u.get("szDecimals"), "max_leverage": u.get("maxLeverage"),
                "margin_table_id": u.get("marginTableId"),
                **{v: _f(c.get(k)) for k, v in _NUM.items()},
                "impact_bid_px": _f(impact[0]), "impact_ask_px": _f(impact[1]),
                "year": ts.year, "month": ts.month,
            })
    return pl.DataFrame(rows, schema=SCHEMA)


class DeskMarketSource:
    """The desk's /api/market endpoints, behind its password."""

    def __init__(self, url: str, password: str, timeout: float = 60.0):
        token = base64.b64encode(f"desk:{password}".encode()).decode()
        self.client = httpx.Client(base_url=url.rstrip("/"), timeout=timeout,
                                   headers={"Authorization": f"Basic {token}"})

    def days(self) -> list[dict]:
        r = self.client.get("/api/market")
        r.raise_for_status()
        return r.json()

    def download(self, day: str) -> bytes:
        r = self.client.get(f"/api/market/{day}")
        r.raise_for_status()
        return r.content


def pull(source, raw_dir: Path) -> list[Path]:
    """Copy every day the desk has and we don't, or that grew since. Today's file
    grows every hour, so it is fetched again until the day is over. Returns the
    files that changed."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    changed = []
    for d in source.days():
        path = raw_dir / f"{d['day']}.jsonl.gz"
        if path.exists() and path.stat().st_size == d["bytes"]:
            continue
        blob = source.download(d["day"])
        tmp = path.with_suffix(".tmp")
        tmp.write_bytes(blob)
        tmp.replace(path)                     # a half-downloaded day never looks complete
        changed.append(path)
    return changed


def ingest(paths: list[Path], table_path: str) -> int:
    """Parse day files into the bronze table. Idempotent on (timestamp, dex, asset)."""
    frames = [parse_sample(s) for p in paths for s in read_samples(p.read_bytes())]
    if not frames:
        return 0
    df = pl.concat(frames).unique(subset=["timestamp", "dex", "asset"], keep="last")
    if DeltaTable.is_deltatable(table_path):
        (DeltaTable(table_path)
         .merge(df.to_arrow(), predicate=MERGE_PREDICATE, source_alias="s", target_alias="t")
         .when_not_matched_insert_all()
         .execute())
    else:
        write_deltalake(table_path, df, mode="overwrite", partition_by=PARTITION_BY)
    return len(df)
