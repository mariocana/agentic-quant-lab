"""End of video 3.2 — gold OHLCV resampling.

Resamples 1m bars to a higher timeframe using Polars' group_by_dynamic.

The mantra: closed='left', label='left'. The 09:00 bar contains the
1-minute bars from 09:00:00 to 09:04:59. The 09:05 1-minute bar starts
the next 5-minute bar. If you mix this up, your backtest is shifted by
one timeframe and your trades fire one bar too late.

compute_features runs a pipeline over a whole history (batch);
update_features pushes a single live bar through it.
"""
from datetime import timedelta

import polars as pl
from oryon import FeaturePipeline

from quantlake.helper import TF_SECONDS

_OHLC = ("open", "high", "low", "close")

# Session-anchored timeframes: "<tf>_<anchor>", e.g. "1d_cme", "4h_cme".
# Windows start at the anchor's local time (DST-aware) instead of 00:00 UTC.
# CME Globex: the trading day opens 17:00 America/Chicago, so "1d_cme" holds
# exactly one session (Sunday/Thursday 17:00 → Friday 16:00, daily halt
# 16:00-17:00) and "4h_cme" windows open at 17, 21, 01, 05, 09, 13 Chicago.
# The bar timestamp is still the window open, in UTC.
SESSION_ANCHORS: dict[str, tuple[str, timedelta]] = {
    "cme": ("America/Chicago", timedelta(hours=17)),
}


def parse_timeframe(timeframe: str) -> tuple[str, str | None]:
    """'4h' -> ('4h', None); '1d_cme' -> ('1d', 'cme'). Raises on unknown names."""
    base, sep, anchor = timeframe.partition("_")
    if base not in TF_SECONDS or (sep and anchor not in SESSION_ANCHORS):
        raise ValueError(f"Unknown timeframe {timeframe!r}")
    return base, anchor or None


def bar_open(timeframe: str, col: str = "timestamp") -> pl.Expr:
    """UTC open of the timeframe window containing each timestamp in col."""
    base, anchor = parse_timeframe(timeframe)
    if anchor is None:
        return pl.col(col).dt.truncate(base)
    tz, offset = SESSION_ANCHORS[anchor]
    wall = pl.col(col).dt.convert_time_zone(tz).dt.replace_time_zone(None)
    return _to_utc((wall - offset).dt.truncate(base) + offset, tz)


def bar_close(timeframe: str, col: str = "timestamp") -> pl.Expr:
    """UTC close of the window whose open is col (window open + timeframe, in local time if anchored)."""
    base, anchor = parse_timeframe(timeframe)
    step = pl.duration(seconds=TF_SECONDS[base])
    if anchor is None:
        return pl.col(col) + step
    tz, _ = SESSION_ANCHORS[anchor]
    wall = pl.col(col).dt.convert_time_zone(tz).dt.replace_time_zone(None)
    return _to_utc(wall + step, tz)


def _to_utc(wall: pl.Expr, tz: str) -> pl.Expr:
    # On the DST fall-back night 01:00 happens twice: take the first one.
    return wall.dt.replace_time_zone(tz, ambiguous="earliest").dt.convert_time_zone("UTC")


def resample(df: pl.DataFrame, timeframe: str) -> pl.DataFrame:
    """Resample 1m OHLC(V) bars to a higher timeframe ('5m', '4h', or session-anchored '1d_cme').

    Expects df to carry a 'symbol' column (added by bronze.ingest).
    ``volume`` is aggregated when present, skipped otherwise (some
    composite silvers intentionally drop it).

    Returns a new DataFrame with the same schema plus recomputed year/month.
    """
    if df.is_empty():
        return df

    has_volume = "volume" in df.columns
    cols = ["timestamp", "symbol", *_OHLC] + (["volume"] if has_volume else [])

    agg_exprs = [
        pl.col("open").first(),
        pl.col("high").max(),
        pl.col("low").min(),
        pl.col("close").last(),
    ]
    if has_volume:
        agg_exprs.append(pl.col("volume").sum())

    base, anchor = parse_timeframe(timeframe)
    if anchor is None:
        resampled = (
            df.select(cols)
            .sort("timestamp")
            .group_by_dynamic(
                "timestamp",
                every=base,
                closed="left",
                label="left",
                group_by="symbol",
            )
            .agg(*agg_exprs)
        )
    else:
        resampled = (
            df.select(cols)
            .sort("timestamp")
            .with_columns(bar_open(timeframe).alias("_open"))
            .group_by("symbol", "_open", maintain_order=True)
            .agg(*agg_exprs)
            .rename({"_open": "timestamp"})
            .select("symbol", "timestamp", *[c for c in cols if c not in ("timestamp", "symbol")])
        )

    return resampled.with_columns(
        pl.col("timestamp").dt.year().cast(pl.Int32).alias("year"),
        pl.col("timestamp").dt.month().cast(pl.Int8).alias("month"),
    ).sort("timestamp")


def compute_features(df: pl.DataFrame, pipeline: FeaturePipeline) -> pl.DataFrame:
    """Run an Oryon FeaturePipeline on df and append the feature columns.

    Processes each symbol independently so state does not bleed across instruments.
    Warm-up bars produce NaN — rows are never dropped.
    """
    if df.is_empty():
        return df

    input_cols = pipeline.input_names()
    output_cols = pipeline.output_names()

    parts = []
    for symbol in df["symbol"].unique(maintain_order=False).to_list():
        symbol_df = df.filter(pl.col("symbol") == symbol).sort("timestamp")
        data = symbol_df.select(input_cols).to_numpy().tolist()
        # run_research = batch mode of Oryon. Same numerical output as
        # update() called bar-by-bar (we use update() in live runners).
        # State is reset between symbol iterations because each iteration
        # drives a different pipeline instance? No — same instance, but
        # run_research resets state automatically on each call.
        raw = pipeline.run_research(data)
        feature_df = pl.DataFrame(
            {name: [row[i] for row in raw] for i, name in enumerate(output_cols)},
            schema={name: pl.Float64 for name in output_cols},
        )
        parts.append(pl.concat([symbol_df, feature_df], how="horizontal"))

    return pl.concat(parts, how="vertical").sort("timestamp")


def update_features(bar: pl.DataFrame, pipeline: FeaturePipeline) -> pl.DataFrame:
    """Live counterpart of compute_features: one bar through pipeline.update.

    The pipeline is stateful, so exactly one bar per call — anything else
    would silently skip bars and leave the state behind.
    """
    if bar.height != 1:
        raise ValueError(f"update_features expects exactly one bar, got {bar.height}")
    outputs = pipeline.update(list(bar.select(pipeline.input_names()).row(0)))
    feats = pl.DataFrame(
        {name: [outputs[i]] for i, name in enumerate(pipeline.output_names())},
        schema={name: pl.Float64 for name in pipeline.output_names()},
    )
    return pl.concat([bar, feats], how="horizontal")