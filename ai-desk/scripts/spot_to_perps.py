#!/usr/bin/env python3
"""Move USDC from the spot balance to the perps balance.

Hyperliquid keeps the two apart, and the testnet faucet credits spot while the
desk trades perps — so a freshly funded account looks empty to the desk. The app
has a control for this; so does the API, and the API does not move depending on
which tab you are on.

    .venv/bin/python scripts/spot_to_perps.py            # moves everything but $1
    .venv/bin/python scripts/spot_to_perps.py 500        # moves $500

Testnet only, and it may well be refused: Hyperliquid allows an API wallet to
trade but not to move funds. When that happens it says so and points at the app.
"""
from __future__ import annotations

import sys

from desk.config import settings


def main() -> int:
    s = settings()
    if not s.testnet:
        print("REFUSING: HL_TESTNET is not 1. Move funds on mainnet from the app, deliberately.")
        return 2
    if not (s.account_address and s.api_wallet_key):
        print("HL_ACCOUNT_ADDRESS and HL_API_WALLET_KEY must be set in .env.")
        return 2

    import eth_account
    from hyperliquid.exchange import Exchange
    from hyperliquid.info import Info

    info = Info(s.base_url, skip_ws=True)
    spot = info.post("/info", {"type": "spotClearinghouseState", "user": s.account_address})
    usdc = sum(float(b["total"]) for b in spot.get("balances", []) if b.get("coin") == "USDC")
    perps = float(info.user_state(s.account_address)["marginSummary"]["accountValue"])
    print(f"\n  spot  ${usdc:,.2f}\n  perps ${perps:,.2f}\n")

    want = float(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] != "--yes" else max(usdc - 1.0, 0.0)
    if want <= 0:
        print("  nothing to move.")
        return 1 if usdc <= 0 else 0
    if want > usdc:
        print(f"  only ${usdc:,.2f} on spot.")
        return 1

    print(f"  move ${want:,.2f} from spot to perps?")
    if "--yes" not in sys.argv and input("  type 'yes': ").strip() != "yes":
        print("  aborted.")
        return 0

    exchange = Exchange(eth_account.Account.from_key(s.api_wallet_key), s.base_url,
                        account_address=s.account_address)
    res = exchange.usd_class_transfer(want, True)
    if res.get("status") != "ok":
        detail = str(res.get("response", res))
        print(f"  -> refused: {detail}\n")
        if "Must deposit" in detail:
            # Not a funding problem: Hyperliquid lets an agent wallet trade, never
            # move money. That is the whole reason its key is safe to keep on disk.
            print("  An API wallet can sign orders but cannot move funds between balances —")
            print("  the restriction that makes it safe to keep this key in .env.")
            print("  Do this one in the app, signed by the wallet that owns the account:")
            print("    Portfolio > Balances tab > the USDC row, or the account panel on the Trade page.")
        return 1
    print("  ->", res)
    perps = float(info.user_state(s.account_address)["marginSummary"]["accountValue"])
    print(f"\n  perps now ${perps:,.2f}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
