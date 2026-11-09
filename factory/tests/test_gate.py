"""The gate on generated code."""
from pathlib import Path

import pytest

from factory.gate import check, static_check

DESK = Path(__file__).resolve().parents[2] / "trading-desk" / "desk" / "signals"

GOOD = '''
"""Toy strategy."""
from __future__ import annotations
import math
from desk.signals.base import Strategy
from desk.schemas import TargetPosition

LOOKBACK = 3

class Toy(Strategy):
    id = "toy_v1"
    interval = "1d"
    bars = 10
    horizon_hours = 24

    def universe(self, contexts):
        return sorted(contexts)[:10]

    def targets(self, candles, contexts, equity_usd):
        out = []
        for a, cs in candles.items():
            if len(cs) < LOOKBACK + 2:
                continue
            r = cs[-2]["c"] / cs[-2 - LOOKBACK]["c"] - 1
            out.append(TargetPosition(asset=a, notional_usd=-math.copysign(100.0, r), strategy_id=self.id,
                                      horizon_hours=self.horizon_hours, reason="toy"))
        return out
'''


def write(tmp_path, src, name="cand.py"):
    p = tmp_path / name
    p.write_text(src)
    return p


def test_the_desk_s_own_strategy_passes():
    assert check(DESK / "reversal.py").passed


def test_a_well_formed_candidate_passes(tmp_path):
    rep = check(write(tmp_path, GOOD))
    assert rep.passed, rep.problems and rep.class_name == "Toy"


@pytest.mark.parametrize("patch,why", [
    ("import math", "import os"),
    ("import math", "from subprocess import run"),
    ("return sorted(contexts)[:10]", "return eval('sorted(contexts)')"),
    ("return sorted(contexts)[:10]", "return sorted(contexts.__class__.__mro__)"),
    ("return sorted(contexts)[:10]", "return getattr(contexts, 'keys')()"),
    ("LOOKBACK = 3", "LOOKBACK = len(open('/etc/passwd').read())"),
])
def test_the_usual_ways_out_are_refused(tmp_path, patch, why):
    rep = static_check(GOOD.replace(patch, why))
    assert not rep.passed, why


def test_exactly_one_strategy_with_both_methods():
    assert not static_check(GOOD.replace("class Toy(Strategy)", "class Toy(object)")).passed
    assert not static_check(GOOD.replace("def universe", "def universo")).passed


def test_a_strategy_that_hangs_is_stopped(tmp_path):
    src = GOOD.replace("return sorted(contexts)[:10]", "while True:\n            pass")
    rep = check(write(tmp_path, src))
    assert not rep.passed and "no answer" in rep.problems[0]


def test_a_strategy_that_crashes_or_invents_assets_is_refused(tmp_path):
    crash = GOOD.replace("return sorted(contexts)[:10]", "return 1 / 0")
    assert "ZeroDivisionError" in check(write(tmp_path, crash, "a.py")).problems[0]
    ghost = GOOD.replace('TargetPosition(asset=a,', 'TargetPosition(asset="GHOST",')
    assert "not listed" in check(write(tmp_path, ghost, "b.py")).problems[0]


def test_the_smoke_process_sees_no_credentials(monkeypatch):
    from factory.gate import SECRETS, clean_env

    monkeypatch.setenv("HL_API_WALLET_KEY", "0xsecret")
    monkeypatch.setenv("DESK_PASSWORD", "hunter2")
    env = clean_env()
    assert env["HL_API_WALLET_KEY"] == "" and env["DESK_PASSWORD"] == ""
    assert all(env[k] == "" for k in SECRETS)


def test_a_strategy_that_breaks_on_a_fresh_listing_is_refused(tmp_path):
    """Found by the first rehearsal on real data: a perp listed two days ago has two
    bars, and indexing past them crashed. Live, that would fail every cycle."""
    fragile = GOOD.replace("            if len(cs) < LOOKBACK + 2:\n                continue\n", "")
    rep = check(write(tmp_path, fragile))
    assert not rep.passed and "IndexError" in rep.problems[0]
