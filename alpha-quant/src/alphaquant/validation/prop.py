"""Stage 7: passing a prop eval, ported from mc/docs/prop_sim.py.

The question is P(touching +target before -MLL), with the number of micros as
an OUTPUT. Days are the unit: the path inside a day is kept in order, and the
worst excursion inside each trade (mae) can breach the limit before the close.

Three ways to string days into an attempt:
    iid         days drawn with replacement: independent attempts. The number
                a decision is made on.
    contiguous  every historical day as a start, real chronology. Overlapping
                windows ride the good clusters, so it overstates: a check only.
    sequential  attempt k starts where k-1 ended: the correlation between
                attempts of Live 004, measured instead of assumed.
"""
import math
import random
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field

import numpy as np

from alphaquant.validation.trades import Day, TradeLog


@dataclass(frozen=True)
class PropAccount:
    name: str
    balance: float
    target: float
    mll: float
    lock_floor: float | None   # the EOD trailing stops here; None = trails forever
    attempt_cost: float

    @property
    def target_mll_ratio(self) -> float:
        """The P/D criterion of pipeline_prop.md: P/D must reach this, whatever the size."""
        return self.target / self.mll


# Verified 30/09/2026 (pipeline_prop.md): EOD trailing, locks at 50,100 once
# the EOD peak reaches 52,100; no daily loss limit, no consistency on the eval.
LUCIDFLEX_50K = PropAccount("LucidFlex 50k", 50_000.0, 3_000.0, 2_000.0, 50_100.0, 100.0)

PASS, FAIL, OPEN = "pass", "fail", "open"


@dataclass(frozen=True)
class Attempt:
    outcome: str
    days: int
    max_dd: float   # deepest fall from the running peak balance, intraday included


def attempt(days: Iterable[Day], n_micro: int, account: PropAccount, max_days: int | None) -> Attempt:
    bal = peak_eod = peak = account.balance
    floor = account.balance - account.mll
    dd = 0.0
    g = 0
    for g, trades in enumerate(days, 1):
        for pnl, mae in trades:
            low = bal + mae * n_micro
            dd = max(dd, peak - low)
            if low <= floor:                   # breached inside the trade, not at the close
                return Attempt(FAIL, g, dd)
            bal += pnl * n_micro
            peak = max(peak, bal)
            if bal <= floor:
                return Attempt(FAIL, g, dd)
            if bal >= account.balance + account.target:
                return Attempt(PASS, g, dd)
        peak_eod = max(peak_eod, bal)          # the trailing moves at end of day only
        floor = peak_eod - account.mll
        if account.lock_floor is not None:
            floor = min(floor, account.lock_floor)
        if max_days and g >= max_days:
            return Attempt(OPEN, g, dd)
    return Attempt(OPEN, g, dd)


