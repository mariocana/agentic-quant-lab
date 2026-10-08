"""Market hours: when an instrument can trade.

Two calendars cover crypto and CME futures:

  AlwaysOpen       24/7 (crypto)
  ExchangeSession  an exchange_calendars calendar (holidays, early closes,
                   DST) plus an optional daily break in local time.
                   exchange_calendars' CME calendar ("CMES") runs
                   17:00 -> 17:00 Chicago and does not model the
                   16:00-17:00 maintenance halt, so the break is added here.
"""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from functools import lru_cache
from typing import Protocol

import exchange_calendars as xc
import polars as pl

ALWAYS_OPEN = "24/7"


class SessionCalendar(Protocol):
    name: str

    def open_mask(self, ts: pl.Series) -> pl.Series:
        """True where the market is open at each UTC timestamp, same order as ts."""
        ...


@dataclass(frozen=True)
class AlwaysOpen:
    name: str = ALWAYS_OPEN

    def open_mask(self, ts: pl.Series) -> pl.Series:
        return pl.Series("open", [True] * len(ts), dtype=pl.Boolean)


@dataclass(frozen=True)
class ExchangeSession:
    calendar: str                   # exchange_calendars code, e.g. "CMES"
    break_start: time | None = None  # daily break, calendar local time
    break_end: time | None = None

    @property
    def name(self) -> str:
        return self.calendar

    @property
    def tz(self) -> str:
        return str(xc.get_calendar(self.calendar).tz)

    def open_mask(self, ts: pl.Series) -> pl.Series:
        if len(ts) == 0:
            return pl.Series("open", [], dtype=pl.Boolean)

        ts = ts.cast(pl.Datetime("us", "UTC"))
        sessions = _sessions(self.calendar, ts.min().date(), ts.max().date())

        # join_asof needs sorted keys: remember the input order and restore it
        frame = (
            pl.DataFrame({"ts": ts})
            .with_row_index("pos")
            .sort("ts")
            .join_asof(sessions, left_on="ts", right_on="open", strategy="backward")
        )
        in_session = (pl.col("ts") >= pl.col("open")) & (pl.col("ts") < pl.col("close"))
        mask = in_session.fill_null(False) & ~self._in_break()
        return frame.sort("pos").select(mask.alias("open")).to_series()

    def session_opens(self, first: datetime, last: datetime) -> pl.Series:
        """UTC open of every session that opens in [first, last]."""
        opens = _schedule(self.calendar, first.year, last.year)["open"]
        return opens.filter(opens.is_between(first, last)).alias("timestamp")

    def _in_break(self) -> pl.Expr:
        if self.break_start is None or self.break_end is None:
            return pl.lit(False)
        local = pl.col("ts").dt.convert_time_zone(self.tz).dt.time()
        if self.break_start < self.break_end:
            return (local >= self.break_start) & (local < self.break_end)
        return (local >= self.break_start) | (local < self.break_end)  # break across midnight


def make_session(calendar: str, break_start: str | None = None, break_end: str | None = None) -> SessionCalendar:
    """Build a calendar from the reference-table fields ('24/7' or an exchange_calendars code)."""
    if calendar == ALWAYS_OPEN:
        return AlwaysOpen()
    if calendar not in xc.get_calendar_names():
        raise ValueError(f"Unknown calendar {calendar!r}: use '{ALWAYS_OPEN}' or an exchange_calendars code (e.g. 'CMES')")
    if (break_start is None) != (break_end is None):
        raise ValueError(f"{calendar}: set both break_start and break_end, or neither")
    return ExchangeSession(
        calendar=calendar,
        break_start=_parse_hhmm(break_start),
        break_end=_parse_hhmm(break_end),
    )


def _parse_hhmm(value: str | None) -> time | None:
    if value is None:
        return None
    return time.fromisoformat(value)


def _sessions(code: str, first: date, last: date) -> pl.DataFrame:
    """Session open/close in UTC covering [first, last], one row per session."""
    schedule = _schedule(code, first.year, last.year)
    return schedule.filter(
        (pl.col("open").dt.date() <= last) & (pl.col("close").dt.date() >= first - timedelta(days=1))
    )


@lru_cache(maxsize=16)
def _schedule(code: str, first_year: int, last_year: int) -> pl.DataFrame:
    # Calendars are slow to build: cache by whole years
    cal = xc.get_calendar(code, start=f"{first_year}-01-01", end=f"{last_year}-12-31")
    sched = cal.schedule[["open", "close"]].reset_index(drop=True)
    return pl.from_pandas(sched).with_columns(
        pl.col("open").cast(pl.Datetime("us", "UTC")),
        pl.col("close").cast(pl.Datetime("us", "UTC")),
    ).sort("open")
