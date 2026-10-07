from datetime import datetime, timezone

import polars as pl
import pytest

from alphaquant.engine import EQUITY_SCHEMA, TRADE_SCHEMA, ExitReason, SimResult, Trade, trades_frame

UTC = timezone.utc


def es_short() -> Trade:
    return Trade(
        symbol="ES", side=-1, qty=2,
        entry_time=datetime(2026, 3, 10, 14, tzinfo=UTC), entry_price=5000.0,
        exit_time=datetime(2026, 3, 10, 15, tzinfo=UTC), exit_price=4990.0,
        exit_reason=ExitReason.TAKE_PROFIT, multiplier=50, fees_quote=10.0,
    )


def test_trade_pnl():
    trade = es_short()
    assert trade.gross_pnl_quote == 1000.0       # 10 points x 2 contracts x $50
    assert trade.net_pnl_quote == 990.0
    perp = Trade(
        symbol="BTCUSDT-PERP", side=1, qty=0.1,
        entry_time=datetime(2026, 1, 1, tzinfo=UTC), entry_price=60_000,
        exit_time=datetime(2026, 1, 2, tzinfo=UTC), exit_price=61_000,
        exit_reason=ExitReason.SIGNAL, multiplier=1, fees_quote=12.1, funding_quote=-3.0,
    )
    assert perp.net_pnl_quote == pytest.approx(100 - 12.1 - 3.0)


def test_trade_validation():
    with pytest.raises(ValueError, match="side"):
        Trade("ES", 0, 1, datetime(2026, 1, 1, tzinfo=UTC), 1.0, datetime(2026, 1, 1, tzinfo=UTC), 1.0, ExitReason.SIGNAL, 50)
    with pytest.raises(ValueError, match="qty"):
        Trade("ES", 1, 0, datetime(2026, 1, 1, tzinfo=UTC), 1.0, datetime(2026, 1, 1, tzinfo=UTC), 1.0, ExitReason.SIGNAL, 50)


def test_frames_and_sim_result():
    trades = trades_frame([es_short()])
    assert trades.schema == TRADE_SCHEMA
    assert trades["exit_reason"].to_list() == ["tp"]
    assert trades_frame([]).schema == TRADE_SCHEMA

    equity = pl.DataFrame({"timestamp": [datetime(2026, 3, 10, 15, tzinfo=UTC)], "equity": [100_990.0]}, schema=EQUITY_SCHEMA)
    result = SimResult(trades=trades, equity=equity, meta={"level": 1})
    assert result.meta["level"] == 1

    with pytest.raises(ValueError, match="equity"):
        SimResult(trades=trades, equity=equity.rename({"equity": "value"}))
