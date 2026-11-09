"""Level 2 for Hyperliquid: the trading desk's own cycle, run over history.

The backtest does not reimplement the desk. It runs `desk.loop.run_cycle` — the
same rebalance, the same nine risk rules, the same time stop, the same paper
fills — once a day over past data, with three things swapped:

  the market    HistoricalMarket serves what HLMarket serves live, from quantlake:
                contexts (marks, funding, 24h volume) and daily candles, as they
                were known at 00:05 UTC that day and not a second later
  the clock     time_machine moves every datetime.now() in the desk to the cycle
                time, so the time stop, the risk day and the paper positions'
                opened_at all live in the simulated past
  the side effects  journal, risk state and paper account go to a temporary
                folder; notifications are collected instead of sent to Telegram

So a strategy that passes here passes through the code that will trade it, and
a difference between backtest and live can only come from the data or the cost
model, never from two implementations drifting apart.

What the past cannot provide, and how it is handled:

  order book    no history. The cycle runs with fetch_depth=False and the risk
                engine marks book_depth_unknown: only the 24h-volume cap limits
                size. Optimistic for thin names.
  open interest no history: 0 in every context. No rule uses it today.
  the open bar  live, the last daily candle is the one just opened at 00:00 and
                the strategy drops it. Here it is rebuilt flat at the last close
                with zero volume, so dropping it costs nothing and keeping it by
                mistake leaks nothing.
  funding       settled between cycles on the open positions, summed hourly rates
                from quantlake (PaperAdapter.apply_funding).
  delisting     a held perp whose bars stop is settled at its last close, as
                Hyperliquid settles a delisted market. Live there is no other way out.
"""
from __future__ import annotations

import bisect
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import polars as pl
import time_machine
from deltalake import DeltaTable

from alphaquant.config import QUANTLAKE_DATA_ROOT
from desk.data.hl_market import Candle
from desk.execution.paper import PaperAdapter
from desk.journal.log import read as read_journal
from desk.journal.log import record as desk_record
from desk.loop import run_cycle
from desk.risk.state import RiskState
from desk.schemas import AssetContext, OrderIntent, RiskVerdict

DAY_MS = 86_400_000


def _ms(t: datetime) -> int:
    return int(t.timestamp() * 1000)


class HistoricalMarket:
    """HLMarket's interface over quantlake tables, frozen at a moment `now`."""

    def __init__(self, daily: pl.DataFrame, funding: pl.DataFrame, listings: pl.DataFrame,
                 meta: dict[str, dict] | None = None):
        self.now: datetime | None = None
        self.meta = meta or {}
        self._bars: dict[str, dict[str, list]] = {}
        for (sym,), g in daily.sort("timestamp").group_by("symbol", maintain_order=True):
            self._bars[sym] = {
                "t": [_ms(x) for x in g["timestamp"]], "T": [_ms(x) for x in g["timestamp_close"]],
                "o": g["open"].to_list(), "h": g["high"].to_list(), "l": g["low"].to_list(),
                "c": g["close"].to_list(), "v": g["volume"].to_list(),
            }
        self._funding: dict[str, tuple[list[int], list[float], list[float]]] = {}
        for (sym,), g in funding.sort("timestamp").group_by("symbol", maintain_order=True):
            rates = g["funding_rate"].to_list()
            cum, s = [], 0.0
            for r in rates:
                s += r
                cum.append(s)
            self._funding[sym] = ([_ms(x) for x in g["timestamp"]], rates, cum)
        self._listings = listings

    @classmethod
    def from_quantlake(cls, root: Path = QUANTLAKE_DATA_ROOT, symbols: list[str] | None = None) -> "HistoricalMarket":
        def load(path, cols=None):
            filters = [("symbol", "in", symbols)] if symbols else None
            return pl.from_arrow(DeltaTable(str(path)).to_pyarrow_table(columns=cols, filters=filters))
        return cls(daily=load(root / "bronze" / "hyperliquid_ohlcv_1d"),
                   funding=load(root / "bronze" / "hyperliquid_funding", ["symbol", "timestamp", "funding_rate"]),
                   listings=pl.from_arrow(DeltaTable(str(root / "reference" / "hyperliquid_listings")).to_pyarrow_table()))

    def at(self, t: datetime) -> None:
        self.now = t

    # ---- what the past knew at `now` -----------------------------------------

    def _last_closed(self, sym: str) -> int:
        """Index of the last bar whose close time is strictly before now, or -1."""
        b = self._bars.get(sym)
        return -1 if b is None else bisect.bisect_left(b["T"], _ms(self.now)) - 1

    def _listed(self) -> list[str]:
        day = self.now.date()
        L = self._listings.filter(
            pl.col("first_bar").is_not_null() & (pl.col("first_bar") <= day)
            & (pl.col("delisted_after").is_null() | (pl.col("delisted_after") >= day)))
        return L["symbol"].to_list()

    def funding_rate(self, sym: str) -> float:
        f = self._funding.get(sym)
        if not f:
            return 0.0
        i = bisect.bisect_right(f[0], _ms(self.now)) - 1
        return f[1][i] if i >= 0 else 0.0

    def funding_between(self, t0: datetime, t1: datetime) -> dict[str, float]:
        """Summed hourly rates settled in (t0, t1], per asset."""
        out = {}
        for sym, (ts, _, cum) in self._funding.items():
            i0, i1 = bisect.bisect_right(ts, _ms(t0)) - 1, bisect.bisect_right(ts, _ms(t1)) - 1
            s = (cum[i1] if i1 >= 0 else 0.0) - (cum[i0] if i0 >= 0 else 0.0)
            if s:
                out[sym] = s
        return out

    def last_close(self, sym: str) -> float | None:
        i = self._last_closed(sym)
        return self._bars[sym]["c"][i] if i >= 0 else None

    def is_dead(self, sym: str) -> bool:
        """No bar for the last two days: the market is gone."""
        b, i = self._bars.get(sym), self._last_closed(sym)
        return b is None or i < 0 or b["T"][i] < _ms(self.now) - 2 * DAY_MS

    # ---- HLMarket's interface --------------------------------------------------

    def contexts(self) -> dict[str, AssetContext]:
        out = {}
        for sym in self._listed():
            i = self._last_closed(sym)
            if i < 0:
                continue
            b, m = self._bars[sym], self.meta.get(sym, {})
            c = b["c"][i]
            out[sym] = AssetContext(asset=sym, mark_px=c, mid_px=c, funding_hourly=self.funding_rate(sym),
                                    open_interest=0.0, day_volume_usd=b["v"][i] * c,
                                    sz_decimals=int(m.get("szDecimals", 3)), max_leverage=int(m.get("maxLeverage", 3)))
        return out

    def candles(self, asset: str, interval: str, bars: int) -> list[Candle]:
        if interval != "1d":
            raise ValueError(f"the historical market serves daily bars only, not {interval!r}")
        i = self._last_closed(asset)
        if i < 0:
            return []
        b = self._bars[asset]
        out = [Candle(t=b["t"][k], o=b["o"][k], h=b["h"][k], l=b["l"][k], c=b["c"][k], v=b["v"][k])
               for k in range(max(0, i - bars + 2), i + 1)]
        c = b["c"][i]
        today = _ms(datetime.combine(self.now.date(), time(), tzinfo=timezone.utc))
        out.append(Candle(t=today, o=c, h=c, l=c, c=c, v=0.0))     # the bar just opened: no information
        return out

    def book_depth_10bps(self, asset: str):
        raise LookupError("no historical order book")


