"""One desk cycle: read -> strategy -> rebalance -> risk -> execute -> journal.

Deterministic end to end. Phase 2 plugs the research layer in between
strategy and rebalance as an extra filter; nothing downstream changes.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from desk.data.hl_market import HLMarket
from desk.execution.base import ExecutionAdapter
from desk.journal.log import record
from desk.pm.notify import notify
from desk.risk import engine as risk
from desk.risk.state import RiskState
from desk.schemas import AccountState, OrderIntent
from desk.signals.base import Strategy
from desk.signals.rebalance import intents_from_targets

log = logging.getLogger(__name__)


def time_stop_intents(account: AccountState, limits: dict, now: datetime | None = None) -> list[OrderIntent]:
    """Close positions that outlived their horizon (+ grace). Reduce-only, always allowed."""
    now = now or datetime.now(timezone.utc)
    out = []
    for p in account.positions:
        if not p.managed or not p.opened_at or not p.horizon_hours:
            continue
        deadline = p.opened_at + timedelta(hours=p.horizon_hours + limits["time_stop_grace_hours"])
        if now >= deadline:
            out.append(OrderIntent(asset=p.asset, side="sell" if p.size > 0 else "buy",
                                   notional_usd=abs(p.notional_usd), order_type="limit_ioc", reduce_only=True,
                                   strategy_id=p.strategy_id or "risk", horizon_hours=0,
                                   reason=f"time stop: opened {p.opened_at.isoformat()} horizon {p.horizon_hours}h"))
    return out


def run_cycle(market: HLMarket, strategy: Strategy, adapter: ExecutionAdapter, limits: dict,
              state: RiskState, fetch_depth: bool = True, dry_run: bool = False) -> dict:
    log.info("cycle start: strategy=%s adapter=%s dry_run=%s", strategy.id, adapter.name, dry_run)
    contexts = market.contexts()
    marks = {a: c.mid_px for a, c in contexts.items()}   # before any filtering: marking is not trading
    if hasattr(adapter, "set_marks"):
        adapter.set_marks(marks)

    if not dry_run and hasattr(adapter, "reconcile"):
        # Before anything else: a post-only order from yesterday may have filled
        # overnight. Reading the account before folding that in would show a
        # position the desk does not recognise.
        adapter.reconcile()
    if hasattr(adapter, "cancel_stale_orders") and not dry_run:
        adapter.cancel_stale_orders()
    account = adapter.account_state()
    fired = state.observe(account.equity_usd, limits)
    state.save()
    summary = {"equity": account.equity_usd, "day_pnl_pct": state.day_pnl_pct(account.equity_usd),
               "intents": 0, "approved": 0, "reduced": 0, "rejected": 0, "fills": 0, "state_rules": fired}

    if state.flatten_requested:
        notify(f"HALT: {state.halt_reason}. Flattening all positions.")
        fills = [] if dry_run else adapter.flatten_all()
        for f in fills:
            record("fill", f)
        state.flatten_requested = False
        state.save()
        summary["fills"] = len(fills)
        return summary
    if fired:
        notify(f"Risk state: {fired} (equity {account.equity_usd:.2f})")

    # strategy — on what this venue can actually trade
    listed = adapter.tradable_assets() if hasattr(adapter, "tradable_assets") else None
    if listed is not None:
        dropped = [a for a in contexts if a not in listed]
        contexts = {a: c for a, c in contexts.items() if a in listed}
        if dropped:
            log.info("%d of the feed's assets are not listed on %s (e.g. %s)",
                     len(dropped), adapter.name, ", ".join(sorted(dropped)[:5]))
    universe = strategy.universe(contexts)
    candles = {a: market.candles(a, strategy.interval, strategy.bars) for a in universe}
    targets = strategy.targets(candles, contexts, account.equity_usd)
    log.info("universe %d names, %d targets, equity %.2f", len(universe), len(targets), account.equity_usd)
    record("targets", {"strategy": strategy.id, "n": len(targets),
                       "targets": [t.model_dump(mode="json") for t in targets]})

    intents = time_stop_intents(account, limits) + intents_from_targets(
        targets, account, strategy.id, min_delta_usd=limits["min_notional_usd"], marks=marks)
    summary["intents"] = len(intents)

    for intent in intents:
        record("intent", intent)
        ctx = contexts.get(intent.asset)
        if ctx is None:
            record("verdict", {"intent_id": intent.id, "decision": "reject", "rules_fired": ["no_context"]})
            summary["rejected"] += 1
            continue
        depth = None
        if fetch_depth and not intent.reduce_only:
            try:
                _, depth = market.book_depth_10bps(intent.asset)
            except Exception as e:                    # noqa: BLE001
                log.warning("book fetch failed for %s: %s", intent.asset, e)
        verdict = risk.evaluate(intent, account, risk.Market(ctx, depth), limits, state)
        record("verdict", verdict)
        log.info("%s %s %.0f -> %s %.0f %s", intent.side, intent.asset, intent.notional_usd, verdict.decision,
                 verdict.approved_notional_usd, verdict.rules_fired or "")
        summary[{"approve": "approved", "reduce": "reduced", "reject": "rejected"}[verdict.decision]] += 1
        if verdict.decision == "reject" or dry_run:
            continue
        fill = adapter.execute(intent, verdict, ctx.mid_px)
        if fill:
            record("fill", fill)
            log.info("filled %s %s %.0f @ %g (%.1f bps)", fill.side, fill.asset, fill.filled_usd, fill.fill_px, fill.slippage_bps)
            summary["fills"] += 1
            # refresh so the next intent sees the new position
            account = adapter.account_state()

    record("cycle", summary)
    log.info("cycle done: %s", summary)
    return summary
