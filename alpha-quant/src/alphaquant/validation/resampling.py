"""Stage 3 (Monte Carlo) and Stage 6 (bootstrap) on a vector of trade P&L.

Every function takes a seed: the same input and seed give the same numbers,
so a gate verdict can be reproduced exactly.

Two different resamplings, not to be confused:
    reshuffle  permutation of the same trades. Net profit is identical in every
               path; only the order, hence the drawdown, changes. It is the
               MultiCharts built-in Monte Carlo of Stage 3.
    resample   draws with replacement. Net profit varies too: it is what the
               Stage 3 criteria on median net and share of losing paths need,
               and what the Colab notebook of Stage 6 does.
"""
from collections.abc import Iterator
from dataclasses import dataclass

import numpy as np

_BATCH_CELLS = 4_000_000  # paths x trades held in memory at once


def path_drawdowns(paths: np.ndarray) -> np.ndarray:
    """Max drawdown of each row of a (paths, trades) P&L matrix, starting flat."""
    equity = np.cumsum(paths, axis=1)
    peak = np.maximum(np.maximum.accumulate(equity, axis=1), 0.0)
    return np.max(peak - equity, axis=1)


def _batches(sims: int, n: int) -> Iterator[int]:
    size = max(1, _BATCH_CELLS // max(n, 1))
    done = 0
    while done < sims:
        k = min(size, sims - done)
        yield k
        done += k


@dataclass(frozen=True)
class MonteCarlo:
    dd_reshuffle: np.ndarray   # max drawdown of each permuted path
    net_resample: np.ndarray   # net profit of each path drawn with replacement

    def dd_pct(self, q: float) -> float:
        return float(np.percentile(self.dd_reshuffle, q))

    @property
    def median_net(self) -> float:
        return float(np.median(self.net_resample))

    @property
    def losing_share(self) -> float:
        return float(np.mean(self.net_resample <= 0))


def monte_carlo(pnl: np.ndarray, sims: int = 1000, seed: int = 0) -> MonteCarlo:
    """Stage 3: reshuffle for the drawdown, resample for the net."""
    rng = np.random.default_rng(seed)
    n = len(pnl)
    dd, net = [], []
    for k in _batches(sims, n):
        dd.append(path_drawdowns(rng.permuted(np.tile(pnl, (k, 1)), axis=1)))
    for k in _batches(sims, n):
        net.append(pnl[rng.integers(0, n, size=(k, n))].sum(axis=1))
    return MonteCarlo(np.concatenate(dd), np.concatenate(net))


@dataclass(frozen=True)
class Bootstrap:
    mean: float
    lo: float
    hi: float
    p_le_zero: float   # share of bootstrap means <= 0
    ci: float

    def overlaps(self, other: "Bootstrap") -> bool:
        return self.lo <= other.hi and other.lo <= self.hi


def bootstrap_mean(x: np.ndarray, sims: int = 10_000, ci: float = 0.95, seed: int = 0) -> Bootstrap:
    """Confidence interval of the average trade (Colab EV notebook, step 10)."""
    n = len(x)
    if n == 0:
        raise ValueError("no trades to bootstrap")
    rng = np.random.default_rng(seed)
    means = np.concatenate([x[rng.integers(0, n, size=(k, n))].mean(axis=1) for k in _batches(sims, n)])
    a = (1 - ci) / 2
    return Bootstrap(
        mean=float(x.mean()),
        lo=float(np.quantile(means, a)),
        hi=float(np.quantile(means, 1 - a)),
        p_le_zero=float(np.mean(means <= 0)),
        ci=ci,
    )


def dd_at_horizons(
    pnl: np.ndarray,
    horizons: tuple[int, ...] = (10, 20, 40),
    pcts: tuple[float, ...] = (50, 75, 90, 95),
    sims: int = 20_000,
    seed: int = 0,
) -> dict[int, dict[float, float]]:
    """Drawdown percentiles after h trades, paths drawn with replacement.

    The live yardstick of Stage 6: after 20 live trades a drawdown beyond the
    95th percentile here says the strategy is not the one we tested.
    """
    rng = np.random.default_rng(seed)
    n = len(pnl)
    out = {}
    for h in horizons:
        dd = np.concatenate([path_drawdowns(pnl[rng.integers(0, n, size=(k, h))]) for k in _batches(sims, h)])
        out[h] = {q: float(np.percentile(dd, q)) for q in pcts}
    return out
