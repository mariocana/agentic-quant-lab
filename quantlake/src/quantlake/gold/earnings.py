"""Earnings screener -> gold/earnings_screener/1d (current snapshot, rebuilt each run).

Two lists, from bronze nasdaq_earnings_calendar / _surprise / nasdaq_stock_daily:

  reported   companies that reported in the last LOOKBACK weekdays with a
             meaningful BEAT (actual - consensus >= $0.01 and surprise >= 1%)
             and the next session opening more than GAP_MIN above the prior close.
  upcoming   companies reporting in the next LOOKAHEAD weekdays with a beat rate
             >= 75% over the last 4 quarters, or a 13-week return > +5%.

Reaction session: report before the open (bmo) -> the report day; after the
close (amc) -> the next session. Nasdaq drops the time of day once the day is
past: the loader keeps the one seen while the report was upcoming, and when
it was never seen the session with the larger opening gap is used
(time_inferred = true).

Scores (0-100, only for ordering; transparent on purpose):
  reported  50 x min(surprise% / 25, 1) + 50 x min(gap% / 8, 1)
  upcoming  60 x beat rate + 40 x clip(13-week return / 20%, 0, 1)

Every row of both lists is kept, with `passes` = the screen condition: the
desk shows the passing ones and can show the rest.
"""
from datetime import date, datetime, timedelta

import polars as pl
from deltalake import write_deltalake

from quantlake.config import GOLD_ROOT

TABLE = "earnings_screener"
TIMEFRAME = "1d"
NY = "America/New_York"
LOOKBACK = 5
LOOKAHEAD = 5
BEAT_ABS = 0.01
BEAT_PCT = 1.0
GAP_MIN = 0.02
BEAT_RATE_MIN = 0.75
RET13_MIN = 0.05
RET13_BARS = 63          # ~13 weeks of sessions
MIN_MARKET_CAP = 2e9     # smaller companies are skipped (and not downloaded)


def weekdays(start: date, n: int, step: int) -> list[date]:
    """n weekdays from start included, going forward (step=1) or back (-1)."""
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=step)
    return out


def _ny_date(col: str = "timestamp") -> pl.Expr:
    return pl.col(col).dt.convert_time_zone(NY).dt.date()


def _reaction(px: pl.DataFrame, day: date, when: str) -> dict:
    """Prior close, reaction open and the gap for one report, from daily bars."""
    px = px.with_columns(_ny_date().alias("d")).sort("d")
    before = px.filter(pl.col("d") < day)
    on = px.filter(pl.col("d") == day)
    after = px.filter(pl.col("d") > day)

    def gap(prev, nxt):
        if prev.is_empty() or nxt.is_empty():
            return None, None, None, None
        p, o = prev["close"][-1], nxt["open"][0]
        return o / p - 1, p, o, nxt["d"][0]

    g_bmo = gap(before, on)
    g_amc = gap(on, after)
    inferred = False
    if when == "bmo":
        g = g_bmo
    elif when == "amc":
        g = g_amc
    else:
        inferred = True
        cand = [x for x in (g_bmo, g_amc) if x[0] is not None]
        g = max(cand, key=lambda x: abs(x[0])) if cand else (None, None, None, None)
        when = None if not cand else ("bmo" if g is g_bmo else "amc")
    last = px["close"][-1] if px.height else None
    gap_pct, prev_close, react_open, react_day = g
    return {
        "time_used": when, "time_inferred": inferred, "reaction_day": react_day,
        "prev_close": prev_close, "reaction_open": react_open, "gap_pct": gap_pct,
        "last_close": last,
        "since_open_pct": None if react_open is None or last is None else last / react_open - 1,
        "since_report_pct": None if prev_close is None or last is None else last / prev_close - 1,
    }


def _ret13(px: pl.DataFrame) -> float | None:
    c = px.sort("timestamp")["close"]
    return None if c.len() <= RET13_BARS else c[-1] / c[-1 - RET13_BARS] - 1


