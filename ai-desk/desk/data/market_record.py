"""Raw market state, recorded as the exchange gave it.

The API answers "what is listed now", never "what was listed on 3 March". A
cross-sectional backtest run on today's universe is choosing, every day of the
past, among the assets that later survived: the point-in-time universe cannot be
rebuilt afterwards, and neither can open interest. So the desk keeps it, raw,
as it goes.

One sample is `metaAndAssetCtxs` for the main dex and for every HIP-3 dex, about
35 KB compressed. Samples append to one gzip file per UTC day: a gzip file may
hold several members back to back, so each sample is written whole in a single
write and a crash can at worst truncate the last one, which the reader skips.

Raw on purpose. This is bronze for quantlake: cleaning happens there, and a
field we did not know we needed today is still in the file tomorrow. The
delisting date in particular only exists here — `isDelisted` flips one day and
the API never says when.

Always mainnet, whatever the execution venue: testnet lists fewer perps and its
prices say nothing.
"""
from __future__ import annotations

import gzip
import json
import re
import zlib
from datetime import datetime, timezone
from pathlib import Path

from desk.config import VAR

MARKET_DIR = VAR / "market"
DAY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def sample(info) -> dict:
    """One reading of every perp dex. A dex that fails is recorded as failed: one
    builder's endpoint being down must not cost the main dex's sample."""
    dexs = [{"dex": "", "data": info.meta_and_asset_ctxs()}]   # the main dex has no name
    try:
        names = [d["name"] for d in info.post("/info", {"type": "perpDexs"}) if d]
    except Exception as e:                    # noqa: BLE001
        return {"dexs": dexs, "errors": [{"dex": "*", "error": repr(e)}]}
    errors = []
    for name in names:
        try:
            dexs.append({"dex": name, "data": info.post("/info", {"type": "metaAndAssetCtxs", "dex": name})})
        except Exception as e:                # noqa: BLE001
            errors.append({"dex": name, "error": repr(e)})
    return {"dexs": dexs, "errors": errors}


def record(info, now: datetime | None = None, root: Path = MARKET_DIR) -> Path:
    """Take a sample and append it to today's file. Returns the file."""
    now = now or datetime.now(timezone.utc)
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{now:%Y-%m-%d}.jsonl.gz"
    line = json.dumps({"ts": now.isoformat(), **sample(info)}, separators=(",", ":")) + "\n"
    blob = gzip.compress(line.encode())
    with open(path, "ab") as f:
        f.write(blob)                         # one member, one write
    return path


def read_day(path: Path) -> list[dict]:
    """Every complete sample in a day file. A truncated last member is dropped."""
    data = path.read_bytes()
    out: list[dict] = []
    while data:
        d = zlib.decompressobj(wbits=31)
        try:
            chunk = d.decompress(data)
        except zlib.error:
            break
        if not d.eof:                         # cut off mid-member
            break
        out.extend(json.loads(x) for x in chunk.decode().splitlines() if x)
        data = d.unused_data
    return out


def days(root: Path = MARKET_DIR) -> list[dict]:
    if not root.exists():
        return []
    return [{"day": p.name[:10], "bytes": p.stat().st_size}
            for p in sorted(root.glob("*.jsonl.gz")) if DAY_RE.match(p.name[:10])]


def day_file(day: str, root: Path = MARKET_DIR) -> Path | None:
    """The file for a day, or None. The day comes from a URL: anything that is not
    a plain date never reaches the filesystem."""
    if not DAY_RE.match(day):
        return None
    p = root / f"{day}.jsonl.gz"
    return p if p.exists() else None
