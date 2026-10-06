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


def test_limits_edit_keeps_comments():
    """limits.yaml documents the rules as much as it sets them: an edit from the UI
    must not strip the comments."""
    import yaml
    from desk.ui.service import set_yaml_scalar

    src = (ROOT.parent / "config" / "limits.yaml").read_text()
    out = set_yaml_scalar(src, "max_notional_pct_equity.hip3", 0.03)
    out = set_yaml_scalar(out, "max_gross_leverage", 2.5)
    assert yaml.safe_load(out)["max_notional_pct_equity"]["hip3"] == 0.03
    assert yaml.safe_load(out)["max_gross_leverage"] == 2.5
    assert yaml.safe_load(out)["max_notional_pct_equity"]["crypto"] == yaml.safe_load(src)["max_notional_pct_equity"]["crypto"]
    assert out.count("#") == src.count("#"), "comments were lost"
    assert "thin builder-deployed books" in out


def test_limits_edit_round_trips_awkward_floats():
    """A value derived from a ratio (0.000264263414306...) must survive the write:
    the file is the source of truth, so what we store must be what we can re-read."""
    import yaml
    from desk.ui.service import _fmt, set_yaml_scalar

    src = (ROOT.parent / "config" / "limits.yaml").read_text()
    for v in (0.00026426341430613176, 1e-7, 0.1, 15.0, 3.0, 2):
        written = float(_fmt(v))
        out = set_yaml_scalar(src, "daily_loss_freeze_pct", written)
        assert yaml.safe_load(out)["daily_loss_freeze_pct"] == written, v


def test_state_reports_stale_code():
    """Python loads modules once: after an edit the running desk keeps the old code.
    The dashboard banner and the acceptance script both rely on this flag."""
    from desk.ui.service import DeskService

    svc = object.__new__(DeskService)        # no network, no threads
    svc._stale_cache = (0.0, False)
    svc.started_at = 0.0                     # every source file is newer than the epoch
    assert svc.code_changed_since_start() is True
    svc._stale_cache = (0.0, False)
    svc.started_at = 2 ** 40                 # ...and none is newer than the far future
    assert svc.code_changed_since_start() is False
