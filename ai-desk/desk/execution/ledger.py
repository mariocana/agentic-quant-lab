"""What the exchange does not remember about a position.

Hyperliquid answers "how much", never "why": coin, size, entry price, P&L. The
desk needs the rest — which strategy opened it, when, with what horizon, which
orders built it — and that is what this file keeps.

One row per asset, because the desk reasons in positions, not in orders; each row
carries the cloids of the fills that built it, so a position can always be traced
back to the intents that caused it.

Orders in flight live in a second table. A post-only order can rest on the book
for hours before it fills, so the context travels with the order from the moment
it is sent: without that, a resting order that fills overnight would produce a
position the desk cannot recognise.

The exchange stays the source of truth for size. The ledger only annotates it: a
row never creates a position, and a position the ledger has never heard of is
reported as unmanaged rather than adopted.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from desk.config import VAR
from desk.schemas import Fill, OrderIntent, Position

LEDGER_PATH = VAR / "position_ledger.json"


class PositionLedger:
    def __init__(self, path: Path = LEDGER_PATH):
        self.path = path
        self._reload()

    def _reload(self) -> None:
        """Read the file back before trusting what is in memory.

        The dashboard, a cycle and a script can all hold a ledger at once, and a
        whole-file write from one of them would otherwise erase what another just
        recorded — which is how eight positions lost their context in one evening.
        """
        raw = json.loads(self.path.read_text()) if self.path.exists() else {}
        # the file used to be a bare {asset: row} map; keep reading those
        self.rows: dict[str, dict] = raw.get("positions", raw if "pending" not in raw else {})
        self.pending: dict[str, dict] = raw.get("pending", {})
        # Orders that have produced at least one fill. An order fills in tranches —
        # 20 units, then 2, on the same oid — so its context has to outlive the
        # first fill or every later tranche looks like somebody else's trade.
        self.settled: dict[str, dict] = raw.get("settled", {})

    def _save(self) -> None:
        """Atomic: a reader never sees a half-written ledger."""
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(
            {"positions": self.rows, "pending": self.pending, "settled": self.settled},
            indent=2, sort_keys=True))
        tmp.replace(self.path)

    # ---- orders in flight ----------------------------------------------------

    def record_sent(self, intent: OrderIntent, cloid: str, oid: str | None) -> None:
        """An order is on the exchange. Store its context now: it may fill in a
        second or rest on the book until tomorrow, and either way the fill must be
        attributable when it arrives."""
        self._reload()
        self.pending[cloid] = {
            "intent_id": intent.id, "asset": intent.asset, "side": intent.side,
            "strategy_id": intent.strategy_id, "horizon_hours": intent.horizon_hours,
            "reduce_only": intent.reduce_only, "oid": str(oid) if oid else None,
            "sent_at": datetime.now(timezone.utc).isoformat(),
        }
        self._save()

    def pending_for(self, *, oid: str | None = None, cloid: str | None = None) -> tuple[str, dict] | None:
        """Find an in-flight order by either id. Exchanges echo the oid on every
        fill; the cloid only when the order carried one."""
        for table in (self.pending, self.settled):
            if cloid and cloid in table:
                return cloid, table[cloid]
            if oid:
                for c, row in table.items():
                    if row.get("oid") == str(oid):
                        return c, row
        return None

    def pending_for_asset(self, asset: str) -> dict | None:
        """An order we sent for this asset that has not come back yet."""
        return next((r for r in self.pending.values() if r.get("asset") == asset), None)

    def settle_pending(self, cloid: str) -> None:
        """A fill arrived for this order. Keep its context: more tranches may follow
        on the same order id."""
        self._reload()
        row = self.pending.pop(cloid, None)
        if row is not None:
            self.settled[cloid] = {**row, "settled_at": datetime.now(timezone.utc).isoformat()}
            self._save()

    def drop_pending(self, cloid: str) -> None:
        self._reload()
        if self.pending.pop(cloid, None) is not None or self.settled.pop(cloid, None) is not None:
            self._save()

    def prune_settled(self, older_than_hours: float = 48.0) -> int:
        """Settled orders cannot fill forever; forget them so the file stays small."""
        cutoff = datetime.now(timezone.utc).timestamp() - older_than_hours * 3600
        gone = [c for c, r in self.settled.items()
                if datetime.fromisoformat(r["settled_at"]).timestamp() < cutoff]
        for c in gone:
            self.settled.pop(c)
        if gone:
            self._save()
        return len(gone)

    def stale_pending(self, older_than_hours: float = 24.0) -> list[str]:
        """Orders we sent and never saw again — cancelled, expired, or lost."""
        cutoff = datetime.now(timezone.utc).timestamp() - older_than_hours * 3600
        return [c for c, r in self.pending.items()
                if datetime.fromisoformat(r["sent_at"]).timestamp() < cutoff]

    # ---- writing -------------------------------------------------------------

    def record(self, fill: Fill, intent: OrderIntent, cloid: str | None = None) -> None:
        """Note a fill. The first fill that opens a position sets `opened_at`;
        later fills on the same side only append their cloid, so adding to a
        position does not restart its time stop."""
        self._reload()
        row = self.rows.get(fill.asset)
        if row is None or intent.reduce_only is False and row.get("closed"):
            row = {"opened_at": datetime.now(timezone.utc).isoformat(), "cloids": []}
        row["strategy_id"] = intent.strategy_id
        row["horizon_hours"] = intent.horizon_hours or row.get("horizon_hours")
        row["last_fill_at"] = fill.created_at.isoformat()
        row.pop("closed", None)
        if cloid:
            row.setdefault("cloids", []).append(cloid)
        if fill.stop_oid:
            row["stop_oid"] = fill.stop_oid
        self.rows[fill.asset] = row
        self._save()

    def forget(self, asset: str) -> None:
        """The position is gone from the exchange: drop the row so a later position
        in the same asset starts its own clock."""
        self._reload()
        if self.rows.pop(asset, None) is not None:
            self._save()

    def reconcile(self, open_assets: set[str]) -> list[str]:
        """Drop rows for positions the exchange no longer reports. Returns what was
        dropped, so the caller can log it."""
        gone = [a for a in self.rows if a not in open_assets]
        for a in gone:
            self.rows.pop(a)
        if gone:
            self._save()
        return gone

    # ---- reading -------------------------------------------------------------

    def enrich(self, positions: list[Position]) -> list[Position]:
        """Fill in what the exchange could not tell us.

        A position with no row keeps `managed = False`: it was opened by hand, or
        by a desk whose ledger was lost. Either way it is not ours to manage, and
        saying so is safer than adopting it.
        """
        self._reload()
        out = []
        for p in positions:
            row = self.rows.get(p.asset)
            if row is None:
                # An order of ours that rested and then filled shows up here before
                # the next reconcile() promotes it. It is ours, just not booked yet;
                # calling it unmanaged would be wrong and would raise a false alarm.
                pending = self.pending_for_asset(p.asset)
                out.append(p.model_copy(update={
                    "managed": bool(pending),
                    "strategy_id": pending.get("strategy_id") if pending else None,
                    "horizon_hours": pending.get("horizon_hours") if pending else None,
                }))
                continue
            opened = row.get("opened_at")
            out.append(p.model_copy(update={
                "managed": True,
                "strategy_id": row.get("strategy_id"),
                "horizon_hours": row.get("horizon_hours"),
                "opened_at": datetime.fromisoformat(opened) if opened else None,
            }))
        return out

    def stop_oid(self, asset: str) -> str | None:
        return (self.rows.get(asset) or {}).get("stop_oid")
