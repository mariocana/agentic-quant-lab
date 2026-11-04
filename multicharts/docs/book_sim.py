#!/usr/bin/env python3
"""Book di piu' strategie su LucidFlex 50k: griglia di micro, pass rate e pass rate a edge zero.

Somma per giorno i P&L per micro dei report (stesso parser, stessi costi per strumento e stesse
regole di gate_marginale.py e prop_sim.py), poi per ogni combinazione di micro: net, t sui
giorni, max DD, giornata peggiore, pass rate iid e contiguo, e il pass rate a **edge zero**
(ogni trade traslato della media della sua strategia: stesso rumore, nessun vantaggio). La
distanza fra pass rate e edge zero e' la parte che viene dall'edge e non dalla fortuna.

Dentro il giorno i trade seguono l'ordine delle strategie sulla riga di comando: l'ordine vero
intraday non e' nei report. Le size scelte guardando questa tabella sono scelte sugli stessi
dati: il pass rate vero sara' piu' basso.

Uso:
    python3 docs/book_sim.py \\
        --strat DPB=strategies/DriftPullback/reports/DPB_S5_OOS_2025-2026.xlsx \\
        --strat GAR=strategies/GoldAsianRange/reports/GAR_S5_OOS_A_pct1_2025-2026.xlsx:25:2.60 \\
        --strat VB8=strategies/VaultBreak/reports/VB8_S5_OOS_2025-2026.xlsx \\
        --micro 2/0/0,2/1/0,1/1/0,1/1/1 --dal 2025-01-01 --dal 2026-01-01

    --strat NOME=file[:costo_report:costo_micro]  costi andata e ritorno in $, come in
                                                  gate_marginale.py (default: NQ -> MNQ)
    --micro a/b/c,...   combinazioni di micro, nell'ordine delle --strat
                        (default: tutte da 0 a 2, almeno una strategia accesa)
    --dal AAAA-MM-GG    inizio della finestra; ripetibile, una tabella per finestra
    --al AAAA-MM-GG     fine, uguale per tutte: l'ultimo giorno comune ai report, altrimenti
                        negli ultimi giorni il book ha solo le strategie con il report piu' lungo
    --sim N             simulazioni per combinazione (default 10000)
"""
import sys, os, random, math, itertools, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate_marginale as gm
import prop_sim as ps

SEED = 20261029


def argomenti():
    arg, strat, micro, dal, n = sys.argv[1:], [], None, [], 10000
    while arg:
        k = arg.pop(0)
        if k == '--strat':
            nome, spec = arg.pop(0).split('=', 1)
            parti = spec.split(':')                     # file[:costo_report:costo_micro]
            strat.append((nome, ':'.join([parti[0], '1'] + parti[1:])))
        elif k == '--micro':
            micro = [tuple(int(x) for x in c.split('/')) for c in arg.pop(0).split(',')]
        elif k == '--dal':
            dal.append(arg.pop(0))
        elif k == '--al':
            gm.AL = arg.pop(0)
        elif k == '--sim':
            n = int(arg.pop(0))
        else:
            raise SystemExit('argomento sconosciuto: %s\n%s' % (k, __doc__))
    if not strat:
        raise SystemExit(__doc__)
    if micro is None:
        micro = [c for c in itertools.product(range(3), repeat=len(strat)) if any(c)]
    if any(len(c) != len(strat) for c in micro):
        raise SystemExit('--micro: ogni combinazione vuole %d numeri' % len(strat))
    return strat, micro, dal or [None], n


def tabella(strat, micro, dal, n, gmax):
    gm.DAL = dal
    P = {nome: gm.carica(spec)[1] for nome, spec in strat}
    nomi = [nome for nome, _ in strat]
    cal = sorted(set().union(*[set(g) for g in P.values()]))
    serie = {k: [sum(t for t, _ in P[k].get(d, [])) for d in cal] for k in nomi}
    corr = ' · '.join('%s/%s %.2f' % (a, b, st.correlation(serie[a], serie[b]))
                      for a, b in itertools.combinations(nomi, 2)) if len(nomi) > 1 else '-'
    print('\n===== %s | %d giorni | correlazione P&L giornaliero: %s' % (
        'dal ' + dal if dal else 'tutto il report', len(cal), corr))
    print('%-14s %9s %6s %7s %8s | %6s %7s | %6s' % (
        '/'.join(nomi), 'net $', 't', 'maxDD', 'peggior', 'iid', 'contig', 'edge0'))

    media = {k: st.mean([t for d in P[k] for t, _ in P[k][d]] or [0]) for k in nomi}
    for c in micro:
        m = dict(zip(nomi, c))
        giorni = [[(t * m[k], g * m[k]) for k in nomi for t, g in P[k].get(d, [])] for d in cal]
        zero = [[((t - media[k]) * m[k], (g - media[k]) * m[k]) for k in nomi for t, g in P[k].get(d, [])]
                for d in cal]
        pnl = [sum(t for t, _ in tr) for tr in giorni]
        eq = pk = dd = 0
        for x in pnl:
            eq += x
            pk = max(pk, eq)
            dd = max(dd, pk - eq)
        s = st.stdev(pnl)
        t = st.mean(pnl) / (s / math.sqrt(len(pnl))) if s else 0.0
        rng, ok, ok0 = random.Random(SEED), 0, 0
        for _ in range(n):
            idx = [rng.randrange(len(cal)) for _ in range(gmax)]
            ok += ps.tentativo([giorni[i] for i in idx], 1, gmax)[0] == 'pass'
            ok0 += ps.tentativo([zero[i] for i in idx], 1, gmax)[0] == 'pass'
        oltre = ' DLL' if min(pnl) < -ps.DLL else ''
        print('%-14s %9.0f %6.2f %7.0f %8.0f%s | %5.1f%% %6.1f%% | %5.1f%%' % (
            '/'.join(map(str, c)), sum(pnl), t, dd, min(pnl), oltre,
            100.0 * ok / n, gm.contiguo(giorni, gmax), 100.0 * ok0 / n))


def main():
    ps.usa_prop(ps.leggi_prop()[ps.PROP_DEFAULT])   # prima di caricare: fissa il costo per micro
    strat, micro, finestre, n = argomenti()
    gmax = ps.PROP['giorni_max'] or ps.GUARDIA_GG
    print('regole: %s · %d simulazioni per combinazione, seed %d · DLL = giornata peggiore oltre $%.0f'
          % (ps.PROP['nome'], n, SEED, ps.DLL))
    for dal in finestre:
        tabella(strat, micro, dal, n, gmax)


if __name__ == '__main__':
    main()
