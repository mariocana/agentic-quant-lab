"""Was the underlying open? Checked against hours anyone can verify on a calendar.
November 2026: New York and Chicago are on standard time (UTC-5, UTC-6)."""
from datetime import datetime, timezone

import polars as pl
import pytest

from quantlake.reference.hyperliquid_underlying import NEEDS_REVIEW, UNIDENTIFIED, calendar_for
from quantlake.silver.hyperliquid import add_underlying, hourly_open_fraction


def utc(*a):
    return datetime(*a, tzinfo=timezone.utc)


def frac(cal, *hour):
    g = hourly_open_fraction(cal, utc(2026, 11, 1), utc(2026, 11, 30))
    return g.filter(pl.col("timestamp") == utc(*hour))["underlying_open_frac"].item()


def test_nyse_opens_at_half_past_and_closes_on_the_hour():
    assert frac("XNYS", 2026, 11, 6, 14) == 0.5          # 09:30 ET falls mid-bar
    assert frac("XNYS", 2026, 11, 6, 15) == 1.0
    assert frac("XNYS", 2026, 11, 6, 21) == 0.0          # closed at 16:00 ET
    assert frac("XNYS", 2026, 11, 7, 15) == 0.0          # Saturday


def test_nyse_holidays_are_closed():
    assert frac("XNYS", 2026, 11, 26, 15) == 0.0         # Thanksgiving


def test_cme_halts_every_afternoon_and_opens_sunday_evening():
    assert frac("CME", 2026, 11, 4, 21) == 1.0
    assert frac("CME", 2026, 11, 4, 22) == 0.0           # 16:00-17:00 Chicago
    assert frac("CME", 2026, 11, 4, 23) == 1.0
    assert frac("CME", 2026, 11, 7, 12) == 0.0           # Saturday
    assert frac("CME", 2026, 11, 8, 22) == 0.0           # Sunday 16:00 Chicago
    assert frac("CME", 2026, 11, 8, 23) == 1.0           # Sunday 17:00 Chicago: open


def test_fx_is_open_from_sunday_to_friday_evening():
    assert frac("FX", 2026, 11, 6, 21) == 1.0
    assert frac("FX", 2026, 11, 6, 22) == 0.0            # Friday 17:00 New York
    assert frac("FX", 2026, 11, 8, 21) == 0.0
    assert frac("FX", 2026, 11, 8, 22) == 1.0            # Sunday 17:00 New York


def test_tokyo_lunch_break():
    assert frac("XTKS", 2026, 11, 6, 2) == 0.5           # 11:00-12:00 JST, closes 11:30
    assert frac("XTKS", 2026, 11, 6, 3) == 0.5           # reopens 12:30


def _bars(symbols, ts):
    return pl.DataFrame({"symbol": symbols, "timestamp": [ts] * len(symbols)},
                        schema={"symbol": pl.String, "timestamp": pl.Datetime("us", "UTC")})


LISTINGS = pl.DataFrame({"symbol": ["BTC", "xyz:TSLA", "xyz:SPCX", "xyz:NEWTHING"],
                         "dex": ["main", "xyz", "xyz", "xyz"]})


def test_unknown_is_null_not_closed():
    out = add_underlying(_bars(LISTINGS["symbol"].to_list(), utc(2026, 11, 6, 15)), LISTINGS, "1h")
    row = {r["symbol"]: r for r in out.iter_rows(named=True)}
    assert row["BTC"]["underlying_market_open"] is True
    assert row["xyz:TSLA"]["underlying_market_open"] is True
    assert row["xyz:SPCX"]["underlying_open_frac"] == 0.0 and row["xyz:SPCX"]["underlying_market_open"] is False
    assert row["xyz:NEWTHING"]["calendar"] is None and row["xyz:NEWTHING"]["underlying_market_open"] is None


def test_a_daily_bar_gets_the_share_of_the_day():
    out = add_underlying(_bars(["xyz:TSLA", "BTC"], utc(2026, 11, 6)), LISTINGS, "1d")
    row = {r["symbol"]: r for r in out.iter_rows(named=True)}
    assert row["xyz:TSLA"]["underlying_open_frac"] == pytest.approx(6.5 / 24)
    assert row["BTC"]["underlying_open_frac"] == 1.0


def test_the_same_ticker_follows_the_same_market_on_every_dex():
    assert calendar_for("xyz:NVDA", "xyz") == calendar_for("io:NVDA", "io") == "XNYS"
    assert NEEDS_REVIEW, "the doubtful mappings must stay listed until checked"


def test_every_live_hip3_perp_is_mapped():
    """Data check: a perp listed after 09/11/2026 shows up here until mapped."""
    from deltalake import DeltaTable
    from quantlake.config import REFERENCE_ROOT

    path = str(REFERENCE_ROOT / "hyperliquid_listings")
    if not DeltaTable.is_deltatable(path):
        pytest.skip("no listings table in this checkout")
    L = pl.from_arrow(DeltaTable(path).to_pyarrow_table())
    live = L.filter((pl.col("dex") != "main") & ~pl.col("is_delisted"))
    unmapped = [s for s, d in zip(live["symbol"], live["dex"])
                if calendar_for(s, d) is None and s.split(":", 1)[-1] not in UNIDENTIFIED]
    assert not unmapped, f"HIP-3 perps with no calendar: {unmapped}"
