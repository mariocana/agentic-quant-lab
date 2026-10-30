#!/usr/bin/env python3
"""Fase 3b -- gate marginale: la candidata alza il pass rate del book fuori campione?

Pre-registrazione in `pipeline_semplice.md` (29/10/2026). Book e candidata sono report
MultiCharts OOS a 1 contratto; ognuno con i suoi micro. Regole: LucidFlex 50k da
`prop_firms.ini`, stesso parser e stesso tentativo di prop_sim.py.

Il confronto e' a **numeri casuali comuni**: ogni simulazione pesca gli stessi giorni del
calendario per il book da solo e per il book con la candidata, cosi la differenza e'
l'effetto della candidata e non del campionamento. I giorni sono l'unione dei giorni di
trading; dentro il giorno i trade del book vengono prima di quelli della candidata.

Uso:
    python3 mc/docs/gate_marginale.py --book DPB_S5_OOS.xlsx:2 --cand ORB_S5_OOS.xlsx:1
    (--book si ripete per un book di piu strategie)
"""
import sys, os, random, math, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prop_sim as ps

N_SIM      = 20000
SEED       = 20261029
SOGLIA_IID = 2.0      # punti percentuali, pre-registrata il 29/10/2026


def carica(spec):
    path, micro = spec.rsplit(':', 1)
    return os.path.basename(path), dict(ps.per_giorno(path, ps.COMM_MICRO)[1]), float(micro)


def giorni_book(parti, calendario):
    out = []
    for d in calendario:
        tr = []
        for _, gg, m in parti:
            tr += [(t * m, g * m) for t, g in gg.get(d, [])]
        out.append(tr)
    return out


def contiguo(seq, gmax):
    esiti = []
    for i in range(max(1, len(seq) - gmax)):
        esiti.append(ps.tentativo(seq[i:], 1, gmax)[0] == 'pass')
    return 100.0 * sum(esiti) / len(esiti)


def main():
    ps.usa_prop(ps.leggi_prop()[ps.PROP_DEFAULT])   # prima di caricare: fissa il costo per micro
    arg = sys.argv[1:]
    book, cand = [], None
    while arg:
        k = arg.pop(0)
        if k == '--book':
            book.append(carica(arg.pop(0)))
        elif k == '--cand':
            cand = carica(arg.pop(0))
    if not book or cand is None:
        raise SystemExit(__doc__)
    gmax = ps.PROP['giorni_max'] or ps.GUARDIA_GG

    cal = sorted(set().union(*[set(gg) for _, gg, _ in book + [cand]]))
    solo = giorni_book(book, cal)
    con = giorni_book(book + [cand], cal)

    rng = random.Random(SEED)
    p_solo = p_con = 0
    for _ in range(N_SIM):
        idx = [rng.randrange(len(cal)) for _ in range(gmax)]
        p_solo += ps.tentativo([solo[i] for i in idx], 1, gmax)[0] == 'pass'
        p_con += ps.tentativo([con[i] for i in idx], 1, gmax)[0] == 'pass'
    iid_solo, iid_con = 100.0 * p_solo / N_SIM, 100.0 * p_con / N_SIM

    _, gg, m = cand
    x = [t for d in gg for t, _ in gg[d]]
    t_cand = st.mean(x) / (st.stdev(x) / math.sqrt(len(x)))
    peggiore = min(sum(t for t, _ in tr) for tr in con if tr)

    print('book : %s' % ' + '.join('%s x%g' % (n, m) for n, _, m in book))
    print('cand : %s x%g  |  %d trade OOS, avg $%.2f per micro, t %.2f'
          % (cand[0], m, len(x), st.mean(x), t_cand))
    print('regole: %s  |  %d giorni di calendario  |  %d simulazioni, seed %d\n'
          % (ps.PROP['nome'], len(cal), N_SIM, SEED))
    print('%-22s %10s %10s' % ('', 'iid', 'contiguo'))
    c_solo, c_con = contiguo(solo, gmax), contiguo(con, gmax)
    print('%-22s %9.1f%% %9.1f%%' % ('book', iid_solo, c_solo))
    print('%-22s %9.1f%% %9.1f%%' % ('book + candidata', iid_con, c_con))
    print('%-22s %+9.1f  %+9.1f\n' % ('differenza (pp)', iid_con - iid_solo, c_con - c_solo))

    crit = [('1. Δ iid >= +%.1f pp' % SOGLIA_IID, iid_con - iid_solo >= SOGLIA_IID),
            ('2. Δ contiguo >= 0', c_con - c_solo >= 0),
            ('3. giornata peggiore del book >= -DLL ($%.0f)' % ps.DLL, peggiore >= -ps.DLL),
            ('4. avg trade OOS della candidata > 0', st.mean(x) > 0)]
    for nome, ok in crit:
        print('  %s %s' % ('✅' if ok else '❌', nome))
    print('  (giornata peggiore del book con la candidata: $%.0f)' % peggiore)
    print('\nVERDETTO: %s' % ('ENTRA NEL BOOK' if all(ok for _, ok in crit) else 'NON ENTRA'))


if __name__ == '__main__':
    main()
