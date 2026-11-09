"""Live decisions of the desk against the same decisions replayed on quantlake data.

Reads the target sets from the local desk journal (ai-desk/var/journal.jsonl) and,
if DESK_URL / DESK_PASSWORD are set (they are in quantlake/.env), from the deployed
desk too. Prints one line per decision and the causes of every disagreement.

Run:
    poetry run python scripts/compare_decisions.py
"""
import base64
import collections
import json
import os
import urllib.request
from pathlib import Path

from dotenv import dotenv_values

from alphaquant.calibration.decision_replay import compare, decisions_from_journal, load_journal
from alphaquant.engine.desk_replay import HistoricalMarket
from desk.signals.reversal import Reversal

LAB = Path(__file__).resolve().parents[2]


def deployed_rows() -> list[dict]:
    env = dotenv_values(LAB / "quantlake" / ".env")
    url, pw = env.get("DESK_URL"), env.get("DESK_PASSWORD")
    if not url or not pw:
        return []
    out = []
    for kind in ("targets", "cycle"):
        req = urllib.request.Request(f"{url.rstrip('/')}/api/journal?kind={kind}&last=500")
        req.add_header("Authorization", "Basic " + base64.b64encode(f"desk:{pw}".encode()).decode())
        rows = json.loads(urllib.request.urlopen(req, timeout=60).read())
        out += [r.get("data", r) | {"ts": r["ts"], "kind": kind} if "data" in r else r for r in rows]
    return out


local = decisions_from_journal(load_journal(LAB / "ai-desk" / "var" / "journal.jsonl"))
remote = decisions_from_journal(deployed_rows())
decisions = sorted(local + remote, key=lambda d: d.ts)
print(f"decisioni live: {len(local)} dal journal locale, {len(remote)} dal desk su Railway")

market = HistoricalMarket.from_quantlake()
rows = compare(Reversal(), market, decisions)
causes = collections.Counter()
for r in rows:
    causes.update(r["causes"].values())
    print(f"{r['ts']:%Y-%m-%d %H:%M}  live {r['live']:2}  replay {r['replay']:2}  uguali {r['agree']:2}"
          f"  jaccard {r['jaccard']:.2f}  scarto size max {r['max_size_gap']:.1%}"
          + (f"  {dict(collections.Counter(r['causes'].values()))}" if r["causes"] else ""))
full = sum(1 for r in rows if r["jaccard"] == 1.0)
print(f"\nidentiche: {full}/{len(rows)}  |  cause delle differenze: {dict(causes)}")
