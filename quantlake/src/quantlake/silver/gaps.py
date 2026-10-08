"""Holes in 1m futures series (MultiCharts exports), read-only checks.

A hole = consecutive bars more than 1 minute apart, 1-59 minutes missing,
not overlapping the 16:00-17:00 Chicago halt (longer gaps are weekends,
holidays, halts). MultiCharts builds a bar only when a tick arrives, so a
minute without trades has no bar: scattered overnight holes are normal.

Checking holes one by one misses a wrong session template: it cuts the
same window every day, and each hole looks unremarkable. Two rules catch it:

  recurring_gaps  the same Chicago time-of-day window missing in more than
                  `threshold` of a month's trading days (e.g. 15:15-15:29 CT,
                  the pause CME removed on 2021-06-28)
  early_fridays   months where more than `threshold` of the Fridays end
                  before 15:59 CT (Globex closes at 16:00 CT on Friday)
"""
from datetime import time

import polars as pl

TZ = "America/Chicago"
TICK = 0.25
RTH = (time(8, 30), time(15, 15))
HALT = (time(16, 0), time(17, 0))
FRIDAY_LAST_BAR = time(15, 59)


def holes(bars: pl.DataFrame) -> pl.DataFrame:
    """before / after bar timestamps (UTC), missing minutes, first/last missing minute in Chicago time."""
    ts = bars.select("timestamp").unique().sort("timestamp")["timestamp"]
    h = pl.DataFrame({"before": ts[:-1], "after": ts[1:]}).with_columns(
        ((pl.col("after") - pl.col("before")).dt.total_minutes() - 1).alias("missing"),
        (pl.col("before") + pl.duration(minutes=1)).dt.convert_time_zone(TZ).alias("first_missing_ct"),
        (pl.col("after") - pl.duration(minutes=1)).dt.convert_time_zone(TZ).alias("last_missing_ct"),
    ).filter(pl.col("missing").is_between(1, 59))
    first_t, last_t = pl.col("first_missing_ct").dt.time(), pl.col("last_missing_ct").dt.time()
    return h.filter(~((last_t >= HALT[0]) & (first_t < HALT[1])))


def _trade_date(col: str = "timestamp") -> pl.Expr:
    """CME trade date: the session opening 17:00 CT belongs to the next day."""
    return (pl.col(col).dt.convert_time_zone(TZ) + pl.duration(hours=7)).dt.date()


def find_gaps(bars: pl.DataFrame, tick: float = TICK) -> pl.DataFrame:
    """One row per hole with its context: RTH or not, neighbours' volume/ticks vs the same hour/year, price jump."""
    b = bars.sort("timestamp")
    local = pl.col("timestamp").dt.convert_time_zone(TZ)
    b = b.with_columns(
        local.dt.year().alias("year"),
        local.dt.hour().alias("hour"),
        (pl.col("ticks") if "ticks" in b.columns else pl.lit(None, dtype=pl.Float64)).alias("ticks"),
        (pl.col("volume") if "volume" in b.columns else pl.lit(None, dtype=pl.Float64)).alias("vol"),
    )
    hourly = b.group_by("year", "hour").agg(pl.col("vol").median().alias("med_vol"))
    b = b.join(hourly, on=["year", "hour"], how="left").with_columns(
        (pl.col("vol") / pl.col("med_vol")).alias("rel_vol"))
    before = b.select(pl.col("timestamp").alias("before"), "year", pl.col("close").alias("close_before"),
                      pl.col("rel_vol").alias("rel_vol_before"), pl.col("ticks").alias("ticks_before"))
    after = b.select(pl.col("timestamp").alias("after"), pl.col("open").alias("open_after"),
                     pl.col("rel_vol").alias("rel_vol_after"), pl.col("ticks").alias("ticks_after"))
    first_t = pl.col("first_missing_ct").dt.time()
    return (
        holes(b).join(before, on="before").join(after, on="after")
        .with_columns(
            ((pl.col("open_after") - pl.col("close_before")).abs() / tick).round(2).alias("jump_ticks"),
            pl.col("first_missing_ct").dt.hour().alias("hour_ct"),
            ((first_t >= RTH[0]) & (first_t < RTH[1])).alias("rth"),
        )
        .sort("before")
    )


