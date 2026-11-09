"""Comparing live decisions with replayed ones."""
from datetime import datetime, timedelta, timezone

import pytest

from alphaquant.calibration.decision_replay import Decision, compare, decisions_from_journal, replay_decision
from alphaquant.engine.desk_replay import HistoricalMarket
from desk.signals.reversal import Reversal

from test_desk_replay import SYMS, D0, _daily, _funding, _listings


def _market():
    daily = _daily(SYMS, 60)
    return HistoricalMarket(daily, _funding(SYMS, 60), _listings(daily))


STRAT = Reversal(universe_size=15, min_day_volume_usd=1e6)


def test_same_data_same_decision():
    m = _market()
    t = D0 + timedelta(days=40, minutes=5)
    live, _, _ = replay_decision(STRAT, m, Decision(ts=t, equity=10_000, targets={}))
    assert live, "the strategy must take positions for the test to mean anything"
    row = compare(STRAT, m, [Decision(ts=t, equity=10_000, targets=live)])[0]
    assert row["jaccard"] == 1.0 and row["max_size_gap"] == pytest.approx(0.0) and not row["causes"]


def test_a_live_asset_with_no_data_is_named_as_such():
    m = _market()
    t = D0 + timedelta(days=40, minutes=5)
    live, _, _ = replay_decision(STRAT, m, Decision(ts=t, equity=10_000, targets={}))
    live = {**live, "GHOST": 100.0}
    row = compare(STRAT, m, [Decision(ts=t, equity=10_000, targets=live)])[0]
    assert row["causes"] == {"GHOST": "no_bars"} and row["jaccard"] < 1.0


def test_each_target_set_takes_the_equity_of_its_own_cycle():
    rows = [
        {"ts": "2026-10-15T00:05:36+00:00", "kind": "targets", "strategy": "reversal_v1",
         "targets": [{"asset": "LIT", "notional_usd": 80.5}, {"asset": "W", "notional_usd": -40.0}]},
        {"ts": "2026-10-15T00:05:46+00:00", "kind": "cycle", "equity": 1148.08},
        {"ts": "2026-10-16T00:05:36+00:00", "kind": "targets", "strategy": "other", "targets": []},
    ]
    ds = decisions_from_journal(rows)
    assert len(ds) == 1 and ds[0].equity == 1148.08 and ds[0].targets == {"LIT": 80.5, "W": -40.0}
