"""The desk's cycle run over history. The failures that matter are silent ones:
a backtest that peeks at the day it is deciding on, or one that writes into the
real desk's files."""
import random
from datetime import date, datetime, timedelta, timezone

import polars as pl
import pytest

from alphaquant.engine.desk_replay import HistoricalMarket, replay
from desk.config import VAR, load_limits
from desk.signals.reversal import Reversal

D0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _daily(symbols, days, seed=7, delist=None, list_late=None):
    rnd, rows = random.Random(seed), []
    for s in symbols:
        px = 100.0
        first = list_late.get(s, 0) if list_late else 0
        last = delist.get(s, days) if delist else days
        for d in range(first, last):
            px *= 1 + rnd.gauss(0, 0.04)
            t = D0 + timedelta(days=d)
            rows.append({"symbol": s, "timestamp": t, "timestamp_close": t + timedelta(days=1) - timedelta(milliseconds=1),
                         "open": px, "high": px * 1.01, "low": px * 0.99, "close": px, "volume": 1e6})
    return pl.DataFrame(rows).with_columns(pl.col("timestamp", "timestamp_close").cast(pl.Datetime("us", "UTC")))


def _listings(daily, delisted=()):
    fl = daily.group_by("symbol").agg(pl.col("timestamp").min().dt.date().alias("first_bar"),
                                      pl.col("timestamp").max().dt.date().alias("last_bar"))
    return fl.with_columns(pl.when(pl.col("symbol").is_in(list(delisted))).then(pl.col("last_bar"))
                           .otherwise(None).alias("delisted_after"))


def _funding(symbols, days, rate=0.0):
    rows = [{"symbol": s, "timestamp": D0 + timedelta(hours=h), "funding_rate": rate}
            for s in symbols for h in range(days * 24)]
    schema = {"symbol": pl.String, "timestamp": pl.Datetime("us", "UTC"), "funding_rate": pl.Float64}
    return pl.DataFrame(rows, schema=schema)


SYMS = [f"C{i:02d}" for i in range(15)]


def test_the_market_at_00_05_does_not_know_that_day():
    daily = _daily(["A"], 10)
    day5 = D0 + timedelta(days=5)
    # make day 5 unmistakable: if anything reads it, it shows
    daily = daily.with_columns(pl.when(pl.col("timestamp") == day5).then(1e9).otherwise(pl.col("close")).alias("close"))
    m = HistoricalMarket(daily, _funding(["A"], 10), _listings(daily))
    m.at(day5 + timedelta(minutes=5))
    prev_close = daily.filter(pl.col("timestamp") == day5 - timedelta(days=1))["close"].item()
    assert m.contexts()["A"].mark_px == prev_close
    cs = m.candles("A", "1d", 4)
    assert max(c["c"] for c in cs) < 1e9, "the day being decided on leaked into the candles"
    assert cs[-1]["v"] == 0 and cs[-1]["c"] == prev_close, "the open bar carries no information"
    assert len(cs) == 4


def test_the_universe_is_point_in_time():
    daily = _daily(["OLD", "NEW", "DEAD"], 20, list_late={"NEW": 10}, delist={"DEAD": 8})
    m = HistoricalMarket(daily, _funding([], 0), _listings(daily, delisted={"DEAD"}))
    m.at(D0 + timedelta(days=5, minutes=5))
    assert set(m.contexts()) == {"OLD", "DEAD"}            # NEW not listed yet
    m.at(D0 + timedelta(days=15, minutes=5))
    assert set(m.contexts()) == {"OLD", "NEW"}             # DEAD gone


def test_funding_is_summed_over_the_period_only():
    m = HistoricalMarket(_daily(["A"], 3), _funding(["A"], 3, rate=0.0001), _listings(_daily(["A"], 3)))
    got = m.funding_between(D0 + timedelta(hours=10), D0 + timedelta(hours=34))
    assert got["A"] == pytest.approx(24 * 0.0001)


def test_replay_runs_the_desk_cycle_in_the_past_and_touches_nothing_real():
    journal = VAR / "journal.jsonl"
    before = journal.stat().st_mtime if journal.exists() else None

    daily = _daily(SYMS, 60)
    m = HistoricalMarket(daily, _funding(SYMS, 60, rate=0.00002), _listings(daily))
    strat = Reversal(universe_size=15, min_day_volume_usd=1e6)
    res = replay(strat, m, load_limits(), D0 + timedelta(days=25), D0 + timedelta(days=50))

    assert res.equity.height == 26
    assert len(res.fills()) > 0, "the strategy never traded"
    stops = [r for r in res.journal if r.get("kind") == "intent" and str(r.get("reason", "")).startswith("time stop")]
    assert stops, "a 120h horizon over 25 days must hit the time stop"
    # the desk's clock was in the past: the journal says 2026-01, not today
    assert all(r["ts"].startswith("2026-01") or r["ts"].startswith("2026-02") for r in res.journal)
    assert res.funding_paid != 0.0
    after = journal.stat().st_mtime if journal.exists() else None
    assert before == after, "the backtest wrote into the real desk's journal"


def test_a_held_perp_that_is_delisted_gets_settled():
    daily = _daily(SYMS, 60, delist={"C00": 35, "C01": 35, "C14": 35})
    m = HistoricalMarket(daily, _funding(SYMS, 60), _listings(daily, delisted={"C00", "C01", "C14"}))
    res = replay(Reversal(universe_size=15, min_day_volume_usd=1e6), m, load_limits(),
                 D0 + timedelta(days=25), D0 + timedelta(days=45))
    held_dead = {"C00", "C01", "C14"} & {f["asset"] for f in res.fills()}
    if not held_dead:
        pytest.skip("the strategy did not happen to hold a delisted perp in this sample")
    assert set(res.settled_delistings) <= {"C00", "C01", "C14"} and res.settled_delistings


def test_the_holdout_is_closed_by_the_code_not_by_a_request(tmp_path):
    from alphaquant.registry import HoldoutLocked, Registry

    daily = _daily(SYMS, 60)
    lock = D0 + timedelta(days=40)
    m = HistoricalMarket(daily, _funding(SYMS, 60), _listings(daily), holdout_start=lock)
    m.at(lock - timedelta(hours=1))                                  # before: fine
    with pytest.raises(HoldoutLocked):
        m.at(lock)
    with pytest.raises(HoldoutLocked):                               # replay goes through the same door
        replay(Reversal(universe_size=15, min_day_volume_usd=1e6), m, load_limits(),
               D0 + timedelta(days=35), D0 + timedelta(days=45))

    reg = Registry(tmp_path / "t.jsonl")
    spec = {"strategy": "desk.signals.reversal.Reversal", "params": {"universe_size": 15}}
    from alphaquant.registry import RegistryError
    with pytest.raises(RegistryError):
        m.unlock_holdout(reg, "not-a-registered-spec")
    h = reg.register_spec(spec)
    m.unlock_holdout(reg, h)
    m.at(lock + timedelta(days=1))                                   # open now, for this spec
    other = HistoricalMarket(daily, _funding(SYMS, 60), _listings(daily), holdout_start=lock)
    with pytest.raises(HoldoutLocked):
        other.unlock_holdout(reg, h)                                 # spent: a second look is refused


def test_quantlake_markets_are_locked_unless_told_otherwise():
    from alphaquant.engine.desk_replay import splits

    s = splits()
    assert s["train"][1] < s["validation"][0] < s["validation"][1] < s["holdout"][0]
    # the last validation cycle (00:05 of its last day) is before the lock
    assert s["validation"][1] + timedelta(minutes=5) < s["holdout"][0]
