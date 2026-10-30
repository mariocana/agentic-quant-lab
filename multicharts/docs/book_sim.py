#!/usr/bin/env python3
"""Book di due strategie su LucidFlex 50k: DriftPullback + VaultBreak, IS e OOS.

Somma per giorno i P&L per micro dei due report (stesso parser e stesse regole di
prop_sim.py), poi per ogni combinazione di micro: net, t sui giorni, max DD, giornata
peggiore, pass rate iid e contiguo, e il pass rate a **edge zero** (ogni trade traslato
della sua media: stesso rumore, nessun vantaggio). Dentro il giorno i trade di DPB
vengono prima di quelli di VB: l'ordine vero intraday non e' nei report.

Uso:  python3 mc/docs/book_sim.py
"""
import sys, random, math, statistics as st
sys.path.insert(0, 'mc/docs')
import prop_sim as ps
props = ps.leggi_prop(); ps.usa_prop(props['lucidflex_50k'])
C = ps.COMM_MICRO
R = 'mc/strategies/'
SETS = {'IS 2020-24': (R+'DriftPullback/reports/DPB_S2_IS_mode0.xlsx', R+'VaultBreak/reports/VB_Stage2_IS-intero_costi-onesti.xlsx'),
        'OOS 2025-26': (R+'DriftPullback/reports/DPB_S5_OOS_2025-2026.xlsx', R+'VaultBreak/reports/VB_S5_OOS_2025-2026.xlsx')}
GMAX = ps.PROP['giorni_max'] or ps.GUARDIA_GG
def carica(p): return dict(ps.per_giorno(p, C)[1])
def book(D, V, a, b):
    out = []
    for d in sorted(set(D) | set(V)):
        tr = [(t*a, g*a) for t, g in D.get(d, [])] + [(t*b, g*b) for t, g in V.get(d, [])]
        tr = [(t, g) for t, g in tr if not (t == 0 and g == 0)]
        if tr: out.append((d, tr))
    return out
def stats(gg):
    pnl = [sum(t for t, _ in tr) for _, tr in gg]
    eq = pk = dd = 0
    for x in pnl: eq += x; pk = max(pk, eq); dd = max(dd, pk - eq)
    m, s = st.mean(pnl), st.stdev(pnl)
    return len(pnl), sum(pnl), m / (s / math.sqrt(len(pnl))), dd, min(pnl)
for nome, (pd, pv) in SETS.items():
    D, V = carica(pd), carica(pv)
    comuni = sorted(set(D) | set(V))
    x = [sum(t for t, _ in D.get(d, [])) for d in comuni]; y = [sum(t for t, _ in V.get(d, [])) for d in comuni]
    print('\n=====', nome, '| giorni', len(comuni), '| correlazione P&L giornaliero DPB/VB = %.2f' % st.correlation(x, y))
    print('%-14s %6s %9s %6s %8s %8s | %7s %7s | %7s' % ('book (micro)', 'giorni', 'net $', 't', 'maxDD', 'peggior', 'iid', 'contig', 'edge0'))
    for a, b in [(2, 0), (0, 2), (2, 1), (2, 2), (2, 3), (1, 1), (3, 0), (4, 0)]:
        gg = book(D, V, a, b)
        n, net, t, dd, worst = stats(gg)
        rng = random.Random(20261015)
        e, _ = ps.sim_iid(gg, 1, 10000, GMAX, rng)
        c, _ = ps.sim_contiguo(gg, 1, GMAX)
        ntr = sum(len(tr) for _, tr in gg); mu = net / ntr
        e0, _ = ps.sim_iid([(d, [(t - mu, g - mu) for t, g in tr]) for d, tr in gg], 1, 10000, GMAX, random.Random(1))
        pr = lambda r: 100.0 * r['pass'] / sum(r.values())
        print('%-14s %6d %9.0f %6.2f %8.0f %8.0f | %6.1f%% %6.1f%% | %6.1f%%' % ('DPB %d + VB %d' % (a, b), n, net, t, dd, worst, pr(e), pr(c), pr(e0)))
