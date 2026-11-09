"""The factory's commands. Agents call some of them; the human calls the rest.

    factory new <id>                 a staging folder with empty hypothesis and spec
    factory check <id>               spec valid? code through the static gate and the smoke run?
    factory freeze <id>              spec + code hash into the registry: from now on, a trial
    factory evaluate <id>            validation run; verdict to the screen, numbers to a file
    factory holdout <id> --yes       the one look at the holdout. Human only.
    factory promote <id>             copy into trading-desk as a shadow strategy
    factory status                   every staged idea and where it stands

The information barrier: `evaluate` prints only PASS/FAIL and the names of the
failing checks. The numbers go to staging/<id>/validation.json, which the coder
is never pointed at: a coder that sees a Sharpe tunes to it, and every tune is a
trial nobody counted.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import yaml

LAB = Path(__file__).resolve().parents[3]
STAGING = LAB / "factory" / "staging"
DESK = LAB / "trading-desk"

HYPOTHESIS_TEMPLATE = """# {id}

## Ipotesi
(l'effetto, in una o due frasi)

## Chi perde, e perche continua a perdere
(chi sta dall'altra parte del trade)

## Fonti
(ogni numero preso da un paper: autore, anno, titolo, PAGINA, cosa dice)

## Cosa la ucciderebbe
(scritto prima di vedere un risultato)
"""


def _dir(sid: str) -> Path:
    return STAGING / sid


def _code_hash(sid: str) -> str:
    return hashlib.sha256((_dir(sid) / "strategy.py").read_bytes()).hexdigest()


def _spec(sid: str):
    from factory.spec import load_spec
    return load_spec(_dir(sid) / "spec.yaml")


def _strategy(sid: str, spec):
    """Load the staged class from its file, not from desk.signals: it is not there yet."""
    from factory.gate import static_check
    path = _dir(sid) / "strategy.py"
    name = static_check(path.read_text()).class_name
    mod_spec = importlib.util.spec_from_file_location(f"staged_{sid}", path)
    mod = importlib.util.module_from_spec(mod_spec)
    mod_spec.loader.exec_module(mod)
    return getattr(mod, name)(**spec.params)


def _registry_spec(sid: str) -> dict:
    return {**_spec(sid).as_registry_spec(), "code_sha256": _code_hash(sid)}


def cmd_new(a):
    d = _dir(a.id)
    if d.exists():
        sys.exit(f"{d} exists already")
    d.mkdir(parents=True)
    (d / "hypothesis.md").write_text(HYPOTHESIS_TEMPLATE.format(id=a.id))
    print(f"created {d.relative_to(LAB)}/hypothesis.md")


def cmd_check(a):
    from factory.gate import check
    problems = []
    try:
        _spec(a.id)
    except Exception as e:                        # noqa: BLE001 - every problem is reported
        problems.append(f"spec.yaml: {e}")
    if (_dir(a.id) / "strategy.py").exists():
        problems += check(_dir(a.id) / "strategy.py").problems
    else:
        problems.append("strategy.py: missing")
    print("PASS" if not problems else "FAIL\n  " + "\n  ".join(problems))
    sys.exit(0 if not problems else 1)


def cmd_freeze(a):
    from alphaquant.registry import Registry
    from factory.gate import check
    rep = check(_dir(a.id) / "strategy.py")
    if not rep.passed:
        sys.exit("the code does not pass the gate: run factory check")
    h = Registry().register_spec(_registry_spec(a.id))
    (_dir(a.id) / "FROZEN").write_text(h + "\n")
    print(f"frozen: {h}\nfrom here any change to spec.yaml or strategy.py is a new trial")


def _frozen_hash(sid: str) -> str:
    f = _dir(sid) / "FROZEN"
    if not f.exists():
        sys.exit("not frozen: run factory freeze first")
    from alphaquant.registry import spec_hash
    h = f.read_text().strip()
    if spec_hash(_registry_spec(sid)) != h:
        sys.exit("spec.yaml or strategy.py changed after freezing: that is a new trial, freeze it again")
    return h


def _run(sid: str, segment: str, validation_metrics=None):
    from alphaquant.evaluate import evaluate
    from desk.config import load_limits
    _frozen_hash(sid)
    spec = _spec(sid)
    return evaluate(_registry_spec(sid), _strategy(sid, spec), segment, load_limits(),
                    validation_metrics=validation_metrics)


def _write_report(sid: str, ev, name: str):
    out = {"spec_hash": ev.spec_hash, "segment": ev.segment, "period": [str(p) for p in ev.period],
           "passed": ev.gate.passed, "checks": [c.__dict__ for c in ev.gate.checks],
           "metrics": ev.metrics.as_dict(), "report": ev.gate.report()}
    (_dir(sid) / f"{name}.json").write_text(json.dumps(out, indent=2, default=str))


def cmd_evaluate(a):
    ev = _run(a.id, "validation")
    _write_report(a.id, ev, "validation")
    print("PASS" if ev.gate.passed else "FAIL: " + ", ".join(c.name for c in ev.gate.failures))
    print(f"(numbers in factory/staging/{a.id}/validation.json; not for the coder)")


def cmd_holdout(a):
    if not a.yes:
        sys.exit("the holdout opens once, ever, for this spec. Re-run with --yes if that is the decision.")
    val = _dir(a.id) / "validation.json"
    if not val.exists() or not json.loads(val.read_text())["passed"]:
        sys.exit("validation has not passed: the holdout is not worth spending")
    from alphaquant.validation.portfolio import PortfolioMetrics
    vm = PortfolioMetrics(**{k: (float("inf") if v is None else v)
                             for k, v in json.loads(val.read_text())["metrics"].items()})
    ev = _run(a.id, "holdout", validation_metrics=vm)
    _write_report(a.id, ev, "holdout")
    print(ev.gate.report())


def cmd_promote(a):
    hold = _dir(a.id) / "holdout.json"
    if not hold.exists() or not json.loads(hold.read_text())["passed"]:
        sys.exit("the holdout has not passed: nothing to promote")
    spec = _spec(a.id)
    module, cls = spec.strategy.rsplit(".", 1)
    target = DESK / (module.replace(".", "/") + ".py")
    if target.exists():
        sys.exit(f"{target.relative_to(LAB)} exists already")
    shutil.copy(_dir(a.id) / "strategy.py", target)
    cfg = DESK / "config" / "strategies.yaml"
    raw = yaml.safe_load(cfg.read_text())
    raw["strategies"].append({"id": spec.id, "class": spec.strategy, "params": spec.params, "mode": "shadow"})
    cfg.write_text(cfg.read_text().split("strategies:")[0] + yaml.safe_dump(raw, sort_keys=False, allow_unicode=True))
    print(f"copied to {target.relative_to(LAB)} and added to strategies.yaml as shadow.\n"
          "Next: a branch, a commit, a pull request. The merge is the human gate.")


def cmd_status(a):
    from alphaquant.registry import Registry
    reg = Registry()
    for d in sorted(p for p in STAGING.iterdir() if p.is_dir()) if STAGING.exists() else []:
        stage = "idea"
        for f, s in (("spec.yaml", "spec"), ("strategy.py", "code"), ("FROZEN", "frozen"),
                     ("validation.json", "validated"), ("holdout.json", "holdout")):
            if (d / f).exists():
                stage = s
        extra = ""
        for f in ("validation.json", "holdout.json"):
            if (d / f).exists():
                extra += f" {f.split('.')[0]}={'PASS' if json.loads((d / f).read_text())['passed'] else 'FAIL'}"
        print(f"{d.name:30} {stage:10}{extra}")
    print(f"\nk (specs judged on validation): {reg.trials()}")


def main():
    ap = argparse.ArgumentParser(prog="factory")
    sub = ap.add_subparsers(required=True)
    for name, fn in (("new", cmd_new), ("check", cmd_check), ("freeze", cmd_freeze),
                     ("evaluate", cmd_evaluate), ("promote", cmd_promote)):
        p = sub.add_parser(name)
        p.add_argument("id")
        p.set_defaults(fn=fn)
    p = sub.add_parser("holdout")
    p.add_argument("id")
    p.add_argument("--yes", action="store_true")
    p.set_defaults(fn=cmd_holdout)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
