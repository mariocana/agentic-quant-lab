#!/usr/bin/env python3
"""Phase-1 acceptance test: does the risk engine really have the last word?

Drives the running desk through its own HTTP API and checks that every brake
works end to end. The unit tests cover the pieces; this covers the system.

    .venv/bin/desk ui                 # in one terminal
    .venv/bin/python scripts/acceptance.py
    DESK_PASSWORD=... .venv/bin/python scripts/acceptance.py https://your-desk.up.railway.app

Paper mode only - it refuses to run against a live account. It changes the paper
account and config/limits.yaml while it works, and restores the limits at the end
(including after a failure). Run it before trusting the desk with real money, and
again after any change to risk/.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765"
PASS, FAIL = "\033[32mPASS\033[0m", "\033[31mFAIL\033[0m"
failures: list[str] = []


def api(path: str, method: str = "GET", body: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    pw = os.environ.get("DESK_PASSWORD", "").strip()
    if pw:                                              # a deployed desk needs the password
        headers["Authorization"] = "Basic " + base64.b64encode(f"desk:{pw}".encode()).decode()
    req = urllib.request.Request(BASE + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read() or "null")
    except urllib.error.HTTPError as e:
        body = (e.read() or b"").decode()[:200]
        if e.code in (401, 403):
            raise SystemExit(f"\n  {e.code} on {path}: wrong or missing DESK_PASSWORD.")
        if e.code in (404, 502, 503, 504):
            raise SystemExit(
                f"\n  the desk returned {e.code} on {path} — it is restarting or not deployed.\n"
                "  Wait for the deployment to go green, check /healthz, then run this again."
            )
        return {"_http_error": e.code, "detail": body}
    except urllib.error.URLError as e:
        raise SystemExit(f"\n  cannot reach {BASE}: {e.reason}")


def check(name: str, ok: bool, detail: str = "", intents: list[dict] | None = None):
    print(f"  {PASS if ok else FAIL}  {name}" + (f"  — {detail}" if detail else ""))
    if ok:
        return
    failures.append(name)
    for i in intents or []:                              # a failure is useless without the evidence
        print(f"        {i['asset']:<10} {i['side']:<5} {i['notional_usd']:>8.0f}"
              f"  reduce_only={str(i['reduce_only']):<5} -> {i['decision']} {i['rules_fired']}")


def run_cycle(dry: bool) -> dict:
    """Start a cycle, wait for it, and return *that* cycle's detail.

    /api/cycle returns the last cycle in the journal. A cycle that raises never
    writes its record, so without the checks below the caller silently reads the
    previous cycle and judges the wrong evidence.
    """
    before = api("/api/cycle").get("ts")
    r = api("/api/run", "POST", {"dry_run": dry})
    if "_http_error" in r:
        raise SystemExit(f"\n  the desk refused to start a cycle: {r}")
    for _ in range(180):
        time.sleep(1)
        st = api("/api/state")
        if "running" not in st:
            raise SystemExit(f"\n  the desk stopped answering: {st}")
        if not st["running"]:
            break
    else:
        raise SystemExit("\n  the cycle is still running after 3 minutes; aborting.")
    if st.get("last_error"):
        raise SystemExit(f"\n  the cycle raised and wrote no record:\n    {st['last_error']}\n"
                         "  Check the platform logs for the traceback.")
    cycle = api("/api/cycle")
    if cycle.get("ts") == before:
        raise SystemExit("\n  the cycle finished but wrote no new journal record — "
                         "the desk is reporting a stale cycle. Check the platform logs.")
    return cycle


def set_limit(path: str, value: float):
    values = {f["path"]: f["value"] for f in api("/api/limits")}
    values[path] = value
    return api("/api/limits", "PUT", {"values": values})


def verdicts(cycle: dict) -> list[dict]:
    return [i for i in cycle.get("intents", []) if i.get("decision")]


def main() -> int:
    print(f"\nai-desk — phase 1 acceptance\n{BASE}\n")
    st = api("/api/state")
    if "_http_error" in st or "mode" not in st:
        print(f"  cannot reach the desk at {BASE}. Start it with: .venv/bin/desk ui")
        return 2
    if st["mode"] != "paper":
        print("  REFUSING: the desk is in live mode. This test opens and closes positions.")
        return 2
    health = api("/healthz")
    up = health.get("uptime_s")
    if isinstance(up, (int, float)) and up < 45:
        print(f"  REFUSING: the desk started {up:.0f}s ago — a deployment is probably still settling.")
        print("  Wait for it to go green and run this again; a restart mid-test invalidates the result.")
        return 2
    if st.get("stale_code"):
        print("  REFUSING: the running desk is older than the source files on disk.")
        print("  Restart it (Ctrl+C in its terminal, then `.venv/bin/desk ui`) and run this again —")
        print("  otherwise you are testing the code you had, not the code you have.")
        return 2

    original = {f["path"]: f["value"] for f in api("/api/limits")}
    # The desk runs its own cycles. One firing between a flatten and the next check
    # would open positions under the test's feet and make the result meaningless,
    # so the schedule is parked for the duration and restored in the finally block.
    scheduler_was_on = bool(st.get("ui", {}).get("schedule_enabled"))
    if scheduler_was_on:
        api("/api/settings", "PUT", {"schedule_enabled": False})
        print("  (the desk's scheduler is parked for the duration of this test)\n")
    try:
        print("1. clean slate")
        api("/api/kill", "POST", {"on": False})
        api("/api/unlock", "POST")
        api("/api/paper/reset", "POST", {"starting_equity": 10_000.0})
        st = api("/api/state")
        check("paper account reset", abs(st["equity_usd"] - 10_000) < 1 and not st["positions"],
              f"equity {st['equity_usd']:.2f}, {len(st['positions'])} positions")

        print("\n2. dry run changes nothing")
        c = run_cycle(dry=True)
        n_intents = len(c.get("intents", []))
        check("the cycle produced intents", n_intents > 0, f"{n_intents} intents")
        check("nothing was executed", not api("/api/state")["positions"])

        print("\n3. a real cycle opens a book inside the limits")
        c = run_cycle(dry=False)
        st = api("/api/state")
        eq = st["equity_usd"]
        cap = original["max_notional_pct_equity.crypto"] * eq
        over = [p for p in st["positions"] if abs(p["notional_usd"]) > cap * 1.02]
        check("positions opened", len(st["positions"]) > 0, f"{len(st['positions'])} positions")
        check("every position within the per-asset cap", not over,
              f"cap ${cap:,.0f}" + (f", breached by {[p['asset'] for p in over]}" if over else ""))
        gross_lev = st["gross_leverage"]
        check("gross leverage within the limit", gross_lev <= original["max_gross_leverage"] + 1e-6,
              f"{gross_lev:.2f}x of max {original['max_gross_leverage']}x")

        print("\n4. a tiny per-asset cap must reject everything new")
        set_limit("max_notional_pct_equity.crypto", 0.0001)
        c = run_cycle(dry=True)
        opening = [i for i in verdicts(c) if not i["reduce_only"]]
        check("some opening intents were evaluated", len(opening) > 0, f"{len(opening)} opening intents")
        check("all of them rejected", all(i["decision"] == "reject" for i in opening),
              ", ".join(sorted({r for i in opening for r in i["rules_fired"]})) or "—", opening)
        set_limit("max_notional_pct_equity.crypto", original["max_notional_pct_equity.crypto"])

        print("\n5. kill switch blocks new risk but never blocks the exit")
        api("/api/kill", "POST", {"on": True})
        check("state reports the kill switch", api("/api/state")["status"] == "kill")
        c = run_cycle(dry=True)
        opening = [i for i in verdicts(c) if not i["reduce_only"]]
        closing = [i for i in verdicts(c) if i["reduce_only"]]
        check("opening intents rejected", bool(opening) and all(i["decision"] == "reject" for i in opening),
              f"{len(opening)} rejected", opening)
        check("closing intents still allowed", not closing or all(i["decision"] != "reject" for i in closing),
              f"{len(closing)} closing intents", closing)
        api("/api/kill", "POST", {"on": False})

        print("\n6. flatten closes everything")
        r = api("/api/flatten", "POST")
        st = api("/api/state")
        left = ", ".join(f"{p['asset']} {p['size']:+.6f}" for p in st["positions"])
        check("no positions left", not st["positions"],
              f"{r.get('fills', '?')} fills" + (f"; left: {left}" if left else ""))

        print("\n7. daily-loss freeze")
        st = api("/api/state")
        day = st["day_pnl_pct"]
        if day >= 0:
            print(f"  ....  skipped — the day is up {day:+.4%}; a freeze threshold cannot be negative")
        else:
            set_limit("daily_loss_freeze_pct", abs(day) / 2)
            st = api("/api/state")
            check("state reports frozen", st["status"] == "frozen", f"day {day:+.4%}")
            c = run_cycle(dry=True)
            opening = [i for i in verdicts(c) if not i["reduce_only"]]
            check("new risk refused while frozen",
                  bool(opening) and all(i["decision"] == "reject" and "daily_loss_freeze" in i["rules_fired"] for i in opening),
                  f"{len(opening)} opening intents, day {day:+.4%}, freeze at {abs(day) / 2:.6%}", opening)
            set_limit("daily_loss_freeze_pct", original["daily_loss_freeze_pct"])

        print("\n8. the journal recorded it all")
        kinds = {row["kind"] for row in api("/api/journal?last=500")}
        check("targets/intents/verdicts/fills in the journal",
              {"targets", "intent", "verdict", "fill"} <= kinds, ", ".join(sorted(kinds)))
    finally:
        now = {f["path"]: f["value"] for f in api("/api/limits")}
        if now != original:
            api("/api/limits", "PUT", {"values": original})
            print("\n  (risk limits restored)")
        api("/api/kill", "POST", {"on": False})
        if scheduler_was_on:
            api("/api/settings", "PUT", {"schedule_enabled": True})
            print("  (scheduler restored)")

    print()
    if failures:
        print(f"{FAIL}  {len(failures)} check(s) failed: " + "; ".join(failures))
        print("  Do not run this desk against real money until these pass.\n")
        return 1
    print(f"{PASS}  phase 1 accepted — the risk engine has the last word.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
