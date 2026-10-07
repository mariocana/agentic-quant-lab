from datetime import datetime, timezone

import polars as pl
import pytest

from alphaquant.instruments import AlwaysOpen, make_session

UTC = timezone.utc


def ts(*values: datetime) -> pl.Series:
    return pl.Series("ts", list(values), dtype=pl.Datetime("us", "UTC"))


@pytest.fixture(scope="module")
def cme():
    return make_session("CMES", "16:00", "17:00")


def test_always_open():
    mask = AlwaysOpen().open_mask(ts(datetime(2026, 1, 3, 12, tzinfo=UTC), datetime(2026, 1, 4, 3, tzinfo=UTC)))
    assert mask.to_list() == [True, True]


def test_cme_regular_hours_and_daily_break(cme):
    mask = cme.open_mask(ts(
        datetime(2026, 3, 10, 14, 0, tzinfo=UTC),   # 09:00 CDT, open
        datetime(2026, 3, 10, 21, 30, tzinfo=UTC),  # 16:30 CDT, maintenance break
        datetime(2026, 3, 10, 22, 0, tzinfo=UTC),   # 17:00 CDT, reopened
        datetime(2026, 3, 10, 20, 59, tzinfo=UTC),  # 15:59 CDT, last minute before the break
    ))
    assert mask.to_list() == [True, False, True, True]


def test_cme_weekend_and_dst_sunday_open(cme):
    mask = cme.open_mask(ts(
        datetime(2026, 3, 7, 15, 0, tzinfo=UTC),    # Saturday
        datetime(2026, 3, 8, 21, 59, tzinfo=UTC),   # Sunday 16:59 CDT, still closed
        datetime(2026, 3, 8, 22, 0, tzinfo=UTC),    # Sunday 17:00 CDT, open (DST already started)
    ))
    assert mask.to_list() == [False, False, True]


def test_cme_holidays_and_early_close(cme):
    mask = cme.open_mask(ts(
        datetime(2025, 12, 25, 16, 0, tzinfo=UTC),  # Christmas
        datetime(2025, 11, 27, 17, 30, tzinfo=UTC), # Thanksgiving 11:30 CST, before the early close
        datetime(2025, 11, 27, 19, 0, tzinfo=UTC),  # Thanksgiving 13:00 CST, after the early close
    ))
    assert mask.to_list() == [False, True, False]


def test_mask_keeps_input_order(cme):
    values = [datetime(2026, 3, 10, 21, 30, tzinfo=UTC), datetime(2026, 3, 7, 15, tzinfo=UTC), datetime(2026, 3, 10, 14, tzinfo=UTC)]
    assert cme.open_mask(ts(*values)).to_list() == [False, False, True]


def test_make_session_validation():
    assert isinstance(make_session("24/7"), AlwaysOpen)
    with pytest.raises(ValueError, match="Unknown calendar"):
        make_session("NOPE")
    with pytest.raises(ValueError, match="both"):
        make_session("CMES", "16:00", None)
