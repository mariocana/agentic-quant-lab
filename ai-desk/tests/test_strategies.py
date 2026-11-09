"""The strategy registry and shadow mode."""
import random
from pathlib import Path

import pytest

from desk.config import VAR, load_limits
from desk.data.hl_market import Candle
from desk.schemas import AssetContext
from desk.shadow import run_shadow, shadow_state
from desk.signals.registry import StrategyConfigError, active, load_strategies, shadows
from desk.signals.reversal import Reversal


def _cfg(tmp_path, body):
    p = tmp_path / "s.yaml"
    p.write_text(body)
    return p


def test_the_shipped_config_runs_reversal_v1_active():
    entries = load_strategies()
    assert active(entries).id == "reversal_v1" and isinstance(active(entries).strategy, Reversal)


@pytest.mark.parametrize("body,why", [
    ("strategies:\n - {id: x, class: os.system, mode: shadow}\n", "outside desk.signals"),
    ("strategies:\n - {id: reversal_v1, class: desk.signals.reversal.Reversal, mode: active}\n"
     " - {id: reversal_v1, class: desk.signals.reversal.Reversal, mode: shadow}\n", "duplicate"),
    ("strategies:\n - {id: other, class: desk.signals.reversal.Reversal, mode: shadow}\n", "its id is"),
    ("strategies:\n - {id: reversal_v1, class: desk.signals.reversal.Reversal, mode: live}\n", "active or shadow"),
])
def test_bad_configs_are_refused(tmp_path, body, why):
    with pytest.raises(StrategyConfigError, match=why):
        load_strategies(_cfg(tmp_path, body))


def test_one_active_at_most(tmp_path, monkeypatch):
    class R2(Reversal):
        id = "reversal_v2"
    import desk.signals.reversal as mod
    monkeypatch.setattr(mod, "R2", R2, raising=False)
    body = ("strategies:\n - {id: reversal_v1, class: desk.signals.reversal.Reversal, mode: active}\n"
            " - {id: reversal_v2, class: desk.signals.reversal.R2, mode: active}\n")
    with pytest.raises(StrategyConfigError, match="more than one active"):
        load_strategies(_cfg(tmp_path, body))
    ok = load_strategies(_cfg(tmp_path, body.replace("R2, mode: active", "R2, mode: shadow")))
    assert [e.id for e in shadows(ok)] == ["reversal_v2"]


class FakeMarket:
    """15 perps with 30 daily bars each: enough for the reversal to take positions."""

    def __init__(self, seed=1):
        rnd = random.Random(seed)
        self.series = {}
        for i in range(15):
            px, bars = 100.0, []
            for d in range(31):
                px *= 1 + rnd.gauss(0, 0.05)
                bars.append(Candle(t=d * 86_400_000, o=px, h=px, l=px, c=px, v=1e6))
            self.series[f"C{i:02d}"] = bars

    def contexts(self):
        return {a: AssetContext(asset=a, mark_px=b[-2]["c"], mid_px=b[-2]["c"], funding_hourly=0.0,
                                open_interest=0.0, day_volume_usd=1e8, sz_decimals=3, max_leverage=3)
                for a, b in self.series.items()}

    def candles(self, asset, interval, bars):
        return self.series[asset][-bars:]

    def book_depth_10bps(self, asset):
        return 100.0, 1e9


def test_a_shadow_trades_on_paper_in_its_own_folder_only(tmp_path):
    main_journal = VAR / "journal.jsonl"
    before = main_journal.stat().st_mtime if main_journal.exists() else None
    summary = run_shadow(FakeMarket(), Reversal(universe_size=15, min_day_volume_usd=1e6), load_limits(), root=tmp_path)
    assert summary["fills"] > 0
    d = tmp_path / "reversal_v1"
    assert {p.name for p in d.iterdir()} == {"paper.json", "risk.json", "journal.jsonl"}
    st = shadow_state("reversal_v1", root=tmp_path)
    assert st["positions"] > 0 and st["equity_usd"] < 10_000          # paid its fees
    after = main_journal.stat().st_mtime if main_journal.exists() else None
    assert before == after, "a shadow wrote into the desk's journal"


def test_a_shadow_has_no_way_to_the_exchange():
    """By construction: the shadow module never imports the live adapter."""
    from tests.test_boundaries import imports_of

    src = Path(__file__).resolve().parent.parent / "desk" / "shadow.py"
    assert not {m for m in imports_of(src) if m.startswith("desk.execution.hyperliquid")}
