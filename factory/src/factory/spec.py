"""What a strategy must say about itself before any result is seen.

A spec is written by the agents, read by a human, and frozen in the registry:
its hash is the trial's id, and anything that changes it is a new trial that k
counts. Fields that would let a model hide its reasoning are required:

  hypothesis      the effect, in one or two sentences
  who_loses       who is on the other side and why they keep losing. An edge
                  with no loser is a pattern in noise.
  sources         every number taken from a paper carries the page it is on.
                  A model that attributes to an author something the author never
                  wrote is caught by opening the paper at that page.
  kill_if         what result would bury the idea, written before the result
  strategy/params the class in desk.signals and its constructor arguments

The thresholds of the gates are not here: they are the lab's, the same for every
spec, so a spec cannot choose the bar it has to clear.
"""
from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator

from alphaquant.registry import Registry


class SourceRef(BaseModel):
    citation: str = Field(min_length=5)          # author, year, title, venue
    page: int = Field(ge=1)                      # where the claimed number is
    claim: str = Field(min_length=10)            # what the source says, in our words


class StrategySpec(BaseModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]{2,40}$")
    hypothesis: str = Field(min_length=40)
    who_loses: str = Field(min_length=40)
    sources: list[SourceRef] = Field(min_length=1)
    kill_if: str = Field(min_length=20)
    strategy: str                                # desk.signals.<module>.<Class>
    params: dict = Field(default_factory=dict)
    venue: str = "hyperliquid"
    parent: str | None = None                    # spec hash this one varies, if any

    @field_validator("strategy")
    @classmethod
    def _in_desk_signals(cls, v: str) -> str:
        if not v.startswith("desk.signals."):
            raise ValueError("the strategy class must live in desk.signals")
        return v

    def as_registry_spec(self) -> dict:
        return {**self.model_dump(), "registered_before_results": True}


def load_spec(path: Path) -> StrategySpec:
    return StrategySpec.model_validate(yaml.safe_load(Path(path).read_text()))


def freeze(spec: StrategySpec, registry: Registry | None = None) -> str:
    """Register the spec. From here its hash is its id; changing a comma makes a new trial."""
    return (registry or Registry()).register_spec(spec.as_registry_spec())
