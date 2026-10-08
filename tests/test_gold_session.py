"""Session-anchored timeframes ('1d_cme', '4h_cme'): CME day opens 17:00 America/Chicago."""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import polars as pl
import pytest

from helpers import minute_bars, utc
from quantlake.gold.ohlcv import bar_close, bar_open, parse_timeframe, resample

CHI = ZoneInfo("America/Chicago")


def chi(*args) -> datetime:
    return datetime(*args, tzinfo=CHI).astimezone(timezone.utc)


def _frame(*ts: datetime) -> pl.DataFrame:
    return pl.DataFrame({"timestamp": pl.Series(list(ts), dtype=pl.Datetime("us", "UTC"))})


def test_parse_timeframe():
    assert parse_timeframe("4h") == ("4h", None)
    assert parse_timeframe("1d_cme") == ("1d", "cme")
    for bad in ("1w", "1d_lse", "1d_", "cme"):
        with pytest.raises(ValueError):
            parse_timeframe(bad)


def test_1d_cme_session_runs_17_to_17_chicago():
    ts = [chi(2026, 10, 1, 16, 59), chi(2026, 10, 1, 17, 0), chi(2026, 10, 2, 15, 59)]
    out = _frame(*ts).select(bar_open("1d_cme").alias("o")).with_columns(bar_close("1d_cme", "o").alias("c"))
    assert out["o"].to_list() == [chi(2026, 9, 30, 17), chi(2026, 10, 1, 17), chi(2026, 10, 1, 17)]
    assert out["c"].to_list() == [chi(2026, 10, 1, 17), chi(2026, 10, 2, 17), chi(2026, 10, 2, 17)]
    assert chi(2026, 10, 1, 17) == utc(2026, 10, 1, 22)  # CDT = UTC-5


def test_sunday_open_labels_mondays_session():
    # Sunday 17:00 CT reopen after the weekend
    out = _frame(chi(2026, 10, 4, 17, 0)).select(bar_open("1d_cme"))
    assert out.item() == chi(2026, 10, 4, 17)


def test_dst_fall_back_session_is_25_hours():
    # 2026-11-01: 02:00 CDT → 01:00 CST
    o = _frame(chi(2026, 11, 1, 10, 0)).select(bar_open("1d_cme").alias("o"))
    c = o.select(bar_close("1d_cme", "o")).item()
    assert o.item() == chi(2026, 10, 31, 17) == utc(2026, 10, 31, 22)
    assert c == chi(2026, 11, 1, 17) == utc(2026, 11, 1, 23)
    assert c - o.item() == timedelta(hours=25)


def test_dst_spring_forward_session_is_23_hours():
    # 2026-03-08: 02:00 CST → 03:00 CDT
    o = _frame(chi(2026, 3, 8, 10, 0)).select(bar_open("1d_cme").alias("o"))
    c = o.select(bar_close("1d_cme", "o")).item()
    assert o.item() == utc(2026, 3, 7, 23) and c == utc(2026, 3, 8, 22)
    assert c - o.item() == timedelta(hours=23)


def test_4h_cme_windows_open_at_17_21_01_05_09_13_chicago():
    ts = [chi(2026, 10, 1, 17) + timedelta(hours=h, minutes=30) for h in range(24)]
    opens = _frame(*ts).select(bar_open("4h_cme")).to_series().unique().sort()
    hours = [o.astimezone(CHI).hour for o in opens.to_list()]
    assert hours == [17, 21, 1, 5, 9, 13]


def test_utc_timeframes_unchanged():
    out = _frame(utc(2026, 10, 1, 23, 30)).select(bar_open("1d").alias("o"), bar_open("4h").alias("h"))
    assert out.row(0) == (utc(2026, 10, 1), utc(2026, 10, 1, 20))


def test_resample_1d_cme_aggregates_one_session():
    # 16:00 → 18:59 Chicago on Thu: 16:00-16:59 belongs to Wed's session, 17:00+ to Thu's
    df = minute_bars(chi(2026, 10, 1, 16, 0), 180, symbol="ES", base=0.0)
    out = resample(df, "1d_cme")
    assert out["timestamp"].to_list() == [chi(2026, 9, 30, 17), chi(2026, 10, 1, 17)]
    assert out["open"].to_list() == [0.0, 60.0]
    assert out["close"].to_list() == [59.25, 179.25]
    assert out["volume"].to_list() == [sum(range(1, 61)), sum(range(61, 181))]
    assert out.schema["timestamp"] == pl.Datetime("us", "UTC")
    assert out.columns == resample(df, "1d").columns


def test_resample_session_keeps_symbols_apart():
    start = chi(2026, 10, 1, 17, 0)
    df = pl.concat([minute_bars(start, 3, symbol="ES"), minute_bars(start, 3, symbol="NQ", base=10.0)])
    out = resample(df, "1d_cme").sort("symbol")
    assert out["symbol"].to_list() == ["ES", "NQ"]
    assert out["open"].to_list() == [100.0, 10.0]