@dataclass
class Outcomes:
    attempts: list[Attempt] = field(default_factory=list)

    def add(self, a: Attempt) -> None:
        self.attempts.append(a)

    def _share(self, outcome: str) -> float:
        return sum(a.outcome == outcome for a in self.attempts) / len(self.attempts) if self.attempts else 0.0

    @property
    def n(self) -> int:
        return len(self.attempts)

    @property
    def pass_rate(self) -> float:
        return self._share(PASS)

    @property
    def fail_rate(self) -> float:
        return self._share(FAIL)

    @property
    def open_rate(self) -> float:
        """Attempts still running at max_days: an expired eval."""
        return self._share(OPEN)

    @property
    def mean_days_to_pass(self) -> float | None:
        d = [a.days for a in self.attempts if a.outcome == PASS]
        return sum(d) / len(d) if d else None

    @property
    def median_days_to_pass(self) -> int | None:
        d = sorted(a.days for a in self.attempts if a.outcome == PASS)
        return d[len(d) // 2] if d else None

    @property
    def mean_max_dd(self) -> float:
        return sum(a.max_dd for a in self.attempts) / len(self.attempts) if self.attempts else 0.0


def _pool(days: Sequence[tuple]) -> list[Day]:
    return [t for _, t in days]


def sim_iid(days, n_micro, account, sims, max_days, rng: random.Random) -> Outcomes:
    pool, out = _pool(days), Outcomes()
    for _ in range(sims):
        out.add(attempt((rng.choice(pool) for _ in range(max_days or 400)), n_micro, account, max_days))
    return out


def sim_contiguous(days, n_micro, account, max_days) -> Outcomes:
    pool, out = _pool(days), Outcomes()
    for i in range(max(1, len(pool) - (max_days or 0))):   # complete windows only
        out.add(attempt(pool[i:], n_micro, account, max_days))
    return out


def sim_sequential(days, n_micro, account, max_days, max_attempts) -> tuple[list[float], int]:
    """Share of starts that passed within k attempts, k = 0..max_attempts."""
    pool = _pool(days)
    counts = [0] * (max_attempts + 1)
    starts = max(1, len(pool) - (max_days or 0) * max_attempts)
    for i in range(starts):
        pos = i
        for k in range(1, max_attempts + 1):
            if pos >= len(pool):
                break
            a = attempt(pool[pos:], n_micro, account, max_days)
            if a.outcome == PASS:
                for kk in range(k, max_attempts + 1):
                    counts[kk] += 1
                break
            pos += a.days
    return [c / starts for c in counts], starts


def cumulative(p: float, k: int) -> float:
    """P(at least one pass in k attempts), attempts independent."""
    return 1.0 - (1.0 - p) ** k


def degrade(days, wr_cut_pp: float, shrink: float, rng: random.Random):
    """The same days as if live paid less: winners turned into real losses, all P&L shrunk."""
    wins = [p for _, tr in days for p, _m in tr if p > 0]
    losses = [(p, m) for _, tr in days for p, m in tr if p <= 0]
    n = sum(len(tr) for _, tr in days)
    if not wins or not losses or n == 0:
        return days
    flip = (wr_cut_pp / 100.0) / (len(wins) / n)
    out = []
    for d, tr in days:
        new = []
        for p, m in tr:
            if p > 0 and flip > 0 and rng.random() < flip:
                p, m = losses[rng.randrange(len(losses))]
            new.append((p * (1 - shrink), m * (1 - shrink)))
        out.append((d, new))
    return out


SCENARIOS = (
    ("as backtested", 0.0, 0.00),
    ("WR -3 pp, P&L -10%", 3.0, 0.10),
    ("WR -5 pp, P&L -15%", 5.0, 0.15),
    ("WR -5 pp, P&L -25%", 5.0, 0.25),
    ("WR -8 pp, P&L -30%", 8.0, 0.30),
)


@dataclass(frozen=True)
class CurrentState:
    dd_now: float
    dd_max: float
    p50: float
    p95: float
    percentile: float   # where dd_now falls among historical drawdowns


def current_state(days) -> CurrentState:
    """Distance from the equity high at the end of the data (Live 004: bench, don't start)."""
    eq = peak = 0.0
    series = []
    for _, trades in days:
        for p, _m in trades:
            eq += p
            peak = max(peak, eq)
            series.append(peak - eq)
    if not series:
        return CurrentState(0.0, 0.0, 0.0, 0.0, 0.0)
    s = sorted(series)
    now = series[-1]
    return CurrentState(now, s[-1], s[len(s) // 2], s[int(0.95 * len(s))],
                        100.0 * sum(x <= now for x in series) / len(series))


def reliable_size(log: TradeLog, account: PropAccount, q: float = 95.0) -> int:
    """Most micros at which the q-th percentile loss of one trade still fits the MLL.

    Above it the simulator's estimates turn optimistic (Colab prop notebook).
    `log` must already be per micro. The loss includes the excursion inside the trade.
    """
    worst = -np.minimum(log.frame["pnl"].to_numpy(), log.frame["mae"].to_numpy())
    losses = worst[worst > 0]
    if len(losses) == 0:
        return 10**6
    return max(0, math.floor(account.mll / float(np.percentile(losses, q))))


@dataclass(frozen=True)
class PropReport:
    account: PropAccount
    max_days: int
    sims: int
    trades: int
    n_days: int
    state: CurrentState
    by_size: dict[int, tuple[Outcomes, Outcomes]]   # micros -> (iid, contiguous)
    best: int
    sequential: list[float]
    sequential_starts: int
    scenarios: dict[str, float]                    # iid pass rate at the best size
    reliable: int

    @property
    def iid(self) -> Outcomes:
        return self.by_size[self.best][0]

    @property
    def independent_windows(self) -> float:
        return self.n_days / float(self.max_days or 1)


def simulate(
    log: TradeLog,
    account: PropAccount = LUCIDFLEX_50K,
    sizes: Sequence[int] = (1, 2, 3, 4, 6, 8),
    sims: int = 20_000,
    max_days: int = 60,
    max_attempts: int = 4,
    seed: int = 20261015,
) -> PropReport:
    """The whole of prop_sim.py on a per-micro TradeLog (see TradeLog.to_micro)."""
    days = log.days()
    if not days:
        raise ValueError("no trades to simulate")
    rng = random.Random(seed)
    by_size = {n: (sim_iid(days, n, account, sims, max_days, rng), sim_contiguous(days, n, account, max_days))
               for n in sizes}
    best = max(by_size, key=lambda n: by_size[n][0].pass_rate)   # decided on iid
    seq, starts = sim_sequential(days, best, account, max_days, max_attempts)
    scenarios = {}
    for name, cut, shrink in SCENARIOS:
        d = days if cut == 0 and shrink == 0 else degrade(days, cut, shrink, rng)
        scenarios[name] = sim_iid(d, best, account, max(2000, sims // 4), max_days, rng).pass_rate
    return PropReport(account, max_days, sims, len(log), len(days), current_state(days), by_size, best,
                      seq, starts, scenarios, reliable_size(log, account))
