"""Cross-sectional short-term reversal on Hyperliquid perps.

Rank the universe on trailing `lookback` bars return; long the bottom quintile,
short the top quintile; inverse-vol weights; dollar-neutral. Same idea as the
rToken reversal, moved to perps where funding and liquidity are much better.

Deterministic. Same candles in, same targets out.
"""
from __future__ import annotations

import math

from desk.data.hl_market import Candle
from desk.schemas import AssetContext, TargetPosition, asset_class
from desk.signals.base import Strategy


class Reversal(Strategy):
    id = "reversal_v1"

    def __init__(self, universe_size: int = 40, lookback: int = 5, vol_window: int = 20,
                 interval: str = "1d", gross_target: float = 0.4, quintile: float = 0.2,
                 min_day_volume_usd: float = 10_000_000, horizon_hours: int = 5 * 24):
        self.universe_size = universe_size
        self.lookback = lookback
        self.vol_window = vol_window
        self.interval = interval
        self.bars = max(lookback, vol_window) + 2
        self.gross_target = gross_target
        self.quintile = quintile
        self.min_day_volume_usd = min_day_volume_usd
        self.horizon_hours = horizon_hours

    def universe(self, contexts: dict[str, AssetContext]) -> list[str]:
        names = [a for a, c in contexts.items()
                 if asset_class(a) == "crypto" and c.day_volume_usd >= self.min_day_volume_usd]
        names.sort(key=lambda a: contexts[a].day_volume_usd, reverse=True)
        return names[:self.universe_size]

    def targets(self, candles: dict[str, list[Candle]], contexts: dict[str, AssetContext],
                equity_usd: float) -> list[TargetPosition]:
        scored: list[tuple[str, float, float]] = []       # (asset, trailing return, vol)
        for asset, cs in candles.items():
            # drop the last (still open) bar: only closed bars carry information
            closes = [c["c"] for c in cs[:-1]]
            if len(closes) < self.bars - 1:
                continue
            ret = closes[-1] / closes[-1 - self.lookback] - 1
            rets = [closes[i] / closes[i - 1] - 1 for i in range(len(closes) - self.vol_window, len(closes))]
            vol = math.sqrt(sum(r * r for r in rets) / len(rets))
            if vol <= 0:
                continue
            scored.append((asset, ret, vol))

        n = len(scored)
        k = int(n * self.quintile)
        if n < 10 or k < 1:
            return []
        scored.sort(key=lambda x: x[1])
        longs, shorts = scored[:k], scored[-k:]
        side_budget = equity_usd * self.gross_target / 2

        def weights(leg):
            inv = [1 / v for _, _, v in leg]
            tot = sum(inv)
            return [w / tot for w in inv]

        out = []
        for leg, sign, label in ((longs, 1, "bottom"), (shorts, -1, "top")):
            for (asset, ret, _), w in zip(leg, weights(leg)):
                out.append(TargetPosition(
                    asset=asset, notional_usd=sign * side_budget * w, strategy_id=self.id,
                    horizon_hours=self.horizon_hours,
                    reason=f"{label} quintile, {self.lookback}-bar ret {ret:+.2%}",
                ))
        return out
