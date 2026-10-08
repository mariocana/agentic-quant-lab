"""Daily context for the Stucchi playbook -> gold/daily_context/1d.

One row per (symbol, trading day) for ES and NQ. The trading day is the
CME session that opens 17:00 Chicago the evening before. Columns are
grouped by the moment they become known, so a study never uses a value
before it existed:

  before London (09:00 Rome)
    prev_*        previous RTH session (high, low, close, range)
    range20       mean RTH range of the previous 20 sessions
    trend20       prev_close vs mean of the previous 20 RTH closes: up / down
    vix vix9d vix1d vix3m vxn   CBOE closes of the previous day
    iv, iv_pct    VIX for ES, VXN for NQ; percentile vs the prior 252 days
    term_9d       vix9d / vix   (> 1: short-term stress)
    term_3m       vix / vix3m   (> 1: backwardation)
    index_close   real cash index close (SPX / NDX): the futures are
                  back-adjusted, so percentages are taken on the cash level
    em            expected move in points = index_close * iv / 100 / sqrt(252)
    em_1d         same with VIX1D (ES only, from 2022-05)
    gex dix gex_pct gex_regime   SqueezeMetrics of the previous day
    vol_regime    high / low (iv_pct >= 0.5)
    quadrant      vol_regime x trend20, e.g. high_down
    asia_*        Globex open -> 09:00 Rome
    london_open   price at 09:00 Rome

  before NY (15:30 Rome)
    london_*      09:00 -> 13:30 Rome; london_range_em = range / em
    on_high on_low  whole overnight, Globex open -> 08:30 Chicago
    rth_open, gap = rth_open - prev_close, gap_em, open_location

  after the close (outcomes, for studies only)
    ib_*          first hour 08:30 -> 09:30 Chicago, ib_break up/down/both/none
    rth_*         08:30 -> 15:00 Chicago (cash session), rth_clv = close
                  location in the range (0 = low, 1 = high), rth_range_em
    complete      the session is over (false on today's row while it trades):
                  filter on it before any study
    day_type      trend_up / trend_down / rotation (TREND_CLV, TREND_RANGE_EM),
                  only on complete sessions
    gap_filled    RTH traded back to prev_close
    moc_move      last 10 minutes (14:50 -> 15:00), pre_moc_move = rth_open
                  -> 14:50, moc_with_day = same sign

Points (ranges, gaps, moves) are exact on back-adjusted bars: the shift
is additive. delta = sum(upticks - downticks), an approximation.

Rows follow the cash calendar (days with a VIX close) plus the session
in progress, so a run in the morning gives today's pre-London row with
the RTH columns still empty. CME holiday sessions (Globex open, cash
closed) are dropped; a cash day missing from the feed stays as an empty
row (rth_bars = null) so prev_* never skips a day. rth_bars = 390 on a
full session, ~210 on a half day.
"""
import math
from datetime import time, timedelta

import numpy as np
import polars as pl
from deltalake import write_deltalake

from quantlake.config import GOLD_ROOT

TABLE = "daily_context"
TIMEFRAME = "1d"
CT, ROME, ET = "America/Chicago", "Europe/Rome", "America/New_York"

# symbol -> (implied vol index, cash index)
SYMBOLS = {"ES": ("VIX", "SPX"), "NQ": ("VXN", "NDX")}
VOL_COLS = ["VIX", "VIX9D", "VIX1D", "VIX3M", "VXN"]

PCT_LOOKBACK, PCT_MIN = 252, 60
TREND_CLV = 0.15        # close in the top / bottom 15% of the RTH range
TREND_RANGE_EM = 1.0    # ... and a range of at least one expected move
SQRT252 = math.sqrt(252)


def _between(t: pl.Expr, start: time, end: time) -> pl.Expr:
    return t.is_between(start, end, closed="left")


