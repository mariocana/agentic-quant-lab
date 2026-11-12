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
    python3 docs/gate_marginale.py --book DPB_S5_OOS.xlsx:2 --cand ORB_S5_OOS.xlsx:1
    (--book si ripete per un book di piu strategie)

Strumenti diversi da NQ: file:micro:costo_report:costo_micro, i costi andata e ritorno in $.
costo_report e' quello gia' dentro il P&L del report full-size, costo_micro quello vero del
micro. Es. GC a 12.5$/lato e MGC: --cand GAR_S5_OOS.xlsx:1:25:2.60

--dal / --al AAAA-MM-GG tengono solo i giorni dentro la finestra (il chart parte qualche giorno
prima dell'OOS; i report possono finire in date diverse).

--intervallo aggiunge, dopo il verdetto, l'intervallo al 90% del Δ iid ricampionando il calendario
(vedi intervallo()). Non cambia il verdetto ne' le righe che lab.py legge.
"""
import sys, os, random, math, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prop_sim as ps

N_SIM      = 20000
SEED       = 20261029
SOGLIA_IID = 2.0      # punti percentuali, pre-registrata il 29/10/2026

# --intervallo: incertezza del Δ iid dovuta ai dati (12/11/2026). Solo informativo.
N_BOOT     = 200      # calendari ricampionati
N_SIM_BOOT = 2000     # tentativi per calendario
BLOCCO     = 5        # giorni per blocco: una settimana di trading


DAL = AL = None


def carica(spec):
    path, micro, *costi = spec.split(':')
    full, c_micro = (float(costi[0]), float(costi[1])) if costi else (ps.COMM_FULL, ps.COMM_MICRO)
    nq_full, ps.COMM_FULL = ps.COMM_FULL, full    # per_giorno toglie COMM_FULL dal report
    gg = ps.per_giorno(path, c_micro)[1]
    ps.COMM_FULL = nq_full
    if DAL:
        gg = [(d, t) for d, t in gg if str(d) >= DAL]
    if AL:
        gg = [(d, t) for d, t in gg if str(d) <= AL]
    return os.path.basename(path), dict(gg), float(micro)


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


def intervallo(solo, con, gmax):
    """Quanto e' incerto il Δ iid per via dei DATI, non del numero di simulazioni.

    Le N_SIM simulazioni pescano sempre dagli stessi giorni: l'errore che tolgono e' quello del
    Monte Carlo, non quello di avere un solo campione di giorni. Qui si ricampiona il calendario
    a blocchi di BLOCCO giorni (N_BOOT volte, stessa lunghezza), e su ogni calendario ricampionato
    si rifa' il confronto a numeri casuali comuni con N_SIM_BOOT tentativi. Il rumore del Monte
    Carlo interno allarga un po' l'intervallo: e' il verso prudente.

    Ritorna (5° percentile, mediana, 95° percentile, quota di Δ > 0, quota di Δ >= SOGLIA_IID).
    """
    rng, n, delta = random.Random(SEED + 1), len(solo), []
    for _ in range(N_BOOT):
        pool = []
        while len(pool) < n:
            i = rng.randrange(n)
            pool += [(i + j) % n for j in range(BLOCCO)]
        pool = pool[:n]
        a = b = 0
        for _ in range(N_SIM_BOOT):
            idx = [pool[rng.randrange(n)] for _ in range(gmax)]
            a += ps.tentativo([solo[i] for i in idx], 1, gmax)[0] == 'pass'
            b += ps.tentativo([con[i] for i in idx], 1, gmax)[0] == 'pass'
        delta.append(100.0 * (b - a) / N_SIM_BOOT)
    delta.sort()
    q = lambda p: delta[min(len(delta) - 1, int(p * len(delta)))]
    return (q(0.05), q(0.50), q(0.95),
            100.0 * sum(d > 0 for d in delta) / len(delta),
            100.0 * sum(d >= SOGLIA_IID for d in delta) / len(delta))


def main():
    global DAL, AL
    con_intervallo = False
    ps.usa_prop(ps.leggi_prop()[ps.PROP_DEFAULT])   # prima di caricare: fissa il costo per micro
    arg = sys.argv[1:]
    spec_book, spec_cand = [], None
    while arg:
        k = arg.pop(0)
        if k == '--book':
            spec_book.append(arg.pop(0))
        elif k == '--cand':
            spec_cand = arg.pop(0)
        elif k == '--dal':
            DAL = arg.pop(0)
        elif k == '--al':
            AL = arg.pop(0)
        elif k == '--intervallo':
            con_intervallo = True
    # si carica dopo aver letto tutti gli argomenti: --dal vale in qualunque posizione
    book = [carica(x) for x in spec_book]
    cand = carica(spec_cand) if spec_cand else None
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

    if con_intervallo:
        lo, med, hi, sopra0, sopra_soglia = intervallo(solo, con, gmax)
        print('\nINTERVALLO SUL Δ iid (informativo, non entra nel verdetto)')
        print('  %d calendari ricampionati a blocchi di %d giorni, %d tentativi ciascuno'
              % (N_BOOT, BLOCCO, N_SIM_BOOT))
        print('  Δ iid: mediana %+.1f pp, 90%% fra %+.1f e %+.1f' % (med, lo, hi))
        print('  calendari con Δ > 0: %.0f%%  |  con Δ >= +%.1f pp: %.0f%%'
              % (sopra0, SOGLIA_IID, sopra_soglia))
        print('  %s il limite inferiore e\' sopra zero'
              % ('✅' if lo > 0 else '❌'))


if __name__ == '__main__':
    main()
