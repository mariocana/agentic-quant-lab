"""Pre-session context card (Stucchi playbook): the numbers, not the layout.

    update(session)  refresh the inputs (R2 chain snapshots, VIX/GEX/NDX,
                     MultiCharts bars, gold/daily_context; for NY also a chain
                     snapshot now). Runs the loaders in applications/ as
                     subprocesses, logs to data/logs/contesto.log, returns warnings.
    card()           one dict with everything both sessions need: rendered as
                     markdown by applications/contesto.py (session sheet) and
                     as the "Contesto sessione" page of the banco di lavoro
                     (mc/docs/build_site.py, which calls it with this venv).

Historical rates (London range quantiles, gap fill, trend days with low GEX)
are recomputed from all complete rows of gold/daily_context on every call;
see education/enrico_stucchi/CALIBRAZIONE_contesto.md.
"""
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import polars as pl
from deltalake import DeltaTable

from quantlake.config import DATA_ROOT, GOLD_ROOT, SILVER_ROOT
from quantlake.storage import read_symbol

APP = Path(__file__).resolve().parents[2] / "applications"
LOG = DATA_ROOT / "logs" / "contesto.log"
ROME = ZoneInfo("Europe/Rome")
NY = ZoneInfo("America/New_York")
SYMBOLS = ("ES", "NQ")
STALE = timedelta(minutes=30)   # bars older than this = MultiCharts CSV not refreshed
GEX_LOW = 0.3
GAP_EDGES = [0, 0.1, 0.25, 0.5, 1.0, 99]

LOADERS = {
    "london": ["cloud_sync.py", "historical/cboe_vix.py", "historical/squeezemetrics.py",
               "historical/nasdaq_index.py", "historical/multicharts.py", "historical/daily_context.py"],
    "ny": ["cloud_sync.py", "historical/multicharts.py", "historical/daily_context.py", "spx_chain_snapshot.py"],
}


def update(session: str) -> list[str]:
    if session not in LOADERS:
        raise ValueError(f"session must be one of {list(LOADERS)}")
    warn = []
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as log:
        log.write(f"=== {datetime.now():%F %T} contesto {session}\n")
        log.flush()
        for script in LOADERS[session]:
            r = subprocess.run([sys.executable, str(APP / script)], cwd=APP.parent, stdout=log, stderr=log)
            if r.returncode != 0:
                warn.append(f"aggiornamento fallito: {script} (vedi data/logs/contesto.log)")
    return warn


def _last_bar(symbol: str) -> tuple[datetime | None, float | None]:
    since = datetime.now(timezone.utc) - timedelta(days=5)
    b = read_symbol(str(SILVER_ROOT / "multicharts_ohlcv"), symbol, columns=["timestamp", "close"], since=since)
    if b is None or b.is_empty():
        return None, None
    r = b.sort("timestamp").row(-1, named=True)
    return r["timestamp"] + timedelta(minutes=1), r["close"]


def _em_0dte() -> dict | None:
    path = str(GOLD_ROOT / "em_0dte" / "snapshot")
    if not DeltaTable.is_deltatable(path):
        return None
    e = pl.from_arrow(DeltaTable(path).to_pyarrow_table()).sort("timestamp")
    e = e.filter(pl.col("expiry") == datetime.now(NY).date())
    return None if e.is_empty() else e.row(-1, named=True)


def _gap_fill(h: pl.DataFrame, symbol: str, gap_em: float) -> dict:
    a = abs(gap_em)
    lo, hi = next((lo, hi) for lo, hi in zip(GAP_EDGES, GAP_EDGES[1:]) if a < hi)
    x = h.filter((pl.col("symbol") == symbol) & pl.col("gap_filled").is_not_null()
                 & (pl.col("gap_em").abs() >= lo) & (pl.col("gap_em").abs() < hi))
    return {"rate": x["gap_filled"].mean() if x.height else None, "days": x.height,
            "lo": lo, "hi": hi if hi < 99 else None}


