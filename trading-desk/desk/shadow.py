"""Shadow strategies: the forward test, run by the desk itself.

Each shadow strategy runs the full cycle — universe, targets, rebalance, the nine
risk rules, the time stop — every day, against live market data, in a paper
account of its own:

    var/shadow/<id>/paper.json     its positions and cash
    var/shadow/<id>/risk.json      its risk state
    var/shadow/<id>/journal.jsonl  its targets, intents, verdicts and fills

The adapter is built here and is always a PaperAdapter, so a shadow strategy has
no path to an order on the exchange whatever its config says. It also does not
notify: a shadow halting is a result for the lab, not a page for a human.

Funding is not settled in the paper account (neither is it for the active paper
desk yet): the lab's replay over the same days is the precise measure, and the
shadow journal is what that replay must reproduce.
"""
from __future__ import annotations

import logging
from pathlib import Path

from desk.config import VAR
from desk.execution.paper import PaperAdapter
from desk.loop import run_cycle
from desk.risk.state import RiskState

SHADOW_ROOT = VAR / "shadow"
log = logging.getLogger(__name__)


def shadow_dir(strategy_id: str, root: Path = SHADOW_ROOT) -> Path:
    d = root / strategy_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def run_shadow(market, strategy, limits: dict, root: Path = SHADOW_ROOT, equity: float = 10_000.0) -> dict:
    d = shadow_dir(strategy.id, root)
    adapter = PaperAdapter(starting_equity=equity, path=d / "paper.json")
    state = RiskState.load(d / "risk.json")
    return run_cycle(market, strategy, adapter, limits, state, fetch_depth=True,
                     journal_path=d / "journal.jsonl", quiet=True)


def shadow_state(strategy_id: str, root: Path = SHADOW_ROOT) -> dict:
    d = root / strategy_id
    if not (d / "paper.json").exists():
        return {"id": strategy_id, "equity_usd": None, "positions": 0}
    a = PaperAdapter(path=d / "paper.json")
    st = a.account_state()
    return {"id": strategy_id, "equity_usd": st.equity_usd, "positions": len(st.positions)}
