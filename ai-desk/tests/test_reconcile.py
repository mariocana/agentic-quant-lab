"""Fills come back from the exchange hours after the order was sent. These tests use
the real shape of a Hyperliquid userFills row."""
from datetime import datetime, timezone

import pytest

from desk.execution.ledger import PositionLedger
from desk.execution.reconcile import reconcile_fills
from desk.schemas import OrderIntent


@pytest.fixture
def ledger(tmp_path):
    return PositionLedger(tmp_path / "l.json")


def intent(asset="SUI", side="buy", usd=400.0, reduce_only=False):
    return OrderIntent(asset=asset, side=side, notional_usd=usd, reduce_only=reduce_only,
                       strategy_id="reversal_v1", horizon_hours=120, reason="t")


def raw_fill(coin="SUI", side="B", px="0.6821", sz="586.0", oid=12345, t=1_791_244_800_027,
             fee="0.1795", cloid=None):
    """A userFills row as the API actually returns it."""
    row = {"coin": coin, "px": px, "sz": sz, "side": side, "time": t, "startPosition": "0.0",
           "dir": "Open Long", "closedPnl": "0.0", "hash": "0xabc", "oid": oid,
           "crossed": False, "fee": fee, "tid": 99, "feeToken": "USDC", "twapId": None}
    if cloid:
        row["cloid"] = cloid
    return row


def test_a_resting_order_that_fills_later_becomes_a_position(ledger):
    """The whole point: execute() returned None, the cycle ended, and the fill
    landed an hour later. It must still be attributable."""
    i = intent()
    ledger.record_sent(i, cloid="0xaaa", oid="12345")
    ours, high_water, foreign = reconcile_fills([raw_fill()], ledger, since_ms=0)

    assert len(ours) == 1 and not foreign
    assert high_water == 1_791_244_800_027
    row = ledger.rows["SUI"]
    assert row["strategy_id"] == "reversal_v1" and row["horizon_hours"] == 120
    assert ledger.pending == {}, "a filled order must leave the in-flight table"


def test_the_fee_is_the_exchange_s_not_our_estimate(ledger):
    i = intent()
    ledger.record_sent(i, cloid="0xaaa", oid="12345")
    ours, _, _ = reconcile_fills([raw_fill(fee="0.1795")], ledger, since_ms=0)
    assert ours[0].fee_usd == 0.1795
    estimate = ours[0].filled_usd * 0.00045
    assert abs(ours[0].fee_usd - estimate) > 1e-6, "the test fixture should differ from the estimate"


def test_matching_by_cloid_when_the_exchange_echoes_it(ledger):
    ledger.record_sent(intent(), cloid="0xbbb", oid=None)
    ours, _, foreign = reconcile_fills([raw_fill(oid=999, cloid="0xbbb")], ledger, since_ms=0)
    assert len(ours) == 1 and not foreign


def test_a_fill_we_did_not_send_is_reported_not_adopted(ledger):
    """A manual trade, or a stop that triggered. Either way the desk must not
    silently take ownership of it."""
    ours, _, foreign = reconcile_fills([raw_fill(coin="DOGE", oid=777)], ledger, since_ms=0)
    assert not ours and len(foreign) == 1
    assert "DOGE" not in ledger.rows


def test_replaying_the_same_window_changes_nothing(ledger):
    ledger.record_sent(intent(), cloid="0xaaa", oid="12345")
    fills = [raw_fill()]
    ours, high_water, _ = reconcile_fills(fills, ledger, since_ms=0)
    opened_at = ledger.rows["SUI"]["opened_at"]
    again, _, foreign = reconcile_fills(fills, ledger, since_ms=high_water)
    assert len(ours) == 1 and not again and not foreign
    assert ledger.rows["SUI"]["opened_at"] == opened_at


def test_fills_are_folded_in_time_order(ledger):
    """Out-of-order input must not make an older fill set the high-water mark."""
    for n, (cloid, oid) in enumerate([("0xa", "1"), ("0xb", "2")]):
        ledger.record_sent(intent(asset="SUI"), cloid=cloid, oid=oid)
    late = raw_fill(oid=2, t=2_000)
    early = raw_fill(oid=1, t=1_000)
    ours, high_water, _ = reconcile_fills([late, early], ledger, since_ms=0)
    assert [f.created_at for f in ours] == sorted(f.created_at for f in ours)
    assert high_water == 2_000


def test_an_order_that_never_fills_is_eventually_dropped(ledger):
    ledger.record_sent(intent(), cloid="0xold", oid="1")
    ledger.pending["0xold"]["sent_at"] = datetime(2020, 1, 1, tzinfo=timezone.utc).isoformat()
    assert ledger.stale_pending() == ["0xold"]
    assert ledger.stale_pending(older_than_hours=10 ** 6) == []
