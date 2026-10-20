from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pytest

from alphaquant.validation import (
    LUCIDFLEX_50K, GateConfig, LiveConfig, TradeLog, bootstrap_mean, gate2, gate5, gate6, gate7, max_drawdown,
    measure, monte_carlo, simulate, split_sample,
)
from alphaquant.validation.prop import FAIL, OPEN, PASS, attempt

REPORTS = Path(__file__).parents[3] / "mc" / "strategies" / "DriftPullback" / "reports"


def prop_profile(n: int = 400, start: datetime = datetime(2021, 1, 4), step_days: int = 4) -> TradeLog:
    """Win rate 60%, R:R 0.83 on 1 NQ: +250 / -300, average trade +$30, spread over the years."""
    return TradeLog.from_rows([
        {"entry_time": start + timedelta(days=step_days * i), "pnl": 250.0 if i % 5 < 3 else -300.0}
        for i in range(n)
    ])


def test_measure_matches_hand_computation():
    m = measure(TradeLog.from_pnl([100, -50, 100, -50]))
    assert (m.n, m.net, m.avg) == (4, 100.0, 25.0)
    assert m.win_rate == 50.0
    assert m.rr == 2.0 and m.pf == 2.0
    assert m.max_dd == 50.0


def test_max_drawdown_starts_flat():
    assert max_drawdown(np.array([-100.0, 50.0])) == 100.0


def test_to_micro_adds_back_report_costs_and_charges_micro_costs():
    log = TradeLog.from_rows([{"entry_time": datetime(2025, 1, 2, 9), "pnl": 985.0, "mae": -400.0}])
    micro = log.to_micro(ratio=10, cost_in_report=15, cost_micro=1.5)
    row = micro.frame.row(0, named=True)
    assert row["pnl"] == pytest.approx(98.5)     # (985 + 15) / 10 - 1.5
    assert row["mae"] == pytest.approx(-40.0)


def test_days_keep_intraday_order():
    log = TradeLog.from_rows([
        {"entry_time": datetime(2025, 1, 2, 9), "pnl": 1.0},
        {"entry_time": datetime(2025, 1, 2, 11), "pnl": -2.0},
        {"entry_time": datetime(2025, 1, 3, 9), "pnl": 3.0},
    ])
    assert log.days() == [(date(2025, 1, 2), [(1.0, 0.0), (-2.0, -2.0)]), (date(2025, 1, 3), [(3.0, 0.0)])]


def test_attempt_breaches_inside_the_trade():
    a = attempt([[(500.0, -2100.0)]], 1, LUCIDFLEX_50K, 60)
    assert (a.outcome, a.days) == (FAIL, 1)


def test_attempt_trailing_moves_at_end_of_day_and_locks():
    # +1,500 on day 1 lifts the floor from 48,000 to 49,500: -2,100 on day 2 breaches it
    assert attempt([[(1500.0, 0.0)], [(-2100.0, -2100.0)]], 1, LUCIDFLEX_50K, 60).outcome == FAIL
    # the same -2,100 inside day 1 is above 48,000: the floor has not moved yet
    assert attempt([[(1500.0, 0.0), (-2100.0, -2100.0)]], 1, LUCIDFLEX_50K, 1).outcome == OPEN
    # above 52,100 the floor locks at 50,100: -1,800 from 52,200 survives, then the target
    days = [[(2200.0, 0.0)], [(-1800.0, -1800.0)], [(2600.0, 0.0)]]
    assert attempt(days, 1, LUCIDFLEX_50K, 60).outcome == PASS
    assert attempt([[(10.0, 0.0)]] * 5, 1, LUCIDFLEX_50K, 5).outcome == OPEN


def test_monte_carlo_is_reproducible_and_reshuffle_keeps_the_trades():
    pnl = prop_profile().pnl
    a, b = monte_carlo(pnl, 200, seed=7), monte_carlo(pnl, 200, seed=7)
    assert np.array_equal(a.dd_reshuffle, b.dd_reshuffle)
    # no permutation can fall deeper than all the losers in a row
    assert a.dd_reshuffle.max() <= -pnl[pnl < 0].sum()
    assert monte_carlo(np.full(50, 10.0), 20).median_net == 500.0


