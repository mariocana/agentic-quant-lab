#!/usr/bin/env python3
"""Rigenera Costi_e_profitti_2026.html dai due CSV nella stessa cartella.

Uso: python3 aggiorna_report_costi.py
- costi_trading_2026.csv   una riga per ogni spesa (prop, formazione, strumenti...)
- entrate_trading_2026.csv una riga per ogni payout o rimborso incassato
"""
import csv, json, os
from collections import defaultdict
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
CATS = ["Prop firm", "Formazione", "Strumenti e dati", "PayPal da attribuire", "Da attribuire"]


def num(s):
    s = (s or "").strip().replace(",", ".")
    return float(s) if s else 0.0


def load():
    costi = []
    with open(os.path.join(HERE, "costi_trading_2026.csv"), newline="") as f:
        for r in csv.DictReader(f):
            if not r.get("data"):
                continue
            r["eur"] = num(r["importo_eur"])
            costi.append(r)
    entrate = []
    p = os.path.join(HERE, "entrate_trading_2026.csv")
    if os.path.exists(p):
        with open(p, newline="") as f:
            for r in csv.DictReader(f):
                if r.get("data"):
                    r["eur"] = num(r["importo_eur"])
                    entrate.append(r)
    return costi, entrate


def month_range(a, b):
    y, m = int(a[:4]), int(a[5:7])
    out = []
    while f"{y:04d}-{m:02d}" <= b:
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def build(costi_all, entrate):
    anno = "2026"
    costi = [c for c in costi_all if c["data"][:4] == anno]
    prima = [c for c in costi_all if c["data"][:4] < anno]
    date_ = [c["data"][:7] for c in costi] + [e["data"][:7] for e in entrate]
    mesi = month_range(min(date_), max(date_))
    per_mese = {m: {k: 0.0 for k in CATS} for m in mesi}
    per_cat = defaultdict(float)
    for c in costi:
        cat = c["categoria"] if c["categoria"] in CATS else "Da attribuire"
        per_mese[c["data"][:7]][cat] += c["eur"]
        per_cat[cat] += c["eur"]
    ent_mese = defaultdict(float)
    for e in entrate:
        ent_mese[e["data"][:7]] += e["eur"]
    corsi = defaultdict(lambda: {"eur": 0.0, "data": "9999"})
    for c in costi_all:
        if c["categoria"] == "Formazione":
            v = corsi[c.get("voce") or c["esercente"]]
            v["eur"] += c["eur"]
            v["data"] = min(v["data"], c["data"])
    prop = [c for c in costi if c["categoria"] == "Prop firm"]
    keys = ("data", "ora", "esercente", "categoria", "voce", "importo_eur", "importo_usd", "nota")
    return dict(
        anno=anno,
        mesi=mesi,
        per_mese=per_mese,
        ent_mese=ent_mese,
        per_cat={k: round(per_cat.get(k, 0), 2) for k in CATS},
        tot_costi=round(sum(c["eur"] for c in costi), 2),
        tot_prima=round(sum(c["eur"] for c in prima), 2),
        tot_entrate=round(sum(e["eur"] for e in entrate), 2),
        n_prop=len(prop),
        corsi=sorted(({"voce": k, "eur": round(v["eur"], 2), "data": v["data"]} for k, v in corsi.items()), key=lambda x: x["data"]),
        costi=[{k: c.get(k, "") for k in keys} for c in costi],
        entrate=[{k: e.get(k, "") for k in ("data", "fonte", "importo_eur", "nota")} for e in entrate],
        oggi=date.today().isoformat(),
    )


TEMPLATE = open(os.path.join(HERE, "_template_costi.html"), encoding="utf-8").read()

if __name__ == "__main__":
    d = build(*load())
    out = TEMPLATE.replace("__DATA__", json.dumps(d, ensure_ascii=False))
    dst = os.path.join(HERE, "Costi_e_profitti_2026.html")
    with open(dst, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"Creato {dst}: costi {d['tot_costi']:.2f} €, entrate {d['tot_entrate']:.2f} €")
