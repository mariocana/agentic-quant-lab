"""hlbridge <command>

  status [--live]   equity, positions, risk state, kill switch
  kill / unkill     engage / release the kill switch (file in var/)
  unlock            clear a drawdown / daily-loss halt
  journal [--kind K] [--last N]
  ui [--port 8765] [--reload]
                    start the web UI (the normal way to run the bridge).
                    Compiles every module and parses the dashboard script first.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys

from hlbridge.config import load_limits, settings
from hlbridge.data.hl_market import HLMarket
from hlbridge.risk.state import RiskState, state_path


def _market() -> HLMarket:
    return HLMarket(settings().data_url)


def _risk_state(live: bool) -> RiskState:
    s = settings()
    return RiskState.load(state_path("live" if live else "paper", s.account_address))


def _adapter(live: bool):
    if not live:
        from hlbridge.execution.paper import PaperAdapter
        return PaperAdapter()
    s = settings()
    if not (s.account_address and s.api_wallet_key):
        sys.exit("--live needs HL_ACCOUNT_ADDRESS and HL_API_WALLET_KEY in .env")
    if not s.testnet:
        print("!! MAINNET. Type MAINNET to continue: ", end="", flush=True)
        if input().strip() != "MAINNET":
            sys.exit("aborted")
    from hlbridge.execution.hyperliquid import HyperliquidAdapter
    return HyperliquidAdapter(s.base_url, s.account_address, s.api_wallet_key, s.unified_collateral)


def cmd_status(args):
    adapter = _adapter(args.live)
    if hasattr(adapter, "set_marks"):
        adapter.set_marks({a: c.mid_px for a, c in _market().contexts().items()})
    acc = adapter.account_state()
    st = _risk_state(args.live)
    print(f"adapter      {adapter.name}   exec: {'testnet' if settings().testnet else 'MAINNET'}   data: mainnet")
    print(f"equity       {acc.equity_usd:,.2f}   gross {acc.gross_notional_usd:,.2f}   day {st.day_pnl_pct(acc.equity_usd):+.2%}")
    print(f"peak         {st.peak_equity:,.2f}   halted={st.halted} {st.halt_reason}   kill={RiskState.kill_engaged()}")
    for p in acc.positions:
        print(f"  {p.asset:<12} {p.notional_usd:>12,.2f}  entry {p.entry_px:<12g} mark {p.mark_px:<12g} upnl {p.unrealized_pnl_usd:>9,.2f}  {p.strategy_id or ''}")


def cmd_kill(args):
    RiskState.engage_kill("cli")
    print("kill switch ENGAGED: no new risk will be taken. Closing is still allowed.")


def cmd_unkill(args):
    RiskState.release_kill()
    print("kill switch released")


def cmd_unlock(args):
    st = _risk_state(getattr(args, "live", False))
    print(f"was: halted={st.halted} {st.halt_reason}")
    st.unlock()
    st.save()
    print("unlocked")


def cmd_journal(args):
    from hlbridge.journal.log import read
    rows = read(kind=args.kind)[-args.last:]
    for r in rows:
        print(json.dumps(r))


def cmd_ui(args):
    from hlbridge.ui.server import main as serve
    serve(host=args.host, port=args.port, reload=args.reload, skip_preflight=args.no_preflight)


def main(argv=None):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    p = argparse.ArgumentParser(prog="hlbridge", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("status"); s.add_argument("--live", action="store_true"); s.set_defaults(fn=cmd_status)
    sub.add_parser("kill").set_defaults(fn=cmd_kill)
    sub.add_parser("unkill").set_defaults(fn=cmd_unkill)
    ul = sub.add_parser("unlock"); ul.add_argument("--live", action="store_true"); ul.set_defaults(fn=cmd_unlock)
    j = sub.add_parser("journal"); j.add_argument("--kind"); j.add_argument("--last", type=int, default=20)
    j.set_defaults(fn=cmd_journal)
    u = sub.add_parser("ui")
    u.add_argument("--port", type=int, default=None, help="default 8765, or $PORT")
    u.add_argument("--host", default=None, help="default 127.0.0.1, or $HOST. Anything else needs DESK_PASSWORD")
    u.add_argument("--reload", action="store_true", help="restart the desk when a source file changes (development only)")
    u.add_argument("--no-preflight", action="store_true", help="skip the compile/parse check before starting")
    u.set_defaults(fn=cmd_ui)

    args = p.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
