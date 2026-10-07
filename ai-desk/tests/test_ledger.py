"""The ledger is what makes the live path safe: it decides which positions the desk
owns. These tests cover the two failure modes that cost money — forgetting a
position we opened, and adopting one we did not."""
from datetime import datetime, timedelta, timezone

import pytest

from desk.execution.ledger import PositionLedger
from desk.schemas import AccountState, Fill, OrderIntent, Position, TargetPosition
from desk.signals.rebalance import intents_from_targets


@pytest.fixture
def ledger(tmp_path):
    return PositionLedger(tmp_path / "ledger.json")


def intent(asset="BTC", side="buy", usd=500.0, strategy="reversal_v1", horizon=120, reduce_only=False):
    return OrderIntent(asset=asset, side=side, notional_usd=usd, reduce_only=reduce_only,
                       strategy_id=strategy, horizon_hours=horizon, reason="t")


def fill(i: OrderIntent, stop_oid=None):
    return Fill(intent_id=i.id, asset=i.asset, side=i.side, requested_usd=i.notional_usd,
                filled_usd=i.notional_usd, decision_px=100.0, fill_px=100.0, fee_usd=0.2,
                partial=False, exchange_oid="999", stop_oid=stop_oid)


def position(asset="BTC", size=5.0):
    return Position(asset=asset, notional_usd=size * 100, size=size, entry_px=100.0,
                    mark_px=100.0, unrealized_pnl_usd=0.0)


def test_exchange_position_gains_its_context(ledger):
    i = intent()
    ledger.record(fill(i, stop_oid="42"), i, cloid="0xabc")
    p = ledger.enrich([position()])[0]
    assert p.managed and p.strategy_id == "reversal_v1" and p.horizon_hours == 120
    assert p.opened_at is not None and ledger.stop_oid("BTC") == "42"


def test_unknown_position_is_not_adopted(ledger):
    """Opened by hand, or by a desk whose ledger was lost. Either way: not ours."""
    p = ledger.enrich([position("ETH")])[0]
    assert p.managed is False and p.strategy_id is None and p.opened_at is None


def test_adding_to_a_position_does_not_restart_its_clock(ledger):
    i = intent()
    ledger.record(fill(i), i, cloid="0xaaa")
    first = ledger.rows["BTC"]["opened_at"]
    ledger.record(fill(intent(usd=100.0)), intent(usd=100.0), cloid="0xbbb")
    assert ledger.rows["BTC"]["opened_at"] == first, "a top-up must not reset the time stop"
    assert ledger.rows["BTC"]["cloids"] == ["0xaaa", "0xbbb"]


def test_reconcile_drops_what_the_exchange_closed(ledger):
    for a in ("BTC", "ETH"):
        i = intent(asset=a)
        ledger.record(fill(i), i)
    assert ledger.reconcile({"BTC"}) == ["ETH"]
    assert ledger.enrich([position("ETH")])[0].managed is False


def test_a_reopened_asset_starts_a_new_clock(ledger):
    i = intent()
    ledger.record(fill(i), i)
    old = ledger.rows["BTC"]["opened_at"]
    ledger.forget("BTC")
    ledger.record(fill(i), i)
    assert ledger.rows["BTC"]["opened_at"] >= old
    assert ledger.enrich([position()])[0].managed


def test_survives_a_restart(tmp_path):
    path = tmp_path / "l.json"
    i = intent()
    PositionLedger(path).record(fill(i), i, cloid="0xabc")
    assert PositionLedger(path).enrich([position()])[0].strategy_id == "reversal_v1"


# ---- what the rest of the desk does with it ---------------------------------

def _account(positions):
    return AccountState(equity_usd=10_000, margin_used_usd=0, positions=positions)


