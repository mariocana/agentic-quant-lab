"""Targets -> OrderIntents. Diff wanted vs. held, ignore dust, emit one intent per asset."""
from __future__ import annotations

from desk.schemas import AccountState, OrderIntent, TargetPosition


def intents_from_targets(targets: list[TargetPosition], account: AccountState, strategy_id: str,
                         min_delta_usd: float = 15.0, stop_pct: float | None = 0.08,
                         marks: dict[str, float] | None = None) -> list[OrderIntent]:
    wanted = {t.asset: t for t in targets}
    # Only this strategy's own positions. One opened by hand, or by a desk whose
    # ledger was lost, is left alone: closing someone else's position because it
    # is not in our target list would be the worst kind of helpful.
    held = {p.asset: p for p in account.positions if p.managed and p.strategy_id == strategy_id}
    out: list[OrderIntent] = []

    for asset in set(wanted) | set(held):
        want = wanted[asset].notional_usd if asset in wanted else 0.0
        have = held[asset].notional_usd if asset in held else 0.0
        delta = want - have
        if abs(delta) < min_delta_usd:
            continue
        side = "buy" if delta > 0 else "sell"
        closing = asset not in wanted
        reducing = have != 0 and (have > 0) != (delta > 0) and abs(delta) <= abs(have) + 1e-9
        stop = None
        if stop_pct and marks and asset in marks and not (closing or reducing):
            stop = marks[asset] * (1 - stop_pct) if want > 0 else marks[asset] * (1 + stop_pct)
        out.append(OrderIntent(
            asset=asset, side=side, notional_usd=abs(delta),
            order_type="limit_ioc" if closing else "limit_alo",
            reduce_only=closing or reducing, stop_px=stop, strategy_id=strategy_id,
            horizon_hours=wanted[asset].horizon_hours if asset in wanted else 0,
            reason=wanted[asset].reason if asset in wanted else "left universe / no longer in a quintile",
        ))
    # closes first: free margin before opening
    out.sort(key=lambda i: not i.reduce_only)
    return out
