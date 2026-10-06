"""What the exchange does not remember about a position.

Hyperliquid answers "how much", never "why": coin, size, entry price, P&L. The
desk needs the rest — which strategy opened it, when, with what horizon, which
orders built it — and that is what this file keeps.

One row per asset, because the desk reasons in positions, not in orders; each row
carries the cloids of the fills that built it, so a position can always be traced
back to the intents that caused it.

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
        self.rows: dict[str, dict] = json.loads(path.read_text()) if path.exists() else {}

    def _save(self) -> None:
        self.path.write_text(json.dumps(self.rows, indent=2, sort_keys=True))

    # ---- writing -------------------------------------------------------------

    def record(self, fill: Fill, intent: OrderIntent, cloid: str | None = None) -> None:
        """Note a fill. The first fill that opens a position sets `opened_at`;
        later fills on the same side only append their cloid, so adding to a
        position does not restart its time stop."""
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
        out = []
        for p in positions:
            row = self.rows.get(p.asset)
            if row is None:
                out.append(p.model_copy(update={"managed": False}))
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
