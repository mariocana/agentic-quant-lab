import pytest

from desk.execution.paper import PaperAdapter
from desk.schemas import OrderIntent, RiskVerdict


def go(adapter, asset, side, usd, px, reduce_only=False):
    i = OrderIntent(asset=asset, side=side, notional_usd=usd, reduce_only=reduce_only,
                    strategy_id="t", horizon_hours=24, reason="t")
    v = RiskVerdict(intent_id=i.id, decision="approve", approved_notional_usd=usd)
    adapter.set_marks({asset: px})
    return i, adapter.execute(i, v, px)


def test_open_mark_close_realises_pnl(tmp_path):
    a = PaperAdapter(starting_equity=1_000.0, fee_bps=0.0, slippage_bps=0.0, path=tmp_path / "p.json")
    go(a, "BTC", "buy", 100.0, 100.0)
    a.set_marks({"BTC": 110.0})
    st = a.account_state()
    assert abs(st.equity_usd - 1_010.0) < 1e-9 and st.positions[0].notional_usd == 110.0
    go(a, "BTC", "sell", 110.0, 110.0, reduce_only=True)
    st = a.account_state()
    assert st.positions == [] and abs(st.equity_usd - 1_010.0) < 1e-9


def test_fees_and_slippage_are_charged(tmp_path):
    a = PaperAdapter(starting_equity=1_000.0, fee_bps=10.0, slippage_bps=10.0, path=tmp_path / "p.json")
    _, f = go(a, "BTC", "buy", 100.0, 100.0)
    assert f.fill_px == 100.1 and f.fee_usd == 0.1 and abs(f.slippage_bps - 10.0) < 1e-9
    assert a.account_state().equity_usd < 1_000.0


def test_idempotent_on_intent_id(tmp_path):
    a = PaperAdapter(starting_equity=1_000.0, path=tmp_path / "p.json")
    i, f1 = go(a, "BTC", "buy", 100.0, 100.0)
    v = RiskVerdict(intent_id=i.id, decision="approve", approved_notional_usd=100.0)
    assert f1 is not None and a.execute(i, v, 100.0) is None
    assert abs(a.account_state().positions[0].notional_usd - 100.0) < 0.5


def test_flip_sets_new_entry(tmp_path):
    a = PaperAdapter(starting_equity=1_000.0, fee_bps=0.0, slippage_bps=0.0, path=tmp_path / "p.json")
    go(a, "BTC", "buy", 100.0, 100.0)
    go(a, "BTC", "sell", 300.0, 120.0)                    # sells 2.5 BTC: closes the 1 BTC long, opens 1.5 short
    p = a.account_state().positions[0]
    assert abs(p.notional_usd + 180.0) < 1e-9 and p.entry_px == 120.0
    assert abs(a.state["cash"] - 1_020.0) < 1e-9          # +20 realised on the long leg


def test_flatten_all(tmp_path):
    a = PaperAdapter(starting_equity=1_000.0, fee_bps=0.0, slippage_bps=0.0, path=tmp_path / "p.json")
    go(a, "BTC", "buy", 100.0, 100.0)
    go(a, "ETH", "sell", 100.0, 10.0)
    fills = a.flatten_all()
    assert len(fills) == 2 and a.account_state().positions == []


def test_reduce_only_closes_exactly_and_never_flips(tmp_path):
    """With slippage, notional/price does not reproduce the open size: a close must
    still land on zero, not on a dust position of the opposite sign."""
    a = PaperAdapter(starting_equity=1_000.0, fee_bps=4.5, slippage_bps=25.0, path=tmp_path / "p.json")
    go(a, "BTC", "buy", 100.0, 100.0)
    size = a.account_state().positions[0].size
    go(a, "BTC", "sell", abs(size) * 100.0, 100.0, reduce_only=True)
    assert a.account_state().positions == []


def test_reduce_only_without_a_position_does_nothing(tmp_path):
    a = PaperAdapter(starting_equity=1_000.0, path=tmp_path / "p.json")
    _, f = go(a, "BTC", "sell", 100.0, 100.0, reduce_only=True)
    assert f is None and a.account_state().positions == []


def test_flatten_all_with_costs_leaves_nothing(tmp_path):
    a = PaperAdapter(starting_equity=1_000.0, fee_bps=4.5, slippage_bps=20.0, path=tmp_path / "p.json")
    go(a, "BTC", "buy", 100.0, 100.0)
    go(a, "ETH", "sell", 100.0, 10.0)
    a.flatten_all()
    assert a.account_state().positions == []


def test_costs_follow_how_the_order_meets_the_book(tmp_path):
    """Measured on the desk's real fills: a post-only order pays the maker fee and
    no slippage, an IOC pays the taker fee and crosses the spread."""
    a = PaperAdapter(starting_equity=10_000.0, path=tmp_path / "p.json")
    def go(order_type, asset):
        i = OrderIntent(asset=asset, side="buy", notional_usd=1_000.0, order_type=order_type,
                        strategy_id="t", horizon_hours=1, reason="t")
        return a.execute(i, RiskVerdict(intent_id=i.id, decision="approve", approved_notional_usd=1_000.0), 100.0)
    maker, taker = go("limit_alo", "A"), go("limit_ioc", "B")
    assert maker.fee_usd == pytest.approx(0.15) and maker.fill_px == 100.0
    assert taker.fee_usd == pytest.approx(0.45) and taker.fill_px == pytest.approx(100.073)
