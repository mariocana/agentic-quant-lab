"""The factory's commands refuse what the process forbids."""
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

import factory.cli as cli
from test_gate import GOOD

SPEC = {
    "id": "toy_v1",
    "hypothesis": "Assets that fell over three days rise over the next one, a toy effect for tests.",
    "who_loses": "Nobody in particular: this spec exists to exercise the factory's commands.",
    "sources": [{"citation": "Test, 2026, A toy", "page": 1, "claim": "a claim made for the test"}],
    "kill_if": "Any validation Sharpe below zero.",
    "strategy": "desk.signals.toy.Toy",
}


@pytest.fixture
def lab(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "STAGING", tmp_path / "staging")
    monkeypatch.setenv("ALPHAQUANT_REGISTRY", str(tmp_path / "trials.jsonl"))
    import alphaquant.registry as reg
    monkeypatch.setattr(reg, "REGISTRY_PATH", tmp_path / "trials.jsonl")
    monkeypatch.setattr(reg.Registry.__init__, "__defaults__", (tmp_path / "trials.jsonl",))
    d = tmp_path / "staging" / "toy_v1"
    d.mkdir(parents=True)
    (d / "spec.yaml").write_text(yaml.safe_dump(SPEC))
    (d / "strategy.py").write_text(GOOD)
    return d


def run(*args):
    class A:
        pass
    a = A()
    a.id, a.yes = args[0], "--yes" in args
    return a


def test_a_page_is_required_for_every_source(lab):
    bad = dict(SPEC, sources=[{"citation": "Test, 2026, A toy", "claim": "a claim made for the test"}])
    (lab / "spec.yaml").write_text(yaml.safe_dump(bad))
    with pytest.raises(SystemExit) as e:
        cli.cmd_check(run("toy_v1"))
    assert e.value.code == 1


def test_freeze_then_any_edit_is_a_new_trial(lab):
    cli.cmd_freeze(run("toy_v1"))
    h = (lab / "FROZEN").read_text().strip()
    assert cli._frozen_hash("toy_v1") == h
    (lab / "strategy.py").write_text(GOOD.replace("LOOKBACK = 3", "LOOKBACK = 4"))
    with pytest.raises(SystemExit, match="new trial"):
        cli._frozen_hash("toy_v1")


def test_the_holdout_needs_a_decision_and_a_passed_validation(lab):
    cli.cmd_freeze(run("toy_v1"))
    with pytest.raises(SystemExit, match="--yes"):
        cli.cmd_holdout(run("toy_v1"))
    with pytest.raises(SystemExit, match="validation has not passed"):
        cli.cmd_holdout(run("toy_v1", "--yes"))
    (lab / "validation.json").write_text(json.dumps({"passed": False, "metrics": {}}))
    with pytest.raises(SystemExit, match="validation has not passed"):
        cli.cmd_holdout(run("toy_v1", "--yes"))


def test_nothing_is_promoted_without_a_passed_holdout(lab):
    with pytest.raises(SystemExit, match="holdout has not passed"):
        cli.cmd_promote(run("toy_v1"))


def test_the_staged_class_loads_from_its_file(lab):
    s = cli._strategy("toy_v1", cli._spec("toy_v1"))
    assert s.id == "toy_v1"
