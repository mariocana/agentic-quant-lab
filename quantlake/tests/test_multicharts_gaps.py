import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import polars as pl

CHI = ZoneInfo("America/Chicago")
path = Path(__file__).parents[1] / "applications" / "diagnostics" / "multicharts_gaps.py"
spec = importlib.util.spec_from_file_location("multicharts_gaps", path)
mg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mg)


def chi(*a) -> datetime:
    return datetime(*a, tzinfo=CHI).astimezone(timezone.utc)


def _bars(minutes: list[datetime], volume, ticks, close) -> pl.DataFrame:
    return pl.DataFrame({
        "timestamp": pl.Series(minutes, dtype=pl.Datetime("us", "UTC")),
        "open": [close(t) for t in minutes], "close": [close(t) for t in minutes],
        "volume": [float(volume(t)) for t in minutes], "ticks": [float(ticks(t)) for t in minutes],
    })


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
    gaps = mg.find_gaps(df).sort("before")
    assert gaps["missing"].to_list() == [2, 1]
    night_gap, day_gap = gaps.row(0, named=True), gaps.row(1, named=True)
    assert not night_gap["rth"] and night_gap["jump_ticks"] == 0 and night_gap["rel_vol_before"] < 0.1
    assert day_gap["rth"] and day_gap["jump_ticks"] == 8.0 and day_gap["hour_ct"] == 10

    s = mg.summarize(gaps)
    assert s["by_year"].row(0, named=True)["missing_min"] == 3
    assert s["rth_with_jumps"].height == 1


def test_daily_halt_and_long_gaps_are_not_counted():
    before_halt = [chi(2016, 3, 2, 15, 58), chi(2016, 3, 2, 15, 59)]
    after_halt = [chi(2016, 3, 2, 17, 0), chi(2016, 3, 2, 17, 1)]
    early = [chi(2016, 3, 2, 15, 55), chi(2016, 3, 2, 15, 56)]  # gap 15:57 only, then 15:58
    df = _bars(early + before_halt + after_halt, volume=lambda t: 10, ticks=lambda t: 5, close=lambda t: 1.0)
    gaps = mg.find_gaps(df)
    assert gaps["missing"].to_list() == [1]  # 15:57; the halt (60 min) is excluded
