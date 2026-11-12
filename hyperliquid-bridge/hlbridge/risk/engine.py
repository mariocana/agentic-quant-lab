"""The risk engine. Pure Python, pure functions of (intent, account, market, limits, state).

Rules run cheapest first; the first REJECT ends the check. Rules that would reject
on size instead cut the ticket, and the ticket is rejected only if what remains is
below the minimum. Risk-reducing intents (true reduce-only) bypass every limit
except the kill switch on *new* risk: closing is always allowed.

This module must never import from hlbridge.research or from any LLM client.
tests/test_no_llm_in_risk.py enforces that.
"""
from __future__ import annotations

from hlbridge.risk.state import RiskState
from hlbridge.schemas import AccountState, AssetContext, OrderIntent, RiskVerdict, asset_class


class Market:
    """What the engine needs from the market for one intent. Depth is optional
    because fetching a book costs a call; if absent that rule is skipped and
    flagged, never silently passed."""

    def __init__(self, ctx: AssetContext, depth_usd_10bps: float | None = None):
        self.ctx = ctx
        self.depth = depth_usd_10bps


def _beta(asset: str, limits: dict) -> float:
    betas = limits["betas"]
    if asset in betas:
        return float(betas[asset])
    return float(betas["default_hip3"] if asset_class(asset) == "hip3" else betas["default_crypto"])


def _is_reducing(intent: OrderIntent, account: AccountState) -> bool:
    pos = account.position(intent.asset)
    if pos is None or pos.notional_usd == 0:
        return False
    opposite = (pos.notional_usd > 0) == (intent.side == "sell")
    return opposite and intent.notional_usd <= abs(pos.notional_usd) + 1e-9


def evaluate(intent: OrderIntent, account: AccountState, market: Market,
             limits: dict, state: RiskState) -> RiskVerdict:
    fired: list[str] = []
    equity = account.equity_usd
    cls = asset_class(intent.asset)

    def reject(rule: str) -> RiskVerdict:
        fired.append(rule)
        return RiskVerdict(intent_id=intent.id, decision="reject", approved_notional_usd=0.0, rules_fired=fired)

    # 0. Closing risk is always allowed.
    if intent.reduce_only or _is_reducing(intent, account):
        if not intent.reduce_only:
            fired.append("treated_as_reduce_only")
        return RiskVerdict(intent_id=intent.id, decision="approve",
                           approved_notional_usd=intent.notional_usd, rules_fired=fired)

    # 1. Hard stops on new risk.
    if RiskState.kill_engaged():
        return reject("kill_switch")
    if state.halted:
        return reject(f"halted:{state.halt_reason}")
    if state.day_pnl_pct(equity) <= -limits["daily_loss_freeze_pct"]:
        return reject("daily_loss_freeze")
    if equity <= 0:
        return reject("no_equity")

    # 2. Minimum ticket.
    if intent.notional_usd < limits["min_notional_usd"]:
        return reject("min_notional")

    allowed = intent.notional_usd
    pos = account.position(intent.asset)
    current = pos.notional_usd if pos else 0.0
    sign = 1 if intent.side == "buy" else -1

    # 3. Per-asset cap on the resulting position.
    cap = limits["max_notional_pct_equity"][cls] * equity
    same_dir = current == 0 or (current > 0) == (sign > 0)
    if abs(current + sign * allowed) > cap:
        fired.append("max_notional_per_asset")
        # same direction: fill the room left; flipping through zero: close + open up to cap
        allowed = max(0.0, cap - abs(current)) if same_dir else cap + abs(current)

    # 4. Gross leverage.
    gross_after = account.gross_notional_usd - abs(current) + abs(current + sign * allowed)
    max_gross = limits["max_gross_leverage"] * equity
    if gross_after > max_gross:
        fired.append("max_gross_leverage")
        allowed = max(0.0, allowed - (gross_after - max_gross))

    # 5. Net beta exposure.
    beta = _beta(intent.asset, limits)
    if beta != 0:
        net_beta = sum(p.notional_usd * _beta(p.asset, limits) for p in account.positions)
        delta = sign * beta                      # beta added per dollar of this intent
        after = net_beta + delta * allowed
        max_beta = limits["max_net_beta_pct_equity"] * equity
        if abs(after) > max_beta and abs(after) > abs(net_beta):
            fired.append("max_net_beta")
            adds_to_current = net_beta == 0 or (net_beta > 0) == (delta > 0)
            allowed = (max(0.0, max_beta - abs(net_beta)) if adds_to_current else max_beta + abs(net_beta)) / abs(delta)

    # 6. Liquidity.
    ctx = market.ctx
    vol_cap = limits["max_pct_of_day_volume"] * ctx.day_volume_usd
    if allowed > vol_cap:
        fired.append("max_pct_of_day_volume")
        allowed = vol_cap
    if market.depth is None:
        fired.append("book_depth_unknown")
    else:
        depth_cap = limits["max_pct_of_book_depth_10bps"] * market.depth
        if allowed > depth_cap:
            fired.append("max_pct_of_book_depth")
            allowed = depth_cap

    # 7. Funding: only matters when we are the side that pays.
    paying = (sign > 0 and ctx.funding_hourly > 0) or (sign < 0 and ctx.funding_hourly < 0)
    if paying:
        f = abs(ctx.funding_hourly)
        if f > 2 * limits["max_abs_funding_hourly"]:
            return reject("funding_too_expensive")
        if f > limits["max_abs_funding_hourly"]:
            fired.append("funding_halved")
            allowed *= 0.5

    # Final.
    if allowed < limits["min_notional_usd"]:
        return reject("min_notional_after_cuts")
    decision = "approve" if abs(allowed - intent.notional_usd) < 1e-9 else "reduce"
    return RiskVerdict(intent_id=intent.id, decision=decision, approved_notional_usd=round(allowed, 2), rules_fired=fired)
