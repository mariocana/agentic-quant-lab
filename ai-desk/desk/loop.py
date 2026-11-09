"""One desk cycle: read -> strategy -> rebalance -> risk -> execute -> journal.

Deterministic end to end. Phase 2 plugs the research layer in between
strategy and rebalance as an extra filter; nothing downstream changes.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from functools import partial
from pathlib import Path

from desk.data.hl_market import HLMarket
from desk.execution.base import ExecutionAdapter
from desk.journal.log import record as _record
from desk.pm.notify import notify as _notify
from desk.risk import engine as risk
from desk.risk.state import RiskState
from desk.schemas import AccountState, OrderIntent
from desk.signals.base import Strategy
from desk.signals.rebalance import intents_from_targets

log = logging.getLogger(__name__)



_LAST_CYCLE_AT: dict[str, datetime] = {}


def _warn_if_too_soon(strategy: Strategy, min_fraction: float = 0.1) -> None:
    """Say something when cycles run far closer together than the strategy thinks.

    reversal_v1 reads daily bars and holds for five days: between two cycles an
    hour apart its targets are the same, but the book still turns over and pays
    the spread both ways. Twenty minutes of back-to-back cycles cost 0.26% of the
    account on testnet — real money, spent on nothing.
    """
    now = datetime.now(timezone.utc)
    last = _LAST_CYCLE_AT.get(strategy.id)
    _LAST_CYCLE_AT[strategy.id] = now
    if last is None:
        return
    gap_h = (now - last).total_seconds() / 3600
    expected_h = strategy.horizon_hours * min_fraction
    if gap_h < expected_h:
        log.warning("cycle %.0f min after the last one; %s holds for %dh. Each turn of the "
                    "book pays the spread, and the targets have barely moved.",
                    gap_h * 60, strategy.id, strategy.horizon_hours)

def time_stop_intents(account: AccountState, limits: dict, now: datetime | None = None) -> list[OrderIntent]:
    """Close positions that reached their horizon. Reduce-only, always allowed.

    The desk can only look when a cycle runs, so a deadline almost never falls on
    a check. With one cycle a day a 120h position is seen at 120h and then not
    again until 144h: waiting for the first check *past* the deadline added a
    fifth of the holding period to every position, and a two-hour grace on top of
    that was enough to make the desk skip the 120h check entirely — in seven days
    the time stop never fired once.

    So the position goes at whichever check sits nearest its deadline: once the
    deadline is less than half a check interval away, it is closed. Ties close
    early, which is the safe side — the thesis has expired either way.
    """
    now = now or datetime.now(timezone.utc)
    tolerance = timedelta(hours=limits["time_stop_check_interval_hours"] / 2)
    out = []
    for p in account.positions:
        if not p.managed or not p.opened_at or not p.horizon_hours:
            continue
        deadline = p.opened_at + timedelta(hours=p.horizon_hours)
        if now + tolerance >= deadline:
            out.append(OrderIntent(asset=p.asset, side="sell" if p.size > 0 else "buy",
                                   notional_usd=abs(p.notional_usd), order_type="limit_ioc", reduce_only=True,
                                   strategy_id=p.strategy_id or "risk", horizon_hours=0,
                                   reason=f"time stop: opened {p.opened_at.isoformat()} horizon {p.horizon_hours}h"))
    return out


def run_cycle(market: HLMarket, strategy: Strategy, adapter: ExecutionAdapter, limits: dict,
              state: RiskState, fetch_depth: bool = True, dry_run: bool = False,
              journal_path: Path | None = None, quiet: bool = False) -> dict:
    """journal_path: write this cycle's records there instead of the desk's journal
    (shadow strategies keep their own). quiet: no notifications (a shadow halting
    is information for the lab, not a page for a human)."""
    record = partial(_record, path=journal_path) if journal_path else _record
    notify = (lambda _t: None) if quiet else _notify
    log.info("cycle start: strategy=%s adapter=%s dry_run=%s", strategy.id, adapter.name, dry_run)
    if not dry_run:
        _warn_if_too_soon(strategy)
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
