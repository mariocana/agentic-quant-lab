"""The registry is only worth anything if it cannot be quietly rewritten."""
import json

import pytest

from alphaquant.registry import HoldoutLocked, Registry, RegistryError, spec_hash

SPEC = {"strategy": "desk.signals.reversal.Reversal", "params": {"lookback": 5}}


def test_same_spec_same_id_whatever_the_key_order():
    assert spec_hash({"a": 1, "b": 2}) == spec_hash({"b": 2, "a": 1})
    assert spec_hash(SPEC) != spec_hash({**SPEC, "params": {"lookback": 6}})


def test_registering_twice_is_one_trial(tmp_path):
    r = Registry(tmp_path / "t.jsonl")
    assert r.register_spec(SPEC) == r.register_spec(dict(SPEC))
    assert len(r.entries()) == 1


def test_a_run_needs_a_frozen_spec(tmp_path):
    r = Registry(tmp_path / "t.jsonl")
    with pytest.raises(RegistryError):
        r.record_run(spec_hash(SPEC), "validation", {}, {}, ("2025-01-01", "2025-12-31"))


def test_the_holdout_opens_once_ever(tmp_path):
    r = Registry(tmp_path / "t.jsonl")
    h = r.register_spec(SPEC)
    with pytest.raises(HoldoutLocked):
        r.record_run(h, "holdout", {"sharpe": 1.0}, {}, ("2026-01-01", "2026-10-31"))
    r.open_holdout(h)
    r.record_run(h, "holdout", {"sharpe": 1.0}, {}, ("2026-01-01", "2026-10-31"))
    with pytest.raises(HoldoutLocked):
        r.open_holdout(h)


def test_k_counts_every_spec_judged_on_validation(tmp_path):
    r = Registry(tmp_path / "t.jsonl")
    for lb in (3, 5, 10):
        h = r.register_spec({**SPEC, "params": {"lookback": lb}})
        r.record_run(h, "train", {"sharpe": 2.0}, {}, ("a", "b"))
        if lb != 10:
            r.record_run(h, "validation", {"sharpe": 0.1 * lb}, {}, ("b", "c"))
    assert r.trials() == 2                       # the third was only trained
    assert r.validation_sharpes() == pytest.approx([0.3, 0.5])


@pytest.mark.parametrize("tamper", ["edit", "delete", "swap"])
def test_any_rewrite_of_the_past_is_caught(tmp_path, tamper):
    r = Registry(tmp_path / "t.jsonl")
    for lb in (3, 5, 10):
        h = r.register_spec({**SPEC, "params": {"lookback": lb}})
        r.record_run(h, "validation", {"sharpe": 0.1 * lb}, {}, ("b", "c"))
    lines = r.path.read_text().splitlines()
    if tamper == "edit":                         # a bad result quietly improved
        e = json.loads(lines[1]); e["metrics"]["sharpe"] = 9.9; lines[1] = json.dumps(e, sort_keys=True)
    elif tamper == "delete":                     # a failed trial quietly forgotten
        del lines[1]
    else:
        lines[1], lines[3] = lines[3], lines[1]
    r.path.write_text("\n".join(lines) + "\n")
    with pytest.raises(RegistryError):
        r.verify()
    with pytest.raises(RegistryError):
        r.register_spec({**SPEC, "params": {"lookback": 20}})   # and nothing is appended to it


# ---- the research desk: ideas ---------------------------------------------------

def test_an_idea_is_counted_from_birth_and_only_once(tmp_path):
    r = Registry(tmp_path / "t.jsonl")
    r.register_idea("fine_mese", "Flussi di fine mese sui futures su indice", "user")
    assert r.ideas() == ["fine_mese"]
    with pytest.raises(RegistryError):
        r.register_idea("fine_mese", "la stessa, con altre parole", "researcher")
    r.verify()


def test_a_variant_names_the_idea_it_varies(tmp_path):
    r = Registry(tmp_path / "t.jsonl")
    with pytest.raises(RegistryError):
        r.register_idea("fine_mese_v2", "variante", "user", parent="fine_mese")
    r.register_idea("fine_mese", "madre", "user")
    r.register_idea("fine_mese_v2", "variante", "user", parent="fine_mese")
    assert r.ideas() == ["fine_mese", "fine_mese_v2"]


def test_a_killed_idea_stays_and_cannot_be_measured_or_killed_again(tmp_path):
    r = Registry(tmp_path / "t.jsonl")
    r.register_idea("a", "idea a", "researcher")
    r.kill_idea("a", "critic", "nessuno che perde")
    assert "a" in r.ideas() and r.killed()["a"]["step"] == "critic"
    with pytest.raises(RegistryError):
        r.record_measure("a", {"eccesso_pp": 1.0})
    with pytest.raises(RegistryError):
        r.kill_idea("a", "user", "di nuovo")


def test_every_measured_idea_counts_once_whatever_its_fate(tmp_path):
    r = Registry(tmp_path / "t.jsonl")
    for i in ("a", "b", "c"):
        r.register_idea(i, f"idea {i}", "user")
    r.record_measure("a", {"eccesso_pp": 2.6})
    r.record_measure("a", {"eccesso_pp": 2.6})          # rerun after a bug: still one idea
    r.record_measure("b", {"eccesso_pp": -0.6})
    r.kill_idea("b", "measure", "sotto soglia")
    r.kill_idea("c", "critic", "le fonti non lo dicono")
    assert r.ideas_measured() == 2
    assert r.trials() == 0                               # ideas do not touch the factory's k


def test_door_and_step_are_closed_sets(tmp_path):
    r = Registry(tmp_path / "t.jsonl")
    with pytest.raises(ValueError):
        r.register_idea("a", "idea", "corso")
    r.register_idea("a", "idea", "user")
    with pytest.raises(ValueError):
        r.kill_idea("a", "coder", "no")
