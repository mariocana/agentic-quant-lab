#!/usr/bin/env python3
"""Il book DPB / Gold pct1 / Overnight Bias sulle regole FTMO: eval, funded e conto intero.

Stesso metodo di audit_stress.py e funded_sim.py, con le quattro sezioni ftmo_* di prop_firms.ini.
I report sono quelli dei futures: il CFD e' simulato in micro equivalenti, con i costi di Lucid.
Quanto costa davvero il CFD lo dira' il test del bridge: qui c'e' la sensibilita' a un costo in
piu' per trade, in $ per micro.

Eval: senza scadenza, guardia a GUARDIA giorni (non i 60 di prop_sim: il target e' il 10%).
Funded. Verificato sulle FAQ FTMO il 12/11/2026: primo reward dal 14° giorno dalla prima
operazione; split 90% sull'1-Step, 80% sul 2-Step (90% solo con Scaling Plan o Premium: non
contato); posizioni chiuse prima della richiesta; nell'1-Step i limiti ripartono dopo il reward.
Assunzioni NON verificate (da confermare):
  - anche i reward successivi ogni CICLO giorni di trading (14 di calendario), prelevando tutto;
  - dopo il reward il saldo torna al capitale iniziale anche nel 2-Step;
  - 1-Step: reward solo se il giorno migliore del ciclo e' <= 50% del profitto del ciclo;
  - 2-Step: la quota dell'eval torna con il primo reward (prop_firms.ini).
Non modellata: la regola dell'Allocazione Massima di Capitale (piu' conti con la stessa strategia,
EA di terze parti): puo' negare il conto funded.

Size scelte guardando queste tabelle sono scelte sugli stessi dati. Solo lettura, nessun verdetto.

Uso, dalla radice del repo:
    python3 docs/audit_ftmo.py
"""
import sys, os, random, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prop_sim as ps
import audit_stress as au

N_SIM, SEED, BLOCCO = 4000, 20261112, 5
GUARDIA, ORIZZONTE, CICLO = 250, 252, 10
SPLIT = {'1step': 0.90, '2step': 0.80}
SEZIONI = ('ftmo_1step_50k', 'ftmo_2step_50k', 'ftmo_1step_100k', 'ftmo_2step_100k')


def sequenze(gg, lunga, n=N_SIM):
    rng = random.Random(SEED)
    for _ in range(n):
        seq = []
        while len(seq) < lunga:
            i = rng.randrange(len(gg))
            seq += [gg[(i + j) % len(gg)] for j in range(BLOCCO)]
        yield seq[:lunga]


def eval_(gg):
    esiti, durate = {'pass': 0, 'fail': 0, 'aperto': 0}, []
    for seq in sequenze(gg, GUARDIA):
        e, g = ps.tentativo(seq, 1, GUARDIA)
        esiti[e] += 1
        if e == 'pass':
            durate.append(g)
    return {k: v / float(N_SIM) for k, v in esiti.items()}, (st.median(durate) if durate else 0)


def funded(seq):
    """Un conto funded FTMO: (incassato, almeno un reward). Limiti come nell'eval, senza target."""
    conto, mll, dll = ps.CONTO, ps.MLL, ps.DLL
    statico = ps.PROP['trailing'] == 'static'
    bal = picco = conto
    limite = conto - mll
    split = SPLIT['2step' if ps.TARGET2 else '1step']
    incassato, premi, migliore, in_ciclo = 0.0, 0, 0.0, 0
    for trades in seq:
        inizio = bal
        for tr in trades:
            fondo = bal + tr[1]
            if fondo <= inizio - dll or fondo <= limite:      # equity sotto un limite: conto chiuso
                return incassato, premi > 0
            bal += tr[0]
            if bal <= limite:
                return incassato, premi > 0
        migliore = max(migliore, bal - inizio)
        in_ciclo += 1
        if not statico:
            picco = max(picco, bal)
            limite = picco - mll
        profitto = bal - conto
        if in_ciclo >= CICLO and profitto > 0 and (not ps.CONSISTENCY or migliore <= ps.CONSISTENCY * profitto):
            incassato += split * profitto
            premi += 1
            bal = picco = conto
            limite, migliore, in_ciclo = conto - mll, 0.0, 0
    return incassato, premi > 0


