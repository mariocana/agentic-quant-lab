"""On-demand COT sync for the desk's SYNC button.

Same contract as cot-analyzer's sync.py (data_status / run_sync), but the
fetch is now the quantlake pipeline itself, run as subprocesses: the
same two scripts you can also run by hand. No scheduled job — data is
pulled when you press SYNC (the first press downloads the full history).

    historical/cftc_cot.py         CFTC API -> bronze/cftc_cot (incremental)
    historical/cot_positioning.py  bronze -> silver/cftc_cot + gold/cot_positioning/1w

COT release schedule: positions as of Tuesday, published the following
Friday ~15:30 ET. A report is treated as reliably available on the
Saturday after its Tuesday.
"""
import re
import subprocess
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import store
from instruments import INSTRUMENTS

_APPS = Path(__file__).resolve().parents[1]
_PROJECT = _APPS.parent
_ERROR_RE = re.compile(r"^\[(?P<ticker>[^\]]+)\] ERROR (?P<error>.*)$")


# ---------------------------------------------------------------------------
# Freshness check (no network — safe to call on every page load)
# ---------------------------------------------------------------------------
def latest_expected_report_date(today: date | None = None) -> date:
    """The most recent COT report date that *should* already be published."""
    today = today or date.today()
    days_since_tue = (today.weekday() - 1) % 7  # Mon=0 … Sun=6, Tuesday=1
    last_tue = today - timedelta(days=days_since_tue)
    if today < last_tue + timedelta(days=4):
        last_tue -= timedelta(days=7)
    return last_tue


def data_status() -> dict:
    """Cheap freshness snapshot read from gold. No CFTC API calls.

    Current only when EVERY tracked instrument has the expected report:
    one fresh instrument must not hide 31 missing ones.
    """
    expected = latest_expected_report_date()
    newest_by = store.newest_by_symbol()
    stale = sorted(t for t in INSTRUMENTS if newest_by.get(t) is None or newest_by[t] < expected)
    newest = max(newest_by.values()) if newest_by else None
    return {
        "current": not stale,
        "newest": newest.isoformat() if newest else None,
        "expected": expected.isoformat(),
        "instruments": len(newest_by),
        "total": len(INSTRUMENTS),
        "stale": stale,
    }


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------
def _run(script: str, args: list[str], say) -> list[str]:
    """Run an applications/historical script, streaming its output to `say`."""
    proc = subprocess.Popen(
        [sys.executable, str(_APPS / "historical" / script), *args],
        cwd=_PROJECT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    lines = []
    for line in proc.stdout:
        line = line.rstrip()
        if line:
            lines.append(line)
            say(line)
    proc.wait()
    if proc.returncode != 0 and script != "cftc_cot.py":
        raise RuntimeError(f"{script} failed: {lines[-1] if lines else proc.returncode}")
    return lines


def run_sync(only_ticker: str | None = None, progress=None) -> dict:
    """Pull new CFTC reports into bronze, then rebuild silver/gold.

    cftc_cot.py exits non-zero when some instruments failed; those are
    reported in `errors` and the rebuild still runs for the others.
    """
    def say(msg: str) -> None:
        if progress:
            progress(msg)

    start = time.time()
    before = store.row_count()
    say("Fetching CFTC reports…")
    fetch_out = _run("cftc_cot.py", [only_ticker] if only_ticker else [], say)
    say("Rebuilding silver + gold…")
    _run("cot_positioning.py", [], say)

    errors = [m.groupdict() for m in map(_ERROR_RE.match, fetch_out) if m]
    status = data_status()
    # Still behind after a clean fetch: CFTC has no report for that week yet
    # (holiday / shutdown delay) or the CFTC code in symbols.py is wrong.
    failed = {e["ticker"] for e in errors}
    errors += [
        {"ticker": t, "error": f"no report for {status['expected']} (release delayed or wrong CFTC code)"}
        for t in status["stale"] if t not in failed
    ]
    return {
        "ok": not errors,
        "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "elapsed_s": round(time.time() - start, 1),
        "instruments": status["instruments"],
        "new_rows": store.row_count() - before,
        "errors": errors,
        "newest": status["newest"],
        "current": status["current"],
    }
