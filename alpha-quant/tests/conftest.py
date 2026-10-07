"""Small Delta tables shaped like quantlake's, built in a temp data root."""
from datetime import datetime, timedelta, timezone

import polars as pl
import pytest

from alphaquant.instruments import Costs, PercentFee, PerContractFee

UTC = timezone.utc


def reference_rows() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "symbol": ["ES", "BTCUSDT"],
            "asset_class": ["future", "crypto_spot"],
            "exchange": ["CME", "BINANCE"],
            "quote_ccy": ["USD", "USDT"],
            "tick_size": [0.25, 0.01],
            "multiplier": [50.0, 1.0],
            "qty_step": [1.0, 0.00001],
            "min_qty": [1.0, 0.00001],
            "calendar": ["CMES", "24/7"],
            "break_start": ["16:00", None],
            "break_end": ["17:00", None],
            "gold_table": ["multicharts_ohlcv", "binance_spot_ohlcv"],
            "data_symbol": ["ES", "BTCUSDT"],
            "updated_at": [datetime(2026, 10, 1, tzinfo=UTC)] * 2,
        },
        schema_overrides={"break_start": pl.String, "break_end": pl.String, "updated_at": pl.Datetime("us", "UTC")},
    )


def gold_bars(symbol: str, start: datetime, n: int, step: timedelta, base: float = 100.0) -> pl.DataFrame:
    ts = [start + i * step for i in range(n)]
    close = [base + i for i in range(n)]
    return pl.DataFrame(
        {
            "timestamp": pl.Series(ts, dtype=pl.Datetime("us", "UTC")),
            "symbol": [symbol] * n,
            "open": close,
            "high": [c + 0.5 for c in close],
            "low": [c - 0.5 for c in close],
            "close": close,
            "volume": [1.0] * n,
        }
    ).with_columns(
        pl.col("timestamp").dt.year().cast(pl.Int32).alias("year"),
        pl.col("timestamp").dt.month().cast(pl.Int8).alias("month"),
    )


def write_delta(df: pl.DataFrame, path, mode: str = "overwrite", partition_by=None) -> None:
    options = {"partition_by": partition_by} if partition_by else {}
    if mode == "overwrite":
        options["schema_mode"] = "overwrite"  # tests rewrite tables with a different (broken) schema
    df.write_delta(str(path), mode=mode, delta_write_options=options or None)


@pytest.fixture
def costs() -> dict[str, Costs]:
    return {
        "ES": Costs(fee=PerContractFee(per_side=2.5), slippage_ticks=1, verified=False),
        "BTCUSDT": Costs(fee=PercentFee(maker=0.001, taker=0.001), slippage_ticks=1, verified=False),
    }


@pytest.fixture
def data_root(tmp_path):
    write_delta(reference_rows(), tmp_path / "reference" / "instruments")
    return tmp_path