def recurring_gaps(bars: pl.DataFrame, threshold: float = 0.5) -> pl.DataFrame:
    """Time-of-day windows missing in more than `threshold` of a month's trading days.

    Columns: month ("2021-07"), window_start_ct / window_end_ct (first and
    last missing minute, "HH:MM"), days_missing, trading_days, share.
    """
    days = (bars.select(_trade_date().alias("day")).unique()
            .group_by(pl.col("day").dt.strftime("%Y-%m").alias("month")).agg(pl.len().alias("trading_days")))
    h = holes(bars)
    if h.is_empty():
        return pl.DataFrame(schema={"month": pl.String, "window_start_ct": pl.String, "window_end_ct": pl.String,
                                    "days_missing": pl.UInt32, "trading_days": pl.UInt32, "share": pl.Float64})
    minutes = (
        h.select(pl.datetime_ranges("first_missing_ct", "last_missing_ct", "1m").alias("m")).explode("m", empty_as_null=False)
        .with_columns(
            (pl.col("m") + pl.duration(hours=7)).dt.date().dt.strftime("%Y-%m").alias("month"),
            (pl.col("m") + pl.duration(hours=7)).dt.date().alias("day"),
            (pl.col("m").dt.hour().cast(pl.Int32) * 60 + pl.col("m").dt.minute().cast(pl.Int32)).alias("mod"),
        )
        .group_by("month", "mod").agg(pl.col("day").n_unique().alias("days_missing"))
        .join(days, on="month")
        .with_columns((pl.col("days_missing") / pl.col("trading_days")).alias("share"))
        .filter(pl.col("share") > threshold)
        .sort("month", "mod")
    )
    windows = (
        minutes.with_columns(
            ((pl.col("mod") - pl.col("mod").shift(1).over("month")) != 1).fill_null(True).cum_sum().alias("w"))
        .group_by("month", "w").agg(
            pl.col("mod").min().alias("start"), pl.col("mod").max().alias("end"),
            pl.col("days_missing").max(), pl.col("trading_days").first(), pl.col("share").max().round(3))
    )
    hhmm = lambda c: pl.format("{}:{}", (pl.col(c) // 60).cast(pl.String).str.zfill(2),  # noqa: E731
                               (pl.col(c) % 60).cast(pl.String).str.zfill(2))
    return windows.select("month", hhmm("start").alias("window_start_ct"), hhmm("end").alias("window_end_ct"),
                          "days_missing", "trading_days", "share").sort("month", "window_start_ct")


def early_fridays(bars: pl.DataFrame, threshold: float = 0.5) -> pl.DataFrame:
    """Months where more than `threshold` of the Fridays end before 15:59 CT.

    Columns: month, fridays, early, share, typical_last_ct (most common last bar).
    """
    local = pl.col("timestamp").dt.convert_time_zone(TZ)
    fri = (
        bars.select(local.alias("t"))
        .filter((pl.col("t").dt.weekday() == 5) & (pl.col("t").dt.time() < HALT[0]))
        .group_by(pl.col("t").dt.date().alias("day")).agg(pl.col("t").max().dt.time().alias("last"))
    )
    return (
        fri.group_by(pl.col("day").dt.strftime("%Y-%m").alias("month"))
        .agg(pl.len().alias("fridays"), (pl.col("last") < FRIDAY_LAST_BAR).sum().alias("early"),
             pl.col("last").mode().first().dt.strftime("%H:%M").alias("typical_last_ct"))
        .with_columns((pl.col("early") / pl.col("fridays")).round(3).alias("share"))
        .filter(pl.col("share") > threshold)
        .select("month", "fridays", "early", "share", "typical_last_ct")
        .sort("month")
    )


def summarize(gaps: pl.DataFrame) -> dict[str, pl.DataFrame]:
    by_year = gaps.group_by("year").agg(
        pl.len().alias("gaps"),
        pl.col("missing").sum().alias("missing_min"),
        (pl.col("missing") == 1).sum().alias("len_1"),
        pl.col("missing").is_between(2, 5).sum().alias("len_2_5"),
        (pl.col("missing") > 5).sum().alias("len_6_59"),
        pl.col("rth").mean().round(3).alias("share_rth"),
        pl.col("rel_vol_before").median().round(3).alias("med_rel_vol_before"),
        pl.col("rel_vol_after").median().round(3).alias("med_rel_vol_after"),
        pl.col("ticks_before").median().alias("med_ticks_before"),
        pl.col("jump_ticks").median().alias("med_jump_ticks"),
        (pl.col("jump_ticks") <= 1).mean().round(3).alias("share_jump_le_1"),
    ).sort("year")
    by_hour = gaps.group_by("hour_ct").agg(pl.len().alias("gaps"), pl.col("missing").sum().alias("missing_min")).sort("hour_ct")
    suspicious = gaps.filter(pl.col("rth") & (pl.col("jump_ticks") >= 4)).sort("jump_ticks", descending=True).head(20)
    return {"by_year": by_year, "by_hour_ct": by_hour, "rth_with_jumps": suspicious}
