import pytest

from hlbridge.config import load_limits
from hlbridge.risk.state import RiskState
from hlbridge.schemas import AccountState, AssetContext, Position


@pytest.fixture
def limits():
    return load_limits()


@pytest.fixture
def ctx():
    def make(asset="BTC", funding=0.0, volume=1e9):
        return AssetContext(asset=asset, mark_px=100.0, mid_px=100.0, funding_hourly=funding,
                            open_interest=1e6, day_volume_usd=volume, sz_decimals=3, max_leverage=40)
    return make


@pytest.fixture
def account():
    def make(equity=10_000.0, positions=()):
        ps = [Position(asset=a, notional_usd=n, size=n / 100.0, entry_px=100.0, mark_px=100.0, unrealized_pnl_usd=0.0)
              for a, n in positions]
        return AccountState(equity_usd=equity, margin_used_usd=0.0, positions=ps)
    return make


@pytest.fixture
def state(tmp_path, monkeypatch):
    # isolate kill switch and state file from the real var/ directory
    monkeypatch.setattr("hlbridge.risk.state.KILL_FILE", tmp_path / "KILL")
    st = RiskState()
    st.day, st.day_start_equity, st.peak_equity = "2026-01-01", 10_000.0, 10_000.0
    return st
