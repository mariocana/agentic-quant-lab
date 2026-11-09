"""Strategy interface. A strategy turns market data into TargetPositions.
It never sees the account, never sizes against risk, never sends orders."""
from __future__ import annotations

from abc import ABC, abstractmethod

from desk.data.hl_market import Candle
from desk.schemas import AssetContext, TargetPosition


class Strategy(ABC):
    id: str
    interval: str          # candle interval it consumes
    bars: int              # how many bars it needs
    horizon_hours: int

    @abstractmethod
    def universe(self, contexts: dict[str, AssetContext]) -> list[str]: ...

    @abstractmethod
    def targets(self, candles: dict[str, list[Candle]], contexts: dict[str, AssetContext],
                equity_usd: float) -> list[TargetPosition]: ...
