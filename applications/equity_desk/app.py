"""Equity Desk — local Flask UI: earnings scanner and insider purchases (later 13F).

Reads gold/earnings_screener/1d, bronze/nasdaq_earnings_calendar and
gold/insider_activity/1d; the "aggiorna" button runs the loader of the open
tab (applications/historical/earnings.py or insiders.py) in the background.
Local only: binds to 127.0.0.1.

Routes:
  GET  /                    page
  GET  /api/screener        screener rows (reported + upcoming)
  GET  /api/calendar        every company in the calendar window
  GET  /api/insiders        insider buys / large sales of the last 30 days
  POST /api/refresh?job=    run a loader: earnings (default) or insiders, one at a time
  GET  /api/refresh/status  state + last lines of its output
  GET  /health

Run (from python/quantlake):
    .venv/bin/python applications/equity_desk/app.py     # http://127.0.0.1:5070
"""
import math
import os
import subprocess
import sys
import threading
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import polars as pl
from deltalake import DeltaTable
from flask import Flask, jsonify, render_template, request

from quantlake.config import BRONZE_ROOT, GOLD_ROOT

APP_DIR = Path(__file__).resolve().parents[1]
LOADERS = {"earnings": APP_DIR / "historical" / "earnings.py",
           "insiders": APP_DIR / "historical" / "insiders.py"}
NY = ZoneInfo("America/New_York")
CAL_DAYS = 7          # calendar tab: weekdays shown on each side of today

app = Flask(__name__)
_refresh = {"state": "idle", "job": None, "started": None, "finished": None, "output": ""}
_lock = threading.Lock()


def _table(path: Path) -> pl.DataFrame:
    return pl.from_arrow(DeltaTable(str(path)).to_pyarrow_table()) if DeltaTable.is_deltatable(str(path)) else pl.DataFrame()


def _rows(df: pl.DataFrame) -> list[dict]:
    def clean(v):
        if isinstance(v, float) and not math.isfinite(v):
            return None
        if isinstance(v, (datetime, date)):
            return v.isoformat()
        return v
    return [{k: clean(v) for k, v in r.items()} for r in df.iter_rows(named=True)]


def _freshness() -> str | None:
    path = GOLD_ROOT / "earnings_screener" / "1d"
    if not DeltaTable.is_deltatable(str(path)):
        return None
    ts = pl.from_arrow(DeltaTable(str(path)).to_pyarrow_table(columns=["timestamp"]))["timestamp"].max()
    return ts.isoformat() if ts else None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/screener")
def api_screener():
    df = _table(GOLD_ROOT / "earnings_screener" / "1d")
    return jsonify({"as_of": _freshness(), "rows": _rows(df)})


@app.route("/api/calendar")
def api_calendar():
    cal = _table(BRONZE_ROOT / "nasdaq_earnings_calendar")
    if cal.is_empty():
        return jsonify({"rows": []})
    today = datetime.now(NY).date()
    lo, hi = today - timedelta(days=CAL_DAYS * 7 // 5 + 2), today + timedelta(days=CAL_DAYS * 7 // 5 + 2)
    cal = cal.with_columns(pl.col("timestamp").dt.convert_time_zone("America/New_York").dt.date().alias("report_date"))
    cal = cal.filter(pl.col("report_date").is_between(lo, hi)).with_columns(
        (pl.col("eps") - pl.col("eps_forecast")).alias("surprise_abs"),
    ).with_columns(
        pl.when(pl.col("eps").is_null()).then(pl.lit(None, pl.String))
        .when((pl.col("surprise_abs") >= 0.01) & (pl.col("surprise_pct") >= 1)).then(pl.lit("BEAT"))
        .when(pl.col("surprise_abs") < 0).then(pl.lit("MISS")).otherwise(pl.lit("IN LINE")).alias("result"),
    ).select("report_date", "time", "symbol", "name", "eps_forecast", "eps", "surprise_pct", "result",
             "market_cap", "n_estimates", "fiscal_quarter").sort(["report_date", "market_cap"], descending=[False, True],
                                                                 nulls_last=True)
    return jsonify({"today": today.isoformat(), "rows": _rows(cal)})


def _run_loader(job: str) -> None:
    try:
        r = subprocess.run([sys.executable, str(LOADERS[job])], cwd=APP_DIR.parent, capture_output=True, text=True,
                           timeout=3 * 3600)
        out = (r.stdout + r.stderr).strip()
        state = "done" if r.returncode == 0 else "error"
    except Exception as exc:  # timeout, missing python...
        out, state = str(exc), "error"
    with _lock:
        _refresh.update(state=state, finished=datetime.now().isoformat(), output="\n".join(out.splitlines()[-12:]))


@app.route("/api/insiders")
def api_insiders():
    df = _table(GOLD_ROOT / "insider_activity" / "1d")
    form4 = BRONZE_ROOT / "sec_form4"
    last = None
    if DeltaTable.is_deltatable(str(form4)):
        last = pl.from_arrow(DeltaTable(str(form4)).to_pyarrow_table(columns=["filed_date"]))["filed_date"].max()
    return jsonify({"last_filed": last.isoformat() if last else None, "rows": _rows(df)})


@app.route("/api/refresh", methods=["POST"])
def api_refresh():
    job = request.args.get("job", "earnings")
    if job not in LOADERS:
        return jsonify({"error": f"job must be one of {list(LOADERS)}"}), 400
    with _lock:
        if _refresh["state"] == "running":
            return jsonify(_refresh), 409
        _refresh.update(state="running", job=job, started=datetime.now().isoformat(), finished=None, output="")
    threading.Thread(target=_run_loader, args=(job,), daemon=True).start()
    return jsonify(_refresh)


@app.route("/api/refresh/status")
def api_refresh_status():
    with _lock:
        return jsonify(_refresh)


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("EQUITY_DESK_PORT", 5070))
    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)