def test_bootstrap_interval_contains_the_mean():
    b = bootstrap_mean(prop_profile().pnl, 2000, seed=1)
    assert b.lo < b.mean < b.hi
    assert b.p_le_zero < 0.05


def test_gate2_judges_the_prop_profile_on_prop_criteria_only():
    # avg trade $30 fails the live $70: frozen, so the prop verdict ignores it
    g = gate2(prop_profile())
    assert g.passed and g.complete
    assert "avg trade (net)" in [c.name for c in g.live if c.passed is False]
    assert "frozen" in g.report().lower()


def test_live_criteria_count_only_when_unfrozen():
    g = gate2(prop_profile(), live=LiveConfig(frozen=False))
    assert not g.passed
    assert [c.name for c in g.failures] == ["avg trade (net)"]


def test_gate2_fails_on_few_trades_and_a_coin_flip():
    g = gate2(TradeLog.from_pnl([250.0, 250.0, -300.0] * 10, datetime(2025, 1, 2)))
    assert "trades IS" in [c.name for c in g.failures]
    flip = TradeLog.from_pnl(list(np.random.default_rng(0).choice([300.0, -300.0], 400)))
    assert "t (avg / error bar)" in [c.name for c in gate2(flip).failures]


def test_gate2_checks_the_declared_period():
    log = prop_profile()                                        # 2021-01-04 -> 2025-05-...
    assert gate2(log, period=(date(2021, 1, 1), date(2025, 5, 31))).passed
    assert not gate2(log, period=(date(2020, 1, 1), date(2025, 5, 31))).passed


def test_split_sample_needs_both_halves():
    base = prop_profile()
    assert split_sample(base, TradeLog(base.frame.with_columns(pnl=base.frame["pnl"] + 5))).passed
    worse_late = base.frame["pnl"].to_numpy().copy()
    worse_late[200:] -= 5
    assert not split_sample(base, TradeLog.from_pnl(list(worse_late), datetime(2021, 1, 4))).passed


def test_gate5_and_gate6_send_a_dead_oos_to_the_cemetery():
    is_log = prop_profile()
    dead = TradeLog.from_pnl([250.0 if i % 2 else -300.0 for i in range(200)], datetime(2025, 1, 2))
    assert gate5(is_log, prop_profile(200, datetime(2025, 1, 2))).passed
    assert not gate5(is_log, dead).passed
    g6 = gate6(is_log, dead, risk_per_contract=300.0, cfg=GateConfig(boot_sims=1000))
    assert not g6.passed
    assert set(g6.data["dd_yardstick"]) == {10, 20, 40}


def test_gate7_runs_and_flags_funded_as_not_modeled():
    rows = [{"entry_time": datetime(2025, 1, 2 + i // 3 % 28, 9 + i % 3), "pnl": p}
            for i, p in enumerate([985.0, 985.0, -1185.0] * 60)]
    g = gate7(TradeLog.from_rows(rows), GateConfig(prop_sims=500, prop_sizes=(1, 2)))
    assert not g.complete
    assert g.data["prop"].best in (1, 2)


# ── against the original scripts, on a real MultiCharts report ──────────────

@pytest.mark.skipif(not (REPORTS / "DPB_S2_IS_mode0.xlsx").exists(), reason="DriftPullback reports not present")
def test_real_report_matches_check_report():
    m = measure(TradeLog.from_mc_xlsx(REPORTS / "DPB_S2_IS_mode0.xlsx"))
    assert m.n == 3499
    assert m.net == pytest.approx(194_110, abs=1)
    assert m.max_dd == pytest.approx(31_670, abs=1)
    assert round(m.win_rate, 1) == 63.5 and round(m.t, 2) == 3.01


@pytest.mark.skipif(not (REPORTS / "DPB_S5_OOS_2025-2026.xlsx").exists(), reason="DriftPullback reports not present")
def test_real_report_matches_prop_sim_contiguous():
    log = TradeLog.from_mc_xlsx(REPORTS / "DPB_S5_OOS_2025-2026.xlsx").to_micro()
    rep = simulate(log, sizes=(1, 2), sims=200)
    assert round(100 * rep.by_size[1][1].pass_rate, 1) == 39.1   # prop_sim.py, contiguous
    assert round(100 * rep.by_size[2][1].pass_rate, 1) == 59.1
    assert round(rep.state.dd_now) == 3341 and round(rep.state.percentile) == 98
