#!/usr/bin/env python3
"""Numeri dell'audit del 12/11/2026 (docs/audit_2026-11-12.md): book DPB / Gold pct1 / Overnight Bias.

Stesso parser e stesso tentativo di prop_sim.py, regole lucidflex_50k. Per ogni book: misure per
micro, distribuzione del P&L giornaliero, pass / fail / aperto a blocchi di 5 giorni, la rovina
(MLL toccato senza target) entro N giorni, e gli stress sull'OOS: ogni trade di una strategia
traslato di una quantita' fissa (stesso rumore, edge diverso).

Solo lettura, nessun verdetto: non e' un gate e non passa da lab.py.

Uso, dalla radice del repo:
    python3 docs/audit_stress.py
"""
import sys, os, random, math, statistics as st
from math import comb
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prop_sim as ps, gate_marginale as gm, book_sim as bs

D = 'strategies/DriftPullback/reports/'
G = 'strategies/GoldAsianRange/reports/'
O = 'strategies/OvernightBiasORB/reports/'
OOS = [('DPB', D + 'DPB_S5_OOS_2025-2026.xlsx', None, None),
       ('GAR', G + 'GAR_S5_OOS_A_pct1_2025-2026.xlsx', '25', 'MGC'),
       ('OBO', O + 'OBO_S5_OOS_2025-2026.xlsx', None, None)]
IS = [('DPB', D + 'DPB_S2_IS_mode0.xlsx', None, None),
      ('GAR', G + 'GAR_S4_IS_A_pct1.xlsx', '25', 'MGC'),
      ('OBO', O + 'OBO_S2_IS_2020-2024.xlsx', None, None)]
N_SIM, SEED, BLOCCO = 20000, 7, 5
BOOK = {'DPB': 1, 'GAR': 1, 'OBO': 1}
DPB2 = {'DPB': 2, 'GAR': 0, 'OBO': 0}


def carica(files, dal, al, prop):
    gm.DAL, gm.AL = dal, al
    return bs.carica(files, prop)


def giorni(P, micro, shift=None):
    """Il book giorno per giorno. shift = {strategia: $ per micro aggiunti a ogni trade}."""
    cal, out = sorted(set().union(*[set(g) for g in P.values()])), []
    for d in cal:
        tr = []
        for k, n in micro.items():
            s = (shift or {}).get(k, 0.0)
            tr += [ps.Trade((x[0] + s) * n, (x[1] + min(s, 0)) * n, x.su * n) for x in P[k].get(d, [])] if n else []
        out.append(tr)
    return out


def sim(gg, gmax=ps.GUARDIA_GG, n=N_SIM):
    rng, esiti, durate = random.Random(SEED), {'pass': 0, 'fail': 0, 'aperto': 0}, []
    for _ in range(n):
        seq = []
        while len(seq) < gmax:
            i = rng.randrange(len(gg))
            seq += [gg[(i + j) % len(gg)] for j in range(BLOCCO)]
        e, g = ps.tentativo(seq[:gmax], 1, gmax)
        esiti[e] += 1
        if e == 'fail':
            durate.append(g)
    return {k: 100.0 * v / n for k, v in esiti.items()}, (st.median(durate) if durate else 0)


def striscia(v):
    run = mx = 0
    for x in v:
        run = run + 1 if x < 0 else 0
        mx = max(mx, run)
    return mx


