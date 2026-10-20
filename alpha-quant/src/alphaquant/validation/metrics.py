"""Stage 2 measures on a trade list (the numbers of mc/docs/check_report.py)."""
import math
from dataclasses import dataclass

import numpy as np

from alphaquant.validation.trades import TradeLog


@dataclass(frozen=True)
class Metrics:
    n: int
    net: float
    avg: float
    sd: float
    se: float           # error bar of the average: sd / sqrt(n)
    t: float            # how many error bars separate the average from zero
    win_rate: float     # percent, a trade at 0 counts as a loss
    avg_win: float
    avg_loss: float     # <= 0
    rr: float           # avg win / |avg loss|
    pf: float
    max_dd: float       # on closed trades, from the starting balance
    worst_trade: float
    by_year: dict[int, float]

    @property
    def top_year_share(self) -> float | None:
        """Largest share of the net made in one year; undefined when net <= 0."""
        if self.net <= 0 or not self.by_year:
            return None
        return max(self.by_year.values()) / self.net


def max_drawdown(pnl: np.ndarray) -> float:
    """Deepest fall of the closed-trade equity, starting flat at 0."""
    if len(pnl) == 0:
        return 0.0
    equity = np.concatenate(([0.0], np.cumsum(pnl)))
    return float(np.max(np.maximum.accumulate(equity) - equity))


def measure(log: TradeLog) -> Metrics:
    pnl = log.pnl
    n = len(pnl)
    if n < 3:
        raise ValueError(f"only {n} trades: nothing to measure")
    avg = float(pnl.mean())
    sd = float(pnl.std(ddof=1))
    se = sd / math.sqrt(n)
    wins, losses = pnl[pnl > 0], pnl[pnl <= 0]
    avg_win = float(wins.mean()) if len(wins) else 0.0
    avg_loss = float(losses.mean()) if len(losses) else 0.0
    by_year: dict[int, float] = {}
    for y, p in zip(log.years, pnl):
        by_year[y] = by_year.get(y, 0.0) + float(p)
    return Metrics(
        n=n,
        net=float(pnl.sum()),
        avg=avg,
        sd=sd,
        se=se,
        t=avg / se if se else 0.0,
        win_rate=100.0 * len(wins) / n,
        avg_win=avg_win,
        avg_loss=avg_loss,
        rr=avg_win / -avg_loss if avg_loss else math.inf,
        pf=float(wins.sum() / -losses.sum()) if losses.sum() else math.inf,
        max_dd=max_drawdown(pnl),
        worst_trade=float(pnl.min()),
        by_year=by_year,
    )