@dataclass
class ReplayResult:
    equity: pl.DataFrame                       # timestamp, equity
    journal: list[dict] = field(default_factory=list)
    notifications: list[str] = field(default_factory=list)
    funding_paid: float = 0.0
    settled_delistings: list[str] = field(default_factory=list)

    def fills(self) -> list[dict]:
        return [r for r in self.journal if r.get("kind") == "fill"]


def replay(strategy, market: HistoricalMarket, limits: dict, start: datetime, end: datetime,
           equity: float = 10_000.0, at: time = time(0, 5), costs: dict | None = None) -> ReplayResult:
    """One desk cycle a day at `at` UTC from `start` to `end`, inclusive."""
    notes: list[str] = []
    rows, paid, settled = [], 0.0, []
    with tempfile.TemporaryDirectory() as d:
        journal = Path(d) / "journal.jsonl"

        def record(kind, payload, path=journal):
            desk_record(kind, payload, path)

        with patch("desk.loop.record", record), patch("desk.loop.notify", notes.append):
            adapter = PaperAdapter(starting_equity=equity, path=Path(d) / "paper.json")
            if costs:
                adapter.costs = {k: dict(v) for k, v in costs.items()}
            state = RiskState.load(Path(d) / "risk.json")
            t = datetime.combine(start.date(), at, tzinfo=timezone.utc)
            stop = datetime.combine(end.date(), at, tzinfo=timezone.utc)
            prev = None
            while t <= stop:
                with time_machine.travel(t, tick=False):
                    market.at(t)
                    if prev is not None:
                        paid += adapter.apply_funding(market.funding_between(prev, t))
                    for asset in list(adapter.state["positions"]):
                        if market.is_dead(asset):
                            settled.append(asset)
                            _settle(adapter, asset, market.last_close(asset) or adapter.state["positions"][asset]["entry_px"])
                    run_cycle(market, strategy, adapter, limits, state, fetch_depth=False)
                    rows.append({"timestamp": t, "equity": adapter.account_state().equity_usd})
                prev, t = t, t + timedelta(days=1)
        log = read_journal(journal) if journal.exists() else []
    eq = pl.DataFrame(rows, schema={"timestamp": pl.Datetime("us", "UTC"), "equity": pl.Float64})
    return ReplayResult(equity=eq, journal=log, notifications=notes, funding_paid=paid, settled_delistings=settled)


def _settle(adapter: PaperAdapter, asset: str, px: float) -> None:
    """Close a position in a perp that stopped trading, at its last price, no costs."""
    p = adapter.state["positions"][asset]
    side = "sell" if p["size"] > 0 else "buy"
    intent = OrderIntent(asset=asset, side=side, notional_usd=abs(p["size"]) * px, reduce_only=True,
                         order_type="limit_ioc", strategy_id="settlement", horizon_hours=0, reason="delisted")
    saved = adapter.costs
    adapter.costs = {k: {"fee_bps": 0.0, "slippage_bps": 0.0} for k in saved}
    adapter.set_marks({asset: px})
    adapter.execute(intent, RiskVerdict(intent_id=intent.id, decision="approve",
                                        approved_notional_usd=intent.notional_usd), px)
    adapter.costs = saved