def per_trade(P):
    medie = {}
    for k in P:
        tr = [x for d in sorted(P[k]) for x in P[k][d]]
        v = [x[0] for x in tr]
        w, l = [x for x in v if x > 0], [x for x in v if x <= 0]
        anni = {}
        for d in P[k]:
            anni[str(d)[:4]] = anni.get(str(d)[:4], 0) + sum(x[0] for x in P[k][d])
        top = sorted(v, reverse=True)[:max(1, len(v) // 20)]
        print('  %s per micro: n %d · WR %.1f%% · avg $%.2f · PF %.2f · perdita max $%.0f · '
              'perdite di fila %d · 5%% migliore = %.0f%% del netto · anni %s'
              % (k, len(v), 100.0 * len(w) / len(v), st.mean(v), sum(w) / -sum(l), min(v),
                 striscia(v), 100.0 * sum(top) / sum(v), {a: round(s) for a, s in sorted(anni.items())}))
        medie[k] = st.mean(v)
    return medie


def per_giorno(nome, gg):
    pnl = [sum(t[0] for t in tr) for tr in gg]
    mu, sd, n = st.mean(pnl), st.stdev(pnl), float(len(pnl))
    print('%s: %d giorni · media $%.1f · sd $%.0f · Sharpe annuo %.2f · P(giorno <= -300) %.1f%% · '
          '<= -600 %.1f%% · <= -1000 %.1f%% · peggiore $%.0f · giorni negativi di fila %d'
          % (nome, n, mu, sd, mu / sd * math.sqrt(252), 100 * sum(x <= -300 for x in pnl) / n,
             100 * sum(x <= -600 for x in pnl) / n, 100 * sum(x <= -1000 for x in pnl) / n,
             min(pnl), striscia([x for x, tr in zip(pnl, gg) if tr])))
    r, d = sim(gg)
    print('    pass %.1f%% · fail %.1f%% · aperto %.1f%% · mediana giorni al fail %.0f'
          % (r['pass'], r['fail'], r['aperto'], d))


def main():
    prop = ps.leggi_prop()[ps.PROP_DEFAULT]
    ps.usa_prop(prop)
    target = ps.TARGET
    print('regole: %s · %d simulazioni a blocchi di %d giorni, seed %d\n' % (prop['nome'], N_SIM, BLOCCO, SEED))
    print('OOS 2025-01-01 -> 2026-10-15')
    Po = carica(OOS, '2025-01-01', '2026-10-15', prop)
    mo = per_trade(Po)
    print('IS 2020-2024')
    Pi = carica(IS, None, None, prop)
    mi = per_trade(Pi)
    print()
    for nome, P in (('OOS', Po), ('IS', Pi)):
        for lab, m in (('DPB 2', DPB2), ('1/1/1', BOOK), ('1/0/1', {'DPB': 1, 'GAR': 0, 'OBO': 1})):
            per_giorno('%s %s' % (nome, lab), giorni(P, m))

    stress = [('base', {}),
              ('Gold alla media IS', {'GAR': mi['GAR'] - mo['GAR']}),
              ('Gold a edge zero', {'GAR': -mo['GAR']}),
              ('slippage +$1 per micro a trade, tutte', {k: -1.0 for k in BOOK}),
              ('edge dimezzato, tutte', {k: -mo[k] / 2 for k in BOOK}),
              ('Gold media IS + slippage $1 + Overnight Bias a meta\'',
               {'GAR': mi['GAR'] - mo['GAR'] - 1, 'DPB': -1.0, 'OBO': -mo['OBO'] / 2 - 1}),
              ('edge zero, tutte', {k: -mo[k] for k in BOOK})]
    print('\nSTRESS sul book 1/1/1, OOS')
    for lab, sh in stress:
        gg = giorni(Po, BOOK, sh)
        r, _ = sim(gg)
        print('  %-52s net $%6.0f · pass %.1f%% · fail %.1f%% · aperto %.1f%%'
              % (lab, sum(t[0] for tr in gg for t in tr), r['pass'], r['fail'], r['aperto']))

    print('\nROVINA: MLL toccato entro N giorni, senza target (base -> stress combinato)')
    ps.TARGET = 10 ** 9
    for lab, m in (('1/1/1', BOOK), ('1/1/0', {'DPB': 1, 'GAR': 1, 'OBO': 0}),
                   ('1/0/1', {'DPB': 1, 'GAR': 0, 'OBO': 1}), ('2/1/1', {'DPB': 2, 'GAR': 1, 'OBO': 1}),
                   ('DPB 2', DPB2)):
        riga = []
        for N in (20, 60, 120):
            a = sim(giorni(Po, m), gmax=N, n=N_SIM // 2)[0]['fail']
            b = sim(giorni(Po, m, stress[5][1]), gmax=N, n=N_SIM // 2)[0]['fail']
            riga.append('%d gg: %.0f%% -> %.0f%%' % (N, a, b))
        print('  %-6s %s' % (lab, ' · '.join(riga)))
    ps.TARGET = target

    p = 0.645
    print('\nRun live: P(<= 6 vinti su 15 | WR 64,5%%) = %.1f%%'
          % (100 * sum(comb(15, k) * p ** k * (1 - p) ** (15 - k) for k in range(7))))


if __name__ == '__main__':
    main()
