"""Gates for portfolio strategies: equity curve and trades in, verdict out.

The prop gates judge an intraday strategy on one instrument by win rate and
reward-to-risk. A dollar-neutral book of thirty perps rebalanced every day has no
win rate worth the name; what matters is whether the curve beats zero after
costs by more than the search that found it could explain. So:

  sharpe        annualised on daily equity returns (365 days: the market never closes)
  deflated      probability that the true Sharpe is above what the best of k
                strategies with no edge would show (Bailey & Lopez de Prado,
                "The Deflated Sharpe Ratio", 2014). k comes from the registry, so
                every variant ever judged on validation raises the bar for this one.
                With k = 1 it is the probabilistic Sharpe ratio.
  max_dd        worst peak-to-trough of the equity curve, as a fraction
  cost_share    fees over gross trading P&L: how much of the edge the venue keeps.
                Infinite when the gross edge is not positive.

Two gates. Validation decides whether a spec is worth its one look at the
holdout. Holdout decides whether it is worth the forward test in shadow mode:
its Sharpe is compared with the spec's own validation Sharpe, its drawdown with
the same absolute cap.
Nothing here promotes a strategy to live money: that is the forward test's job.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import NormalDist

import numpy as np

from alphaquant.engine.types import SimResult
from alphaquant.validation.gates import Check, GateResult

PERIODS_PER_YEAR = 365
EULER_GAMMA = 0.5772156649015329
_N = NormalDist()


@dataclass(frozen=True)
class PortfolioMetrics:
    days: int
    trades: int
    total_return: float
    sharpe: float              # annualised
    sharpe_daily: float
    skew: float
    kurtosis: float            # not excess: 3 for a normal
    max_dd: float
    gross_pnl: float
    fees: float
    funding: float
    cost_share: float

    def as_dict(self) -> dict:
        return {k: (None if isinstance(v, float) and not math.isfinite(v) else v) for k, v in self.__dict__.items()}


def measure_portfolio(sim: SimResult, start_equity: float) -> PortfolioMetrics:
    eq = np.concatenate([[start_equity], sim.equity["equity"].to_numpy()])
    r = eq[1:] / eq[:-1] - 1
    sd = r.std(ddof=1) if len(r) > 1 else 0.0
    sr = r.mean() / sd if sd > 0 else 0.0
    z = (r - r.mean()) / sd if sd > 0 else np.zeros_like(r)
    peak = np.maximum.accumulate(eq)
    t = sim.trades
    gross, fees = float(t["gross_pnl_quote"].sum()), float(t["fees_quote"].sum())
    return PortfolioMetrics(
        days=len(r), trades=t.height, total_return=float(eq[-1] / eq[0] - 1),
        sharpe=float(sr * math.sqrt(PERIODS_PER_YEAR)), sharpe_daily=float(sr),
        skew=float((z ** 3).mean()) if len(r) > 2 else 0.0,
        kurtosis=float((z ** 4).mean()) if len(r) > 3 else 3.0,
        max_dd=float((1 - eq / peak).max()), gross_pnl=gross, fees=fees,
        funding=float(t["funding_quote"].sum()),
        cost_share=fees / gross if gross > 0 else math.inf,
    )


def deflated_sharpe(m: PortfolioMetrics, k: int, trial_sharpes_daily: list[float] | None = None) -> float:
    """Probability that the true daily Sharpe exceeds the expected maximum of k
    zero-edge trials. The spread of Sharpes across trials comes from the registry
    when there are at least two; otherwise the estimator's own variance is used."""
    T, sr = m.days, m.sharpe_daily
    if T < 3:
        return float("nan")
    denom = 1 - m.skew * sr + (m.kurtosis - 1) / 4 * sr * sr
    if denom <= 0:
        return float("nan")
    if k <= 1:
        sr0 = 0.0
    else:
        trials = trial_sharpes_daily or []
        var = float(np.var(trials, ddof=1)) if len(trials) >= 2 else denom / (T - 1)
        sr0 = math.sqrt(var) * ((1 - EULER_GAMMA) * _N.inv_cdf(1 - 1 / k)
                                + EULER_GAMMA * _N.inv_cdf(1 - 1 / (k * math.e)))
    return _N.cdf((sr - sr0) * math.sqrt(T - 1) / math.sqrt(denom))


@dataclass(frozen=True)
class PortfolioGateConfig:
    min_days: int = 180
    min_trades: int = 100
    min_deflated: float = 0.95
    max_dd: float = 0.25
    max_cost_share: float = 0.5
    holdout_min_sharpe_ratio: float = 0.5      # holdout Sharpe >= half the validation Sharpe


def _pct(x):
    return "inf" if not math.isfinite(x) else f"{x:.1%}"


def validation_gate(m: PortfolioMetrics, k: int, trial_sharpes_daily: list[float] | None = None,
                    cfg: PortfolioGateConfig = PortfolioGateConfig()) -> GateResult:
    dsr = deflated_sharpe(m, k, trial_sharpes_daily)
    checks = [
        Check("days of history", m.days >= cfg.min_days, str(m.days), f">= {cfg.min_days}"),
        Check("trades", m.trades >= cfg.min_trades, str(m.trades), f">= {cfg.min_trades}"),
        Check("Sharpe after costs", m.sharpe > 0, f"{m.sharpe:.2f}", "> 0"),
        Check(f"deflated Sharpe (k={k})", None if math.isnan(dsr) else dsr >= cfg.min_deflated,
              "n/a" if math.isnan(dsr) else f"{dsr:.3f}", f">= {cfg.min_deflated}"),
        Check("max drawdown", m.max_dd <= cfg.max_dd, _pct(m.max_dd), f"<= {cfg.max_dd:.0%}"),
        Check("fees / gross edge", m.cost_share <= cfg.max_cost_share, _pct(m.cost_share),
              f"<= {cfg.max_cost_share:.0%}"),
    ]
    return GateResult(stage=1, title="portfolio: validation", checks=checks,
                      data={"metrics": m.as_dict(), "k": k, "deflated_sharpe": dsr})


def holdout_gate(m: PortfolioMetrics, validation: PortfolioMetrics,
                 cfg: PortfolioGateConfig = PortfolioGateConfig()) -> GateResult:
    need = cfg.holdout_min_sharpe_ratio * validation.sharpe
    checks = [
        Check("return over the holdout", m.total_return > 0, _pct(m.total_return), "> 0"),
        Check("Sharpe vs validation", m.sharpe > 0 and m.sharpe >= need, f"{m.sharpe:.2f}",
              f">= {need:.2f} ({cfg.holdout_min_sharpe_ratio:.0%} of {validation.sharpe:.2f})"),
        # The same absolute cap as validation, not a multiple of validation's drawdown:
        # a drawdown is one draw from a noisy distribution that widens with the length
        # of the sample, and a 300-day holdout with Sharpe 2.6 failed "1.5x a 270-day
        # validation" on chance alone.
        Check("max drawdown", m.max_dd <= cfg.max_dd, _pct(m.max_dd), f"<= {cfg.max_dd:.0%}"),
    ]
    return GateResult(stage=2, title="portfolio: holdout", checks=checks, data={"metrics": m.as_dict()})