def build(calendar: pl.DataFrame, surprise: pl.DataFrame, prices: pl.DataFrame, today: date) -> pl.DataFrame:
    cal = calendar.with_columns(_ny_date().alias("report_date")).filter(
        pl.col("market_cap").fill_null(0) >= MIN_MARKET_CAP)
    past = weekdays(today, LOOKBACK, -1)
    ahead = weekdays(today, LOOKAHEAD, 1)
    px_by = {s: g for (s,), g in prices.group_by("symbol")} if not prices.is_empty() else {}
    sp_by = {s: g for (s,), g in surprise.group_by("symbol")} if not surprise.is_empty() else {}
    rows = []

    for r in cal.filter(pl.col("report_date").is_in(past) & pl.col("eps").is_not_null()).iter_rows(named=True):
        est, eps = r["eps_forecast"], r["eps"]
        diff = None if est is None else eps - est
        surprise_pct = r["surprise_pct"]
        if surprise_pct is None and est:
            surprise_pct = diff / abs(est) * 100
        beat = diff is not None and surprise_pct is not None and diff >= BEAT_ABS - 1e-9 and surprise_pct >= BEAT_PCT
        rx = _reaction(px_by[r["symbol"]], r["report_date"], r["time"]) if r["symbol"] in px_by else {}
        gap = rx.get("gap_pct")
        passes = bool(beat and gap is not None and gap > GAP_MIN)
        score = None
        if surprise_pct is not None and gap is not None:
            score = round(50 * min(max(surprise_pct, 0) / 25, 1) + 50 * min(max(gap * 100, 0) / 8, 1))
        rows.append({
            "list": "reported", **{k: r[k] for k in ("symbol", "name", "report_date", "time", "eps", "eps_forecast",
                                                    "n_estimates", "market_cap", "fiscal_quarter")},
            "surprise_abs": diff, "surprise_pct": surprise_pct,
            "result": "BEAT" if beat else ("MISS" if diff is not None and diff < 0 else "IN LINE"),
            **{k: rx.get(k) for k in ("time_used", "time_inferred", "reaction_day", "prev_close", "reaction_open",
                                      "gap_pct", "last_close", "since_open_pct", "since_report_pct")},
            "beat_rate": None, "beats": None, "quarters": None, "ret_13w": None,
            "passes": passes, "score": score,
        })

    for r in cal.filter(pl.col("report_date").is_in(ahead) & pl.col("eps").is_null()).iter_rows(named=True):
        hist = sp_by.get(r["symbol"])
        beats = quarters = None
        if hist is not None:
            h = hist.sort("timestamp").tail(4).drop_nulls(["eps", "eps_forecast"])
            quarters = h.height
            beats = int((h["eps"] > h["eps_forecast"]).sum()) if quarters else None
        rate = beats / quarters if quarters else None
        ret = _ret13(px_by[r["symbol"]]) if r["symbol"] in px_by else None
        passes = bool((rate is not None and rate >= BEAT_RATE_MIN) or (ret is not None and ret > RET13_MIN))
        score = round(60 * (rate or 0) + 40 * min(max((ret or 0) / 0.20, 0), 1))
        last = px_by[r["symbol"]].sort("timestamp")["close"][-1] if r["symbol"] in px_by else None
        rows.append({
            "list": "upcoming", **{k: r[k] for k in ("symbol", "name", "report_date", "time", "eps", "eps_forecast",
                                                    "n_estimates", "market_cap", "fiscal_quarter")},
            "surprise_abs": None, "surprise_pct": None, "result": None,
            "time_used": None, "time_inferred": None, "reaction_day": None, "prev_close": None,
            "reaction_open": None, "gap_pct": None, "last_close": last, "since_open_pct": None,
            "since_report_pct": None, "beat_rate": rate, "beats": beats, "quarters": quarters, "ret_13w": ret,
            "passes": passes, "score": score,
        })

    if not rows:
        return pl.DataFrame()
    now = datetime.now().astimezone()
    return pl.DataFrame(rows, infer_schema_length=None).with_columns(
        pl.lit(today).alias("as_of"),
        pl.lit(now).cast(pl.Datetime("us", "UTC")).alias("timestamp"),
    ).sort(["list", "passes", "score"], descending=[False, True, True], nulls_last=True)


def save(df: pl.DataFrame) -> None:
    if df.is_empty():
        return
    write_deltalake(str(GOLD_ROOT / TABLE / TIMEFRAME), df.to_arrow(), mode="overwrite", schema_mode="overwrite")
