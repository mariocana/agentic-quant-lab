"""Portfolio gates. The property that matters most: the same curve that passes
alone must fail once it is the best of a long search."""
import math
from datetime import datetime, timedelta, timezone

import numpy as np
import polars as pl
import pytest

from alphaquant.engine.types import EQUITY_SCHEMA, ExitReason, SimResult, Trade, trades_frame
from alphaquant.validation.portfolio import (
    PortfolioGateConfig, deflated_sharpe, holdout_gate, measure_portfolio, validation_gate,
)

T0 = datetime(2025, 4, 1, tzinfo=timezone.utc)


def sim(returns, gross=1000.0, fees=100.0, n_trades=200, start=10_000.0):
    eq = start * np.cumprod(1 + np.asarray(returns))
    equity = pl.DataFrame({"timestamp": [T0 + timedelta(days=i) for i in range(len(eq))], "equity": eq}).cast(dict(EQUITY_SCHEMA))
    per = gross / n_trades
    trades = [Trade(symbol="A", side=1, qty=1.0, entry_time=T0, entry_price=100.0, exit_time=T0,
                    exit_price=100.0 + per, exit_reason=ExitReason.SIGNAL, multiplier=1.0,
                    fees_quote=fees / n_trades) for _ in range(n_trades)]
    return SimResult(trades=trades_frame(trades), equity=equity)


def noisy(mean, sd=0.01, n=270, seed=3):
    return np.random.default_rng(seed).normal(mean, sd, n)


def test_drawdown_and_return_on_a_known_path():
    m = measure_portfolio(sim([0.10, -0.50, 0.20], start=100.0), 100.0)
    assert m.total_return == pytest.approx(1.1 * 0.5 * 1.2 - 1)
    assert m.max_dd == pytest.approx(0.5)


def test_k_of_one_is_the_probabilistic_sharpe_and_more_trials_only_lower_it():
    m = measure_portfolio(sim(noisy(0.0015)), 10_000.0)
    psr = deflated_sharpe(m, 1)
    expected = 0.5 * (1 + math.erf(m.sharpe_daily * math.sqrt(m.days - 1)
                                   / math.sqrt(1 - m.skew * m.sharpe_daily + (m.kurtosis - 1) / 4 * m.sharpe_daily ** 2)
                                   / math.sqrt(2)))
    assert psr == pytest.approx(expected)
    ladder = [deflated_sharpe(m, k) for k in (1, 2, 10, 100)]
    assert ladder == sorted(ladder, reverse=True) and ladder[-1] < ladder[0]


def test_noise_does_not_pass():
    m = measure_portfolio(sim(noisy(0.0)), 10_000.0)
    assert not validation_gate(m, k=1).passed


def test_a_good_curve_alone_passes_and_fails_as_the_best_of_a_long_search():
    m = measure_portfolio(sim(noisy(0.0012, sd=0.008)), 10_000.0)
    assert validation_gate(m, k=1).passed, validation_gate(m, k=1).report()
    rng = np.random.default_rng(0)
    search = list(rng.normal(0, 0.06, 200))          # 200 variants tried, daily Sharpes all over the place
    g = validation_gate(m, k=200, trial_sharpes_daily=search)
    assert not g.passed and any("deflated" in c.name for c in g.failures)


def test_an_edge_the_fees_eat_is_refused():
    m = measure_portfolio(sim(noisy(0.0012, sd=0.008), gross=1000.0, fees=700.0), 10_000.0)
    g = validation_gate(m, k=1)
    assert [c.name for c in g.failures] == ["fees / gross edge"]


def test_no_gross_edge_means_infinite_cost_share():
    m = measure_portfolio(sim(noisy(0.0012, sd=0.008), gross=-50.0, fees=10.0), 10_000.0)
    assert m.cost_share == math.inf and m.as_dict()["cost_share"] is None


def test_holdout_is_judged_against_the_spec_s_own_validation():
    val = measure_portfolio(sim(noisy(0.0012, sd=0.008)), 10_000.0)
    good = measure_portfolio(sim(noisy(0.0010, sd=0.008, n=300, seed=9)), 10_000.0)
    decay = measure_portfolio(sim(noisy(0.0001, sd=0.008, n=300, seed=9)), 10_000.0)
    assert holdout_gate(good, val).passed, holdout_gate(good, val).report()
    assert [c.name for c in holdout_gate(decay, val).failures] == ["Sharpe vs validation"]
