"""Continuous ES / NQ series built from single contracts + check against @ES.

gold/multicharts_continuous/<tf>: symbol = root ("ES"), unadjusted OHLCV of
the contract active at each bar, plus

    contract    TradeStation code of that contract ("ESZ25")
    adj_offset  sum of gap_points of every later roll (reference/rolls);
                back-adjusted price = price + adj_offset (additive, keeps
                point P&L). Null when a later roll has no gap_points.

The contract active in [previous roll_ts, own roll_ts) is the one used.
Timeframes are limited to windows that never straddle a roll (17:00 CT):
CONTINUOUS_TIMEFRAMES. A new roll shifts adj_offset of all older bars, so
the table is rebuilt whole and rows are overwritten (new Delta version).
"""
from datetime import datetime

import polars as pl

import quantlake.gold.ingest as gold
from quantlake.gold.ohlcv import bar_open
from quantlake.reference.rolls import parse_contract

GOLD_TABLE = "multicharts_continuous"
CONTINUOUS_TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h_cme", "1d_cme"]


def continuous_1m(root: str, contract_bars: pl.DataFrame, rolls: pl.DataFrame) -> pl.DataFrame:
    """1m continuous series for root.

    contract_bars: silver contract bars (symbol = contract code, timestamp, OHLCV...).
    rolls: reference/rolls rows (any roots; only `root` is used).
    """
    rolls = rolls.filter(pl.col("symbol") == root).sort("roll_ts")
    codes = sorted({c for c in contract_bars["symbol"].unique().to_list() if parse_contract(c).root == root},
                   key=parse_contract)
    parts = []
    for code in codes:
        start = rolls.filter(pl.col("to_contract") == code)["roll_ts"]
        end = parse_contract(code).roll_ts
        later = rolls.filter(pl.col("roll_ts") >= end)["gap_points"]
        offset = None if later.null_count() else float(later.sum())
        seg = contract_bars.filter((pl.col("symbol") == code) & (pl.col("timestamp") < end))
        if len(start):
            seg = seg.filter(pl.col("timestamp") >= start[0])
        if seg.is_empty():
            continue
        parts.append(seg.with_columns(
            pl.lit(root).alias("symbol"),
            pl.lit(code).alias("contract"),
            pl.lit(offset, dtype=pl.Float64).alias("adj_offset"),
        ))
    if not parts:
        return pl.DataFrame()
    return pl.concat(parts, how="diagonal_relaxed").sort("timestamp")


def check_no_straddle(series: pl.DataFrame, timeframe: str) -> None:
    """Raise if a timeframe window would hold bars of two contracts."""
    mixed = (
        series.with_columns(bar_open(timeframe).alias("_open"))
        .group_by("symbol", "_open").agg(pl.col("contract").n_unique().alias("n"))
        .filter(pl.col("n") > 1)
    )
    if not mixed.is_empty():
        raise ValueError(f"{timeframe}: {mixed.height} windows mix two contracts, first {mixed['_open'].min()}")


def write_continuous(series: pl.DataFrame, timeframes: list[str] = CONTINUOUS_TIMEFRAMES) -> dict[str, int]:
    """Resample the 1m continuous series per contract segment and upsert gold. Returns bars per timeframe."""
    written = {}
    for tf in timeframes:
        check_no_straddle(series, tf)
        n = 0
        for (symbol, contract), seg in series.group_by("symbol", "contract", maintain_order=True):
            offset = seg["adj_offset"][0]

            def add_contract(df: pl.DataFrame, _symbol: str, contract=contract, offset=offset) -> pl.DataFrame:
                return df.with_columns(pl.lit(contract).alias("contract"),
                                       pl.lit(offset, dtype=pl.Float64).alias("adj_offset"))

            n += gold.ingest(seg, GOLD_TABLE, tf, transform_gold=add_contract).height
        written[tf] = n
    return written


# ── check against TradeStation's @ES / @NQ ─────────────────────────────────

