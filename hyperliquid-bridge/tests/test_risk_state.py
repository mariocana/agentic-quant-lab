from datetime import datetime, timezone

from hlbridge.risk.state import RiskState


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


def test_paper_and_live_do_not_share_a_peak(tmp_path, monkeypatch):
    """Switching mode must not read as a crash. A paper account at 10,000 and a
    testnet account at 999 share nothing but a desk; with one state file the
    switch produced a -90% drawdown and halted trading."""
    import hlbridge.risk.state as mod

    monkeypatch.setattr(mod, "VAR", tmp_path)
    monkeypatch.setattr(mod, "STATE_PATH", tmp_path / "risk_state.json")

    paper = mod.state_path("paper")
    live = mod.state_path("live", "0x566d819b945421b09b33f91ae9a3b2cbd7195094")
    assert paper != live

    st = RiskState.load(paper)
    st.observe(10_000, limits_for_test())
    st.save()

    fresh = RiskState.load(live)
    fired = fresh.observe(999, limits_for_test())
    assert fired == [], f"a fresh live account must not inherit the paper peak: {fired}"
    assert fresh.peak_equity == 999
    assert RiskState.load(paper).peak_equity == 10_000, "and the paper history must survive"


def test_two_live_accounts_keep_separate_state():
    import hlbridge.risk.state as mod
    a = mod.state_path("live", "0xaaaaaaaabbbbbbbbccccccccdddddddd11111111")
    b = mod.state_path("live", "0xeeeeeeeeffffffff0000000011111111222222222")
    assert a != b


def limits_for_test():
    return {"daily_loss_flatten_pct": 0.05, "max_drawdown_pct": 0.15}
