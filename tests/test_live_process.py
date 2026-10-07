"""_process_df / gap-fill behaviour of the live runner (no I/O, no network)."""
from datetime import datetime, timedelta

import polars as pl

import quantlake.live as live
from helpers import utc

SYMBOL = "BTCUSDT"


def _ws_bars(*timestamps: datetime) -> pl.DataFrame:
    """1m bars shaped like live._bar_to_df output; volume = minute of the hour + 1."""
    ts = list(timestamps)
    return pl.DataFrame({
        "timestamp":       pl.Series(ts, dtype=pl.Datetime("us", "UTC")),
        "timestamp_close": pl.Series([t + timedelta(seconds=59, milliseconds=999) for t in ts],
                                     dtype=pl.Datetime("us", "UTC")),
        "open":   [100.0 + t.minute for t in ts],
        "high":   [100.5 + t.minute for t in ts],
        "low":    [99.5 + t.minute for t in ts],
        "close":  [100.25 + t.minute for t in ts],
        "volume": [float(t.minute + 1) for t in ts],
        "ingested_at": pl.Series(ts, dtype=pl.Datetime("us", "UTC")),
    })


def _minutes(start: datetime, *offsets: int) -> list[datetime]:
    return [start + timedelta(minutes=m) for m in offsets]


class _EchoPipeline:
    """Minimal stand-in for an Oryon FeaturePipeline: feature = bar close."""

    def input_names(self):
        return ["close"]

    def output_names(self):
        return ["f_close"]

    def update(self, inputs):
        return [inputs[0]]


class _Runner:
    """Holds the buffers live.run would own and feeds bars one at a time."""

    def __init__(self, timeframe: str = "5m"):
        self.timeframe = timeframe
        self.pipelines = {SYMBOL: _EchoPipeline()}
        self.bronze = {SYMBOL: []}
        self.silver = {SYMBOL: []}
        self.gold_buf = {SYMBOL: []}
        self.gold_out = {SYMBOL: []}

    def feed(self, *timestamps: datetime) -> None:
        for ts in timestamps:
            live._process_df(
                _ws_bars(ts), SYMBOL, self.timeframe,
                self.bronze, self.silver, self.gold_buf, self.gold_out,
                pipelines=self.pipelines, transform_gold=None, from_live=True,
            )

    @property
    def gold(self) -> pl.DataFrame:
        return pl.concat(self.gold_out[SYMBOL]) if self.gold_out[SYMBOL] else pl.DataFrame()


def test_complete_windows_emit_one_bar_each():
    r = _Runner()
    r.feed(*_minutes(utc(2024, 1, 2, 9, 0), *range(10)))
    assert r.gold["timestamp"].to_list() == [utc(2024, 1, 2, 9, 0), utc(2024, 1, 2, 9, 5)]
    assert r.gold["volume"].to_list() == [1 + 2 + 3 + 4 + 5, 6 + 7 + 8 + 9 + 10]
    assert r.gold["f_close"].to_list() == r.gold["close"].to_list()
    assert r.gold_buf[SYMBOL] == []


def test_missing_closing_minute_does_not_merge_windows():
    # 09:04 never arrives: the 09:00 bar must still be emitted on its own
    # once the first bar of the next window shows up.
    r = _Runner()
    r.feed(*_minutes(utc(2024, 1, 2, 9, 0), 0, 1, 2, 3, 5, 6, 7, 8, 9))
    g = r.gold
    assert g["timestamp"].to_list() == [utc(2024, 1, 2, 9, 0), utc(2024, 1, 2, 9, 5)]
    assert g["volume"].to_list() == [1 + 2 + 3 + 4, 6 + 7 + 8 + 9 + 10]
    assert g["close"].to_list() == [103.25, 109.25]
    # every bar went through the feature pipeline with its own inputs
    assert g["f_close"].to_list() == g["close"].to_list()


def test_missing_closing_minute_bar_is_emitted_before_the_next_window_starts():
    r = _Runner()
    r.feed(*_minutes(utc(2024, 1, 2, 9, 0), 0, 1, 2, 3, 5))
    assert r.gold["timestamp"].to_list() == [utc(2024, 1, 2, 9, 0)]
    # the 09:05 bar is still being built
    assert pl.concat(r.gold_buf[SYMBOL])["timestamp"].to_list() == [utc(2024, 1, 2, 9, 5)]


def test_whole_window_missing_is_skipped():
    # nothing between 09:04 and 09:11 → 09:05 bar does not exist
    r = _Runner()
    r.feed(*_minutes(utc(2024, 1, 2, 9, 0), 0, 1, 2, 3, 11, 12, 13, 14))
    assert r.gold["timestamp"].to_list() == [utc(2024, 1, 2, 9, 0), utc(2024, 1, 2, 9, 10)]
    assert r.gold["volume"].to_list() == [1 + 2 + 3 + 4, 12 + 13 + 14 + 15]
    assert r.gold["f_close"].to_list() == r.gold["close"].to_list()


class _FakeRest:
    """REST connector that, like Binance/Capital, includes `end` and the open candle."""

    TABLE_NAME = "fake"

    def __init__(self, available: list[datetime]):
        self.available = available

    def fetch(self, symbol, start, end):
        return _ws_bars(*[t for t in self.available if start <= t <= end])


def test_fetch_gap_excludes_end_bar_and_open_candle():
    rest = _FakeRest(_minutes(utc(2024, 1, 2, 9, 0), *range(10)))
    # reconnect: WS just delivered 09:06, gap is 09:03..09:05
    out = live._fetch_gap(rest, SYMBOL, utc(2024, 1, 2, 9, 3), utc(2024, 1, 2, 9, 6))
    assert out["timestamp"].to_list() == _minutes(utc(2024, 1, 2, 9, 0), 3, 4, 5)
    # startup at 09:07:30: the 09:07 candle is still open
    out = live._fetch_gap(rest, SYMBOL, utc(2024, 1, 2, 9, 5), utc(2024, 1, 2, 9, 7, 30))
    assert out["timestamp"].to_list() == _minutes(utc(2024, 1, 2, 9, 0), 5, 6)


def test_fetch_gap_empty():
    rest = _FakeRest([])
    assert live._fetch_gap(rest, SYMBOL, utc(2024, 1, 2, 9, 3), utc(2024, 1, 2, 9, 6)).is_empty()