def compare_with_reference(
    contract_bars: pl.DataFrame,
    reference: pl.DataFrame,
    root: str,
    rolls: pl.DataFrame,
    tick: float = 0.25,
    min_minutes: int = 30,
) -> pl.DataFrame:
    """Per CME session: which contract @ES follows vs the one our calendar uses.

    @ES is back-adjusted additively, so on the contract it follows the
    difference @ES close - contract close is constant over a session (to a
    fraction of a tick); on any other contract it isn't. Sessions are
    1d_cme windows with at least `min_minutes` common minutes.

    Columns: session (UTC open), ours (our contract), theirs (@ES contract,
    null when none / more than one fits), offset (@ES - theirs), minutes.
    """
    ref = reference.filter(pl.col("symbol") == root).select("timestamp", pl.col("close").alias("ref"))
    bars = contract_bars.filter(pl.col("symbol").str.contains(rf"^{root}[FGHJKMNQUVXZ]\d{{2}}$"))
    if ref.is_empty() or bars.is_empty():
        return pl.DataFrame()

    joined = (
        bars.select("symbol", "timestamp", "close").join(ref, on="timestamp")
        .filter(pl.col("close").is_not_nan() & pl.col("ref").is_not_nan())
        .with_columns(bar_open("1d_cme").alias("session"), (pl.col("ref") - pl.col("close")).alias("d"))
    )
    stats = (
        joined.group_by("session", "symbol")
        .agg(pl.len().alias("minutes"), (pl.col("d").max() - pl.col("d").min()).alias("spread"),
             pl.col("d").median().alias("offset"))
        .filter(pl.col("minutes") >= min_minutes)
    )
    fits = stats.filter(pl.col("spread") <= tick / 2)
    theirs = (
        fits.group_by("session")
        .agg(pl.col("symbol").first().alias("theirs"), pl.col("offset").first(),
             pl.col("minutes").first(), pl.len().alias("n_fit"))
        .with_columns(pl.when(pl.col("n_fit") == 1).then(pl.col("theirs")).alias("theirs"))
        .drop("n_fit")
    )
    sessions = stats.select("session").unique()
    ours = _our_contract(sessions, root, rolls, sorted(bars["symbol"].unique().to_list(), key=parse_contract))
    return ours.join(theirs, on="session", how="left").sort("session")


def _our_contract(sessions: pl.DataFrame, root: str, rolls: pl.DataFrame, codes: list[str]) -> pl.DataFrame:
    rolls = rolls.filter(pl.col("symbol") == root).sort("roll_ts")
    first = codes[0]
    out = []
    for s in sessions["session"].to_list():
        done = rolls.filter(pl.col("roll_ts") <= s)
        out.append(done["to_contract"][-1] if len(done) else first)
    return sessions.with_columns(pl.Series("ours", out, dtype=pl.String))


def roll_differences(comparison: pl.DataFrame, rolls: pl.DataFrame, root: str) -> pl.DataFrame:
    """For each roll: our roll_ts vs the first session where @ES is on to_contract.

    days_late > 0: TradeStation rolls later than us; < 0: earlier; null: not
    observable (no session where @ES matches to_contract).
    """
    rows = []
    for r in rolls.filter(pl.col("symbol") == root).sort("roll_ts").iter_rows(named=True):
        on_new = comparison.filter(pl.col("theirs") == r["to_contract"])["session"]
        ts_roll: datetime | None = on_new.min() if len(on_new) else None
        rows.append({
            "symbol": root, "from_contract": r["from_contract"], "to_contract": r["to_contract"],
            "our_roll": r["roll_ts"], "ts_roll": ts_roll,
            "days_late": None if ts_roll is None else round((ts_roll - r["roll_ts"]).total_seconds() / 86400, 2),
        })
    return pl.DataFrame(rows, schema={
        "symbol": pl.String, "from_contract": pl.String, "to_contract": pl.String,
        "our_roll": pl.Datetime("us", "UTC"), "ts_roll": pl.Datetime("us", "UTC"), "days_late": pl.Float64,
    })
