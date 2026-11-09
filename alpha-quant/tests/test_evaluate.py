"""From a frozen spec to a recorded verdict, on synthetic history."""
from datetime import timedelta

import pytest

from alphaquant.evaluate import evaluate
from alphaquant.engine.desk_replay import HistoricalMarket
from alphaquant.registry import HoldoutLocked, Registry
from desk.config import load_limits
from desk.signals.reversal import Reversal

from test_desk_replay import SYMS, D0, _daily, _funding, _listings

SPEC = {"id": "t", "strategy": "desk.signals.reversal.Reversal", "params": {"universe_size": 15}}
VAL = (D0 + timedelta(days=25), D0 + timedelta(days=60))
HOLD = (D0 + timedelta(days=70), D0 + timedelta(days=95))


def _market():
    daily = _daily(SYMS, 100)
    return HistoricalMarket(daily, _funding(SYMS, 100), _listings(daily), holdout_start=HOLD[0])


def strat():
    return Reversal(universe_size=15, min_day_volume_usd=1e6)


def test_every_evaluation_is_recorded_and_the_holdout_is_one_shot(tmp_path):
    reg = Registry(tmp_path / "t.jsonl")
    v = evaluate(SPEC, strat(), "validation", load_limits(), _market(), reg, period=VAL)
    assert v.gate is not None and reg.trials() == 1
    assert [c.name for c in v.gate.checks][3].startswith("deflated Sharpe (k=1)")

    with pytest.raises(HoldoutLocked):                         # the market alone will not serve it
        evaluate(SPEC, strat(), "validation", load_limits(), _market(), reg, period=HOLD)

    h = evaluate(SPEC, strat(), "holdout", load_limits(), _market(), reg, period=HOLD,
                 validation_metrics=v.metrics)
    assert h.gate is not None
    with pytest.raises(HoldoutLocked):                         # never twice
        evaluate(SPEC, strat(), "holdout", load_limits(), _market(), reg, period=HOLD,
                 validation_metrics=v.metrics)
    kinds = [e["kind"] for e in reg.entries()]
    assert kinds == ["spec", "run", "holdout", "run"]
    reg.verify()


def test_a_second_variant_raises_k(tmp_path):
    reg = Registry(tmp_path / "t.jsonl")
    evaluate(SPEC, strat(), "validation", load_limits(), _market(), reg, period=VAL)
    v2 = evaluate({**SPEC, "params": {"universe_size": 12}}, Reversal(universe_size=12, min_day_volume_usd=1e6),
                  "validation", load_limits(), _market(), reg, period=VAL)
    assert "k=2" in v2.gate.checks[3].name and reg.trials() == 2
