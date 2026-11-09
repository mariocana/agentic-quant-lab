"""Paper adapter: simulates fills at mid +/- a cost, keeps positions in a JSON
file, marks them to market from the same context feed the live loop uses.

This is the default adapter. The live one is opt-in.

Costs depend on how the order meets the book, measured on 126 real fills of this
desk (testnet, 07-15/10/2026, alpha-quant calibration/desk_fills):

  maker (post-only, limit_alo)   1.5 bps fee, no slippage: it rests at the price
  taker (limit_ioc)              4.5 bps fee + 7.3 bps mean slippage

One flat 4.5 + 2 bps for everything, as before, made a maker round trip four
times too expensive and a taker one half as expensive as it really is.

Still optimistic in one way: a post-only order here always fills, at once. On
the exchange it can rest and be cancelled, and how often that happens is not
measured yet. The taker slippage was measured on testnet books, thinner than
mainnet's: prudent for liquid names.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from desk.config import VAR
from desk.execution.base import ExecutionAdapter
from desk.schemas import AccountState, Fill, OrderIntent, Position, RiskVerdict

PAPER_PATH = VAR / "paper_account.json"


class PaperAdapter(ExecutionAdapter):
    name = "paper"

    COSTS = {"maker": {"fee_bps": 1.5, "slippage_bps": 0.0},
             "taker": {"fee_bps": 4.5, "slippage_bps": 7.3}}

    def __init__(self, starting_equity: float = 10_000.0, fee_bps: float | None = None,
                 slippage_bps: float | None = None, path: Path = PAPER_PATH):
        """fee_bps / slippage_bps, if given, apply the same cost to every order
        (tests use zero to check the accounting alone)."""
        self.path = path
        self.costs = {k: dict(v) for k, v in self.COSTS.items()}
        for c in self.costs.values():
            if fee_bps is not None:
                c["fee_bps"] = fee_bps
            if slippage_bps is not None:
                c["slippage_bps"] = slippage_bps
        self.marks: dict[str, float] = {}
        if path.exists():
            self.state = json.loads(path.read_text())
        else:
            self.state = {"cash": starting_equity, "positions": {}, "filled_intents": []}
            self._save()

    # ---- helpers -------------------------------------------------------------

    def _save(self) -> None:
        self.path.write_text(json.dumps(self.state, indent=2))

    def set_marks(self, marks: dict[str, float]) -> None:
        self.marks.update(marks)

    def _mark(self, asset: str, fallback: float) -> float:
        return self.marks.get(asset, fallback)

    # ---- interface -----------------------------------------------------------

    def account_state(self) -> AccountState:
        positions = []
        upnl_total = 0.0
        for asset, p in self.state["positions"].items():
            mark = self._mark(asset, p["entry_px"])
            upnl = (mark - p["entry_px"]) * p["size"]
            upnl_total += upnl
            positions.append(Position(
                asset=asset, size=p["size"], notional_usd=p["size"] * mark, entry_px=p["entry_px"],
                mark_px=mark, unrealized_pnl_usd=upnl,
                opened_at=datetime.fromisoformat(p["opened_at"]), strategy_id=p.get("strategy_id"),
                horizon_hours=p.get("horizon_hours"),
            ))
        return AccountState(equity_usd=self.state["cash"] + upnl_total, margin_used_usd=0.0, positions=positions)

    def execute(self, intent: OrderIntent, verdict: RiskVerdict, mid_px: float) -> Fill | None:
        if verdict.decision == "reject" or verdict.approved_notional_usd <= 0:
            return None
        if intent.id in self.state["filled_intents"]:
            return None                                       # idempotent
        sign = 1 if intent.side == "buy" else -1
        cost = self.costs["maker" if intent.order_type == "limit_alo" else "taker"]
        fill_px = mid_px * (1 + sign * cost["slippage_bps"] / 1e4)
        notional = verdict.approved_notional_usd
        size = sign * notional / fill_px

        p = self.state["positions"].get(intent.asset)
        if intent.reduce_only:
            # A reduce-only order can never open or flip a position. The notional was
            # computed at the mark, so with slippage it buys slightly more or less size
            # than is open; without this clamp a "close" leaves a dust position behind.
            if p is None:
                return None
            if size * p["size"] >= 0 or abs(size) > abs(p["size"]) * 0.995:
                # within half a percent of the whole position: this is a close, not a trim.
                # The caller sizes in notional at the mark, so slippage always leaves a
                # sliver one way or the other; closing exactly is what the venue would do.
                size = -p["size"]
                notional = abs(size) * fill_px
        fee = notional * cost["fee_bps"] / 1e4
        if p is None:
            self.state["positions"][intent.asset] = {
                "size": size, "entry_px": fill_px, "opened_at": datetime.now(timezone.utc).isoformat(),
                "strategy_id": intent.strategy_id, "horizon_hours": intent.horizon_hours,
            }
        else:
            old_size, old_px = p["size"], p["entry_px"]
            new_size = old_size + size
            if old_size * size > 0:                           # adding: average entry
                p["entry_px"] = (old_size * old_px + size * fill_px) / new_size
            else:                                             # reducing / flipping: realise P&L
                closed = min(abs(size), abs(old_size)) * (1 if old_size > 0 else -1)
                self.state["cash"] += (fill_px - old_px) * closed
                if abs(new_size) < 1e-12:
                    del self.state["positions"][intent.asset]
                elif old_size * new_size < 0:                 # flipped
                    p["entry_px"] = fill_px
                    p["opened_at"] = datetime.now(timezone.utc).isoformat()
            if intent.asset in self.state["positions"]:
                p["size"] = new_size
        self.state["cash"] -= fee
        self.state["filled_intents"].append(intent.id)
        self._save()
        return Fill(intent_id=intent.id, asset=intent.asset, side=intent.side, requested_usd=intent.notional_usd,
                    filled_usd=notional, decision_px=mid_px, fill_px=fill_px, fee_usd=fee,
                    partial=notional < intent.notional_usd - 1e-9)

    def apply_funding(self, rates: dict[str, float]) -> float:
        """Settle funding: `rates` is the summed hourly rate per asset over the
        period. On Hyperliquid a long pays size x price x rate when the rate is
        positive and is paid when it is negative. Returns what the account paid.

        The paper desk does not call this yet, so its equity ignores funding; a
        backtest does, because over a five-day hold funding at 0.01%/h is 1.2%
        of the position, more than the round trip costs."""
        paid = 0.0
        for asset, p in self.state["positions"].items():
            r = rates.get(asset)
            if r:
                paid += p["size"] * self._mark(asset, p["entry_px"]) * r
        self.state["cash"] -= paid
        self._save()
        return paid

    def flatten_all(self) -> list[Fill]:
        fills = []
        for asset, p in list(self.state["positions"].items()):
            mark = self._mark(asset, p["entry_px"])
            side = "sell" if p["size"] > 0 else "buy"
            # size the ticket at the price it will actually fill at, not at the mark
            fill_px = mark * (1 + (1 if side == "buy" else -1) * self.costs["taker"]["slippage_bps"] / 1e4)
            intent = OrderIntent(asset=asset, side=side, notional_usd=abs(p["size"]) * fill_px, reduce_only=True,
                                 order_type="limit_ioc", strategy_id="risk", horizon_hours=0, reason="flatten_all")
            verdict = RiskVerdict(intent_id=intent.id, decision="approve", approved_notional_usd=intent.notional_usd)
            f = self.execute(intent, verdict, mark)
            if f:
                fills.append(f)
        return fills
