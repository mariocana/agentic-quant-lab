"""Live Hyperliquid adapter. Signs with an API wallet (agent key) that cannot withdraw.

Order path:
  1. idempotency check: an order with this intent's cloid already known -> skip
  2. limit order, ALO (post-only, offset inside the spread) or IOC (cross)
  3. on fill, place an exchange-side stop (trigger, reduce-only, market) so the
     stop survives this process dying

Only run this against testnet until the paper track has weeks of history.
"""
from __future__ import annotations

import json
import logging
import time

import eth_account
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from hyperliquid.utils.types import Cloid

from desk.config import VAR
from desk.data.hl_market import HLMarket
from desk.execution.base import ExecutionAdapter, round_price, round_size
from desk.execution.ledger import PositionLedger
from desk.execution.reconcile import reconcile_fills
from desk.journal.log import record
from desk.schemas import AccountState, Fill, OrderIntent, RiskVerdict

log = logging.getLogger(__name__)

ALO_OFFSET_BPS = 1.0     # rest 1 bp inside our side of the mid
IOC_CROSS_BPS = 20.0     # cross up to 20 bps to get done


def cloid_for(intent_id: str) -> Cloid:
    return Cloid.from_str("0x" + intent_id.ljust(32, "0")[:32])


class HyperliquidAdapter(ExecutionAdapter):
    name = "hyperliquid"

    def __init__(self, base_url: str, account_address: str, api_wallet_key: str,
                 unified_collateral: bool = False):
        try:
            wallet = eth_account.Account.from_key(api_wallet_key)
        except Exception as e:                    # noqa: BLE001 - the message matters more than the type
            raise SystemExit(
                "HL_API_WALLET_KEY is not a valid private key "
                f"({type(e).__name__}). Expected 64 hex characters, with or without the 0x prefix — "
                "the value from 'Create API Wallet' at app.hyperliquid-testnet.xyz/API, "
                "not the placeholder from .env.example."
            ) from None
        if not account_address.startswith("0x") or len(account_address) != 42:
            raise SystemExit(f"HL_ACCOUNT_ADDRESS does not look like an address: {account_address!r}")
        self.address = account_address
        self.exchange = Exchange(wallet, base_url, account_address=account_address)
        self.info: Info = self.exchange.info
        # account reads and asset metadata come from the venue we execute on,
        # not from the (mainnet) data feed the strategy looks at
        self.venue = HLMarket(base_url)
        self.unified_collateral = unified_collateral
        self.ledger = PositionLedger()
        self._said_unmanaged: frozenset[str] = frozenset()
        self._said_awaiting: frozenset[str] = frozenset()
        log.info("HL adapter: signing with agent %s for account %s (%s)", wallet.address, account_address, base_url)

    def tradable_assets(self) -> set[str] | None:
        try:
            return set(self.venue.refresh_meta())
        except Exception as e:                    # noqa: BLE001 - better to trade nothing than to guess
            log.warning("could not read the venue universe: %s", e)
            return set()

    def account_state(self) -> AccountState:
        """Sizes from the exchange, context from the ledger.

        The exchange is the only source of truth for what is open; the ledger adds
        who opened it and when. A position with no ledger row comes back with
        managed=False, and the rest of the desk leaves it alone.
        """
        acc = self.venue.account_state(self.address, self.unified_collateral)
        gone = self.ledger.reconcile({p.asset for p in acc.positions})
        if gone:
            log.info("ledger: closed on the exchange, dropping %s", ", ".join(gone))
        acc.positions = self.ledger.enrich(acc.positions)
        # The dashboard reads the account every 15s. Say these things when they
        # change, not on every read: a line repeated 200 times is not a log, it is
        # a wall, and the one line that matters hides behind it.
        unmanaged = frozenset(p.asset for p in acc.positions if not p.managed)
        if unmanaged and unmanaged != self._said_unmanaged:
            log.warning("positions on the exchange that this desk did not open: %s "
                        "(left untouched)", ", ".join(sorted(unmanaged)))
        self._said_unmanaged = unmanaged

        awaiting = frozenset(p.asset for p in acc.positions
                             if p.managed and p.asset not in self.ledger.rows)
        if awaiting and awaiting != self._said_awaiting:
            log.info("filled from a resting order, booked at the next reconcile: %s",
                     ", ".join(sorted(awaiting)))
        self._said_awaiting = awaiting
        return acc

    # ---- orders --------------------------------------------------------------

    def cancel_stale_orders(self) -> int:
        """Cancel resting limit orders from earlier cycles. Stops (trigger orders) stay."""
        n = 0
        for o in self.info.frontend_open_orders(self.address):
            if o.get("isTrigger"):
                continue
            r = self.exchange.cancel(o["coin"], o["oid"])
            n += 1
            # the order is gone, so no fill can arrive for it: drop the context too,
            # or the in-flight table grows a tail of orders that will never return
            match = self.ledger.pending_for(oid=str(o["oid"]))
            if match and match[0] in self.ledger.pending:
                self.ledger.drop_pending(match[0])
            log.info("cancelled stale %s %s oid=%s -> %s", o["side"], o["coin"], o["oid"], _first_status(r))
        return n

    def _already_sent(self, cloid: Cloid) -> bool:
        try:
            r = self.info.query_order_by_cloid(self.address, cloid)
            return r.get("status") == "order"
        except Exception as e:                    # noqa: BLE001 - be conservative: unknown == not sent
            log.warning("cloid lookup failed: %s", e)
            return False

    def _venue_mid(self, asset: str, fallback: float) -> float:
        """Price the order against the book it is going to.

        The strategy reads mainnet (testnet has no volume to speak of), but an
        order has to be priced where it will rest. The two differ — the same perp
        can sit a hundred dollars apart — and a limit priced off the wrong book is
        either instantly through the spread or never touched.
        """
        try:
            mid, _ = self.venue.book_depth_10bps(asset)
        except Exception as e:                    # noqa: BLE001
            log.warning("no book for %s on the execution venue (%s); pricing off the feed", asset, e)
            return fallback
        if mid <= 0:
            return fallback
        if fallback > 0 and abs(mid / fallback - 1) > 0.005:
            log.warning("%s: execution venue %g vs feed %g (%.2f%% apart)",
                        asset, mid, fallback, (mid / fallback - 1) * 100)
        return mid

    def reconcile(self) -> list[Fill]:
        """Fold the exchange's own fill history back in.

        Call at the top of every cycle: a post-only order from yesterday may have
        filled overnight, and the fees charged are only knowable here.
        """
        since = self._fills_since()
        try:
            raw = self.info.user_fills(self.address)
        except Exception as e:                    # noqa: BLE001 - a bad read must not stop the cycle
            log.warning("could not read fills: %s", e)
            return []
        ours, high_water, foreign = reconcile_fills(raw, self.ledger, since)
        for f in ours:
            record("fill_reconciled", f)
            log.info("reconciled %s %s %.2f @ %g, fee %.4f", f.side, f.asset, f.filled_usd, f.fill_px, f.fee_usd)
        for r in foreign:
            log.warning("fill this desk did not send: %s %s @ %s (oid %s) — not adopted",
                        r.get("coin"), r.get("sz"), r.get("px"), r.get("oid"))
        if foreign:
            record("foreign_fills", {"n": len(foreign), "assets": sorted({r.get("coin") for r in foreign})})
        if high_water > since:
            self._fills_since(high_water)
        self.ledger.prune_settled()
        for cloid in self.ledger.stale_pending():
            log.warning("order sent and never seen again, dropping: %s", cloid)
            self.ledger.drop_pending(cloid)
        return ours

    FILLS_CURSOR = "fills_cursor.json"

    def _fills_since(self, set_to: int | None = None) -> int:
        """High-water mark for fills already folded in. On disk, so a restart does
        not replay (or skip) a day of history.

        The first run starts from now — an account with history should not replay
        it — and **writes that immediately**. Deriving it from the clock on every
        call instead looks identical until a fill happens: it is always in the
        past relative to "now", so every fill is skipped and nothing is ever
        reconciled. That is exactly what the testnet smoke test caught.
        """
        path = VAR / self.FILLS_CURSOR
        if set_to is not None:
            path.write_text(json.dumps({"since_ms": set_to}))
            return set_to
        if path.exists():
            return int(json.loads(path.read_text()).get("since_ms", 0))
        now = int(time.time() * 1000)
        path.write_text(json.dumps({"since_ms": now}))
        return now

    def execute(self, intent: OrderIntent, verdict: RiskVerdict, mid_px: float) -> Fill | None:
        if verdict.decision == "reject" or verdict.approved_notional_usd <= 0:
            return None
        cloid = cloid_for(intent.id)
        if self._already_sent(cloid):
            log.info("intent %s already on exchange, skipping", intent.id)
            return None

        meta = self.venue.meta(intent.asset)
        szd = int(meta["szDecimals"])
        is_buy = intent.side == "buy"
        sign = 1 if is_buy else -1
        mid_px = self._venue_mid(intent.asset, mid_px)
        if intent.limit_px is not None:
            px = intent.limit_px
        elif intent.order_type == "limit_alo":
            px = mid_px * (1 - sign * ALO_OFFSET_BPS / 1e4)
        else:
            px = mid_px * (1 + sign * IOC_CROSS_BPS / 1e4)
        px = round_price(px, szd)
        sz = round_size(verdict.approved_notional_usd / px, szd)
        if sz <= 0:
            log.info("size rounds to zero for %s, skipping", intent.asset)
            return None

        tif = "Alo" if intent.order_type == "limit_alo" else "Ioc"
        resp = self.exchange.order(intent.asset, is_buy, sz, px, {"limit": {"tif": tif}},
                                   reduce_only=intent.reduce_only, cloid=cloid)
        status = _first_status(resp)
        if "error" in status:
            log.error("order rejected by exchange: %s", status["error"])
            return None
        if "resting" in status:
            oid = status["resting"]["oid"]
            # It may fill in an hour, or tomorrow. Remember why we sent it, or the
            # fill will arrive with nobody to attribute it to.
            self.ledger.record_sent(intent, cloid.to_raw(), oid)
            log.info("resting %s %s %s @ %s oid=%s", intent.side, sz, intent.asset, px, oid)
            return None                                     # the fill arrives through reconcile()
        filled = status["filled"]
        avg_px, total_sz = float(filled["avgPx"]), float(filled["totalSz"])
        filled_usd = avg_px * total_sz
        fee = filled_usd * 0.00045                          # an estimate; reconcile() replaces it with the real one
        self.ledger.record_sent(intent, cloid.to_raw(), filled.get("oid"))

        stop_oid = None
        if intent.stop_px and not intent.reduce_only:
            stop_oid = self._place_stop(intent.asset, is_buy, total_sz, intent.stop_px, szd,
                                        intent.strategy_id, intent.horizon_hours)

        fill = Fill(intent_id=intent.id, asset=intent.asset, side=intent.side, requested_usd=intent.notional_usd,
                    filled_usd=filled_usd, decision_px=mid_px, fill_px=avg_px, fee_usd=fee,
                    partial=total_sz < sz - 1e-12, exchange_oid=str(filled["oid"]),
                    stop_oid=str(stop_oid) if stop_oid else None)
        # Record before returning: a desk that dies here would otherwise own a
        # position it can no longer recognise.
        self.ledger.record(fill, intent, cloid=cloid.to_raw())
        return fill

    def _place_stop(self, asset: str, entry_is_buy: bool, sz: float, stop_px: float, szd: int,
                    strategy_id: str = "risk", horizon_hours: int = 0) -> int | None:
        trigger = round_price(stop_px, szd)
        # A stop fires hours later, unattended. It carries a cloid and a ledger row
        # like any other order, or the fill it produces reads as a stranger's trade
        # and the desk decides a position it closed itself was never its own.
        intent = OrderIntent(asset=asset, side="sell" if entry_is_buy else "buy",
                             notional_usd=max(sz * trigger, 0.01), reduce_only=True,
                             order_type="limit_ioc", strategy_id=strategy_id,
                             horizon_hours=horizon_hours, reason="exchange-side stop")
        cloid = cloid_for(intent.id)
        resp = self.exchange.order(asset, not entry_is_buy, sz, trigger,
                                   {"trigger": {"triggerPx": trigger, "isMarket": True, "tpsl": "sl"}},
                                   reduce_only=True, cloid=cloid)
        status = _first_status(resp)
        if "error" in status:
            log.error("STOP NOT PLACED for %s: %s", asset, status["error"])
            return None
        oid = status.get("resting", {}).get("oid")
        self.ledger.record_sent(intent, cloid.to_raw(), oid)
        return oid

    def flatten_all(self) -> list[Fill]:
        """Close everything. These orders are ours too: without a cloid their fills
        come back unattributable, and a desk that cannot recognise its own closing
        trade will warn about positions it shut itself."""
        fills = []
        for p in self.account_state().positions:
            intent = OrderIntent(asset=p.asset, side="sell" if p.size > 0 else "buy",
                                 notional_usd=max(abs(p.notional_usd), 0.01), reduce_only=True,
                                 order_type="limit_ioc", strategy_id=p.strategy_id or "risk",
                                 horizon_hours=0, reason="flatten_all")
            cloid = cloid_for(intent.id)
            self.ledger.record_sent(intent, cloid.to_raw(), None)
            resp = self.exchange.market_close(p.asset, cloid=cloid)
            status = _first_status(resp)
            if "filled" in status:
                f = status["filled"]
                self.ledger.forget(p.asset)
                fills.append(Fill(intent_id=intent.id, asset=p.asset, side="sell" if p.size > 0 else "buy",
                                  requested_usd=abs(p.notional_usd), filled_usd=float(f["avgPx"]) * float(f["totalSz"]),
                                  decision_px=p.mark_px, fill_px=float(f["avgPx"]), fee_usd=0.0, partial=False,
                                  exchange_oid=str(f["oid"])))
            else:
                log.error("flatten %s failed: %s", p.asset, status)
        return fills


def _first_status(resp: dict) -> dict:
    try:
        return resp["response"]["data"]["statuses"][0]
    except (KeyError, IndexError, TypeError):
        return {"error": str(resp)}