def test_rebalance_leaves_unmanaged_positions_alone():
    """The desk must not close a position just because it is not in its target list."""
    mine = position("BTC").model_copy(update={"managed": True, "strategy_id": "reversal_v1"})
    yours = position("ETH").model_copy(update={"managed": False})
    out = intents_from_targets([TargetPosition(asset="SOL", notional_usd=300, strategy_id="reversal_v1",
                                               horizon_hours=24, reason="new")],
                               _account([mine, yours]), "reversal_v1", marks={"SOL": 10.0})
    assets = {i.asset for i in out}
    assert "ETH" not in assets, "closed a position the desk did not open"
    assert "BTC" in assets and "SOL" in assets


def test_time_stop_ignores_unmanaged_positions(limits):
    from desk.loop import time_stop_intents

    now = datetime.now(timezone.utc)
    old_mine = position("BTC").model_copy(update={
        "managed": True, "strategy_id": "reversal_v1", "horizon_hours": 24,
        "opened_at": now - timedelta(hours=40)})
    old_yours = position("ETH").model_copy(update={
        "managed": False, "horizon_hours": 24, "opened_at": now - timedelta(hours=40)})
    out = time_stop_intents(_account([old_mine, old_yours]), limits, now=now)
    assert [i.asset for i in out] == ["BTC"]


def test_spot_is_not_margin_unless_declared():
    """A Unified account lets spot USDC back perp margin and the app shows the sum.
    The API never says which mode the account is in, so the desk is told — guessing
    would mean sizing every limit off a number that might not be collateral."""
    from unittest.mock import patch

    from desk.data.hl_market import HLMarket

    empty_perps = {"marginSummary": {"accountValue": "0.0", "totalMarginUsed": "0.0"}, "assetPositions": []}
    m = HLMarket("https://api.hyperliquid-testnet.xyz")
    with patch.object(m.info, "user_state", return_value=empty_perps), \
         patch.object(m, "spot_usdc", return_value=999.0):
        classic = m.account_state("0xabc", unified_collateral=False)
        unified = m.account_state("0xabc", unified_collateral=True)

    assert classic.equity_usd == 0.0 and classic.spot_usdc == 999.0, "spot must not be sized against"
    assert unified.equity_usd == 999.0


def test_a_resting_order_that_filled_is_ours_before_it_is_booked(ledger):
    """execute() returns None for an order that rests; the fill can land before the
    next reconcile(). In that window the position has no row yet — but calling it
    unmanaged would make the desk disown its own trade and warn about it."""
    i = intent(asset="SUI")
    ledger.record_sent(i, cloid="0xaaa", oid="1")
    p = ledger.enrich([position("SUI")])[0]
    assert p.managed and p.strategy_id == "reversal_v1"
    assert "SUI" not in ledger.rows, "still not booked, just recognised"


def test_truly_foreign_positions_stay_unmanaged(ledger):
    ledger.record_sent(intent(asset="SUI"), cloid="0xaaa", oid="1")
    p = ledger.enrich([position("DOGE")])[0]
    assert p.managed is False


def test_two_ledgers_on_one_file_do_not_erase_each_other(tmp_path):
    """The dashboard, a cycle and a script can each hold a ledger. A whole-file
    write from one erased what another had just recorded — eight positions lost
    their context that way in a single evening."""
    path = tmp_path / "l.json"
    ui, script = PositionLedger(path), PositionLedger(path)

    ui.record_sent(intent(asset="SUI"), cloid="0xui", oid="1")
    script.record_sent(intent(asset="BTC"), cloid="0xscript", oid="2")

    fresh = PositionLedger(path)
    assert set(fresh.pending) == {"0xui", "0xscript"}, "a writer dropped the other's order"


def test_the_file_is_never_left_half_written(tmp_path):
    import json

    path = tmp_path / "l.json"
    led = PositionLedger(path)
    for n in range(20):
        led.record_sent(intent(asset=f"A{n}"), cloid=f"0x{n:02d}", oid=str(n))
        json.loads(path.read_text())            # readable after every single write
    assert len(PositionLedger(path).pending) == 20
