"""Silver for Hyperliquid bars: bronze plus whether the underlying market was open.

Three columns are added to every bar:

  calendar               the market the perp follows (reference/hyperliquid_underlying)
  underlying_open_frac   share of the bar during which that market was open, 0..1
  underlying_market_open true only if it was open for the whole bar

Null, not false, when the calendar is unknown: a strategy must be able to tell
"closed" from "we never mapped this perp".

The fraction is computed once per calendar on an hourly grid, then joined: a
1h bar takes its hour, a 1d bar the mean of its 24 hours.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import polars as pl

from quantlake.reference.hyperliquid_underlying import calendar_for

HOUR = timedelta(hours=1)
_XC_CODES = {"XNYS", "XKRX", "XTKS", "XHKG", "XSHG", "XBOM"}
_NY, _CHI = ZoneInfo("America/New_York"), ZoneInfo("America/Chicago")


def _xc_intervals(code: str, start: datetime, end: datetime) -> list[tuple[datetime, datetime]]:
    """Sessions of an exchange calendar, split at the lunch break where there is one."""
    import exchange_calendars as xc

    cal = xc.get_calendar(code, start=(start - timedelta(days=7)).strftime("%Y-%m-%d"),
                          end=(end + timedelta(days=7)).strftime("%Y-%m-%d"))
    out = []
    for _, s in cal.schedule.iterrows():
        o, c = s["open"].to_pydatetime(), s["close"].to_pydatetime()
        bs, be = s.get("break_start"), s.get("break_end")
        if bs is not None and str(bs) != "NaT":
            out += [(o, bs.to_pydatetime()), (be.to_pydatetime(), c)]
        else:
            out.append((o, c))
    return out


def _cme_intervals(start: datetime, end: datetime) -> list[tuple[datetime, datetime]]:
    """Globex: each trading day runs 17:00 Chicago the evening before to 16:00.
    Holidays are taken from exchange_calendars' CMES sessions; its own session
    closes at 17:00 and misses the daily halt, so the hours are rebuilt here."""
    import exchange_calendars as xc

    cal = xc.get_calendar("CMES", start=(start - timedelta(days=7)).strftime("%Y-%m-%d"),
                          end=(end + timedelta(days=7)).strftime("%Y-%m-%d"))
    out = []
    for day in cal.sessions:
        d = day.date()
        close = datetime(d.year, d.month, d.day, 16, tzinfo=_CHI)
        prev = d - timedelta(days=1)          # Monday's session opens Sunday evening
        open_ = datetime(prev.year, prev.month, prev.day, 17, tzinfo=_CHI)
        out.append((open_.astimezone(timezone.utc), close.astimezone(timezone.utc)))
    return out


def _fx_intervals(start: datetime, end: datetime) -> list[tuple[datetime, datetime]]:
    """Sunday 17:00 to Friday 17:00 New York, every week."""
    out = []
    d = (start - timedelta(days=start.weekday() + 1)).date()        # the Sunday before
    while d <= end.date():
        o = datetime(d.year, d.month, d.day, 17, tzinfo=_NY)
        f = d + timedelta(days=5)
        c = datetime(f.year, f.month, f.day, 17, tzinfo=_NY)
        out.append((o.astimezone(timezone.utc), c.astimezone(timezone.utc)))
        d += timedelta(days=7)
    return out


def intervals(calendar: str, start: datetime, end: datetime) -> list[tuple[datetime, datetime]]:
    if calendar == "always":
        return [(start, end)]
    if calendar == "none":
        return []
    if calendar == "CME":
        return _cme_intervals(start, end)
    if calendar == "FX":
        return _fx_intervals(start, end)
    if calendar in _XC_CODES:
        return _xc_intervals(calendar, start, end)
    raise ValueError(f"unknown calendar {calendar!r}")


def hourly_open_fraction(calendar: str, start: datetime, end: datetime) -> pl.DataFrame:
    """One row per UTC hour in [start, end): the share of it the market was open."""
    start = start.replace(minute=0, second=0, microsecond=0)
    hours = int((end - start) / HOUR) + 1
    frac = [0.0] * hours
    for o, c in intervals(calendar, start, end):
        o, c = max(o, start), min(c, start + hours * HOUR)
        while o < c:
            i = int((o - start) / HOUR)
            h_end = start + (i + 1) * HOUR
            frac[i] += (min(c, h_end) - o) / HOUR
            o = h_end
    return pl.DataFrame({
        "timestamp": pl.datetime_range(start, start + (hours - 1) * HOUR, "1h", time_zone="UTC", eager=True),
        "underlying_open_frac": [min(f, 1.0) for f in frac],
    }).with_columns(pl.col("timestamp").cast(pl.Datetime("us", "UTC")))


def add_underlying(bars: pl.DataFrame, listings: pl.DataFrame, interval: str) -> pl.DataFrame:
    """bars: bronze rows (symbol, timestamp, ...). listings: symbol, dex."""
    if bars.is_empty():
        return bars
    dex = dict(zip(listings["symbol"], listings["dex"]))
    bars = bars.with_columns(
        pl.col("symbol").map_elements(lambda s: calendar_for(s, dex.get(s, "")), return_dtype=pl.String)
        .alias("calendar"))
    start, end = bars["timestamp"].min(), bars["timestamp"].max() + timedelta(days=1)
    grids = []
    for cal in bars["calendar"].drop_nulls().unique().to_list():
        g = hourly_open_fraction(cal, start, end).with_columns(pl.lit(cal).alias("calendar"))
        if interval == "1d":
            g = (g.group_by(pl.col("timestamp").dt.truncate("1d"), "calendar")
                 .agg(pl.col("underlying_open_frac").mean()))
        grids.append(g)
    if not grids:
        return bars.with_columns(pl.lit(None, pl.Float64).alias("underlying_open_frac"),
                                 pl.lit(None, pl.Boolean).alias("underlying_market_open"))
    grid = pl.concat(grids).select("calendar", "timestamp", "underlying_open_frac")
    return (bars.join(grid, on=["calendar", "timestamp"], how="left")
            .with_columns((pl.col("underlying_open_frac") >= 0.999999).alias("underlying_market_open")))
