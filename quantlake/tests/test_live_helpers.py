import pytest

from helpers import utc
from quantlake.live import _closes_gold_bar, _current_tf_start


@pytest.mark.parametrize("minute, expected", [
    (0, False), (3, False), (4, True), (5, False), (9, True),
])
def test_closes_gold_bar_5m(minute, expected):
    # ts is the open time of a 1m bar; the 09:04 bar closes the 09:00 5m bar
    assert _closes_gold_bar(utc(2024, 1, 2, 9, minute), "5m") is expected


def test_closes_gold_bar_1m_always_closes():
    assert _closes_gold_bar(utc(2024, 1, 2, 9, 3), "1m")


def test_closes_gold_bar_1h_on_last_minute_only():
    assert _closes_gold_bar(utc(2024, 1, 2, 9, 59), "1h")
    assert not _closes_gold_bar(utc(2024, 1, 2, 9, 58), "1h")


def test_closes_gold_bar_1d_at_midnight_utc():
    assert _closes_gold_bar(utc(2024, 1, 2, 23, 59), "1d")
    assert not _closes_gold_bar(utc(2024, 1, 2, 0, 0), "1d")


@pytest.mark.parametrize("ts, tf, expected", [
    (utc(2024, 1, 2, 9, 7, 45), "5m",  utc(2024, 1, 2, 9, 5)),
    (utc(2024, 1, 2, 9, 5),     "5m",  utc(2024, 1, 2, 9, 5)),
    (utc(2024, 1, 2, 9, 59),    "1h",  utc(2024, 1, 2, 9, 0)),
    (utc(2024, 1, 2, 9, 59),    "4h",  utc(2024, 1, 2, 8, 0)),
    (utc(2024, 1, 2, 23, 59),   "1d",  utc(2024, 1, 2)),
])
def test_current_tf_start(ts, tf, expected):
    assert _current_tf_start(ts, tf) == expected
