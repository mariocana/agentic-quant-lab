"""Trading costs per instrument, loaded from config/costs.yaml.

Costs depend on the broker or exchange account, not on the market, so they
live in alphaquant's config while market specs (tick, multiplier, session)
come from quantlake. Every instrument used in a backtest must have a cost
entry: a missing one is an error, never a silent zero.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

import yaml

from alphaquant.config import COSTS_FILE

Liquidity = Literal["maker", "taker"]


class FeeModel(Protocol):
    def fee(self, qty: float, price: float, multiplier: float, liquidity: Liquidity = "taker") -> float:
        """Commission for one side of a trade, in the instrument's quote currency."""
        ...


@dataclass(frozen=True)
class PerContractFee:
    """Fixed commission per contract per side (CME futures)."""

    per_side: float

    def fee(self, qty: float, price: float, multiplier: float, liquidity: Liquidity = "taker") -> float:
        return abs(qty) * self.per_side


@dataclass(frozen=True)
class PercentFee:
    """Commission as a fraction of notional (crypto exchanges)."""

    maker: float
    taker: float

    def fee(self, qty: float, price: float, multiplier: float, liquidity: Liquidity = "taker") -> float:
        rate = self.maker if liquidity == "maker" else self.taker
        return abs(qty) * price * multiplier * rate


@dataclass(frozen=True)
class Costs:
    fee: FeeModel
    slippage_ticks: float
    verified: bool  # False = conservative placeholder, not the account's real figure


def load_costs(path: Path = COSTS_FILE, profile: str = "default") -> dict[str, Costs]:
    """Read one cost profile from the YAML file, keyed by instrument symbol."""
    raw = yaml.safe_load(Path(path).read_text()) or {}
    profiles = raw.get("profiles", {})
    if profile not in profiles:
        raise KeyError(f"Cost profile '{profile}' not found in {path}; available: {sorted(profiles)}")
    return {symbol: _parse_costs(symbol, spec) for symbol, spec in profiles[profile].items()}


def _parse_costs(symbol: str, spec: dict) -> Costs:
    kind = spec.get("fee")
    if kind == "per_contract":
        fee: FeeModel = PerContractFee(per_side=float(spec["per_side"]))
    elif kind == "percent":
        fee = PercentFee(maker=float(spec["maker"]), taker=float(spec["taker"]))
    else:
        raise ValueError(f"{symbol}: unknown fee type {kind!r} (expected 'per_contract' or 'percent')")

    slippage = float(spec.get("slippage_ticks", 0))
    if slippage < 0:
        raise ValueError(f"{symbol}: slippage_ticks must be >= 0, got {slippage}")
    return Costs(fee=fee, slippage_ticks=slippage, verified=bool(spec.get("verified", False)))


@dataclass(frozen=True)
class VenueCosts:
    """One fee schedule for every instrument on a venue (Hyperliquid lists ~560
    perps). Fees and slippage are verified separately: the fee is a rule of the
    venue, the slippage depends on the book it was measured on."""

    fee: PercentFee
    slippage_bps: dict[str, float]          # by liquidity: maker / taker
    fee_verified: bool
    slippage_verified: bool
    source: str

    def round_trip_bps(self, liquidity: Liquidity = "taker") -> float:
        rate = self.fee.maker if liquidity == "maker" else self.fee.taker
        return 2 * (rate * 1e4 + self.slippage_bps[liquidity])


def load_venue_costs(venue: str, path: Path = COSTS_FILE) -> VenueCosts:
    raw = yaml.safe_load(Path(path).read_text()) or {}
    venues = raw.get("venues", {})
    if venue not in venues:
        raise KeyError(f"Venue '{venue}' not found in {path}; available: {sorted(venues)}")
    v = venues[venue]
    if v.get("fee") != "percent":
        raise ValueError(f"{venue}: venue fees must be 'percent', got {v.get('fee')!r}")
    slip = {k: float(x) for k, x in v["slippage_bps"].items()}
    if set(slip) != {"maker", "taker"} or min(slip.values()) < 0:
        raise ValueError(f"{venue}: slippage_bps needs non-negative maker and taker")
    return VenueCosts(fee=PercentFee(maker=float(v["maker"]), taker=float(v["taker"])),
                      slippage_bps=slip, fee_verified=bool(v.get("fee_verified", False)),
                      slippage_verified=bool(v.get("slippage_verified", False)),
                      source=str(v.get("source", "")))
