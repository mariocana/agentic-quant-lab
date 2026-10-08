"""Shared test data builders."""
from datetime import datetime, timedelta, timezone

import polars as pl


def utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


def minute_bars(start: datetime, n: int, symbol: str = "BTCUSDT", base: float = 100.0) -> pl.DataFrame:
    """n consecutive 1m bars starting at start, with predictable prices.

    Bar i: open=base+i, high=base+i+0.5, low=base+i-0.5, close=base+i+0.25, volume=i+1.
    """
    ts = [start + timedelta(minutes=i) for i in range(n)]
    return pl.DataFrame({
        "timestamp": pl.Series(ts, dtype=pl.Datetime("us", "UTC")),
        "symbol":    [symbol] * n,
        "open":      [base + i for i in range(n)],
        "high":      [base + i + 0.5 for i in range(n)],
        "low":       [base + i - 0.5 for i in range(n)],
        "close":     [base + i + 0.25 for i in range(n)],
        "volume":    [float(i + 1) for i in range(n)],
    })
