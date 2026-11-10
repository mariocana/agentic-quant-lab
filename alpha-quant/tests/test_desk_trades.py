"""From the desk's fills to the trade list the gates read."""
from datetime import datetime, timedelta, timezone

import pytest

from alphaquant.engine.desk_replay import HistoricalMarket, replay
from alphaquant.engine.desk_trades import to_simresult, trades_from_journal
from alphaquant.engine.types import ExitReason
from desk.config import load_limits
from desk.signals.reversal import Reversal

from test_desk_replay import SYMS, D0, _daily, _funding, _listings

T = datetime(2026, 1, 1, tzinfo=timezone.utc)


def ts(h):
    return (T + timedelta(hours=h)).isoformat()


def fill(h, side, usd, px, fee=0.0, intent="i"):
    return {"kind": "fill", "ts": ts(h), "asset": "A", "side": side, "filled_usd": usd, "fill_px": px,
            "fee_usd": fee, "intent_id": intent}


def test_open_topup_trim_close_is_one_trade_that_reconciles():
    j = [{"kind": "intent", "id": "stop", "reason": "time stop: opened ..."},
         fill(0, "buy", 1000, 100, fee=0.45),         # 10 @ 100
         fill(24, "buy", 1100, 110, fee=0.5),          # +10 @ 110 -> avg 105
         fill(48, "sell", 1200, 120, fee=0.5),         # -10 @ 120: +150 realised
         {"kind": "funding", "ts": ts(60), "asset": "A", "paid_usd": 2.0},
         fill(72, "sell", 900, 90, fee=0.4, intent="stop")]   # -10 @ 90: -150 realised
    (t,) = trades_from_journal(j, {}, T + timedelta(days=4))
    assert t.side == 1 and t.qty == pytest.approx(20) and t.entry_price == pytest.approx(105)
    assert t.gross_pnl_quote == pytest.approx(0.0)
    assert t.fees_quote == pytest.approx(1.85) and t.funding_quote == pytest.approx(-2.0)
    assert t.exit_reason == ExitReason.TIME


def test_a_flip_closes_one_trade_and_opens_the_next():
    j = [fill(0, "buy", 1000, 100), fill(24, "sell", 2200, 110)]     # 10 long, then 20 short
    trades = trades_from_journal(j, {"A": 100.0}, T + timedelta(days=2))
    assert [x.side for x in trades] == [1, -1]
    assert trades[0].gross_pnl_quote == pytest.approx(100.0)
    assert trades[1].qty == pytest.approx(10) and trades[1].exit_reason == ExitReason.END_OF_DATA
    assert trades[1].gross_pnl_quote == pytest.approx(100.0)          # short 10 @ 110, marked at 100


def test_a_real_replay_becomes_a_simresult_whose_trades_add_up_to_the_equity_change():
    daily = _daily(SYMS, 70)
    m = HistoricalMarket(daily, _funding(SYMS, 70, rate=0.00003), _listings(daily))
    res = replay(Reversal(universe_size=15, min_day_volume_usd=1e6), m, load_limits(),
                 D0 + timedelta(days=25), D0 + timedelta(days=60))
    sim = to_simresult(res, {"strategy": "reversal_v1"})
    pnl = sim.trades["net_pnl_account"].sum()
    assert pnl == pytest.approx(res.equity["equity"][-1] - res.start_equity, abs=1e-6)
    assert sim.trades["funding_quote"].sum() == pytest.approx(-res.funding_paid, abs=1e-9)
    assert "time" in sim.trades["exit_reason"].to_list()
    assert sim.meta["strategy"] == "reversal_v1" and sim.meta["level"] == 2
