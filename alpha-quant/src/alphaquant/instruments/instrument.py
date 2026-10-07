"""Instrument: everything the engine needs to know about what it trades.

The engine has no market-specific logic. It asks the Instrument what a point
is worth, how big an order can be, what a trade costs and when the market is
open. Market specs come from quantlake's reference/instruments table, costs
from config/costs.yaml (see source.py).
"""
import math
from dataclasses import dataclass
from enum import StrEnum

from alphaquant.instruments.fees import Costs
from alphaquant.instruments.sessions import SessionCalendar


class AssetClass(StrEnum):
    FUTURE = "future"
    CRYPTO_SPOT = "crypto_spot"
    CRYPTO_PERP = "crypto_perp"
    FX = "fx"
    EQUITY = "equity"


@dataclass(frozen=True)
class DataRef:
    """Where the instrument's bars live in quantlake: gold/<gold_table>/<timeframe>."""

    gold_table: str
    symbol: str  # value of the 'symbol' column in that table (e.g. 'ES_1min')


@dataclass(frozen=True)
class Instrument:
    symbol: str
    asset_class: AssetClass
    exchange: str
    quote_ccy: str
    tick_size: float
    multiplier: float   # value of one point per unit of quantity (ES 50, crypto 1)
    qty_step: float
    min_qty: float
    session: SessionCalendar
    data: DataRef
    costs: Costs

    def __post_init__(self) -> None:
        for field in ("tick_size", "multiplier", "qty_step", "min_qty"):
            value = getattr(self, field)
            if not value > 0:
                raise ValueError(f"{self.symbol}: {field} must be > 0, got {value}")

    @property
    def slippage(self) -> float:
        """Default market-order slippage, in price units."""
        return self.costs.slippage_ticks * self.tick_size

    def round_qty(self, qty: float) -> float:
        """Round a size down to qty_step; 0 if it ends up below min_qty. Keeps the sign."""
        steps = math.floor(abs(qty) / self.qty_step + 1e-9)
        size = round(steps * self.qty_step, 12)
        if size < self.min_qty:
            return 0.0
        return math.copysign(size, qty)

    def round_price(self, price: float) -> float:
        """Round a price to the nearest tick."""
        return round(round(price / self.tick_size) * self.tick_size, 12)