def session_stats(bars: pl.DataFrame) -> pl.DataFrame:
    """1m bars of one symbol (timestamp = bar open, UTC) -> one row per trading day."""
    b = bars.sort("timestamp").with_columns(
        pl.col("timestamp").dt.convert_time_zone(CT).alias("ct"),
        pl.col("timestamp").dt.convert_time_zone(ROME).alias("rome"),
    ).with_columns(
        (pl.col("ct").dt.replace_time_zone(None) + timedelta(hours=7)).dt.date().alias("date"),
        (pl.col("upticks") - pl.col("downticks")).alias("delta"),
    )
    ct_day = pl.col("ct").dt.date() == pl.col("date")
    ct_t = pl.col("ct").dt.time()
    rome_day = pl.col("rome").dt.date() == pl.col("date")
    rome_t = pl.col("rome").dt.time()

    windows = {
        "asia":   ~rome_day | (rome_t < time(9, 0)),
        "london": rome_day & _between(rome_t, time(9, 0), time(13, 30)),
        "on":     ~ct_day | (ct_t < time(8, 30)),
        "ib":     ct_day & _between(ct_t, time(8, 30), time(9, 30)),
        "postib": ct_day & _between(ct_t, time(9, 30), time(15, 0)),
        "rth":    ct_day & _between(ct_t, time(8, 30), time(15, 0)),
        "moc":    ct_day & _between(ct_t, time(14, 50), time(15, 0)),
    }
    out = b.group_by("date").agg(pl.col("timestamp").max().alias("last_bar"))
    for name, cond in windows.items():
        w = b.filter(cond).group_by("date").agg(
            pl.len().alias(f"{name}_bars"),
            pl.col("timestamp").first().alias(f"{name}_start"),
            pl.col("open").first().alias(f"{name}_open"),
            pl.col("high").max().alias(f"{name}_high"),
            pl.col("low").min().alias(f"{name}_low"),
            pl.col("close").last().alias(f"{name}_close"),
            pl.col("volume").sum().alias(f"{name}_volume"),
            pl.col("delta").sum().alias(f"{name}_delta"),
        )
        out = out.join(w, on="date", how="left")
    return out.sort("date")


def _prior_pct(x: np.ndarray) -> np.ndarray:
    """Share of the prior PCT_LOOKBACK values below x[i] (NaN until PCT_MIN values)."""
    out = np.full(len(x), np.nan)
    for i in range(len(x)):
        if np.isnan(x[i]):
            continue
        w = x[max(0, i - PCT_LOOKBACK):i]
        w = w[~np.isnan(w)]
        if len(w) >= PCT_MIN:
            out[i] = (w < x[i]).mean()
    return out


