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
