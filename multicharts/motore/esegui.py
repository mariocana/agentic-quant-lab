"""Gira una fase della pipeline col motore e scrive il report nella cartella della strategia.

    python3 -m motore.esegui dpb s1  strategies/DriftPullback/SPEC.md
    python3 -m motore.esegui dpb is  strategies/DriftPullback/SPEC.md --set LongTPpts=40
    python3 -m motore.esegui dpb oos strategies/DriftPullback/SPEC.md

Finestre: s1 = gli ultimi 100 giorni di dati (con anche il report x10, per lo scaling);
is = 2020-01-01 -> 2024-12-31; oos = 2025-01-01 -> ultimo giorno completo dei dati.
File: <cartella della SPEC>/reports/<PREF>_S1_100gg_motore.xlsx (e _x10), <PREF>_S2_IS_2020-2024_motore.xlsx,
<PREF>_S5_OOS_2025-<anno>_motore.xlsx. Il suffisso _motore e' un rerun per il k di lab.py, non una
variante. Poi: python3 docs/lab.py giudica <SPEC> <fase> <report> come per MC.

--set Nome=valore cambia un input (numeri, true/false); va scritto nella SPEC, come su MC.
--pref XYZ sceglie il prefisso dei file (default: il nome della strategia in maiuscolo).
"""
import argparse, datetime as dt, os

from . import dati, report
from .motore import Motore
from .strategie import STRATEGIE

IS = (dt.date(2020, 1, 1), dt.date(2024, 12, 31))
OOS_DAL = dt.date(2025, 1, 1)


def valore(v):
    if v.lower() in ('true', 'false'):
        return v.lower() == 'true'
    try:
        return int(v)
    except ValueError:
        return float(v)


def finestra(fase, simbolo):
    fine = dati.ultimo_giorno(simbolo) - dt.timedelta(days=1)     # l'ultimo giorno puo' essere parziale
    if fase == 's1':
        return fine - dt.timedelta(days=100), fine
    if fase == 'is':
        return IS
    return OOS_DAL, fine


def gira(nome, dal, al, inp, molt=1):
    st = STRATEGIE[nome]
    caldo = dal - dt.timedelta(days=st['riscaldamento'])
    serie = [dati.barre(st['simbolo'], tf, caldo, al) for tf in st['tf']]
    s = st['classe'](*serie[1:], **inp)
    m = Motore(serie[0], s, punto=st['punto'], comm_lato=st['comm_lato'], molt=molt)
    tr = m.gira(dt.datetime.combine(dal, dt.time(0, 0)))
    return [t for t in tr if t.nome_out != 'FINE'], s.p, st


def mostra(p):
    r = os.path.relpath(p)
    return p if r.startswith('..') else r


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('strategia', choices=sorted(STRATEGIE))
    ap.add_argument('fase', choices=['s1', 'is', 'oos'])
    ap.add_argument('spec')
    ap.add_argument('--set', action='append', default=[], metavar='Nome=valore')
    ap.add_argument('--pref')
    a = ap.parse_args()
    if not os.path.isfile(a.spec):
        raise SystemExit('SPEC non trovata: %s' % a.spec)
    st = STRATEGIE[a.strategia]
    inp = {}
    for x in a.set:
        k, v = x.split('=', 1)
        inp[k] = valore(v)
    dal, al = finestra(a.fase, st['simbolo'])
    pref = a.pref or a.strategia.upper()
    cartella = os.path.join(os.path.dirname(os.path.abspath(a.spec)), 'reports')
    nomi = {'s1': '%s_S1_100gg_motore' % pref, 'is': '%s_S2_IS_2020-2024_motore' % pref,
            'oos': '%s_S5_OOS_2025-%d_motore' % (pref, al.year)}
    comp = '%d Minutes' % st['tf'][0]
    giri = [(1, nomi[a.fase])] + ([(10, nomi[a.fase] + '_x10')] if a.fase == 's1' else [])
    for molt, base in giri:
        tr, p, _ = gira(a.strategia, dal, al, inp, molt)
        path = os.path.join(cartella, base + '.xlsx')
        net = report.scrivi(path, tr, st, p, a.strategia, comp, dal, al)
        print('%s: %d trade, net $%.0f, %s -> %s' % (mostra(path), len(tr), net, dal, al))
    print('Ora: python3 docs/lab.py giudica %s %s %s%s' % (
        mostra(os.path.abspath(a.spec)), a.fase, mostra(os.path.join(cartella, giri[0][1] + '.xlsx')),
        ' --x10 %s' % mostra(os.path.join(cartella, giri[1][1] + '.xlsx')) if a.fase == 's1' else ''))


if __name__ == '__main__':
    main()
