"""Architectural rules that must hold regardless of what gets added later."""
import ast
from pathlib import Path

from desk.execution.base import round_price, round_size

ROOT = Path(__file__).resolve().parent.parent / "desk"
LLM_MODULES = {"anthropic", "openai", "google", "langchain", "desk.research"}


def imports_of(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            out |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            out.add(n.module)
    return out


def test_risk_and_execution_never_import_llm_code():
    for pkg in ("risk", "execution", "signals"):
        for f in (ROOT / pkg).glob("*.py"):
            bad = {m for m in imports_of(f) if any(m == x or m.startswith(x + ".") for x in LLM_MODULES)}
            assert not bad, f"{f} imports {bad}"


def test_research_never_imports_execution():
    for f in (ROOT / "research").rglob("*.py"):
        bad = {m for m in imports_of(f) if m.startswith("desk.execution")}
        assert not bad, f"{f} imports {bad}"


def test_strategies_and_execution_never_read_limits():
    """Limits are the risk engine's. Strategies size blind; execution sends what it is told."""
    for pkg in ("signals", "execution", "data", "research"):
        for f in (ROOT / pkg).rglob("*.py"):
            assert "load_limits" not in f.read_text() and "limits.yaml" not in f.read_text(), f"{f} reads limits"


def test_hyperliquid_rounding():
    assert round_price(75335.123456, 5) == 75335.0          # 5 sig figs
    assert round_price(0.0033343312, 0) == 0.003334          # 6 decimals max for szDecimals 0
    assert round_price(1.234567, 2) == 1.2346
    assert round_size(0.123456789, 3) == 0.123
