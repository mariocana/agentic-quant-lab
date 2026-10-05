"""Persistent risk state: day-start equity, peak equity, halt flag, kill switch.

Plain JSON on disk so it survives restarts and can be inspected / edited by hand.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from desk.config import KILL_FILE, VAR

STATE_PATH = VAR / "risk_state.json"


@dataclass
class RiskState:
    day: str = ""                      # UTC date "YYYY-MM-DD"
    day_start_equity: float = 0.0
    peak_equity: float = 0.0
    halted: bool = False
    halt_reason: str = ""
    flatten_requested: bool = False
    history: list[dict] = field(default_factory=list)   # [{day, start, end}]

    # ---- persistence ---------------------------------------------------------

    @classmethod
    def load(cls, path: Path = STATE_PATH) -> "RiskState":
        if path.exists():
            return cls(**json.loads(path.read_text()))
        return cls()

    def save(self, path: Path = STATE_PATH) -> None:
        path.write_text(json.dumps(asdict(self), indent=2))

    # ---- updates -------------------------------------------------------------

    def observe(self, equity: float, limits: dict, now: datetime | None = None) -> list[str]:
        """Fold a fresh equity reading in. Returns the list of rules that fired."""
        now = now or datetime.now(timezone.utc)
        today = now.strftime("%Y-%m-%d")
        fired: list[str] = []

        if self.day != today:
            if self.day:
                self.history.append({"day": self.day, "start": self.day_start_equity, "end": equity})
            self.day = today
            self.day_start_equity = equity
        if equity > self.peak_equity:
            self.peak_equity = equity

        if self.day_start_equity > 0:
            day_pnl = equity / self.day_start_equity - 1
            if day_pnl <= -limits["daily_loss_flatten_pct"] and not self.halted:
                self.halted, self.halt_reason = True, f"daily_loss_flatten {day_pnl:.2%}"
                self.flatten_requested = True
                fired.append("daily_loss_flatten")
        if self.peak_equity > 0:
            dd = equity / self.peak_equity - 1
            if dd <= -limits["max_drawdown_pct"] and not self.halted:
                self.halted, self.halt_reason = True, f"max_drawdown {dd:.2%}"
                fired.append("max_drawdown")
        return fired

    def day_pnl_pct(self, equity: float) -> float:
        return equity / self.day_start_equity - 1 if self.day_start_equity > 0 else 0.0

    def unlock(self) -> None:
        self.halted, self.halt_reason, self.flatten_requested = False, "", False

    # ---- kill switch (a file, so a human or any process can flip it) ---------

    @staticmethod
    def kill_engaged(path: Path | None = None) -> bool:
        return (path or KILL_FILE).exists()

    @staticmethod
    def engage_kill(reason: str = "manual", path: Path | None = None) -> None:
        (path or KILL_FILE).write_text(f"{datetime.now(timezone.utc).isoformat()} {reason}\n")

    @staticmethod
    def release_kill(path: Path | None = None) -> None:
        (path or KILL_FILE).unlink(missing_ok=True)
