"""The go-live path's gates: a strategy's equity curve and trades in, verdict out.

    validation  is it worth its one look at the holdout?
    holdout     is it worth the forward test in shadow mode?

Deterministic: same replay, same verdict. Nothing here sends a strategy to live
money; that is the forward test's job, in the trading desk.
"""
from alphaquant.validation.checks import Check, GateResult
from alphaquant.validation.portfolio import (
    PortfolioGateConfig, PortfolioMetrics, deflated_sharpe, holdout_gate, measure_portfolio, validation_gate,
)

__all__ = ["Check", "GateResult", "PortfolioGateConfig", "PortfolioMetrics", "deflated_sharpe",
           "holdout_gate", "measure_portfolio", "validation_gate"]
