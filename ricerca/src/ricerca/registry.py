"""Il registro delle idee: ogni idea mai nata, e cosa le è successo.

La soglia t della pipeline sale con il numero totale di idee provate (pipeline_live.md,
fase 2): 20 idee senza edge danno un t massimo atteso di 1,9, 50 di 2,25. Quel numero va
contato, e un conto che nessuno scrive è un conto scelto dopo. Quindi ogni idea entra qui
alla nascita, e niente viene mai tolto.

Append-only, e verificabile: ogni voce porta l'hash di quella prima. Modificare, spostare o
cancellare una riga rompe la catena, e verify() dice dove. La storia di git non basta: un
rebase la riscrive.

Voci:
  idea      un'idea esiste: da quale porta è entrata (Mario o il ricercatore), orizzonte,
            mercato e, per una variante, l'idea madre
  measure   la misura preliminare è stata lanciata: uno sguardo ai dati, contato
  killed    l'idea è chiusa, dal critico, dalla misura o da Mario. Resta qui, così non può
            tornare con altre parole
  note      qualunque cosa cambi come si legge un risultato (uno sguardo di troppo, un bug)

Le prime tre righe del file (spec, note, run) sono della fabbrica Hyperliquid, chiusa il
12/11/2026: il verdetto su reversal_v1. Restano perché la catena non si riscrive.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

# RICERCA_REGISTRO manda altrove un test o una prova a secco: una prova non deve aggiungere
# idee al conto vero.
REGISTRY_PATH = Path(os.getenv("RICERCA_REGISTRO") or
                     Path(__file__).resolve().parents[2] / "registro" / "trials.jsonl")
GENESIS = "0" * 64
DOORS = ("user", "researcher")
STEPS = ("critic", "measure", "user")


def entry_hash(body: dict) -> str:
    """JSON canonico: l'ordine delle chiavi e gli spazi non cambiano l'hash."""
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class RegistryError(Exception):
    pass


class Registry:
    def __init__(self, path: Path | None = None):
        self.path = Path(path or REGISTRY_PATH)

    # ---- la catena ----------------------------------------------------------------

    def entries(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [json.loads(x) for x in self.path.read_text().splitlines() if x.strip()]

    def verify(self) -> None:
        prev = GENESIS
        for i, e in enumerate(self.entries()):
            body = {k: v for k, v in e.items() if k != "hash"}
            if e.get("prev") != prev:
                raise RegistryError(f"la voce {i} non segue la {i - 1}: una riga è stata tolta, spostata o modificata")
            if entry_hash(body) != e.get("hash"):
                raise RegistryError(f"la voce {i} è stata modificata dopo essere stata scritta")
            prev = e["hash"]

    def _append(self, kind: str, body: dict) -> dict:
        self.verify()                                   # mai allungare una catena rotta
        es = self.entries()
        entry = {"seq": len(es), "ts": datetime.now(timezone.utc).isoformat(), "kind": kind,
                 "prev": es[-1]["hash"] if es else GENESIS, **body}
        entry["hash"] = entry_hash(entry)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a") as f:
            f.write(json.dumps(entry, sort_keys=True) + "\n")
        return entry

    # ---- cosa si scrive -------------------------------------------------------------

    def register_idea(self, idea: str, title: str, door: str, parent: str | None = None,
                      horizon: str | None = None, market: str | None = None) -> None:
        """Un'idea conta dalla nascita, qualunque cosa le succeda dopo."""
        if door not in DOORS:
            raise ValueError(f"la porta è una di {DOORS}, non {door!r}")
        if idea in self.ideas():
            raise RegistryError(f"l'idea {idea!r} è già nel registro: una variante è un'idea nuova con parent=")
        if parent is not None and parent not in self.ideas():
            raise RegistryError(f"la madre {parent!r} non è un'idea del registro")
        self._append("idea", {"idea": idea, "title": title, "door": door, "parent": parent,
                              "horizon": horizon, "market": market})

    def record_measure(self, idea: str, metrics: dict) -> None:
        self._require_open(idea)
        self._append("measure", {"idea": idea, "metrics": metrics})

    def kill_idea(self, idea: str, step: str, reason: str) -> None:
        if step not in STEPS:
            raise ValueError(f"il passo è uno di {STEPS}, non {step!r}")
        self._require_open(idea)
        self._append("killed", {"idea": idea, "step": step, "reason": reason})

    def note(self, idea: str | None, text: str) -> None:
        self._append("note", {"idea": idea, "text": text})

    def _require_open(self, idea: str) -> None:
        if idea not in self.ideas():
            raise RegistryError(f"l'idea {idea!r} non è nel registro")
        if idea in self.killed():
            raise RegistryError(f"l'idea {idea!r} è stata uccisa: un nuovo tentativo è un'idea nuova con parent=")

    # ---- cosa si legge --------------------------------------------------------------

    def ideas(self) -> list[str]:
        return [e["idea"] for e in self.entries() if e["kind"] == "idea"]

    def killed(self) -> dict[str, dict]:
        return {e["idea"]: e for e in self.entries() if e["kind"] == "killed"}

    def ideas_measured(self) -> int:
        """Quante idee hanno guardato i dati: il numero con cui sale la soglia t della pipeline."""
        return len({e["idea"] for e in self.entries() if e["kind"] == "measure"})

    def ideas_first_measured_in(self, month: str) -> list[str]:
        """Le idee la cui PRIMA misura cade in `month` ("AAAA-MM", UTC): quello che conta il
        tetto mensile. Rimisurare un'idea già misurata non è uno sguardo nuovo."""
        first: dict[str, str] = {}
        for e in self.entries():
            if e["kind"] == "measure":
                first.setdefault(e["idea"], e["ts"])
        return [i for i, ts in first.items() if ts.startswith(month)]
