"""Match what the exchange actually did against what the desk thinks it asked for.

Two things the desk cannot know at send time:

* **a post-only order may rest.** `execute()` returns None and the cycle moves on;
  the fill can land minutes or hours later. Nothing downstream would ever hear
  about it, so the position would show up unmanaged.
* **the fee.** Until the fill exists there is only an estimate, and an estimate is
  not what a P&L should be built on.

So every cycle starts by reading `userFills` and folding reality back in: pending
orders become positions, estimated fees become real ones, and anything we did not
send is reported rather than adopted.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from desk.execution.ledger import PositionLedger
from desk.schemas import Fill, OrderIntent

log = logging.getLogger(__name__)


def _as_fill(raw: dict, intent_id: str) -> Fill:
    px, sz = float(raw["px"]), float(raw["sz"])
    return Fill(
        intent_id=intent_id,
        asset=raw["coin"],
        side="buy" if raw["side"] == "B" else "sell",
        requested_usd=px * sz,                 # the ask is gone; the fill is what happened
        filled_usd=px * sz,
        decision_px=px,
        fill_px=px,
        fee_usd=float(raw.get("fee") or 0.0),  # the real one, not 0.045% of a guess
        partial=False,
        exchange_oid=str(raw.get("oid") or ""),
        created_at=datetime.fromtimestamp(raw["time"] / 1000, tz=timezone.utc),
    )


def reconcile_fills(raw_fills: list[dict], ledger: PositionLedger, since_ms: int) -> tuple[list[Fill], int, list[dict]]:
    """Fold exchange fills into the ledger.

    Returns the fills that belonged to orders we sent, the timestamp to resume
    from, and the fills we did not recognise (a manual trade, or a stop that
    triggered) — reported, never adopted.

    Idempotent: `since_ms` is the high-water mark, so replaying the same window
    cannot record a fill twice.
    """
    ours: list[Fill] = []
    foreign: list[dict] = []
    high_water = since_ms

    for raw in sorted(raw_fills, key=lambda r: r["time"]):
        ts = int(raw["time"])
        if ts <= since_ms:
            continue
        high_water = max(high_water, ts)
        match = ledger.pending_for(oid=raw.get("oid"), cloid=raw.get("cloid"))
        if match is None:
            foreign.append(raw)
            continue
        cloid, row = match
        fill = _as_fill(raw, row["intent_id"])
        intent = OrderIntent(
            id=row["intent_id"], asset=row["asset"], side=row["side"],
            notional_usd=max(fill.filled_usd, 0.01), reduce_only=row["reduce_only"],
            strategy_id=row["strategy_id"], horizon_hours=row["horizon_hours"] or 0,
            reason="reconciled from exchange fills",
        )
        # A closing fill still writes its row: account_state() drops it on the next
        # read if the exchange no longer reports the position.
        ledger.record(fill, intent, cloid=cloid)
        ledger.settle_pending(cloid)
        ours.append(fill)

    return ours, high_water, foreign
