"""A desk replay as a SimResult: the one shape the validation gates read.

The desk trades a portfolio by rebalancing: a position is opened, topped up,
trimmed, closed, sometimes flipped, one fill at a time. The gates want trades.
A trade here is a position from flat to flat (a flip closes one and opens the
next), with:

  qty          everything bought (long) or sold (short) to build it
  entry_price  the quantity-weighted average of those fills
  exit_price   set so that side * (exit - entry) * qty is exactly the realised
               P&L of the average-cost ledger. With top-ups after a trim the
               naive average of exit fills would not reconcile; this does.
  fees         every fill's fee, opening and closing
  funding      what the position paid or received while it was open (> 0 received)
  exit_reason  time (time stop), signal (rebalance), end_of_data (delisting
               settlement, or still open when the replay ends: closed at the
               last mark so the trade list and the equity curve tell one story)

Checked by construction: the sum of the trades' net P&L equals the change in
equity over the replay.
"""
from __future__ import annotations

from datetime import datetime

import polars as pl

from alphaquant.engine.types import EQUITY_SCHEMA, ExitReason, SimResult, Trade, trades_frame


class _Open:
    def __init__(self, side: int, t: datetime):
        self.side, self.t = side, t
        self.size = 0.0                 # signed
        self.cost = 0.0                 # average-cost basis of the open size
        self.qty_in = self.notional_in = 0.0
        self.realised = self.fees = self.funding = 0.0
        self.reason = ExitReason.SIGNAL

    def to_trade(self, symbol: str, t_exit: datetime) -> Trade:
        entry = self.notional_in / self.qty_in
        exit_px = entry + self.realised / (self.side * self.qty_in)
        return Trade(symbol=symbol, side=self.side, qty=self.qty_in, entry_time=self.t, entry_price=entry,
                     exit_time=t_exit, exit_price=exit_px, exit_reason=self.reason, multiplier=1.0,
                     fees_quote=self.fees, funding_quote=self.funding)


def _reason(intent_reason: str) -> ExitReason:
    if intent_reason.startswith("time stop"):
        return ExitReason.TIME
    if intent_reason in ("delisted", "end_of_data"):
        return ExitReason.END_OF_DATA
    return ExitReason.SIGNAL


def trades_from_journal(journal: list[dict], last_marks: dict[str, float], end: datetime) -> list[Trade]:
    reasons = {r["id"]: r.get("reason", "") for r in journal if r.get("kind") == "intent"}
    events = sorted((r for r in journal if r.get("kind") in ("fill", "funding")), key=lambda r: r["ts"])
    open_: dict[str, _Open] = {}
    out: list[Trade] = []

    for e in events:
        a, t = e["asset"], datetime.fromisoformat(e["ts"])
        if e["kind"] == "funding":
            if a in open_:
                open_[a].funding -= e["paid_usd"]
            continue
        sign = 1 if e["side"] == "buy" else -1
        qty, px, fee = e["filled_usd"] / e["fill_px"], e["fill_px"], e["fee_usd"]
        reason = reasons.get(e.get("intent_id"), "")
        while qty > 1e-12:
            pos = open_.get(a)
            if pos is None:
                pos = open_[a] = _Open(sign, t)
            if sign == pos.side:                                      # open or add
                pos.size += sign * qty
                pos.cost += qty * px
                pos.qty_in += qty
                pos.notional_in += qty * px
                pos.fees += fee
                qty = 0.0
                continue
            closing = min(qty, abs(pos.size))                         # trim, close or flip
            avg = pos.cost / abs(pos.size)
            pos.realised += pos.side * (px - avg) * closing
            pos.cost -= avg * closing
            pos.size += sign * closing
            share = closing / qty
            pos.fees += fee * share
            fee *= 1 - share
            qty -= closing
            if abs(pos.size) < 1e-12:
                pos.reason = _reason(reason)
                out.append(pos.to_trade(a, t))
                del open_[a]

    for a, pos in open_.items():                                      # still open at the end
        px = last_marks.get(a, pos.cost / abs(pos.size))
        pos.realised += pos.side * (px - pos.cost / abs(pos.size)) * abs(pos.size)
        pos.reason = ExitReason.END_OF_DATA
        out.append(pos.to_trade(a, end))
    return sorted(out, key=lambda x: x.entry_time)


def to_simresult(result, meta: dict | None = None) -> SimResult:
    """`result` is a desk_replay.ReplayResult."""
    end = result.equity["timestamp"][-1]
    trades = trades_from_journal(result.journal, result.last_marks, end)
    equity = result.equity.cast(dict(EQUITY_SCHEMA))
    return SimResult(trades=trades_frame(trades), equity=equity, meta={"level": 2, **(meta or {})})
