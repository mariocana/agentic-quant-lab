from datetime import datetime, timezone

from desk.risk.state import RiskState


def test_day_roll_and_peak(limits):
    st = RiskState()
    st.observe(10_000, limits, now=datetime(2026, 1, 1, tzinfo=timezone.utc))
    st.observe(10_500, limits, now=datetime(2026, 1, 1, 12, tzinfo=timezone.utc))
    assert st.peak_equity == 10_500 and st.day_start_equity == 10_000
    st.observe(10_400, limits, now=datetime(2026, 1, 2, tzinfo=timezone.utc))
    assert st.day_start_equity == 10_400 and st.history[-1] == {"day": "2026-01-01", "start": 10_000, "end": 10_400}


def test_daily_flatten_halts_and_requests_flatten(limits):
    st = RiskState()
    st.observe(10_000, limits)
    fired = st.observe(9_400, limits)          # -6%
    assert fired == ["daily_loss_flatten"] and st.halted and st.flatten_requested


def test_drawdown_halts(limits):
    st = RiskState()
    st.observe(10_000, limits, now=datetime(2026, 1, 1, tzinfo=timezone.utc))
    st.observe(9_800, limits, now=datetime(2026, 1, 2, tzinfo=timezone.utc))
    st.observe(9_600, limits, now=datetime(2026, 1, 3, tzinfo=timezone.utc))
    fired = st.observe(8_400, limits, now=datetime(2026, 1, 4, tzinfo=timezone.utc))   # -16% from peak, -12.5% day
    assert fired == ["max_drawdown"] and st.halted and not st.flatten_requested
    st.unlock()
    assert not st.halted


def test_roundtrip(tmp_path, limits):
    st = RiskState()
    st.observe(10_000, limits)
    st.save(tmp_path / "s.json")
    assert RiskState.load(tmp_path / "s.json") == st
