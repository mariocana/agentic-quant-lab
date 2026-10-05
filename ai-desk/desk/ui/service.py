"""Everything the UI can do, in one object. The HTTP layer is a thin wrapper on this.

Holds the market feed, the active adapter, the risk state, a lock so only one
cycle runs at a time, a log ring buffer, and the scheduler thread.
"""
from __future__ import annotations

import collections
import json
import logging
import threading
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

from desk.config import LIMITS_PATH, VAR, load_limits, settings
from desk.data.hl_market import HLMarket
from desk.execution.paper import PAPER_PATH, PaperAdapter
from desk.journal.log import read as read_journal, record
from desk.loop import run_cycle
from desk.risk.state import RiskState
from desk.signals.reversal import Reversal

UI_SETTINGS_PATH = VAR / "ui_settings.json"
DEFAULT_UI_SETTINGS = {
    "mode": "paper",                 # paper | live
    "schedule_enabled": False,
    "schedule_time_utc": "00:05",
    "snapshot_minutes": 15,
}

# Field descriptions for the limits editor. Keys are dotted paths into limits.yaml.
LIMIT_FIELDS = [
    ("max_notional_pct_equity.crypto", "Max per asset, crypto", "fraction of equity", "Largest position in one main-dex perp."),
    ("max_notional_pct_equity.hip3", "Max per asset, HIP-3", "fraction of equity", "Builder-deployed perps (xyz:TSLA, xyz:GOLD…): thin books, isolated margin."),
    ("max_gross_leverage", "Max gross leverage", "x equity", "Sum of |notional| over all positions."),
    ("max_net_beta_pct_equity", "Max net beta", "fraction of equity", "Signed exposure weighted by beta. Alts count as BTC."),
    ("daily_loss_freeze_pct", "Daily loss: freeze", "fraction", "Past this on the day, no new risk is taken. Closing still allowed."),
    ("daily_loss_flatten_pct", "Daily loss: flatten", "fraction", "Past this, everything is closed and the desk halts until you unlock."),
    ("max_drawdown_pct", "Max drawdown from peak", "fraction", "Halts the desk. Needs unlock."),
    ("max_pct_of_book_depth_10bps", "Max share of book depth", "fraction", "Ticket ≤ this share of resting size within 10 bps of mid."),
    ("max_pct_of_day_volume", "Max share of 24h volume", "fraction", "Ticket ≤ this share of the asset's 24h notional volume."),
    ("max_abs_funding_hourly", "Max funding paid", "per hour", "Paying more than this halves the ticket; more than 2x rejects it."),
    ("min_notional_usd", "Minimum ticket", "USD", "Below this the fee floor dominates. Rejected."),
    ("time_stop_grace_hours", "Time stop grace", "hours", "Positions are closed at horizon + grace."),
]


class RingHandler(logging.Handler):
    def __init__(self, buf):
        super().__init__()
        self.buf = buf
        self.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s", "%H:%M:%S"))

    def emit(self, record):
        self.buf.append(self.format(record))