def _trend_rate(h: pl.DataFrame, symbol: str, low: bool) -> float | None:
    x = h.filter((pl.col("symbol") == symbol) & pl.col("gex_pct").is_not_null())
    x = x.filter(pl.col("gex_pct") < GEX_LOW) if low else x.filter(pl.col("gex_pct") >= GEX_LOW)
    return (x["day_type"] != "rotation").mean() if x.height else None


def card() -> dict:
    ctx = pl.from_arrow(DeltaTable(str(GOLD_ROOT / "daily_context" / "1d")).to_pyarrow_table()).sort("symbol", "date")
    h = ctx.filter("complete")
    today = {s: ctx.filter(pl.col("symbol") == s).row(-1, named=True) for s in SYMBOLS}
    e = _em_0dte()
    now = datetime.now(timezone.utc)
    warnings, inst = [], {}

    for s in SYMBOLS:
        r = today[s]
        bar_ts, px = _last_bar(s)
        if bar_ts is None or now - bar_ts > STALE:
            warnings.append(f"barre {s} ferme alle {bar_ts.astimezone(ROME):%d/%m %H:%M}: il CSV di MultiCharts "
                            "non è aggiornato, range asiatico, prezzo e gap non sono affidabili" if bar_ts else
                            f"nessuna barra {s} recente")
        em = r["em"]
        q = h.filter((pl.col("symbol") == s) & pl.col("london_range_em").is_not_null())["london_range_em"]
        lq = [q.quantile(p) * em if em else None for p in (0.25, 0.5, 0.75)]
        gap = None if px is None or r["prev_close"] is None else px - r["prev_close"]
        gap_em = gap / em if gap is not None and em else None
        em0 = None
        if e is not None and px is not None:
            em0 = e["em_pct"] * px
            if s == "NQ":  # SPX straddle scaled to Nasdaq vol: an estimate
                em0 *= (today["NQ"]["vxn"] or 0) / (today["ES"]["vix"] or 1)
        inst[s] = {
            "last_bar": bar_ts, "price": px,
            "prev_high": r["prev_high"], "prev_low": r["prev_low"], "prev_close": r["prev_close"],
            "em": em, "iv": r["iv"], "iv_pct": r["iv_pct"],
            "london_range_q": lq,                                 # p25 / p50 / p75 in points
            "stop_max": lq[0] / 2 if lq[0] else None,             # beyond this the morning is "ferma"
            "asia_high": r["asia_high"], "asia_low": r["asia_low"], "asia_range": r["asia_range"],
            "london_high": r["london_high"], "london_low": r["london_low"],
            "london_range": r["london_range"], "london_range_em": r["london_range_em"], "london_move": r["london_move"],
            "gap": gap, "gap_em": gap_em,
            "gap_fill": _gap_fill(h, s, gap_em) if gap_em is not None else None,
            "em_0dte": em0, "em_0dte_estimated": s == "NQ",
        }

    r = today["ES"]
    gex_low = r["gex_pct"] is not None and r["gex_pct"] < GEX_LOW
    if e is None:
        warnings.append("nessuna foto 0DTE di oggi nella catena SPX: EM live non disponibile")
    return {
        "generated_at": now,
        "session_date": r["date"],
        "warnings": warnings,
        "instruments": inst,
        "regime": {
            "vol_regime": r["vol_regime"], "iv_pct": r["iv_pct"], "trend20": r["trend20"], "quadrant": r["quadrant"],
            "term_9d": r["term_9d"], "term_3m": r["term_3m"],
            "gex": r["gex"], "gex_regime": r["gex_regime"], "gex_pct": r["gex_pct"], "gex_low": gex_low,
            "trend_rate_gex_low": _trend_rate(h, "ES", True), "trend_rate_gex_high": _trend_rate(h, "ES", False),
        },
        "em_0dte": None if e is None else {
            "timestamp": e["timestamp"], "pre_open": e["pre_open"], "minutes_to_close": e["minutes_to_close"],
            "em_pct": e["em_pct"], "forward": e["forward"], "straddle": e["straddle"],
        },
        "stucchi_em_stats": {"touch_1": 0.75, "beyond_2": 0.21, "close_within_2": 0.90},
    }
