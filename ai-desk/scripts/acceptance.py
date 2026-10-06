#!/usr/bin/env python3
"""Phase-1 acceptance test: does the risk engine really have the last word?

Drives the running desk through its own HTTP API and checks that every brake
works end to end. The unit tests cover the pieces; this covers the system.

    .venv/bin/desk ui                 # in one terminal
    .venv/bin/python scripts/acceptance.py

Paper mode only - it refuses to run against a live account. It changes the paper
account and config/limits.yaml while it works, and restores the limits at the end
(including after a failure). Run it before trusting the desk with real money, and
again after any change to risk/.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765"
PASS, FAIL = "\033[32mPASS\033[0m", "\033[31mFAIL\033[0m"
failures: list[str] = []


def api(path: str, method: str = "GET", body: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read() or "null")
    except urllib.error.HTTPError as e:
        return {"_http_error": e.code, "detail": (e.read() or b"").decode()[:200]}


def check(name: str, ok: bool, detail: str = ""):
    print(f"  {PASS if ok else FAIL}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        failures.append(name)


def run_cycle(dry: bool) -> dict:
    """Start a cycle and wait for it to finish; returns the joined cycle detail."""
    r = api("/api/run", "POST", {"dry_run": dry})
    if "_http_error" in r:
        return {"intents": [], "error": r}
    for _ in range(120):
        time.sleep(1)
        if not api("/api/state")["running"]:
            break
    return api("/api/cycle")


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
    if st.get("stale_code"):
        print("  REFUSING: the running desk is older than the source files on disk.")
        print("  Restart it (Ctrl+C in its terminal, then `.venv/bin/desk ui`) and run this again —")
        print("  otherwise you are testing the code you had, not the code you have.")
        return 2

    original = {f["path"]: f["value"] for f in api("/api/limits")}
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
              ", ".join(sorted({r for i in opening for r in i["rules_fired"]})) or "—")
        set_limit("max_notional_pct_equity.crypto", original["max_notional_pct_equity.crypto"])

        print("\n5. kill switch blocks new risk but never blocks the exit")
        api("/api/kill", "POST", {"on": True})
        check("state reports the kill switch", api("/api/state")["status"] == "kill")
        c = run_cycle(dry=True)
        opening = [i for i in verdicts(c) if not i["reduce_only"]]
        closing = [i for i in verdicts(c) if i["reduce_only"]]
        check("opening intents rejected", opening and all(i["decision"] == "reject" for i in opening),
              f"{len(opening)} rejected")
        check("closing intents still allowed", not closing or all(i["decision"] != "reject" for i in closing),
              f"{len(closing)} closing intents")
        api("/api/kill", "POST", {"on": False})

        print("\n6. flatten closes everything")
        r = api("/api/flatten", "POST")
        st = api("/api/state")
        check("no positions left", not st["positions"], f"{r.get('fills', '?')} fills")

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
                  f"{len(opening)} opening intents")
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

    print()
    if failures:
        print(f"{FAIL}  {len(failures)} check(s) failed: " + "; ".join(failures))
        print("  Do not run this desk against real money until these pass.\n")
        return 1
    print(f"{PASS}  phase 1 accepted — the risk engine has the last word.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
