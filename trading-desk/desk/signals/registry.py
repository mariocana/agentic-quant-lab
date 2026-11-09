"""Which strategies the desk runs, and how: read from config/strategies.yaml.

Before this the strategy was a line of code, `Reversal()`, in two places. Now it
is a file a pull request changes, which is where a human approves it.

  active   trades on the desk's account. At most one: the ledger keeps one row
           per asset with a single strategy_id, so two active strategies wanting
           the same perp could not be told apart.
  shadow   runs every day in its own paper account (desk/shadow.py) and never
           sends an order. This is the forward test.

The file can only name classes inside desk.signals: a config line must not be a
way to import and run arbitrary code in the process that holds the API key.
"""
from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml

from desk.config import ROOT
from desk.signals.base import Strategy

STRATEGIES_PATH = ROOT / "config" / "strategies.yaml"
ALLOWED_PACKAGE = "desk.signals."


@dataclass(frozen=True)
class StrategyEntry:
    id: str
    strategy: Strategy
    mode: Literal["active", "shadow"]


class StrategyConfigError(ValueError):
    pass


def _build(entry: dict) -> StrategyEntry:
    sid, path, mode = entry.get("id"), entry.get("class", ""), entry.get("mode")
    if mode not in ("active", "shadow"):
        raise StrategyConfigError(f"{sid}: mode must be active or shadow, not {mode!r}")
    if not path.startswith(ALLOWED_PACKAGE):
        raise StrategyConfigError(f"{sid}: {path!r} is outside {ALLOWED_PACKAGE}*")
    module, _, name = path.rpartition(".")
    cls = getattr(importlib.import_module(module), name)
    if not (isinstance(cls, type) and issubclass(cls, Strategy)):
        raise StrategyConfigError(f"{sid}: {path} is not a Strategy")
    strategy = cls(**(entry.get("params") or {}))
    if strategy.id != sid:
        raise StrategyConfigError(f"{sid}: the class says its id is {strategy.id!r}; the journal "
                                  "would file its trades under another name")
    return StrategyEntry(id=sid, strategy=strategy, mode=mode)


def load_strategies(path: Path = STRATEGIES_PATH) -> list[StrategyEntry]:
    raw = yaml.safe_load(Path(path).read_text()) or {}
    entries = [_build(e) for e in raw.get("strategies", [])]
    ids = [e.id for e in entries]
    if len(ids) != len(set(ids)):
        raise StrategyConfigError(f"duplicate strategy ids: {ids}")
    if sum(e.mode == "active" for e in entries) > 1:
        raise StrategyConfigError("more than one active strategy: the ledger cannot attribute "
                                  "shared perps (one subaccount per strategy first)")
    return entries


def active(entries: list[StrategyEntry]) -> StrategyEntry | None:
    return next((e for e in entries if e.mode == "active"), None)


def shadows(entries: list[StrategyEntry]) -> list[StrategyEntry]:
    return [e for e in entries if e.mode == "shadow"]
