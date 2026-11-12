"""The trial registry: every strategy ever specified, every time it was run.

Multiple testing cannot be corrected without counting the tests. If fifty
variants are tried and the best one is shown, its Sharpe measures the size of
the search, not an edge; the correction (deflated Sharpe, a threshold that rises
with k) needs k, and a k that nobody records is a k chosen afterwards. So every
spec and every run go here, and nothing is ever removed.

Append-only, and verifiably so: each entry carries the hash of the one before
it. Editing, reordering or deleting a line breaks the chain, and verify() says
where. Git history is not enough for this — a rebase rewrites it.

Entries:
  spec        a strategy frozen before any result is seen: its hash is the id
  run         one evaluation of a spec on one segment (train, validation, holdout)
  holdout     the holdout opened for a spec. Written BEFORE the data is served,
              so a second opening is refused even if the first run crashed
  note        anything that changes how a result should be read (a peek, a bug)

The research desk (docs/desk_ricerca.md) adds three, keyed by the idea's id:
  idea        an idea exists, the moment it is born: who brought it (the user or the
              researcher) and, for a variant, the idea it varies
  measure     the preliminary measure was run on it: a look at the data, counted
  killed      the idea is closed, by the critic, by the measure or by the user. It
              stays here so it cannot come back in other words
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

# ALPHAQUANT_REGISTRY points a test or a dry run elsewhere: a rehearsal must not
# add trials to the real count.
REGISTRY_PATH = Path(os.getenv("ALPHAQUANT_REGISTRY") or
                     Path(__file__).resolve().parents[2] / "registry" / "trials.jsonl")
GENESIS = "0" * 64


def spec_hash(spec: dict) -> str:
    """Canonical JSON, so key order and spacing never change the id."""
    return hashlib.sha256(json.dumps(spec, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class RegistryError(Exception):
    pass


class HoldoutLocked(RegistryError):
    pass


class Registry:
    def __init__(self, path: Path = REGISTRY_PATH):
        self.path = Path(path)

    # ---- the chain -------------------------------------------------------------

    def entries(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [json.loads(x) for x in self.path.read_text().splitlines() if x.strip()]

    def verify(self) -> None:
        prev = GENESIS
        for i, e in enumerate(self.entries()):
            body = {k: v for k, v in e.items() if k != "hash"}
            if e.get("prev") != prev:
                raise RegistryError(f"entry {i} does not follow entry {i - 1}: a line was removed, moved or edited")
            if spec_hash(body) != e.get("hash"):
                raise RegistryError(f"entry {i} was edited after it was written")
            prev = e["hash"]

    def _append(self, kind: str, body: dict) -> dict:
        self.verify()                                   # never extend a broken chain
        es = self.entries()
        entry = {"seq": len(es), "ts": datetime.now(timezone.utc).isoformat(), "kind": kind,
                 "prev": es[-1]["hash"] if es else GENESIS, **body}
        entry["hash"] = spec_hash(entry)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a") as f:
            f.write(json.dumps(entry, sort_keys=True) + "\n")
        return entry

    # ---- what gets written -----------------------------------------------------

    def register_spec(self, spec: dict) -> str:
        """Freeze a spec. Registering the same spec twice returns the same id and
        writes nothing: it is the same trial."""
        h = spec_hash(spec)
        if not any(e["kind"] == "spec" and e["spec_hash"] == h for e in self.entries()):
            self._append("spec", {"spec_hash": h, "spec": spec})
        return h

    def record_run(self, h: str, segment: str, metrics: dict, data_versions: dict, period: tuple[str, str]) -> dict:
        if segment not in ("train", "validation", "holdout"):
            raise ValueError(f"unknown segment {segment!r}")
        self._require_spec(h)
        if segment == "holdout" and not self.holdout_opened(h):
            raise HoldoutLocked("a holdout run without an opened holdout: open it first")
        return self._append("run", {"spec_hash": h, "segment": segment, "metrics": metrics,
                                    "data_versions": data_versions, "period": list(period)})

    def open_holdout(self, h: str) -> None:
        """Once per spec, ever. The entry is written before any data is read."""
        self._require_spec(h)
        if self.holdout_opened(h):
            raise HoldoutLocked(f"the holdout was already opened for {h[:12]}: it is spent")
        self._append("holdout", {"spec_hash": h})

    def note(self, h: str | None, text: str) -> None:
        self._append("note", {"spec_hash": h, "text": text})

    # ---- the research desk: ideas ------------------------------------------------

    def register_idea(self, idea: str, title: str, door: str, parent: str | None = None,
                      horizon: str | None = None, market: str | None = None) -> None:
        """An idea is counted from birth, whatever happens to it next."""
        if door not in ("user", "researcher"):
            raise ValueError(f"door is 'user' or 'researcher', not {door!r}")
        if idea in self.ideas():
            raise RegistryError(f"idea {idea!r} is already registered: a variant is a new idea with parent=")
        if parent is not None and parent not in self.ideas():
            raise RegistryError(f"parent {parent!r} is not a registered idea")
        self._append("idea", {"idea": idea, "title": title, "door": door, "parent": parent,
                              "horizon": horizon, "market": market})

    def record_measure(self, idea: str, metrics: dict) -> None:
        self._require_open(idea)
        self._append("measure", {"idea": idea, "metrics": metrics})

    def kill_idea(self, idea: str, step: str, reason: str) -> None:
        if step not in ("critic", "measure", "user"):
            raise ValueError(f"step is 'critic', 'measure' or 'user', not {step!r}")
        self._require_open(idea)
        self._append("killed", {"idea": idea, "step": step, "reason": reason})

    def _require_open(self, idea: str) -> None:
        if idea not in self.ideas():
            raise RegistryError(f"idea {idea!r} is not registered")
        if idea in self.killed():
            raise RegistryError(f"idea {idea!r} was killed: a new attempt is a new idea with parent=")

    def ideas(self) -> list[str]:
        return [e["idea"] for e in self.entries() if e["kind"] == "idea"]

    def killed(self) -> dict[str, dict]:
        return {e["idea"]: e for e in self.entries() if e["kind"] == "killed"}

    def ideas_measured(self) -> int:
        """How many ideas have looked at the data: the number the pipeline's t
        threshold rises with (pipeline_live.md, fase 2)."""
        return len({e["idea"] for e in self.entries() if e["kind"] == "measure"})

    def ideas_first_measured_in(self, month: str) -> list[str]:
        """Ideas whose FIRST measure fell in `month` ("YYYY-MM", UTC): what the monthly
        cap counts. A rerun of an idea already measured is not a new look."""
        first: dict[str, str] = {}
        for e in self.entries():
            if e["kind"] == "measure":
                first.setdefault(e["idea"], e["ts"])
        return [i for i, ts in first.items() if ts.startswith(month)]

    # ---- what gets read --------------------------------------------------------

    def _require_spec(self, h: str) -> None:
        if not any(e["kind"] == "spec" and e["spec_hash"] == h for e in self.entries()):
            raise RegistryError(f"spec {h[:12]} is not registered: freeze it before running it")

    def holdout_opened(self, h: str) -> bool:
        return any(e["kind"] == "holdout" and e["spec_hash"] == h for e in self.entries())

    def trials(self) -> int:
        """k for the multiple-testing correction: every spec that has ever been
        evaluated on validation, whatever the outcome. Specs that were only
        registered, or only trained, have not been selected on and do not count."""
        return len({e["spec_hash"] for e in self.entries() if e["kind"] == "run" and e["segment"] == "validation"})

    def validation_sharpes(self) -> list[float]:
        return [e["metrics"]["sharpe"] for e in self.entries()
                if e["kind"] == "run" and e["segment"] == "validation" and "sharpe" in e.get("metrics", {})]
