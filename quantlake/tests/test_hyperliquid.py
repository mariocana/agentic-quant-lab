"""Hyperliquid history. The two things that would quietly ruin a backtest: storing
a bar that was still open, and a universe that knows the future."""
from datetime import date, datetime, timezone

import polars as pl

from quantlake.bronze.connectors import hyperliquid as hl

H = 3_600_000
T0 = int(datetime(2026, 11, 9, 0, tzinfo=timezone.utc).timestamp() * 1000)


def _bar(t, c="100"):
    return {"t": t, "T": t + H - 1, "s": "BTC", "i": "1h", "o": "99", "h": "101", "l": "98", "c": c, "v": "12.5", "n": 7}


def test_the_open_bar_is_never_stored():
    now = datetime(2026, 11, 9, 2, 30, tzinfo=timezone.utc)          # the 02:00 bar is still open
    df = hl.parse_candles([_bar(T0), _bar(T0 + H), _bar(T0 + 2 * H)], now=now)
    assert df["timestamp"].dt.hour().to_list() == [0, 1]
    assert df.schema == pl.Schema(hl.OHLCV_SCHEMA)


def test_funding_parses_and_dedups():
    rows = [{"coin": "BTC", "fundingRate": "0.0000125", "premium": "-0.0003", "time": T0},
            {"coin": "BTC", "fundingRate": "0.0000130", "premium": None, "time": T0 + H},
            {"coin": "BTC", "fundingRate": "0.0000130", "premium": None, "time": T0 + H}]
    df = hl.parse_funding(rows)
    assert df.height == 2 and df["funding_rate"].to_list() == [0.0000125, 0.000013]
    assert df["premium"].to_list() == [-0.0003, None]


class FakeApi:
    """candleSnapshot returns at most `cap` bars, the latest in the window, like the API."""

    def __init__(self, n_bars, cap=5000):
        self.bars = [_bar(T0 + i * H) for i in range(n_bars)]
        self.cap, self.calls = cap, 0

    def post(self, body):
        self.calls += 1
        r = body["req"]
        inside = [b for b in self.bars if r["startTime"] <= b["t"] <= r["endTime"]]
        return inside[: self.cap]


def test_ohlcv_walks_the_window_forward_past_the_cap():
    api = FakeApi(n_bars=9000)
    c = hl.HyperliquidOHLCVConnector("1h", client=api)
    end = datetime.fromtimestamp((T0 + 9000 * H) / 1000, timezone.utc)
    df = c.fetch("BTC", datetime.fromtimestamp(T0 / 1000, timezone.utc), end)
    assert df.height == 9000 and api.calls >= 2
    assert c.TABLE_NAME == "hyperliquid_ohlcv_1h"


def _listings():
    first_last = pl.DataFrame({
        "symbol": ["BTC", "MATIC", "xyz:TSLA"],
        "first_bar": [date(2020, 8, 19), date(2020, 10, 22), date(2025, 11, 13)],
        "last_bar": [date(2026, 11, 8), date(2024, 9, 9), date(2026, 11, 8)],
    })
    uni = [{"symbol": "BTC", "dex": "main", "is_delisted": False},
           {"symbol": "MATIC", "dex": "main", "is_delisted": True},
           {"symbol": "xyz:TSLA", "dex": "xyz", "is_delisted": False},
           {"symbol": "flx:DEAD", "dex": "flx", "is_delisted": True}]      # never traded
    return hl.listings(first_last, uni)


def test_listings_carry_the_delisting_date():
    df = _listings()
    matic = df.filter(pl.col("symbol") == "MATIC").row(0, named=True)
    assert matic["delisted_after"] == date(2024, 9, 9)
    assert df.filter(pl.col("symbol") == "BTC")["delisted_after"].item() is None
    assert df.filter(pl.col("symbol") == "flx:DEAD")["first_bar"].item() is None


def test_the_universe_on_a_past_date_does_not_know_the_future():
    df = _listings()
    assert hl.universe_on(df, date(2023, 1, 1)) == ["BTC", "MATIC"]           # TSLA not yet, MATIC alive
    assert hl.universe_on(df, date(2026, 1, 1)) == ["BTC", "xyz:TSLA"]        # MATIC gone
    assert "flx:DEAD" not in hl.universe_on(df, date(2026, 11, 8))


def test_funding_stops_where_the_market_stopped():
    """After delisting the API answers with zero funding forever; those rows are
    not carry, they are the absence of a market."""
    from datetime import timedelta
    now = datetime(2026, 11, 9, tzinfo=timezone.utc)
    last = datetime(2024, 9, 9, tzinfo=timezone.utc)
    assert hl.funding_end(now, False, last) == now
    assert hl.funding_end(now, True, last) == last + timedelta(days=1)
    assert hl.funding_end(now, True, None) is None          # never traded: no funding at all