class DeskService:
    def __init__(self):
        self.settings = settings()
        self.market = HLMarket(self.settings.data_url)
        self.strategy = Reversal()
        self.ui = self._load_ui_settings()
        self.lock = threading.Lock()
        self.running = False
        self.last_cycle: dict | None = None
        self.last_error: str | None = None
        self.logs: collections.deque[str] = collections.deque(maxlen=500)
        desk_log = logging.getLogger("desk")
        desk_log.setLevel(logging.INFO)
        desk_log.addHandler(RingHandler(self.logs))
        self._adapter = None
        self._contexts_cache: tuple[float, dict] = (0.0, {})
        self._stop = threading.Event()
        self.scheduler = threading.Thread(target=self._scheduler, daemon=True, name="desk-scheduler")
        self.scheduler.start()

    # ---- settings ------------------------------------------------------------

    def _load_ui_settings(self) -> dict:
        s = dict(DEFAULT_UI_SETTINGS)
        if UI_SETTINGS_PATH.exists():
            s.update(json.loads(UI_SETTINGS_PATH.read_text()))
        return s

    def update_ui_settings(self, patch: dict) -> dict:
        if "mode" in patch and patch["mode"] != self.ui["mode"]:
            if patch["mode"] == "live":
                if not (self.settings.account_address and self.settings.api_wallet_key):
                    raise ValueError("Live mode needs HL_ACCOUNT_ADDRESS and HL_API_WALLET_KEY in .env")
                if not self.settings.testnet and patch.get("confirm") != "MAINNET":
                    raise ValueError("Mainnet needs confirm=MAINNET")
            self._adapter = None
        for k in DEFAULT_UI_SETTINGS:
            if k in patch:
                self.ui[k] = patch[k]
        UI_SETTINGS_PATH.write_text(json.dumps(self.ui, indent=2))
        return self.ui

    @property
    def adapter(self):
        if self._adapter is None:
            if self.ui["mode"] == "live":
                from desk.execution.hyperliquid import HyperliquidAdapter
                self._adapter = HyperliquidAdapter(self.settings.base_url, self.settings.account_address,
                                                   self.settings.api_wallet_key)
            else:
                self._adapter = PaperAdapter()
        return self._adapter

    def venue_label(self) -> str:
        if self.ui["mode"] == "paper":
            return "paper"
        return "testnet" if self.settings.testnet else "MAINNET"

    # ---- reads ---------------------------------------------------------------

    def contexts(self, max_age_s: float = 10.0) -> dict:
        ts, ctx = self._contexts_cache
        now = datetime.now(timezone.utc).timestamp()
        if now - ts > max_age_s:
            ctx = self.market.contexts()
            self._contexts_cache = (now, ctx)
        return ctx

    def state(self) -> dict:
        ctx = self.contexts()
        adapter = self.adapter
        if hasattr(adapter, "set_marks"):
            adapter.set_marks({a: c.mid_px for a, c in ctx.items()})
        acc = adapter.account_state()
        rs = RiskState.load()
        limits = load_limits()
        equity = acc.equity_usd
        day_pnl = rs.day_pnl_pct(equity)
        dd = equity / rs.peak_equity - 1 if rs.peak_equity > 0 else 0.0
        if RiskState.kill_engaged():
            status = "kill"
        elif rs.halted:
            status = "halted"
        elif day_pnl <= -limits["daily_loss_freeze_pct"]:
            status = "frozen"
        else:
            status = "ok"
        positions = []
        now = datetime.now(timezone.utc)
        for p in acc.positions:
            c = ctx.get(p.asset)
            age_h = (now - p.opened_at).total_seconds() / 3600 if p.opened_at else None
            positions.append({
                "asset": p.asset, "side": "long" if p.notional_usd > 0 else "short",
                "notional_usd": p.notional_usd, "size": p.size, "entry_px": p.entry_px, "mark_px": p.mark_px,
                "upnl_usd": p.unrealized_pnl_usd,
                "upnl_pct": p.unrealized_pnl_usd / abs(p.notional_usd) if p.notional_usd else 0.0,
                "funding_hourly": c.funding_hourly if c else None,
                "strategy_id": p.strategy_id, "age_hours": age_h, "horizon_hours": p.horizon_hours,
            })
        return {
            "venue": self.venue_label(), "mode": self.ui["mode"], "status": status,
            "running": self.running, "last_error": self.last_error,
            "equity_usd": equity, "day_pnl_pct": day_pnl, "day_pnl_usd": equity - rs.day_start_equity if rs.day_start_equity else 0.0,
            "drawdown_pct": dd, "peak_equity": rs.peak_equity,
            "gross_usd": acc.gross_notional_usd, "gross_leverage": acc.gross_notional_usd / equity if equity else 0.0,
            "net_usd": sum(p.notional_usd for p in acc.positions),
            "halted": rs.halted, "halt_reason": rs.halt_reason, "kill": RiskState.kill_engaged(),
            "positions": positions, "last_cycle": self.last_cycle,
            "limits": limits, "ui": self.ui, "next_run_utc": self._next_run().isoformat() if self.ui["schedule_enabled"] else None,
            "strategy": {"id": self.strategy.id, "interval": self.strategy.interval, "horizon_hours": self.strategy.horizon_hours},
            "as_of": now.isoformat(),
        }

    def equity_series(self) -> list[dict]:
        rows = read_journal()
        out = [{"ts": r["ts"], "equity": r["equity"], "kind": r["kind"]}
               for r in rows if r["kind"] in ("cycle", "snapshot") and "equity" in r]
        return out

    def last_cycle_detail(self) -> dict:
        """Intents of the most recent cycle, joined with their verdict and fill."""
        rows = read_journal()
        cycles = [i for i, r in enumerate(rows) if r["kind"] == "cycle"]
        if not cycles:
            return {"targets": [], "intents": []}
        start = cycles[-2] + 1 if len(cycles) > 1 else 0
        chunk = rows[start:cycles[-1] + 1]
        targets = next((r["targets"] for r in chunk if r["kind"] == "targets"), [])
        verdicts = {r["intent_id"]: r for r in chunk if r["kind"] == "verdict"}
        fills = {r["intent_id"]: r for r in chunk if r["kind"] == "fill"}
        intents = []
        for r in chunk:
            if r["kind"] != "intent":
                continue
            v, f = verdicts.get(r["id"]), fills.get(r["id"])
            intents.append({
                "id": r["id"], "asset": r["asset"], "side": r["side"], "notional_usd": r["notional_usd"],
                "reduce_only": r["reduce_only"], "reason": r["reason"], "stop_px": r.get("stop_px"),
                "decision": v["decision"] if v else None, "approved_usd": v["approved_notional_usd"] if v else None,
                "rules_fired": v["rules_fired"] if v else [],
                "fill_px": f["fill_px"] if f else None, "filled_usd": f["filled_usd"] if f else None,
                "fee_usd": f["fee_usd"] if f else None,
            })
        summary = chunk[-1]
        return {"ts": summary["ts"], "summary": summary, "targets": targets, "intents": intents}

    def journal(self, kind: str | None, last: int) -> list[dict]:
        return read_journal(kind=kind)[-last:]

    def universe(self) -> list[dict]:
        ctx = self.contexts()
        return [{"asset": a, "day_volume_usd": ctx[a].day_volume_usd, "funding_hourly": ctx[a].funding_hourly,
                 "mid_px": ctx[a].mid_px, "open_interest_usd": ctx[a].open_interest * ctx[a].mark_px}
                for a in self.strategy.universe(ctx)]

    # ---- actions -------------------------------------------------------------

    def run(self, dry_run: bool = False, fetch_depth: bool = True) -> dict:
        if not self.lock.acquire(blocking=False):
            raise RuntimeError("a cycle is already running")
        self.running, self.last_error = True, None
        try:
            summary = run_cycle(self.market, self.strategy, self.adapter, load_limits(), RiskState.load(),
                                fetch_depth=fetch_depth, dry_run=dry_run)
            summary["dry_run"] = dry_run
            summary["ts"] = datetime.now(timezone.utc).isoformat()
            self.last_cycle = summary
            return summary
        except Exception as e:                    # noqa: BLE001
            self.last_error = f"{type(e).__name__}: {e}"
            logging.getLogger(__name__).error("cycle failed\n%s", traceback.format_exc())
            raise
        finally:
            self.running = False
            self.lock.release()

    def run_async(self, dry_run: bool = False) -> None:
        threading.Thread(target=self._safe_run, args=(dry_run,), daemon=True).start()

    def _safe_run(self, dry_run: bool):
        try:
            self.run(dry_run=dry_run)
        except Exception:                          # noqa: BLE001 - already logged
            pass

    def kill(self, on: bool):
        if on:
            RiskState.engage_kill("ui")
            record("event", {"event": "kill_engaged", "by": "ui"})
        else:
            RiskState.release_kill()
            record("event", {"event": "kill_released", "by": "ui"})

    def unlock(self):
        st = RiskState.load()
        reason = st.halt_reason
        st.unlock()
        st.save()
        record("event", {"event": "unlocked", "was": reason, "by": "ui"})

    def reset_paper(self, starting_equity: float = 10_000.0):
        if self.ui["mode"] != "paper":
            raise ValueError("not in paper mode")
        PAPER_PATH.unlink(missing_ok=True)
        st = RiskState.load()
        st.day, st.day_start_equity, st.peak_equity = "", 0.0, 0.0
        st.unlock()
        st.save()
        self._adapter = PaperAdapter(starting_equity=starting_equity)
        record("event", {"event": "paper_reset", "starting_equity": starting_equity, "by": "ui"})

    def flatten(self):
        adapter = self.adapter
        if hasattr(adapter, "set_marks"):
            adapter.set_marks({a: c.mid_px for a, c in self.contexts().items()})
        fills = adapter.flatten_all()
        for f in fills:
            record("fill", f)
        record("event", {"event": "flatten_all", "fills": len(fills), "by": "ui"})
        return len(fills)

    # ---- limits editor -------------------------------------------------------

    def limits_form(self) -> list[dict]:
        limits = load_limits()
        out = []
        for path, label, unit, help_ in LIMIT_FIELDS:
            v = limits
            for k in path.split("."):
                v = v[k]
            out.append({"path": path, "label": label, "unit": unit, "help": help_, "value": v})
        return out

    def save_limits(self, values: dict[str, float]) -> None:
        limits = load_limits()
        for path, v in values.items():
            if path not in {f[0] for f in LIMIT_FIELDS}:
                raise ValueError(f"unknown limit {path}")
            v = float(v)
            if v < 0:
                raise ValueError(f"{path} must be >= 0")
            keys = path.split(".")
            d = limits
            for k in keys[:-1]:
                d = d[k]
            d[keys[-1]] = int(v) if path == "time_stop_grace_hours" else v
        if limits["daily_loss_freeze_pct"] > limits["daily_loss_flatten_pct"]:
            raise ValueError("freeze must be below flatten")
        header = "# Risk limits. Read by desk/risk/engine.py and nowhere else.\n# Edited from the UI; every number here is enforced in code.\n"
        LIMITS_PATH.write_text(header + yaml.safe_dump(limits, sort_keys=False))
        record("event", {"event": "limits_changed", "values": values, "by": "ui"})

    # ---- scheduler -----------------------------------------------------------

    def _next_run(self) -> datetime:
        hh, mm = (int(x) for x in self.ui["schedule_time_utc"].split(":"))
        now = datetime.now(timezone.utc)
        nxt = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if nxt <= now:
            nxt += timedelta(days=1)
        return nxt

    def _scheduler(self):
        last_run_day = None
        last_snapshot = datetime.min.replace(tzinfo=timezone.utc)
        while not self._stop.wait(30):
            try:
                now = datetime.now(timezone.utc)
                if self.ui["schedule_enabled"]:
                    hh, mm = (int(x) for x in self.ui["schedule_time_utc"].split(":"))
                    due = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
                    if due <= now < due + timedelta(minutes=5) and last_run_day != now.date():
                        last_run_day = now.date()
                        logging.getLogger(__name__).info("scheduled cycle")
                        self._safe_run(False)
                if (now - last_snapshot).total_seconds() >= self.ui["snapshot_minutes"] * 60:
                    last_snapshot = now
                    st = self.state()
                    record("snapshot", {"equity": st["equity_usd"], "gross": st["gross_usd"], "n_positions": len(st["positions"])})
            except Exception:                      # noqa: BLE001
                logging.getLogger(__name__).error("scheduler tick failed\n%s", traceback.format_exc())
