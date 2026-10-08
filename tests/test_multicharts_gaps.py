from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import polars as pl

from quantlake.silver.gaps import early_fridays, find_gaps, recurring_gaps, summarize

CHI = ZoneInfo("America/Chicago")


def chi(*a) -> datetime:
    return datetime(*a, tzinfo=CHI).astimezone(timezone.utc)


def _bars(minutes: list[datetime], volume=lambda t: 10, ticks=lambda t: 5, close=lambda t: 1.0) -> pl.DataFrame:
    return pl.DataFrame({
        "timestamp": pl.Series(minutes, dtype=pl.Datetime("us", "UTC")),
        "open": [close(t) for t in minutes], "close": [close(t) for t in minutes],
        "volume": [float(volume(t)) for t in minutes], "ticks": [float(ticks(t)) for t in minutes],
    })


# ── single holes ───────────────────────────────────────────────────────────

def test_overnight_no_trade_gap_vs_rth_lost_bar():
    night = [chi(2016, 3, 2, 1, 0) + timedelta(minutes=i) for i in range(60)]
    day = [chi(2016, 3, 2, 10, 0) + timedelta(minutes=i) for i in range(60)]
    drop = {chi(2016, 3, 2, 1, 30), chi(2016, 3, 2, 1, 31), chi(2016, 3, 2, 10, 20)}
    minutes = [t for t in night + day if t not in drop]
    thin = {chi(2016, 3, 2, 1, 29), chi(2016, 3, 2, 1, 32)}
    df = _bars(
        minutes,
        volume=lambda t: 1 if t in thin else (20 if t.astimezone(CHI).hour < 5 else 500),
        ticks=lambda t: 1 if t in thin else 10,
        close=lambda t: 2000.0 if t.astimezone(CHI).hour < 5 else 2000.0 + (t.minute >= 21) * 2.0,
    )
    gaps = find_gaps(df).sort("before")
    assert gaps["missing"].to_list() == [2, 1]
    night_gap, day_gap = gaps.row(0, named=True), gaps.row(1, named=True)
    assert not night_gap["rth"] and night_gap["jump_ticks"] == 0 and night_gap["rel_vol_before"] < 0.1
    assert day_gap["rth"] and day_gap["jump_ticks"] == 8.0 and day_gap["hour_ct"] == 10

    s = summarize(gaps)
    assert s["by_year"].row(0, named=True)["missing_min"] == 3
    assert s["rth_with_jumps"].height == 1


def test_daily_halt_and_long_gaps_are_not_counted():
    minutes = [chi(2016, 3, 2, 15, 55), chi(2016, 3, 2, 15, 56), chi(2016, 3, 2, 15, 58), chi(2016, 3, 2, 15, 59),
               chi(2016, 3, 2, 17, 0), chi(2016, 3, 2, 17, 1)]
    assert find_gaps(_bars(minutes))["missing"].to_list() == [1]  # 15:57; the 60-min halt is excluded


# ── session-template rules ─────────────────────────────────────────────────

def _month(year: int, month: int, cut_1515: bool, friday_end: time, scatter: bool = False) -> pl.DataFrame:
    """Day sessions 08:00-15:59 CT on weekdays (enough to exercise the rules)."""
    minutes = []
    d = date(year, month, 1)
    while d.month == month:
        if d.weekday() < 5:
            for i in range(8 * 60):
                t = datetime.combine(d, time(8, 0), tzinfo=CHI) + timedelta(minutes=i)
                lt = t.timetz()
                if d.weekday() == 4 and lt.replace(tzinfo=None) > friday_end:
                    continue
                if cut_1515 and d.weekday() < 4 and time(15, 15) <= lt.replace(tzinfo=None) < time(15, 30):
                    continue
                if scatter and t.minute == (d.day * 7) % 60 and t.hour == 3 + d.day % 5 + 6:
                    continue  # one hole per day, never at the same time
                minutes.append(t.astimezone(timezone.utc))
        d += timedelta(days=1)
    return _bars(minutes)


def test_recurring_window_and_early_fridays_are_flagged():
    bars = _month(2021, 7, cut_1515=True, friday_end=time(15, 14))
    rec = recurring_gaps(bars)
    assert rec.select("month", "window_start_ct", "window_end_ct").rows() == [("2021-07", "15:15", "15:29")]
    row = rec.row(0, named=True)
    assert row["days_missing"] == 17 and row["trading_days"] == 22  # Mon-Thu of July 2021
    fri = early_fridays(bars)
    assert fri.rows() == [("2021-07", 5, 5, 1.0, "15:14")]


def test_correct_template_and_scattered_holes_pass():
    bars = _month(2021, 7, cut_1515=False, friday_end=time(15, 59), scatter=True)
    assert find_gaps(bars).height > 0  # there are holes...
    assert recurring_gaps(bars).is_empty()  # ...but never the same window
    assert early_fridays(bars).is_empty()