def conto_intero(gg):
    e, gp = eval_(gg)
    tot, uno = zip(*[funded(seq) for seq in sequenze(gg, ORIZZONTE)])
    ev, p1 = st.mean(tot), sum(uno) / float(len(uno))
    rimborso = ps.COSTO_TENT * p1 if ps.TARGET2 else 0.0       # 2-Step: quota resa al primo reward
    return dict(passa=e['pass'], fail=e['fail'], aperto=e['aperto'], gg=gp, ev=ev, p1=p1,
                tent=e['pass'] * (ev + rimborso) - ps.COSTO_TENT)


RIGA = '%-10s %5.0f%% %5.0f%% %6.0f%% %5.0f | %8.0f %7.0f%% | %10.0f'
TESTA = '%-10s %6s %6s %7s %5s | %8s %8s | %10s' % ('micro', 'pass', 'fail', 'aperto', 'gg', 'EV fund', '>=1 rew', 'EV/tent')


def stampa(lab, r):
    print(RIGA % (lab, 100 * r['passa'], 100 * r['fail'], 100 * r['aperto'], r['gg'], r['ev'], 100 * r['p1'], r['tent']))


def main():
    tutte = ps.leggi_prop()
    ps.usa_prop(tutte[ps.PROP_DEFAULT])
    Po = au.carica(au.OOS, '2025-01-01', '2026-10-15', tutte[SEZIONI[0]])
    Pi = au.carica(au.IS, None, None, tutte[SEZIONI[0]])
    media = lambda P: {k: st.mean([x[0] for d in P[k] for x in P[k][d]]) for k in P}
    mo, mi = media(Po), media(Pi)
    book = lambda k, sh=None: au.giorni(Po, {'DPB': k, 'GAR': k, 'OBO': k}, sh)
    print('%d simulazioni per riga, blocchi di %d giorni · eval: guardia %d giorni · funded: %d giorni, '
          'reward ogni %d, split 90%% (1-Step) e 80%% (2-Step)' % (N_SIM, BLOCCO, GUARDIA, ORIZZONTE, CICLO))
    print('gg = giorni mediani al pass · EV fund = $ incassati per conto funded · EV/tent = pass x EV - quota\n')

    scelta = {}
    for sez in SEZIONI:
        p = tutte[sez]
        ps.usa_prop(p)
        passo = int(p['conto'] // 50000)
        print('===== %s · quota $%.0f · book k/k/k sull\'OOS' % (p['nome'], p['costo_tentativo']))
        print(TESTA)
        meglio = None
        for k in (1, 2, 3, 4, 5, 6):
            r = conto_intero(book(k * passo))
            stampa('%d/%d/%d' % ((k * passo,) * 3), r)
            if meglio is None or r['tent'] > meglio[1]:
                meglio = (k * passo, r['tent'])
        scelta[sez] = meglio[0]
        print()

    for sez in SEZIONI:
        p = tutte[sez]
        ps.usa_prop(p)
        k = scelta[sez]
        stress = [('OOS com\'e\'', {}),
                  ('costo CFD +$1 per micro a trade', {x: -1.0 for x in au.BOOK}),
                  ('costo CFD +$2', {x: -2.0 for x in au.BOOK}),
                  ('costo CFD +$3', {x: -3.0 for x in au.BOOK}),
                  ('costo CFD +$6 (DPB a edge zero)', {x: -6.0 for x in au.BOOK}),
                  ('Gold alla media IS', {'GAR': mi['GAR'] - mo['GAR']}),
                  ('Gold media IS + $1 + OBO a meta\'', {'GAR': mi['GAR'] - mo['GAR'] - 1, 'DPB': -1.0, 'OBO': -mo['OBO'] / 2 - 1}),
                  ('edge zero, tutte', {x: -mo[x] for x in au.BOOK})]
        print('===== %s · STRESS a %d/%d/%d (la size con l\'EV piu\' alto, scelta su questi dati)' % ((p['nome'],) + (k,) * 3))
        print(TESTA.replace('micro     ', 'scenario' + ' ' * 26))
        for lab, sh in stress:
            r = conto_intero(book(k, sh))
            print(('%-34s' + RIGA[5:]) % (lab, 100 * r['passa'], 100 * r['fail'], 100 * r['aperto'], r['gg'], r['ev'],
                                          100 * r['p1'], r['tent']))
        print()


if __name__ == '__main__':
    main()
