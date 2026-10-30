from desk.risk import engine
from desk.risk.state import RiskState
from desk.schemas import OrderIntent


def intent(asset="BTC", side="buy", usd=100.0, reduce_only=False):
    return OrderIntent(asset=asset, side=side, notional_usd=usd, reduce_only=reduce_only,
                       strategy_id="t", horizon_hours=24, reason="test")


def ev(i, acc, c, limits, st, depth=1e6):
    return engine.evaluate(i, acc, engine.Market(c, depth), limits, st)


def test_clean_intent_approved(limits, ctx, account, state):
    v = ev(intent(), account(), ctx(), limits, state)
    assert v.decision == "approve" and v.approved_notional_usd == 100.0 and v.rules_fired == []


def test_min_notional(limits, ctx, account, state):
    v = ev(intent(usd=5.0), account(), ctx(), limits, state)
    assert v.decision == "reject" and "min_notional" in v.rules_fired


def test_per_asset_cap_reduces(limits, ctx, account, state):
    # 5% of 10k = 500 for crypto
    v = ev(intent(usd=2000.0), account(), ctx(), limits, state)
    assert v.decision == "reduce" and v.approved_notional_usd == 500.0
    assert "max_notional_per_asset" in v.rules_fired


def test_per_asset_cap_hip3_is_tighter(limits, ctx, account, state):
    v = ev(intent(asset="xyz:TSLA", usd=2000.0), account(), ctx("xyz:TSLA"), limits, state)
    assert v.approved_notional_usd == 200.0


def test_per_asset_cap_with_existing_position(limits, ctx, account, state):
    v = ev(intent(usd=400.0), account(positions=[("BTC", 300.0)]), ctx(), limits, state)
    assert v.approved_notional_usd == 200.0


def test_flip_through_zero_allowed_up_to_cap(limits, ctx, account, state):
    # long 300, sell 1000 -> would be short 700 > cap 500 -> allowed = 300 + 500 = 800
    v = ev(intent(side="sell", usd=1000.0), account(positions=[("BTC", 300.0)]), ctx(), limits, state)
    assert v.approved_notional_usd == 800.0


def test_reduce_only_bypasses_everything(limits, ctx, account, state):
    state.halted = True
    RiskState.engage_kill("test")
    v = ev(intent(side="sell", usd=300.0, reduce_only=True), account(positions=[("BTC", 300.0)]), ctx(), limits, state)
    assert v.decision == "approve" and v.approved_notional_usd == 300.0


def test_opposite_side_within_position_is_treated_as_reducing(limits, ctx, account, state):
    v = ev(intent(side="sell", usd=100.0), account(positions=[("BTC", 300.0)]), ctx(), limits, state)
    assert v.decision == "approve" and "treated_as_reduce_only" in v.rules_fired


def test_kill_switch_blocks_new_risk(limits, ctx, account, state):
    RiskState.engage_kill("test")
    v = ev(intent(), account(), ctx(), limits, state)
    assert v.decision == "reject" and v.rules_fired == ["kill_switch"]
    RiskState.release_kill()
    assert ev(intent(), account(), ctx(), limits, state).decision == "approve"


def test_halted_blocks_new_risk(limits, ctx, account, state):
    state.halted, state.halt_reason = True, "max_drawdown"
    v = ev(intent(), account(), ctx(), limits, state)
    assert v.decision == "reject" and v.rules_fired == ["halted:max_drawdown"]


def test_daily_loss_freeze(limits, ctx, account, state):
    v = ev(intent(), account(equity=9_650.0), ctx(), limits, state)   # -3.5% on the day
    assert v.decision == "reject" and "daily_loss_freeze" in v.rules_fired


def test_gross_leverage_cap(limits, ctx, account, state):
    # 3x of 10k = 30k gross. Already 29.9k in other names.
    acc = account(positions=[("ETH", 15_000.0), ("SOL", -14_900.0)])
    v = ev(intent(usd=400.0), acc, ctx(), limits, state)
    assert "max_gross_leverage" in v.rules_fired and v.approved_notional_usd == 100.0


def test_gross_leverage_cut_below_min_rejects(limits, ctx, account, state):
    acc = account(positions=[("ETH", 15_000.0), ("SOL", -14_995.0)])
    v = ev(intent(usd=400.0), acc, ctx(), limits, state)
    assert v.decision == "reject" and "min_notional_after_cuts" in v.rules_fired


def test_net_beta_cap(limits, ctx, account, state):
    # net beta 9,900 (99% of equity); another 200 long BTC breaks 100% -> cut to 100
    acc = account(positions=[("SOL", 4_950.0), ("AVAX", 4_950.0)])
    v = ev(intent(usd=200.0), acc, ctx(), limits, state)
    assert "max_net_beta" in v.rules_fired and abs(v.approved_notional_usd - 100.0) < 1e-6


def test_net_beta_short_against_long_book_is_fine(limits, ctx, account, state):
    acc = account(positions=[("SOL", 4_950.0), ("AVAX", 4_950.0)])
    v = ev(intent(side="sell", usd=400.0), acc, ctx(), limits, state)
    assert "max_net_beta" not in v.rules_fired and v.approved_notional_usd == 400.0


def test_hip3_has_no_crypto_beta(limits, ctx, account, state):
    acc = account(positions=[("SOL", 4_950.0), ("AVAX", 4_950.0)])
    v = ev(intent(asset="xyz:TSLA", usd=150.0), acc, ctx("xyz:TSLA"), limits, state)
    assert "max_net_beta" not in v.rules_fired


def test_volume_and_depth_caps(limits, ctx, account, state):
    v = ev(intent(usd=400.0), account(), ctx(volume=100_000.0), limits, state, depth=1e9)   # 0.1% of 100k = 100
    assert "max_pct_of_day_volume" in v.rules_fired and v.approved_notional_usd == 100.0
    v = ev(intent(usd=400.0), account(), ctx(), limits, state, depth=2_000.0)              # 10% of 2k = 200
    assert "max_pct_of_book_depth" in v.rules_fired and v.approved_notional_usd == 200.0


def test_missing_depth_is_flagged_not_ignored(limits, ctx, account, state):
    v = ev(intent(), account(), ctx(), limits, state, depth=None)
    assert v.decision == "approve" and "book_depth_unknown" in v.rules_fired


def test_funding_only_when_paying(limits, ctx, account, state):
    hi = limits["max_abs_funding_hourly"] * 1.5
    assert "funding_halved" in ev(intent(side="buy"), account(), ctx(funding=hi), limits, state).rules_fired
    assert "funding_halved" not in ev(intent(side="sell"), account(), ctx(funding=hi), limits, state).rules_fired
    v = ev(intent(side="sell"), account(), ctx(funding=-3 * limits["max_abs_funding_hourly"]), limits, state)
    assert v.decision == "reject" and "funding_too_expensive" in v.rules_fired


def test_the_kill_switch_also_takes_resting_orders_off_the_book():
    """The engine refuses new intents, but an order already resting keeps filling:
    risk still arriving while the switch reads as engaged. Stops stay — they are
    the protection, not the exposure."""
    import ast
    from pathlib import Path

    src = (Path(__file__).resolve().parent.parent / "desk" / "ui" / "service.py").read_text()
    fn = next(n for n in ast.walk(ast.parse(src))
              if isinstance(n, ast.FunctionDef) and n.name == "kill")
    body = ast.dump(fn)
    assert "cancel_orders" in body
    assert "include_triggers" in body and "False" in body, "stops must survive the kill switch"
