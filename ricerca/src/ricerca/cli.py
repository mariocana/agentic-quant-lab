"""I comandi del desk di ricerca. Li chiama la skill /ricerca; il disegno è in docs/desk_ricerca.md.

    ricerca idea <id> --title T --door user|researcher --horizon H --market M [--parent ID]
                                un'idea esiste: una cartella in idee/ e una riga nel registro.
                                Rifiutata se è fuori dal perimetro di perimetro.yaml
    ricerca measure <id>        registra idee/<id>/misura.json (scritto da
                                `python3 -m motore.misura <id> --json`): uno sguardo contato.
                                Rifiutata oltre il tetto mensile; stampa SOPRA / SOTTO SOGLIA
    ricerca kill <id> --step critic|measure|user --reason R
                                chiude l'idea; resta nel registro
    ricerca status              ogni idea, a che punto è, e i conti

Quello che un agente legge in un prompt è una richiesta; quello che questi comandi rifiutano
è un muro. Il verdetto sulla strategia non è qui: è di /lab e della pipeline.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ricerca.perimetro import load_perimeter, this_month
from ricerca.registry import Registry

LAB = Path(__file__).resolve().parents[3]
IDEE = LAB / "ricerca" / "idee"

HYPOTHESIS_TEMPLATE = """# {id}

## Ipotesi
(l'effetto, in una o due frasi, falsificabile)

## Meccanismo
(perche' i prezzi dovrebbero comportarsi cosi')

## Chi perde, e perche' continua a perdere
(chi sta dall'altra parte del trade)

## Fonti
(ogni numero: autore, anno, titolo, rivista, PAGINA, cosa dice)

## Regola eseguibile
(mercato, timeframe, setup, ingresso, stop, target, uscita a tempo, finestra, massimo al giorno)

## Frequenza e costi
(segnali al giorno attesi; l'effetto della fonte contro il costo di un trade)

## Cosa la ucciderebbe, e la soglia della misura
(scritto prima di vedere un numero)
"""

STAGES = (("hypothesis.md", "ipotesi"), ("critique.md", "critica"), ("misura.json", "misurata"),
          ("dossier.md", "dossier"), ("KILLED", "uccisa"))


def _dir(idea: str) -> Path:
    return IDEE / idea


def cmd_idea(a):
    d = _dir(a.id)
    if d.exists():
        sys.exit(f"ricerca/idee/{a.id} esiste già")
    outside = load_perimeter().check_idea(a.horizon, a.market)
    if outside:
        sys.exit("fuori dal perimetro:\n  " + "\n  ".join(outside))
    Registry().register_idea(a.id, a.title, a.door, a.parent, a.horizon, a.market)   # rifiuta prima di scrivere
    d.mkdir(parents=True)
    (d / "hypothesis.md").write_text(HYPOTHESIS_TEMPLATE.format(id=a.id))
    print(f"idea {a.id} registrata ({a.door}, {a.horizon}, {a.market}); creato ricerca/idee/{a.id}/hypothesis.md")


def cmd_measure(a):
    f = _dir(a.id) / "misura.json"
    if not f.exists():
        sys.exit(f"manca ricerca/idee/{a.id}/misura.json: lancia prima la misura con --json")
    per, reg = load_perimeter(), Registry()
    month = reg.ideas_first_measured_in(this_month())
    if a.id not in month and len(month) >= per.misura.idee_al_mese_max:
        sys.exit(f"tetto mensile raggiunto: {len(month)} idee misurate questo mese "
                 f"(massimo {per.misura.idee_al_mese_max} in perimetro.yaml). L'idea aspetta il mese prossimo.")
    metrics = json.loads(f.read_text())
    reg.record_measure(a.id, metrics)
    below = per.check_measure(metrics)
    print("SOPRA SOGLIA" if not below else "SOTTO SOGLIA: " + "; ".join(below))
    print(f"(idee misurate: {len(reg.ideas_first_measured_in(this_month()))} questo mese su "
          f"{per.misura.idee_al_mese_max}, {reg.ideas_measured()} in tutto)")


def cmd_kill(a):
    Registry().kill_idea(a.id, a.step, a.reason)
    if _dir(a.id).exists():
        (_dir(a.id) / "KILLED").write_text(f"{a.step}: {a.reason}\n")
    print(f"idea {a.id} chiusa al passo {a.step}")


def cmd_status(a):
    reg = Registry()
    killed = reg.killed()
    for e in (e for e in reg.entries() if e["kind"] == "idea"):
        d, stage = _dir(e["idea"]), "nata"
        for f, s in STAGES:
            if (d / f).exists():
                stage = s
        if e["idea"] in killed:
            stage = f"uccisa ({killed[e['idea']]['step']})"
        print(f"{e['idea']:32} {stage:18} {e.get('horizon') or '':9} {e.get('market') or '':5} {e['door']}")
    per = load_perimeter()
    print(f"\nidee: {len(reg.ideas())} nate, {reg.ideas_measured()} misurate, {len(killed)} uccise")
    print(f"questo mese alla misura: {len(reg.ideas_first_measured_in(this_month()))} su {per.misura.idee_al_mese_max}")
    print("orizzonti accesi: " + ", ".join(k for k, h in per.orizzonti.items() if h.attivo and h.misura)
          + " · mercati con dati: " + ", ".join(k for k, m in per.mercati.items() if m.dati))


def main():
    ap = argparse.ArgumentParser(prog="ricerca", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(required=True)
    p = sub.add_parser("idea")
    p.add_argument("id")
    p.add_argument("--title", required=True)
    p.add_argument("--door", required=True, choices=("user", "researcher"))
    p.add_argument("--horizon", required=True, help="intraday, daily, swing: acceso in perimetro.yaml")
    p.add_argument("--market", required=True, help="un mercato con dati in perimetro.yaml")
    p.add_argument("--parent")
    p.set_defaults(fn=cmd_idea)
    p = sub.add_parser("measure")
    p.add_argument("id")
    p.set_defaults(fn=cmd_measure)
    p = sub.add_parser("kill")
    p.add_argument("id")
    p.add_argument("--step", required=True, choices=("critic", "measure", "user"))
    p.add_argument("--reason", required=True)
    p.set_defaults(fn=cmd_kill)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
