#!/usr/bin/env python3
"""Quanto rende un conto funded LucidFlex 50k con il book DPB / Gold pct1 / Overnight Bias?

La domanda che il pass rate non fa: passata l'eval, quanti dollari di payout escono dal conto
prima che tocchi l'MLL. Metro della Live 006: **EV per conto funded** nei primi 12 mesi, incassato
dal trader (dopo lo split), conti bruciati compresi con quello che avevano gia' pagato.

Regole: prop_funded.ini (fonti e assunzioni li'). Giorni OOS ricampionati a blocchi di 5, stesso
parser di prop_sim.py, stessi stress di audit_stress.py. La **soglia** e' la politica di prelievo:
si chiede il payout quando il profitto sul conto arriva a quella cifra (e i giorni qualificanti ci
sono). Chiedere presto lascia poco margine: dopo la richiesta l'MLL sta a $50.100 e il saldo scende.

Poi il conto intero: EV per tentativo di eval = pass rate x EV funded - prezzo dell'eval.

Soglia e size scelte guardando queste tabelle sono scelte sugli stessi dati: l'EV vero e' piu' basso.
Solo lettura, nessun verdetto: non passa da lab.py.

Uso, dalla radice del repo:
    python3 docs/funded_sim.py
"""
import sys, os, random, statistics as st, configparser
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prop_sim as ps
import audit_stress as au

N_SIM, SEED, BLOCCO, ORIZZONTE = 10000, 20261112, 5, 252
SOGLIE = (1000, 2000, 3000, 4000, 5000, 6000)
QUI = os.path.dirname(os.path.abspath(__file__))


def regole(sezione='lucidflex_50k_funded'):
    cp = configparser.ConfigParser(inline_comment_prefixes=None)
    cp.read(os.path.join(QUI, 'prop_funded.ini'), encoding='utf-8')
    s = cp[sezione]
    R = {k: float(s[k]) for k in ('conto', 'mll', 'lock_sopra_conto', 'lock_oltre', 'dll', 'giorni_qual',
                                  'giorno_min', 'payout_min', 'payout_max', 'payout_quota', 'split',
                                  'payout_n')}
    R['nome'] = s['nome']
    return R


def conto(seq, R, soglia):
    """Un conto funded. Ritorna (esito, [(giorno, incassato), ...]); esito: bruciato, live, vivo."""
    bal = picco = R['conto']
    blocco = R['conto'] + R['lock_sopra_conto']
    limite, fermo = bal - R['mll'], False
    qual, inizio_ciclo, pagati = 0, bal, []
    for g, trades in enumerate(seq, 1):
        inizio = bal
        stop_dll = bal - R['dll'] if R['dll'] else None
        for tr in trades:
            fondo = bal + tr[1]
            if stop_dll is not None and fondo <= stop_dll and stop_dll > limite:
                bal = stop_dll                 # DLL soft: giornata chiusa, conto vivo
                break
            if fondo <= limite:                # MLL toccato dentro il trade
                return 'bruciato', pagati
            bal += tr[0]
            if bal <= limite:
                return 'bruciato', pagati
        if bal - inizio >= R['giorno_min']:
            qual += 1
        if not fermo:                          # trailing a fine giornata, fino al blocco
            picco = max(picco, bal)
            limite = min(picco - R['mll'], blocco)
            fermo = bal > R['conto'] + R['lock_oltre']
        profitto = bal - R['conto']
        if qual >= R['giorni_qual'] and bal > inizio_ciclo and profitto >= soglia:
            richiesta = min(R['payout_quota'] * profitto, R['payout_max'])
            if richiesta >= R['payout_min']:
                bal -= richiesta
                pagati.append((g, richiesta * R['split']))
                limite, fermo = blocco, True   # alla richiesta l'MLL va al valore bloccato
                qual, inizio_ciclo = 0, bal
                if len(pagati) >= R['payout_n']:
                    return 'live', pagati
    return 'vivo', pagati


def misura(gg, R, soglia, n=N_SIM):
    rng, tot, primo, esiti = random.Random(SEED), [], [], {'bruciato': 0, 'live': 0, 'vivo': 0}
    senza = 0
    for _ in range(n):
        seq = []
        while len(seq) < ORIZZONTE:
            i = rng.randrange(len(gg))
            seq += [gg[(i + j) % len(gg)] for j in range(BLOCCO)]
        e, pagati = conto(seq[:ORIZZONTE], R, soglia)
        esiti[e] += 1
        tot.append(sum(p for _, p in pagati))
        if pagati:
            primo.append(pagati[0][0])
        else:
            senza += 1
    return dict(ev=st.mean(tot), mediana=st.median(tot), almeno1=100.0 * (n - senza) / n,
                bruciati=100.0 * esiti['bruciato'] / n, tutti=100.0 * esiti['live'] / n,
                primo=st.median(primo) if primo else 0)