def _by_et_date(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(
        pl.col("timestamp").dt.convert_time_zone(ET).dt.date().alias("src_date")
    ).drop("timestamp").sort("src_date")


def daily_sources(vol: pl.DataFrame, sm: pl.DataFrame, cash: pl.DataFrame) -> dict[str, pl.DataFrame]:
    """Daily external series keyed by src_date (US Eastern date of the close)."""
    v = _by_et_date(
        vol.filter(pl.col("symbol").is_in(VOL_COLS))
        .pivot(on="symbol", index="timestamp", values="close")
    )
    v = v.with_columns(
        *[pl.Series(f"{c}_pct", _prior_pct(v[c].cast(pl.Float64).fill_null(np.nan).to_numpy()))
          for c in ("VIX", "VXN") if c in v.columns]
    )
    g = _by_et_date(sm.select("timestamp", "spx_close", "gex", "dix"))
    g = g.with_columns(pl.Series("gex_pct", _prior_pct(g["gex"].fill_null(np.nan).to_numpy())))
    c = _by_et_date(cash.filter(pl.col("symbol") == "NDX").select("timestamp", pl.col("close").alias("ndx_close")))
    return {"vol": v.fill_nan(None), "gex": g.fill_nan(None), "cash": c}


def build(symbol: str, bars: pl.DataFrame, sources: dict[str, pl.DataFrame]) -> pl.DataFrame:
    iv_name, cash_name = SYMBOLS[symbol]
    s = session_stats(bars)
    first, last = s["date"].min(), s["date"].max()
    cash_days = sources["vol"].filter(pl.col("VIX").is_not_null()).select(pl.col("src_date").alias("date"))
    days = pl.concat([cash_days, pl.DataFrame({"date": [last]})]).unique().filter(
        pl.col("date").is_between(first, last)
    ).sort("date")
    s = days.join(s, on="date", how="left")

    s = s.with_columns(
        pl.lit(symbol).alias("symbol"),
        (pl.col("date") - timedelta(days=1)).alias("src_date"),
        (pl.col("rth_high") - pl.col("rth_low")).alias("rth_range"),
    ).with_columns(
        pl.col("rth_high").shift(1).alias("prev_high"),
        pl.col("rth_low").shift(1).alias("prev_low"),
        pl.col("rth_close").shift(1).alias("prev_close"),
        pl.col("rth_range").shift(1).alias("prev_range"),
        pl.col("rth_range").shift(1).rolling_mean(20).alias("range20"),
        pl.col("rth_close").shift(1).rolling_mean(20).alias("close20"),
    )
    # previous-day closes: as-of join on (date - 1 day), never the same day
    s = (
        s.join_asof(sources["vol"], left_on="src_date", right_on="src_date", strategy="backward")
        .join_asof(sources["gex"], left_on="src_date", right_on="src_date", strategy="backward")
        .join_asof(sources["cash"], left_on="src_date", right_on="src_date", strategy="backward")
    )
    index_close = pl.col("spx_close") if cash_name == "SPX" else pl.col("ndx_close")
    iv = pl.col(iv_name)
    em = pl.col("em")
    s = s.with_columns(
        iv.alias("iv"),
        pl.col(f"{iv_name}_pct").alias("iv_pct"),
        index_close.alias("index_close"),
        (index_close * iv / 100 / SQRT252).alias("em"),
        (pl.col("spx_close") * pl.col("VIX1D") / 100 / SQRT252 if symbol == "ES" else pl.lit(None, pl.Float64)).alias("em_1d"),
        (pl.col("VIX9D") / pl.col("VIX")).alias("term_9d"),
        (pl.col("VIX") / pl.col("VIX3M")).alias("term_3m"),
        pl.when(pl.col("gex") >= 0).then(pl.lit("positive")).when(pl.col("gex") < 0).then(pl.lit("negative")).alias("gex_regime"),
        pl.when(pl.col("prev_close") >= pl.col("close20")).then(pl.lit("up"))
        .when(pl.col("prev_close") < pl.col("close20")).then(pl.lit("down")).alias("trend20"),
        (pl.col("london_high") - pl.col("london_low")).alias("london_range"),
        (pl.col("london_close") - pl.col("london_open")).alias("london_move"),
        (pl.col("asia_high") - pl.col("asia_low")).alias("asia_range"),
        (pl.col("rth_open") - pl.col("prev_close")).alias("gap"),
        ((pl.col("rth_close") - pl.col("rth_low")) / pl.col("rth_range")).alias("rth_clv"),
        (pl.col("rth_bars").is_not_null() & (
            (pl.col("date") < last)
            | (pl.col("last_bar").dt.convert_time_zone(CT).dt.time() >= time(15, 59))
        )).alias("complete"),
    ).with_columns(
        pl.when(pl.col("iv_pct") >= 0.5).then(pl.lit("high")).when(pl.col("iv_pct") < 0.5).then(pl.lit("low")).alias("vol_regime"),
        (pl.col("london_range") / em).alias("london_range_em"),
        (pl.col("gap") / em).alias("gap_em"),
        (pl.col("rth_range") / em).alias("rth_range_em"),
        pl.when(pl.col("rth_open") > pl.col("prev_high")).then(pl.lit("above"))
        .when(pl.col("rth_open") < pl.col("prev_low")).then(pl.lit("below"))
        .when(pl.col("rth_open").is_not_null()).then(pl.lit("inside")).alias("open_location"),
        pl.when((pl.col("postib_high") > pl.col("ib_high")) & (pl.col("postib_low") < pl.col("ib_low"))).then(pl.lit("both"))
        .when(pl.col("postib_high") > pl.col("ib_high")).then(pl.lit("up"))
        .when(pl.col("postib_low") < pl.col("ib_low")).then(pl.lit("down"))
        .when(pl.col("postib_high").is_not_null()).then(pl.lit("none")).alias("ib_break"),
        pl.when(pl.col("gap") > 0).then(pl.col("rth_low") <= pl.col("prev_close"))
        .when(pl.col("gap") < 0).then(pl.col("rth_high") >= pl.col("prev_close")).alias("gap_filled"),
        (pl.col("moc_close") - pl.col("moc_open")).alias("moc_move"),
        (pl.col("moc_open") - pl.col("rth_open")).alias("pre_moc_move"),
    ).with_columns(
        (pl.col("vol_regime") + "_" + pl.col("trend20")).alias("quadrant"),
        pl.when(~pl.col("complete")).then(pl.lit(None, pl.String))
        .when((pl.col("rth_clv") >= 1 - TREND_CLV) & (pl.col("rth_range_em") >= TREND_RANGE_EM)).then(pl.lit("trend_up"))
        .when((pl.col("rth_clv") <= TREND_CLV) & (pl.col("rth_range_em") >= TREND_RANGE_EM)).then(pl.lit("trend_down"))
        .when(pl.col("rth_clv").is_not_null()).then(pl.lit("rotation")).alias("day_type"),
        pl.when((pl.col("moc_move") != 0) & (pl.col("pre_moc_move") != 0))
        .then(pl.col("moc_move").sign() == pl.col("pre_moc_move").sign()).alias("moc_with_day"),
    )
    # bar timestamp of the row: RTH open, or the last bar for today's partial row
    s = s.with_columns(
        pl.coalesce(
            "rth_start", "last_bar",
            pl.col("date").cast(pl.Datetime("us")).dt.replace_time_zone(CT).dt.offset_by("8h30m").dt.convert_time_zone("UTC"),
        ).alias("timestamp"),
        pl.col("date").dt.weekday().alias("weekday"),
    ).rename({c: c.lower() for c in VOL_COLS})

    cols = [
        "timestamp", "date", "symbol", "weekday", "complete",
        # before London
        "prev_high", "prev_low", "prev_close", "prev_range", "range20", "trend20",
        "vix", "vix9d", "vix1d", "vix3m", "vxn", "iv", "iv_pct", "term_9d", "term_3m",
        "index_close", "em", "em_1d",
        "gex", "dix", "gex_pct", "gex_regime", "vol_regime", "quadrant",
        "asia_high", "asia_low", "asia_range", "london_open",
        # before NY
        "london_high", "london_low", "london_close", "london_range", "london_range_em",
        "london_move", "london_volume", "london_delta",
        "on_high", "on_low", "rth_open", "gap", "gap_em", "open_location",
        # outcomes
        "ib_high", "ib_low", "ib_break",
        "rth_high", "rth_low", "rth_close", "rth_range", "rth_range_em", "rth_clv",
        "rth_volume", "rth_delta", "rth_bars", "day_type", "gap_filled",
        "moc_open", "moc_close", "moc_move", "pre_moc_move", "moc_with_day",
    ]
    return s.select(cols).with_columns(pl.col(pl.Float64).fill_nan(None))


def save(df: pl.DataFrame) -> None:
    """Overwrite gold/daily_context/1d (small: full rebuild every run)."""
    if df.is_empty():
        return
    write_deltalake(str(GOLD_ROOT / TABLE / TIMEFRAME), df.to_arrow(), mode="overwrite",
                    partition_by=["symbol"], schema_mode="overwrite")
