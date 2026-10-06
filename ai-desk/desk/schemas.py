"""Contracts between modules. Everything that crosses a module boundary is one of these.

Phase 1 uses Signal -> OrderIntent -> RiskVerdict -> Fill. Thesis / Review are the
research-layer contracts for phase 2; they are defined now so the boundary is fixed
before any LLM code exists.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _id() -> str:
    return uuid.uuid4().hex[:16]


AssetClass = Literal["crypto", "hip3"]


def asset_class(asset: str) -> AssetClass:
    """HIP-3 (builder-deployed) perps are namespaced, e.g. 'xyz:TSLA'. Thin books,
    isolated margin: the risk engine treats them as a separate class."""
    return "hip3" if ":" in asset else "crypto"


class SourceRef(BaseModel):
    url: str
    quote: str
    observed_at: datetime


class Thesis(BaseModel):
    """Analyst output (phase 2). Verifiable evidence, explicit falsifier, hard expiry."""
    id: str = Field(default_factory=_id)
    asset: str
    direction: Literal["long", "short", "neutral"]
    horizon_hours: int
    catalyst: str
    evidence: list[SourceRef]
    confidence: float = Field(ge=0.0, le=1.0)
    falsified_if: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=_now)


class Review(BaseModel):
    """Adversary output (phase 2)."""
    thesis_id: str
    verdict: Literal["pass", "reject"]
    already_priced: bool
    single_source: bool
    counter: str


class Signal(BaseModel):
    """A strategy's opinion. Strength in [-1, 1]; sign is direction."""
    asset: str
    strength: float = Field(ge=-1.0, le=1.0)
    source: str
    ttl_seconds: int
    created_at: datetime = Field(default_factory=_now)


class TargetPosition(BaseModel):
    """What a strategy wants to hold. Signed notional in USD."""
    asset: str
    notional_usd: float
    strategy_id: str
    horizon_hours: int
    reason: str


class OrderIntent(BaseModel):
    """The only thing execution ever receives, and only after a RiskVerdict."""
    id: str = Field(default_factory=_id)
    asset: str
    side: Literal["buy", "sell"]
    notional_usd: float = Field(gt=0)
    order_type: Literal["limit_alo", "limit_ioc"] = "limit_alo"
    limit_px: float | None = None       # None: execution derives from mid +/- offset
    stop_px: float | None = None        # exchange-side stop placed after fill
    take_profit_px: float | None = None
    reduce_only: bool = False
    strategy_id: str
    horizon_hours: int
    reason: str
    created_at: datetime = Field(default_factory=_now)

    @property
    def signed_notional(self) -> float:
        return self.notional_usd if self.side == "buy" else -self.notional_usd


class RiskVerdict(BaseModel):
    intent_id: str
    decision: Literal["approve", "reduce", "reject"]
    approved_notional_usd: float = Field(ge=0)
    rules_fired: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_now)


class Fill(BaseModel):
    intent_id: str
    asset: str
    side: Literal["buy", "sell"]
    requested_usd: float
    filled_usd: float
    decision_px: float
    fill_px: float
    fee_usd: float
    partial: bool
    exchange_oid: str | None = None
    stop_oid: str | None = None
    created_at: datetime = Field(default_factory=_now)

    @property
    def slippage_bps(self) -> float:
        if self.decision_px == 0:
            return 0.0
        sign = 1 if self.side == "buy" else -1
        return sign * (self.fill_px - self.decision_px) / self.decision_px * 1e4


class Position(BaseModel):
    asset: str
    notional_usd: float                 # signed
    size: float                         # signed, in coin units
    entry_px: float
    mark_px: float
    unrealized_pnl_usd: float
    opened_at: datetime | None = None
    strategy_id: str | None = None
    horizon_hours: int | None = None
    managed: bool = True                # False: on the exchange but not in our ledger


class AssetContext(BaseModel):
    asset: str
    mark_px: float
    mid_px: float
    funding_hourly: float
    open_interest: float                # coin units
    day_volume_usd: float
    sz_decimals: int
    max_leverage: int
    book_depth_usd_10bps: float | None = None   # sum of both sides within 10 bps of mid


class AccountState(BaseModel):
    equity_usd: float
    margin_used_usd: float
    positions: list[Position]
    as_of: datetime = Field(default_factory=_now)

    @property
    def gross_notional_usd(self) -> float:
        return sum(abs(p.notional_usd) for p in self.positions)

    def position(self, asset: str) -> Position | None:
        return next((p for p in self.positions if p.asset == asset), None)
