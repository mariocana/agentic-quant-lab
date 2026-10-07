"""Common output of both simulation levels.

Screener (level 1) and simulator (level 2) return the same SimResult, so
metrics and validation never depend on which level produced it.

Money columns: *_quote in the instrument's quote currency, net_pnl_account
in the account currency (USD) via fx_rate (1.0 for USD and USDT).
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

import polars as pl


class ExitReason(StrEnum):
    TAKE_PROFIT = "tp"
    STOP_LOSS = "sl"
    SIGNAL = "signal"
    TIME = "time"
    SESSION_END = "session_end"
    ROLL = "roll"
    END_OF_DATA = "end_of_data"


_TS = pl.Datetime("us", "UTC")

TRADE_SCHEMA = pl.Schema({
    "symbol": pl.String(),
    "side": pl.Int8(),               # +1 long, -1 short
    "qty": pl.Float64(),
    "entry_time": _TS,
    "entry_price": pl.Float64(),
    "exit_time": _TS,
    "exit_price": pl.Float64(),
    "exit_reason": pl.String(),
    "gross_pnl_quote": pl.Float64(),
    "fees_quote": pl.Float64(),
    "funding_quote": pl.Float64(),   # > 0 received, < 0 paid
    "net_pnl_quote": pl.Float64(),
    "net_pnl_account": pl.Float64(),
})

EQUITY_SCHEMA = pl.Schema({"timestamp": _TS, "equity": pl.Float64()})


@dataclass(frozen=True)
class Trade:
    symbol: str
    side: int
    qty: float
    entry_time: datetime
    entry_price: float
    exit_time: datetime
    exit_price: float
    exit_reason: ExitReason
    multiplier: float
    fees_quote: float = 0.0
    funding_quote: float = 0.0
    fx_rate: float = 1.0  # quote currency -> account currency

    def __post_init__(self) -> None:
        if self.side not in (1, -1):
            raise ValueError(f"side must be +1 or -1, got {self.side}")
        if self.qty <= 0:
            raise ValueError(f"qty must be > 0, got {self.qty}")

    @property
    def gross_pnl_quote(self) -> float:
        return self.side * (self.exit_price - self.entry_price) * self.qty * self.multiplier

    @property
    def net_pnl_quote(self) -> float:
        return self.gross_pnl_quote - self.fees_quote + self.funding_quote

    @property
    def net_pnl_account(self) -> float:
        return self.net_pnl_quote * self.fx_rate


def trades_frame(trades: list[Trade]) -> pl.DataFrame:
    """Trades as a DataFrame with TRADE_SCHEMA."""
    rows = [
        {
            "symbol": t.symbol,
            "side": t.side,
            "qty": t.qty,
            "entry_time": t.entry_time,
            "entry_price": t.entry_price,
            "exit_time": t.exit_time,
            "exit_price": t.exit_price,
            "exit_reason": t.exit_reason.value,
            "gross_pnl_quote": t.gross_pnl_quote,
            "fees_quote": t.fees_quote,
            "funding_quote": t.funding_quote,
            "net_pnl_quote": t.net_pnl_quote,
            "net_pnl_account": t.net_pnl_account,
        }
        for t in trades
    ]
    return pl.DataFrame(rows, schema=TRADE_SCHEMA)


@dataclass(frozen=True)
class SimResult:
    trades: pl.DataFrame
    equity: pl.DataFrame
    meta: dict = field(default_factory=dict)  # instrument, params, Delta versions read, level

    def __post_init__(self) -> None:
        for name, frame, schema in (("trades", self.trades, TRADE_SCHEMA), ("equity", self.equity, EQUITY_SCHEMA)):
            if frame.schema != schema:
                raise ValueError(f"SimResult.{name} schema {dict(frame.schema)} != expected {dict(schema)}")
