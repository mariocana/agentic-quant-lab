from datetime import datetime, timedelta, timezone

from desk.data.hl_market import Candle
from desk.loop import time_stop_intents
from desk.schemas import AccountState, AssetContext, Position, TargetPosition
from desk.signals.rebalance import intents_from_targets
from desk.signals.reversal import Reversal


def series(path):
    return [Candle(t=i, o=p, h=p, l=p, c=p, v=1.0) for i, p in enumerate(path)]


def test_reversal_is_deterministic_and_dollar_neutral():
    s = Reversal(universe_size=10, lookback=3, vol_window=5, quintile=0.2)
    candles = {}
    for k in range(10):
        # asset k trends by (k+1)% per bar; the last (open) bar must be ignored
        path = [100 * (1 + (k + 1) / 100) ** i for i in range(s.bars)] + [1e9]
        candles[f"A{k}"] = series(path)
    ctx = {a: AssetContext(asset=a, mark_px=1, mid_px=1, funding_hourly=0, open_interest=0,
                           day_volume_usd=1e8, sz_decimals=2, max_leverage=10) for a in candles}
    t1 = s.targets(candles, ctx, 10_000.0)
    t2 = s.targets(candles, ctx, 10_000.0)
    assert [x.model_dump(exclude={"created_at"}) for x in t1] == [x.model_dump(exclude={"created_at"}) for x in t2]
    longs = [t for t in t1 if t.notional_usd > 0]
    shorts = [t for t in t1 if t.notional_usd < 0]
    assert {t.asset for t in longs} == {"A0", "A1"} and {t.asset for t in shorts} == {"A8", "A9"}
    assert abs(sum(t.notional_usd for t in t1)) < 1e-6
    assert abs(sum(abs(t.notional_usd) for t in t1) - 10_000 * s.gross_target) < 1e-6


def test_reversal_needs_enough_names():
    s = Reversal(lookback=3, vol_window=5)
    assert s.targets({}, {}, 10_000.0) == []


def test_rebalance_diffs_and_closes_first():
    now = datetime.now(timezone.utc)
    acc = AccountState(equity_usd=10_000, margin_used_usd=0, positions=[
        Position(asset="BTC", notional_usd=500, size=5, entry_px=100, mark_px=100, unrealized_pnl_usd=0, strategy_id="r"),
        Position(asset="ETH", notional_usd=-300, size=-3, entry_px=100, mark_px=100, unrealized_pnl_usd=0, strategy_id="r"),
        Position(asset="SOL", notional_usd=200, size=2, entry_px=100, mark_px=100, unrealized_pnl_usd=0, strategy_id="r"),
    ])
    targets = [TargetPosition(asset="BTC", notional_usd=505, strategy_id="r", horizon_hours=24, reason="dust"),
               TargetPosition(asset="ETH", notional_usd=-100, strategy_id="r", horizon_hours=24, reason="trim"),
               TargetPosition(asset="AVAX", notional_usd=250, strategy_id="r", horizon_hours=24, reason="new")]
    out = intents_from_targets(targets, acc, "r", marks={"AVAX": 10.0, "ETH": 100.0})
    by = {i.asset: i for i in out}
    assert "BTC" not in by                                         # 5 usd delta is dust
    assert by["SOL"].reduce_only and by["SOL"].side == "sell" and by["SOL"].order_type == "limit_ioc"
    assert by["ETH"].reduce_only and by["ETH"].side == "buy" and by["ETH"].notional_usd == 200
    assert not by["AVAX"].reduce_only and abs(by["AVAX"].stop_px - 9.2) < 1e-9 and by["AVAX"].order_type == "limit_alo"
    assert [i.reduce_only for i in out] == [True, True, False]


def test_time_stop(limits):
    now = datetime.now(timezone.utc)
    acc = AccountState(equity_usd=10_000, margin_used_usd=0, positions=[
        Position(asset="OLD", notional_usd=100, size=1, entry_px=100, mark_px=100, unrealized_pnl_usd=0,
                 opened_at=now - timedelta(hours=30), horizon_hours=24, strategy_id="r"),
        Position(asset="NEW", notional_usd=-100, size=-1, entry_px=100, mark_px=100, unrealized_pnl_usd=0,
                 opened_at=now - timedelta(hours=10), horizon_hours=24, strategy_id="r"),
    ])
    out = time_stop_intents(acc, limits, now=now)
    assert len(out) == 1 and out[0].asset == "OLD" and out[0].reduce_only and out[0].side == "sell"
