"""The gate generated strategy code passes before anything runs it.

Two parts, and the honest limits of each:

  static   the AST of the file: only whitelisted imports, exactly one Strategy
           subclass with universe() and targets(), no eval/exec/open/getattr and
           no dunder attribute access (the usual ways out of a whitelist), no
           module-level statements but imports, constants and the class.
           It is a linter, not a sandbox: a determined author can get past an
           AST check. That is why the second part exists, and why generated
           code never runs in the trading desk until a human merges it.

  smoke    the class is imported and asked for targets on synthetic data, in a
           separate process, with a timeout and with every credential the lab
           knows blanked from the environment. A third of the synthetic perps
           have only a few bars, like a fresh listing: the first rehearsal on
           real data crashed on exactly that. It must answer, in time, with a
           list of TargetPosition for listed assets only.
"""
from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ALLOWED_IMPORTS = {"__future__", "math", "statistics", "typing",
                   "desk.signals.base", "desk.schemas", "desk.data.hl_market"}
FORBIDDEN_NAMES = {"eval", "exec", "compile", "open", "__import__", "globals", "locals", "vars",
                   "getattr", "setattr", "delattr", "input", "breakpoint", "memoryview", "help",
                   "exit", "quit"}
REQUIRED_METHODS = {"universe", "targets"}
SECRETS = ("HL_API_WALLET_KEY", "HL_ACCOUNT_ADDRESS", "DESK_PASSWORD", "TELEGRAM_BOT_TOKEN",
           "ANTHROPIC_API_KEY", "FRED_API_KEY", "DUNE_API_KEY", "CAPITAL_API_KEY", "CAPITAL_PASSWORD")


@dataclass
class GateReport:
    problems: list[str] = field(default_factory=list)
    class_name: str | None = None

    @property
    def passed(self) -> bool:
        return not self.problems


def static_check(source: str) -> GateReport:
    rep = GateReport()
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        rep.problems.append(f"syntax: {e}")
        return rep

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.ClassDef)):
            continue
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            continue                                            # docstring
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and _is_literal(node.value):
            continue                                            # a constant
        rep.problems.append(f"line {node.lineno}: module-level code ({type(node).__name__})")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name not in ALLOWED_IMPORTS:
                    rep.problems.append(f"line {node.lineno}: import {a.name} is not allowed")
        elif isinstance(node, ast.ImportFrom):
            if node.module not in ALLOWED_IMPORTS:
                rep.problems.append(f"line {node.lineno}: from {node.module} import is not allowed")
        elif isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            rep.problems.append(f"line {node.lineno}: {node.id} is not allowed")
        elif isinstance(node, ast.Attribute) and node.attr.startswith("__") and node.attr != "__init__":
            rep.problems.append(f"line {node.lineno}: dunder attribute {node.attr}")

    classes = [n for n in tree.body if isinstance(n, ast.ClassDef)
               and any(isinstance(b, ast.Name) and b.id == "Strategy" for b in n.bases)]
    if len(classes) != 1:
        rep.problems.append(f"expected exactly one Strategy subclass, found {len(classes)}")
    else:
        c = classes[0]
        rep.class_name = c.name
        methods = {n.name for n in c.body if isinstance(n, ast.FunctionDef)}
        missing = REQUIRED_METHODS - methods
        if missing:
            rep.problems.append(f"{c.name} lacks {sorted(missing)}")
    return rep


def _is_literal(v) -> bool:
    try:
        ast.literal_eval(v)
        return True
    except (ValueError, TypeError, SyntaxError, RecursionError):
        return False


_SMOKE = r'''
import importlib.util, json, math, random, sys
from desk.data.hl_market import Candle
from desk.schemas import AssetContext, TargetPosition
spec = importlib.util.spec_from_file_location("candidate", sys.argv[1])
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
cls = getattr(mod, sys.argv[2])
s = cls()
rnd = random.Random(7)
ctx, candles = {}, {}
need = max(getattr(s, "bars", 30), 30) + 1
for i in range(30):
    a, px, bars = f"C{i:02d}", 100.0, []
    # a third of the perps were listed days ago: on real data a fresh listing has two
    # or three bars, and a strategy that indexes past them crashes the desk's cycle
    for d in range(need if i % 3 else rnd.randint(1, 4)):
        px *= 1 + rnd.gauss(0, 0.04)
        bars.append(Candle(t=d * 86400000, o=px, h=px * 1.01, l=px * 0.99, c=px, v=1e6))
    ctx[a] = AssetContext(asset=a, mark_px=px, mid_px=px, funding_hourly=0.00001, open_interest=1e5,
                          day_volume_usd=5e7, sz_decimals=3, max_leverage=10)
    candles[a] = bars[-getattr(s, "bars", 30):]
uni = s.universe(ctx)
ts = s.targets({a: candles[a] for a in uni}, ctx, 10000.0)
assert isinstance(ts, list) and all(isinstance(t, TargetPosition) for t in ts), "targets must be TargetPosition"
assert all(t.asset in ctx for t in ts), "a target on an asset that is not listed"
assert all(math.isfinite(t.notional_usd) for t in ts), "a non-finite notional"
print(json.dumps({"id": s.id, "universe": len(uni), "targets": len(ts),
                  "gross": sum(abs(t.notional_usd) for t in ts)}))
'''


def clean_env() -> dict[str, str]:
    """The environment of the smoke process: every known secret present but empty,
    so a load_dotenv somewhere down an import chain cannot fill it back in."""
    env = {k: v for k, v in os.environ.items() if k not in SECRETS}
    env.update({k: "" for k in SECRETS})
    return env


def smoke_check(path: Path, class_name: str, timeout_s: float = 10.0) -> GateReport:
    env = clean_env()
    try:
        r = subprocess.run([sys.executable, "-c", _SMOKE, str(path), class_name], env=env,
                           capture_output=True, text=True, timeout=timeout_s)
    except subprocess.TimeoutExpired:
        return GateReport([f"smoke: no answer in {timeout_s:.0f}s"], class_name)
    if r.returncode != 0:
        last = (r.stderr.strip().splitlines() or ["?"])[-1]
        return GateReport([f"smoke: {last}"], class_name)
    rep = GateReport(class_name=class_name)
    out = json.loads(r.stdout.strip().splitlines()[-1])
    if out["targets"] == 0:
        rep.problems.append("smoke: no targets on 30 synthetic perps; the strategy never trades")
    return rep


def check(path: Path) -> GateReport:
    rep = static_check(Path(path).read_text())
    if not rep.passed:
        return rep
    return smoke_check(Path(path), rep.class_name)
