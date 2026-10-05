"""desk <command>

  status            equity, positions, risk state, kill switch
  run [--live] [--dry-run] [--no-depth]
                    one cycle (paper by default)
  kill / unkill     engage / release the kill switch (file in var/)
  unlock            clear a drawdown / daily-loss halt
  universe          what the strategy would trade right now
  journal [--kind K] [--last N]
  ui [--port 8765]  start the web UI (the normal way to run the desk)
"""
from __future__ import annotations

import argparse
import json
import logging
import sys

from desk.config import load_limits, settings
from desk.data.hl_market import HLMarket
from desk.risk.state import RiskState


def _market() -> HLMarket:
    return HLMarket(settings().data_url)


def _adapter(live: bool):
    if not live:
        from desk.execution.paper import PaperAdapter
        return PaperAdapter()
    s = settings()
    if not (s.account_address and s.api_wallet_key):
        sys.exit("--live needs HL_ACCOUNT_ADDRESS and HL_API_WALLET_KEY in .env")
    if not s.testnet:
        print("!! MAINNET. Type MAINNET to continue: ", end="", flush=True)
        if input().strip() != "MAINNET":
            sys.exit("aborted")
    from desk.execution.hyperliquid import HyperliquidAdapter
    return HyperliquidAdapter(s.base_url, s.account_address, s.api_wallet_key)


def cmd_status(args):
    adapter = _adapter(args.live)
    if hasattr(adapter, "set_marks"):
        adapter.set_marks({a: c.mid_px for a, c in _market().contexts().items()})
    acc = adapter.account_state()
    st = RiskState.load()
    print(f"adapter      {adapter.name}   exec: {'testnet' if settings().testnet else 'MAINNET'}   data: mainnet")
    print(f"equity       {acc.equity_usd:,.2f}   gross {acc.gross_notional_usd:,.2f}   day {st.day_pnl_pct(acc.equity_usd):+.2%}")
    print(f"peak         {st.peak_equity:,.2f}   halted={st.halted} {st.halt_reason}   kill={RiskState.kill_engaged()}")
    for p in acc.positions:
        print(f"  {p.asset:<12} {p.notional_usd:>12,.2f}  entry {p.entry_px:<12g} mark {p.mark_px:<12g} upnl {p.unrealized_pnl_usd:>9,.2f}  {p.strategy_id or ''}")


def cmd_run(args):
    from desk.loop import run_cycle
    from desk.signals.reversal import Reversal
    summary = run_cycle(_market(), Reversal(), _adapter(args.live), load_limits(), RiskState.load(),
                        fetch_depth=not args.no_depth, dry_run=args.dry_run)
    print(json.dumps(summary, indent=2))


def cmd_universe(args):
    from desk.signals.reversal import Reversal
    m = _market()
    ctx = m.contexts()
    for a in Reversal().universe(ctx):
        c = ctx[a]
        print(f"{a:<10} vol24h {c.day_volume_usd/1e6:>9,.1f}M  funding/h {c.funding_hourly:+.5%}  mid {c.mid_px:g}")


def cmd_kill(args):
    RiskState.engage_kill("cli")
    print("kill switch ENGAGED: no new risk will be taken. Closing is still allowed.")


def cmd_unkill(args):
    RiskState.release_kill()
    print("kill switch released")


def cmd_unlock(args):
    st = RiskState.load()
    print(f"was: halted={st.halted} {st.halt_reason}")
    st.unlock()
    st.save()
    print("unlocked")


def cmd_journal(args):
    from desk.journal.log import read
    rows = read(kind=args.kind)[-args.last:]
    for r in rows:
        print(json.dumps(r))


def cmd_ui(args):
    from desk.ui.server import main as serve
    serve(port=args.port)


def main(argv=None):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    p = argparse.ArgumentParser(prog="desk", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("status"); s.add_argument("--live", action="store_true"); s.set_defaults(fn=cmd_status)
    r = sub.add_parser("run")
    r.add_argument("--live", action="store_true"); r.add_argument("--dry-run", action="store_true")
    r.add_argument("--no-depth", action="store_true", help="skip per-intent book fetch (faster, rule flagged)")
    r.set_defaults(fn=cmd_run)
    sub.add_parser("universe").set_defaults(fn=cmd_universe)
    sub.add_parser("kill").set_defaults(fn=cmd_kill)
    sub.add_parser("unkill").set_defaults(fn=cmd_unkill)
    sub.add_parser("unlock").set_defaults(fn=cmd_unlock)
    j = sub.add_parser("journal"); j.add_argument("--kind"); j.add_argument("--last", type=int, default=20)
    j.set_defaults(fn=cmd_journal)
    u = sub.add_parser("ui"); u.add_argument("--port", type=int, default=8765); u.set_defaults(fn=cmd_ui)

    args = p.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
