#!/usr/bin/env python3
"""First contact with a real wallet: one order, on testnet, watched end to end.

The acceptance script proves the brakes work. This proves the plumbing does — that
the API wallet can sign, that an order reaches the book, that the stop lands on the
exchange and survives this process, that the fill reconciles into the ledger, and
that closing leaves nothing behind.

    HL_TESTNET=1 .venv/bin/python scripts/testnet_smoke.py

It sends exactly one order, at the minimum ticket, and closes it. It refuses to run
against mainnet. It asks before the one step that costs money.
"""
from __future__ import annotations

import sys
import time

from desk.config import load_limits, settings
from desk.execution.hyperliquid import HyperliquidAdapter, cloid_for
from desk.schemas import OrderIntent, RiskVerdict

PASS, FAIL, INFO = "\033[32mPASS\033[0m", "\033[31mFAIL\033[0m", "\033[33m····\033[0m"
failures: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> bool:
    print(f"  {PASS if ok else FAIL}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        failures.append(name)
    return ok


def main() -> int:
    s = settings()
    print("\nai-desk — testnet smoke test\n")

    if not s.testnet:
        print("  REFUSING: HL_TESTNET is not 1. This sends a real order.")
        return 2
    if not (s.account_address and s.api_wallet_key):
        print("  HL_ACCOUNT_ADDRESS and HL_API_WALLET_KEY must be set in .env.")
        print("  Create an API wallet at https://app.hyperliquid-testnet.xyz/API —")
        print("  it can sign orders and cannot withdraw.")
        return 2

    adapter = HyperliquidAdapter(s.base_url, s.account_address, s.api_wallet_key)

    print("1. the wallet can read the account")
    acc = adapter.account_state()
    if not check("account reachable", acc.equity_usd >= 0, f"equity ${acc.equity_usd:,.2f}"):
        return 1
    notional = max(load_limits()["min_notional_usd"], 12.0)
    if acc.equity_usd < notional * 1.2:
        print(f"  {INFO}  not enough to send the minimum ticket (${notional:.2f}).")
        print(f"  {INFO}  Get testnet USDC at faucet.circle.com (Arbitrum Sepolia), then send it")
        print(f"  {INFO}  straight to the bridge 0x08cfc1B6b2dCF36A1480b99353A354AA8AC56f89.")
        return 2
    unmanaged = [p.asset for p in acc.positions if not p.managed]
    print(f"  {INFO}  {len(acc.positions)} open position(s)"
          + (f", not opened by this desk: {', '.join(unmanaged)}" if unmanaged else ""))

    print("\n2. reconciliation runs clean on an untouched account")
    try:
        folded = adapter.reconcile()
        check("reconcile() completed", True, f"{len(folded)} fills folded in")
    except Exception as e:                        # noqa: BLE001
        check("reconcile() completed", False, f"{type(e).__name__}: {e}")
        return 1

    print("\n3. pick the most liquid perp on this venue")
    ctx = adapter.venue.contexts()
    asset = max(ctx, key=lambda a: ctx[a].day_volume_usd)
    mid = ctx[asset].mid_px
    print(f"  {INFO}  {asset} at {mid:g}, 24h volume ${ctx[asset].day_volume_usd:,.0f}")

    stop_px = mid * 0.90                          # far away: this is a plumbing test, not a strategy
    intent = OrderIntent(asset=asset, side="buy", notional_usd=notional, order_type="limit_ioc",
                         stop_px=stop_px, strategy_id="smoke_test", horizon_hours=1,
                         reason="testnet smoke test")
    print(f"\n4. send ONE order: buy ${notional:.2f} of {asset}, stop at {stop_px:g}")
    if "--yes" not in sys.argv:
        if input("  type 'send' to continue: ").strip() != "send":
            print("  aborted, nothing sent.")
            return 0

    verdict = RiskVerdict(intent_id=intent.id, decision="approve", approved_notional_usd=notional)
    fill = adapter.execute(intent, verdict, mid)
    if fill is None:
        rest = adapter.ledger.pending_for(cloid=cloid_for(intent.id).to_raw())
        check("order accepted by the exchange", rest is not None,
              "resting on the book (an IOC should not rest — check the logs above)")
        return 1 if rest is None else 0
    check("order filled", True, f"{fill.filled_usd:.2f} @ {fill.fill_px:g}, slippage {fill.slippage_bps:+.1f} bps")
    check("the stop reached the exchange", fill.stop_oid is not None,
          f"stop oid {fill.stop_oid}" if fill.stop_oid else "NO STOP — a position with no exchange-side stop")

    print("\n5. the desk recognises what it just opened")
    acc = adapter.account_state()
    pos = acc.position(asset)
    check("position is in the ledger", pos is not None and pos.managed,
          f"strategy {pos.strategy_id}, opened {pos.opened_at:%H:%M:%S}" if pos and pos.managed else "unmanaged")

    print("\n6. the stop is visible among the open orders")
    try:
        orders = adapter.info.frontend_open_orders(adapter.address)
        triggers = [o for o in orders if o.get("isTrigger") and o.get("coin") == asset]
        check("a trigger order rests on the exchange", bool(triggers),
              f"{len(triggers)} trigger order(s); it outlives this process")
    except Exception as e:                        # noqa: BLE001
        check("a trigger order rests on the exchange", False, f"{type(e).__name__}: {e}")

    print("\n7. the exchange's own fills reconcile")
    time.sleep(2)
    folded = adapter.reconcile()
    real_fee = folded[0].fee_usd if folded else None
    check("fill folded in with the charged fee", bool(folded),
          f"fee ${real_fee:.4f} (estimate was ${fill.fee_usd:.4f})" if folded else "nothing folded in")

    print("\n8. close it and leave nothing behind")
    closed = adapter.flatten_all()
    acc = adapter.account_state()
    check("position closed", acc.position(asset) is None, f"{len(closed)} fill(s)")
    check("ledger row dropped", asset not in adapter.ledger.rows)
    adapter.cancel_stale_orders()

    print()
    if failures:
        print(f"{FAIL}  {len(failures)} check(s) failed: " + "; ".join(failures))
        return 1
    print(f"{PASS}  the live path works on testnet. Mainnet next, with size you can lose.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
