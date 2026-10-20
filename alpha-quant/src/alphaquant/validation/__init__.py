"""Stages 2-7 of mc/docs/pipeline_prop.md: trade list in, gate verdict out.

Deterministic: same trades, config and seed give the same verdict.
"""
from alphaquant.validation.gates import (
    Check, GateConfig, GateResult, gate2, gate3, gate4, gate5, gate6, gate7, split_sample,
)
from alphaquant.validation.metrics import Metrics, max_drawdown, measure
from alphaquant.validation.prop import LUCIDFLEX_50K, PropAccount, PropReport, simulate
from alphaquant.validation.resampling import bootstrap_mean, dd_at_horizons, monte_carlo
from alphaquant.validation.trades import TRADE_LOG_SCHEMA, TradeLog

__all__ = [
    "Check", "GateConfig", "GateResult", "LUCIDFLEX_50K", "Metrics", "PropAccount", "PropReport",
    "TRADE_LOG_SCHEMA", "TradeLog", "bootstrap_mean", "dd_at_horizons", "gate2", "gate3", "gate4",
    "gate5", "gate6", "gate7", "max_drawdown", "measure", "monte_carlo", "simulate", "split_sample",
]
