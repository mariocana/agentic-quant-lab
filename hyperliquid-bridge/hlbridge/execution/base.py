"""Execution adapter interface. One venue = one adapter. Whoever sends orders only talks to this."""
from __future__ import annotations

from abc import ABC, abstractmethod

from hlbridge.schemas import AccountState, Fill, OrderIntent, RiskVerdict


class ExecutionAdapter(ABC):
    name: str

    @abstractmethod
    def account_state(self) -> AccountState: ...

    @abstractmethod
    def execute(self, intent: OrderIntent, verdict: RiskVerdict, mid_px: float) -> Fill | None:
        """Send the approved notional. Returns None if nothing was filled.
        Must be idempotent on intent.id: resending the same intent must not double-fill."""

    @abstractmethod
    def flatten_all(self) -> list[Fill]:
        """Close every open position at market. Used by the halt path only."""

    def tradable_assets(self) -> set[str] | None:
        """What this venue actually lists, or None when it takes anything.

        The strategy ranks on mainnet data because that is where the volume is,
        but a venue need not list the same perps: testnet is missing 21 of
        mainnet's names. Without this the desk picks a name it cannot trade and
        the cycle dies on it."""
        return None


def round_size(sz: float, sz_decimals: int) -> float:
    return round(sz, sz_decimals)


def round_price(px: float, sz_decimals: int, is_perp: bool = True) -> float:
    """Hyperliquid tick rule: max 5 significant figures, and at most
    (6 - szDecimals) decimals for perps."""
    if px <= 0:
        return px
    max_decimals = (6 if is_perp else 8) - sz_decimals
    sig = float(f"{px:.5g}")
    return round(sig, max_decimals)
