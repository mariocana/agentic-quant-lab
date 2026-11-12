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


# ---- the research desk ----------------------------------------------------------

def idea_args(**kw):
    class A:
        pass
    a = A()
    a.id, a.title, a.door, a.parent, a.step, a.reason = "fine_mese", "Flussi di fine mese", "user", None, None, None
    a.horizon, a.market = "intraday", "NQ"
    for k, v in kw.items():
        setattr(a, k, v)
    return a


def test_an_idea_gets_a_folder_and_a_line_in_the_registry(lab, tmp_path):
    from alphaquant.registry import Registry
    cli.cmd_idea(idea_args())
    assert (tmp_path / "staging" / "fine_mese" / "hypothesis.md").exists()
    assert Registry().ideas() == ["fine_mese"]
    with pytest.raises(SystemExit, match="exists already"):
        cli.cmd_idea(idea_args())


def test_a_measure_is_recorded_from_its_file_and_counted(lab, tmp_path):
    from alphaquant.registry import Registry
    cli.cmd_idea(idea_args())
    with pytest.raises(SystemExit, match="misura.json"):
        cli.cmd_measure(idea_args())
    (tmp_path / "staging" / "fine_mese" / "misura.json").write_text(json.dumps({"eccesso_pp": 0.4, "trade": 900}))
    cli.cmd_measure(idea_args())
    assert Registry().ideas_measured() == 1


def test_an_idea_outside_the_perimeter_is_not_registered(lab, tmp_path):
    from alphaquant.registry import Registry
    for kw in ({"horizon": "daily"}, {"horizon": "scalping"}, {"market": "GC"}, {"market": "YM"}):
        with pytest.raises(SystemExit, match="fuori dal perimetro"):
            cli.cmd_idea(idea_args(**kw))
    assert Registry().ideas() == [] and not (tmp_path / "staging" / "fine_mese").exists()


def test_the_monthly_cap_stops_new_ideas_but_not_a_rerun(lab, tmp_path, capsys):
    import factory.research as research
    cap = research.load_perimeter().misura.idee_al_mese_max
    good = {"errori_standard": 3.4, "dollari_al_giorno_per_micro": 15.0}
    for i in range(cap + 1):
        a = idea_args(id=f"idea_{i}")
        cli.cmd_idea(a)
        (tmp_path / "staging" / a.id / "misura.json").write_text(json.dumps(good))
        if i < cap:
            cli.cmd_measure(a)
    with pytest.raises(SystemExit, match="tetto mensile"):
        cli.cmd_measure(idea_args(id=f"idea_{cap}"))
    cli.cmd_measure(idea_args(id="idea_0"))                 # already measured: a rerun, not a new look


def test_the_floor_is_the_same_for_every_idea(lab, tmp_path, capsys):
    cli.cmd_idea(idea_args())
    f = tmp_path / "staging" / "fine_mese" / "misura.json"
    f.write_text(json.dumps({"errori_standard": 3.2, "dollari_al_giorno_per_micro": 15.0}))
    cli.cmd_measure(idea_args())
    assert "SOPRA SOGLIA" in capsys.readouterr().out
    f.write_text(json.dumps({"errori_standard": 0.45, "dollari_al_giorno_per_micro": 2.0}))
    cli.cmd_measure(idea_args())
    assert "SOTTO SOGLIA" in capsys.readouterr().out


def test_a_killed_idea_is_closed_for_good(lab, tmp_path):
    from alphaquant.registry import Registry, RegistryError
    cli.cmd_idea(idea_args())
    cli.cmd_kill(idea_args(step="critic", reason="nessuno che perde"))
    assert (tmp_path / "staging" / "fine_mese" / "KILLED").read_text().startswith("critic")
    assert "fine_mese" in Registry().killed()
    with pytest.raises(RegistryError):
        cli.cmd_kill(idea_args(step="user", reason="di nuovo"))