def main():
    R = regole()
    prop = ps.leggi_prop()[ps.PROP_DEFAULT]
    ps.usa_prop(prop)
    Po = au.carica(au.OOS, '2025-01-01', '2026-10-15', prop)
    Pi = au.carica(au.IS, None, None, prop)
    media = lambda P: {k: st.mean([x[0] for d in P[k] for x in P[k][d]]) for k in P}
    mo, mi = media(Po), media(Pi)
    scenari = [('OOS com\'e\'', {}),
               ('Gold alla media IS', {'GAR': mi['GAR'] - mo['GAR']}),
               ('edge dimezzato, tutte', {k: -mo[k] / 2 for k in au.BOOK}),
               ('Gold media IS + slippage $1 + Overnight Bias a meta\'',
                {'GAR': mi['GAR'] - mo['GAR'] - 1, 'DPB': -1.0, 'OBO': -mo['OBO'] / 2 - 1}),
               ('edge zero, tutte', {k: -mo[k] for k in au.BOOK})]
    book = [('1/1/1', au.BOOK), ('1/0/1', {'DPB': 1, 'GAR': 0, 'OBO': 1}),
            ('2/1/1', {'DPB': 2, 'GAR': 1, 'OBO': 1}), ('2/2/2', {'DPB': 2, 'GAR': 2, 'OBO': 2})]

    print('regole: %s · %d conti per riga, blocchi di %d giorni, orizzonte %d giorni, seed %d'
          % (R['nome'], N_SIM, BLOCCO, ORIZZONTE, SEED))
    print('EV e mediana = $ incassati dal trader per conto funded (dopo lo split del %.0f%%)\n' % (100 * R['split']))
    testa = '%-8s %7s %8s %9s %9s %9s %8s' % ('soglia', 'EV $', 'mediana', '>=1 pay', 'bruciati', 'tutti e 5', '1° pay g')

    print('BOOK 1/1/1, OOS com\'e\': la politica di prelievo')
    print(testa)
    migliore = {}
    for s in SOGLIE:
        r = misura(au.giorni(Po, au.BOOK), R, s)
        migliore[s] = r['ev']
        print('%-8d %7.0f %8.0f %8.0f%% %8.0f%% %8.0f%% %8.0f' % (s, r['ev'], r['mediana'], r['almeno1'],
                                                                 r['bruciati'], r['tutti'], r['primo']))
    soglia = max(migliore, key=migliore.get)
    print('soglia con l\'EV piu\' alto: $%d (scelta su questi dati)\n' % soglia)

    print('SIZE, OOS com\'e\', soglia $%d' % soglia)
    print('%-8s %7s %8s %9s %9s %9s %8s' % ('book', 'EV $', 'mediana', '>=1 pay', 'bruciati', 'tutti e 5', '1° pay g'))
    for lab, m in book:
        r = misura(au.giorni(Po, m), R, soglia)
        print('%-8s %7.0f %8.0f %8.0f%% %8.0f%% %8.0f%% %8.0f' % (lab, r['ev'], r['mediana'], r['almeno1'],
                                                                 r['bruciati'], r['tutti'], r['primo']))

    print('\nIL CONTO INTERO, book 1/1/1, soglia $%d: EV per tentativo = pass x EV funded - $%.0f'
          % (soglia, ps.COSTO_TENT))
    print('%-52s %6s %8s %9s %9s %12s' % ('scenario', 'pass', 'EV fund', '>=1 pay', 'bruciati', 'EV/tentativo'))
    for lab, sh in scenari:
        gg = au.giorni(Po, au.BOOK, sh)
        p = au.sim(gg, n=N_SIM)[0]['pass'] / 100.0
        r = misura(gg, R, soglia)
        print('%-52s %5.0f%% %8.0f %8.0f%% %8.0f%% %12.0f' % (lab, 100 * p, r['ev'], r['almeno1'], r['bruciati'],
                                                             p * r['ev'] - ps.COSTO_TENT))


if __name__ == '__main__':
    main()
