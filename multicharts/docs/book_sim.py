#!/usr/bin/env python3
"""Book di piu' strategie su una o piu' prop: griglia di micro, pass rate, edge zero, costo per funded.

Somma per giorno i P&L per micro dei report (stesso parser e stesse regole di gate_marginale.py
e prop_sim.py), poi per ogni combinazione di micro: net, t sui giorni, max DD, giornata peggiore,
pass rate iid e contiguo, pass rate a **edge zero** (ogni trade traslato della media della sua
strategia: stesso rumore, nessun vantaggio), giorni al pass e costo atteso per ottenere un funded
(prezzo dell'eval / pass rate + attivazione). Regole e costi vengono da prop_firms.ini.

La distanza fra pass rate e edge zero e' la parte che viene dall'edge e non dalla fortuna. Solo
regole dell'EVAL: quanto si incassa dal funded qui non c'e'. Una prop senza scadenza ha un tentativo
aperto dopo 60 giorni contato come non passato. Dentro il giorno i trade seguono l'ordine delle
--strat: l'ordine vero intraday non e' nei report. Le size scelte guardando questa tabella sono
scelte sugli stessi dati: il pass rate vero sara' piu' basso.

Uso:
    python3 docs/book_sim.py \\
        --strat DPB=strategies/DriftPullback/reports/DPB_S5_OOS_2025-2026.xlsx \\
        --strat GAR=strategies/GoldAsianRange/reports/GAR_S5_OOS_A_pct1_2025-2026.xlsx:25:MGC \\
        --strat OBO=strategies/OvernightBiasORB/reports/OBO_S5_OOS_2025-2026.xlsx \\
        --micro 2/0/0,2/1/0,1/1/1 --dal 2025-01-01 --dal 2026-01-01 --al 2026-10-15 --confronta

    --strat NOME=file[:costo_report:micro]  costo_report: andata e ritorno gia' nel report, in $
                        micro: simbolo (costo da comm_<simbolo>_rt della prop) o costo in $
                        default: NQ -> MNQ
    --micro a/b/c,...   combinazioni di micro, nell'ordine delle --strat
                        (default: tutte da 0 a 2, almeno una strategia accesa)
    --prop a,b          sezioni di prop_firms.ini (default lucidflex_50k)
    --confronta         tutte le prop di prop_firms.ini, una riga per prop
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
    arg, strat, micro, dal, n, nomi_prop = sys.argv[1:], [], None, [], 10000, [ps.PROP_DEFAULT]
    tutte = ps.leggi_prop()
    while arg:
        k = arg.pop(0)
        if k == '--strat':
            nome, spec = arg.pop(0).split('=', 1)
            parti = spec.split(':')                     # file[:costo_report:micro]
            strat.append((nome, parti[0], parti[1] if len(parti) > 1 else None,
                          parti[2] if len(parti) > 2 else None))
        elif k == '--micro':
            micro = [tuple(int(x) for x in c.split('/')) for c in arg.pop(0).split(',')]
        elif k == '--dal':
            dal.append(arg.pop(0))
        elif k == '--al':
            gm.AL = arg.pop(0)
        elif k == '--prop':
            nomi_prop = arg.pop(0).split(',')
        elif k == '--confronta':
            nomi_prop = list(tutte)
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
    for x in nomi_prop:
        if x not in tutte:
            raise SystemExit('prop sconosciuta: %s. Sezioni: %s' % (x, ', '.join(tutte)))
    return strat, micro, dal or [None], n, [tutte[x] for x in nomi_prop]


def spec_per_prop(file, full, micro, prop):
    """La spec di gate_marginale.carica con i costi di questa prop."""
    if full is None:
        return file + ':1'
    try:
        costo = float(micro)
    except ValueError:
        costo = prop['comm'].get(micro.upper())
        if costo is None:
            raise SystemExit('%s: manca comm_%s_rt in prop_firms.ini' % (prop['sezione'], micro.lower()))
    return '%s:1:%s:%s' % (file, full, costo)


def carica(strat, prop):
    ps.usa_prop(prop)                                   # prima di caricare: fissa il costo per micro
    return {nome: gm.carica(spec_per_prop(f, full, mic, prop))[1] for nome, f, full, mic in strat}


def misura(P, nomi, c, n, gmax):
    cal = sorted(set().union(*[set(g) for g in P.values()]))
    m = dict(zip(nomi, c))
    media = {k: st.mean([t for d in P[k] for t, _ in P[k][d]] or [0]) for k in nomi}
    giorni = [[ps.Trade(x[0] * m[k], x[1] * m[k], x.su * m[k]) for k in nomi for x in P[k].get(d, [])]
              for d in cal]
    zero = [[ps.Trade((x[0] - media[k]) * m[k], (x[1] - media[k]) * m[k], (x.su - media[k]) * m[k])
             for k in nomi for x in P[k].get(d, [])] for d in cal]
    pnl = [sum(t for t, _ in tr) for tr in giorni]
    eq = pk = dd = 0
    for x in pnl:
        eq += x
        pk = max(pk, eq)
        dd = max(dd, pk - eq)
    s = st.stdev(pnl)
    rng, ok0, durate = random.Random(SEED), 0, []
    for _ in range(n):
        idx = [rng.randrange(len(cal)) for _ in range(gmax)]
        esito, g = ps.tentativo([giorni[i] for i in idx], 1, gmax)
        if esito == 'pass':
            durate.append(g)
        ok0 += ps.tentativo([zero[i] for i in idx], 1, gmax)[0] == 'pass'
    p = len(durate) / float(n)
    costo = None
    if ps.COSTO_TENT is not None and p > 0:
        costo = ps.COSTO_TENT / p + (ps.ATTIVAZIONE or 0)
    return dict(net=sum(pnl), t=st.mean(pnl) / (s / math.sqrt(len(pnl))) if s else 0.0, dd=dd,
                peggiore=min(pnl), iid=100 * p, contiguo=gm.contiguo(giorni, gmax),
                edge0=100.0 * ok0 / n, gg=st.median(durate) if durate else 0, costo=costo)


def celle(r, prop, c):
    oltre = ' DLL' if ps.DLL and r['peggiore'] < -ps.DLL else ''
    tetto = ' oltre max_micro' if prop['max_micro'] is not None and sum(c) > prop['max_micro'] else ''
    return '%9.0f %6.2f %7.0f %8.0f%-4s | %5.1f%% %6.1f%% | %5.1f%% | %4.0f %8s %4s%s' % (
        r['net'], r['t'], r['dd'], r['peggiore'], oltre, r['iid'], r['contiguo'], r['edge0'], r['gg'],
        '$%.0f' % r['costo'] if r['costo'] is not None else 'n/d', prop['automazione'][:4], tetto)


TESTA = '%9s %6s %7s %8s     | %6s %7s | %6s | %4s %8s %4s' % (
    'net $', 't', 'maxDD', 'peggior', 'iid', 'contig', 'edge0', 'gg', '$/funded', 'auto')


def tabella(strat, micro, dal, n, props):
    gm.DAL = dal
    nomi = [s[0] for s in strat]
    P = carica(strat, props[0])
    cal = sorted(set().union(*[set(g) for g in P.values()]))
    serie = {k: [sum(t for t, _ in P[k].get(d, [])) for d in cal] for k in nomi}
    corr = ' · '.join('%s/%s %.2f' % (a, b, st.correlation(serie[a], serie[b]))
                      for a, b in itertools.combinations(nomi, 2)) if len(nomi) > 1 else '-'
    print('\n===== %s | %d giorni | correlazione P&L giornaliero: %s' % (
        'dal ' + dal if dal else 'tutto il report', len(cal), corr))
    if len(props) == 1:
        print('%-16s %s' % ('/'.join(nomi), TESTA))
        for c in micro:
            print('%-16s %s' % ('/'.join(map(str, c)), celle(misura(P, nomi, c, n, gmax(props[0])), props[0], c)))
        return
    print('%-26s %s' % ('prop', TESTA))
    dati = {p['sezione']: carica(strat, p) for p in props}
    for c in micro:
        print('--- %s = %s' % ('/'.join(nomi), '/'.join(map(str, c))))
        for p in props:
            ps.usa_prop(p)
            print('%-26s %s' % (p['nome'][:26], celle(misura(dati[p['sezione']], nomi, c, n, gmax(p)), p, c)))


def gmax(prop):
    return prop['giorni_max'] or ps.GUARDIA_GG


def main():
    strat, micro, finestre, n, props = argomenti()
    print('regole: %s · %d simulazioni per combinazione, seed %d' % (
        ', '.join(p['nome'] for p in props), n, SEED))
    print('gg = giorni mediani al pass · $/funded = prezzo eval / pass rate + attivazione · '
          'DLL = giornata peggiore oltre il limite · auto = automazione permessa')
    for dal in finestre:
        tabella(strat, micro, dal, n, props)


if __name__ == '__main__':
    main()
