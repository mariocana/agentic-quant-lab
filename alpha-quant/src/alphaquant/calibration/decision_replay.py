"""Does the backtest decide what the desk decided?

The desk journals every set of targets it computed live, with the equity it
sized against. For each of them the historical market is frozen at the same
second and the same strategy is asked again. If the data in quantlake is the
data the desk saw, the answers match; every difference has a cause, and the
cause is the finding:

  no_bars        quantlake has no daily bar for the asset before that moment
  not_listed     the listing table does not consider it trading that day
  universe       it has bars but did not make the strategy's universe: the live
                 24h volume is a rolling window, the replay's is the previous UTC
                 day, and at the edge of the top-N the two can rank differently
  ranked         it was in both universes and ended in a different quintile

Prices are not compared through P&L: the testnet desk filled at testnet prices,
up to 2.6% away from mainnet's, so a P&L gap would measure the venue, not the
simulator. Decisions are made on the same mainnet feed live and in replay, so
they can be compared exactly.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class Decision:
    ts: datetime
    equity: float
    targets: dict[str, float]          # asset -> signed notional


def decisions_from_journal(rows: list[dict], strategy_id: str = "reversal_v1") -> list[Decision]:
    """Live target sets, each with the equity of the cycle that produced it (the
    first cycle record after the targets)."""
    rows = sorted(rows, key=lambda r: r["ts"])
    out = []
    for i, r in enumerate(rows):
        if r.get("kind") != "targets" or r.get("strategy") != strategy_id:
            continue
        eq = next((c.get("equity") for c in rows[i + 1:] if c.get("kind") == "cycle"), None)
        if not eq:
            continue
        out.append(Decision(ts=datetime.fromisoformat(r["ts"]), equity=float(eq),
                            targets={t["asset"]: float(t["notional_usd"]) for t in r["targets"]}))
    return out


def load_journal(path: Path) -> list[dict]:
    return [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]


def replay_decision(strategy, market, d: Decision) -> tuple[dict[str, float], set[str], set[str]]:
    """What the strategy decides at d.ts from the historical market, the way
    run_cycle asks it. Returns targets, the contexts' assets and the universe."""
    market.at(d.ts)
    contexts = market.contexts()
    universe = strategy.universe(contexts)
    candles = {a: market.candles(a, strategy.interval, strategy.bars) for a in universe}
    targets = strategy.targets(candles, contexts, d.equity)
    return {t.asset: t.notional_usd for t in targets}, set(contexts), set(universe)


def compare(strategy, market, decisions: list[Decision]) -> list[dict]:
    """One row per decision: agreement on (asset, side) and the cause of each miss."""
    out = []
    for d in decisions:
        replayed, ctx, uni = replay_decision(strategy, market, d)
        live = {(a, n > 0) for a, n in d.targets.items()}
        rep = {(a, n > 0) for a, n in replayed.items()}
        both = live & rep
        causes: dict[str, str] = {}
        for a, _ in live ^ rep:
            if market.last_close(a) is None:
                causes[a] = "no_bars"
            elif a not in ctx:
                causes[a] = "not_listed"
            elif a not in uni:
                causes[a] = "universe"          # live picked it, the replay's top-N left it out
            else:
                causes[a] = "ranked"
        rel = [abs(replayed[a] / d.targets[a] - 1) for a, _ in both if d.targets[a]]
        out.append({
            "ts": d.ts, "live": len(live), "replay": len(rep), "agree": len(both),
            "jaccard": len(both) / len(live | rep) if live | rep else 1.0,
            "max_size_gap": max(rel) if rel else 0.0,
            "causes": causes,
        })
    return out
