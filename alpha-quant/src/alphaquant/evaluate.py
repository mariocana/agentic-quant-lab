"""One call from a frozen spec to a recorded verdict.

    evaluate(spec, strategy, "validation")   replay the desk on the validation
                                             dates, measure, gate, record
    evaluate(spec, strategy, "holdout")      the same on the holdout, once ever:
                                             the registry opens it first

Every evaluation is written to the registry, the failures as much as the
passes: a run that is not recorded is a trial that k does not count. Train runs
are recorded too but do not count toward k, because nothing has been selected on
them yet.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from alphaquant.engine.desk_replay import HistoricalMarket, replay, splits
from alphaquant.engine.desk_trades import to_simresult
from alphaquant.registry import Registry
from alphaquant.validation.checks import GateResult
from alphaquant.validation.portfolio import (
    PERIODS_PER_YEAR, PortfolioMetrics, holdout_gate, measure_portfolio, validation_gate,
)


@dataclass
class Evaluation:
    spec_hash: str
    segment: str
    metrics: PortfolioMetrics
    gate: GateResult | None
    period: tuple[datetime, datetime]


def evaluate(spec: dict, strategy, segment: str, limits: dict, market: HistoricalMarket | None = None,
             registry: Registry | None = None, period: tuple[datetime, datetime] | None = None,
             equity: float = 10_000.0, validation_metrics: PortfolioMetrics | None = None) -> Evaluation:
    registry = registry or Registry()
    market = market or HistoricalMarket.from_quantlake()
    h = registry.register_spec(spec)
    start, end = period or splits()[segment]
    if segment == "holdout":
        market.unlock_holdout(registry, h)            # written before a single bar is served

    res = replay(strategy, market, limits, start, end, equity=equity)
    sim = to_simresult(res, {"strategy": spec.get("id"), "spec_hash": h, "segment": segment})
    m = measure_portfolio(sim, res.start_equity)

    gate = None
    if segment == "validation":
        k = registry.trials() + 1                     # this run counts too
        prior = [s / PERIODS_PER_YEAR ** 0.5 for s in registry.validation_sharpes()]
        gate = validation_gate(m, k, prior + [m.sharpe_daily])
    elif segment == "holdout":
        if validation_metrics is None:
            raise ValueError("a holdout is judged against the spec's own validation: pass validation_metrics")
        gate = holdout_gate(m, validation_metrics)

    registry.record_run(h, segment, {**m.as_dict(), "passed": None if gate is None else gate.passed},
                        res.versions, (start.date().isoformat(), end.date().isoformat()))
    return Evaluation(spec_hash=h, segment=segment, metrics=m, gate=gate, period=(start, end))
