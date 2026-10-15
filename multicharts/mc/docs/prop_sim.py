#!/usr/bin/env python3
"""Stage 7 -- simulatore di passaggio di una eval prop su una lista di trade MultiCharts.

Risponde alla domanda che il corso affida al simulatore e non a una formula:
**P(toccare +target prima di -MLL)**, con il numero di micro come OUTPUT.

Fa quattro cose, in ordine di importanza:

  1. STATO ATTUALE -- a che distanza dal massimo e' la curva *alla fine dei dati*, e dove
     cade quella distanza nella distribuzione storica dei drawdown. Live 004: *"don't be
     afraid to bench strategies that are in a heavy drawdown"* -- il corso mette in panchina
     proprio questa strategia per questo motivo.
  2. PASS RATE iid -- ricampionamento dei GIORNI con reimmissione, preservando la sequenza
     dei trade dentro il giorno (Live 003: *"we consider the path inside the day as well"*).
     E' il caso dei tentativi indipendenti.
  3. PASS RATE contiguo -- finestre cronologiche vere, ogni giorno dello storico come
     possibile partenza. Cattura la correlazione fra tentativi senza inventarsi un
     parametro: e' l'effetto che Live 004 chiama *"attempts correlation"*.
  4. CUMULATO SUI TENTATIVI e costo per arrivare funded.

Regole LucidFlex 50k (verificate sui transcript): nessuna regola di consistency, MLL
trailing EOD, flat EOD obbligatorio. Il minimo di $150/giorno riguarda il payout da funded,
non il passaggio, quindi non entra qui.

Uso:
    python3 mc/docs/prop_sim.py reports/DPB_S5_OOS_2025-2026.xlsx
    python3 mc/docs/prop_sim.py report.xlsx --micro 1,2,3,4,6,8 --sim 20000
    python3 mc/docs/prop_sim.py report.xlsx --comm-micro 2.50     # sensibilita' ai costi
"""
import sys, os, math, random, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_report import leggi, _data   # riuso del parser, niente duplicazione

# ----------------------------------------------------------- conto e strumento
CONTO   = 50000.0
TARGET  = 3000.0     # balance 53.000
MLL     = 2000.0     # trailing EOD
LOCK    = 50100.0    # il trailing si ferma qui (quando il picco EOD tocca 52.100)
COMM_FULL  = 15.00   # $/round-turn gia' dentro il P&L del report (NQ: 7,50 per lato)
COMM_MICRO = 1.50    # $/round-turn effettivo su MNQ
COSTO_TENT = 100.0   # $ per tentativo


def per_giorno(path, comm_micro):
    """Lista di giorni, ognuno la sequenza dei P&L **per 1 micro**, in ordine."""
    cfg, pl, cum, anni, cts = leggi(path)
    import zipfile, re, html
    from check_report import _sheet, _find
    z = zipfile.ZipFile(path)
    righe = _sheet(z, _find(z, 'List of Trades'))
    hdr = next(i for i, r in enumerate(righe[:10])
               if any(c.strip() == 'Profit ($)' for c in r))
    col = {c.strip(): j for j, c in enumerate(righe[hdr])}
    jp, jd = col['Profit ($)'], col['Date']

    jdd = col.get('Drawdown ($)')     # escursione peggiore DENTRO il trade

    giorni, ordine = {}, []
    for r in righe[hdr + 1:]:
        if jp >= len(r) or not r[jp].strip():
            continue
        try:
            v = float(r[jp])
        except ValueError:
            continue
        d = _data(r[jd]) if jd < len(r) else None
        if d is None:
            continue
        # il P&L del report e' NQ full-size con COMM_FULL dentro: si torna al lordo,
        # si divide per 10 (il micro e' 1/10) e si applica il costo vero del micro
        micro = (v + COMM_FULL) / 10.0 - comm_micro
        # il minimo toccato durante il trade, non solo la chiusura: e' la conservativita'
        # che il corso ha aggiunto in Live 003 ("we consider the path inside the day")
        giu = 0.0
        if jdd is not None and jdd < len(r) and r[jdd].strip():
            try:
                giu = min(0.0, float(r[jdd]) / 10.0)
            except ValueError:
                giu = 0.0
        giu = min(giu, micro)             # non puo' essere meno profondo della chiusura
        if d not in giorni:
            giorni[d] = []
            ordine.append(d)
        giorni[d].append((micro, giu))
    return cfg, [(d, giorni[d]) for d in ordine]


def stato_attuale(giorni):
    """Distanza dal massimo alla fine dei dati, e dove cade nello storico."""
    eq, picco, dd_serie = 0.0, 0.0, []
    for _, trades in giorni:
        for t, _giu in trades:
            eq += t
            picco = max(picco, eq)
            dd_serie.append(picco - eq)
    dd_ora = dd_serie[-1] if dd_serie else 0.0
    dd_max = max(dd_serie) if dd_serie else 0.0
    peggiori = sorted(dd_serie)
    pct = 100.0 * sum(1 for x in dd_serie if x <= dd_ora) / len(dd_serie)
    return dict(dd_ora=dd_ora, dd_max=dd_max, pct=pct,
                p50=peggiori[len(peggiori) // 2], p95=peggiori[int(0.95 * len(peggiori))])


def tentativo(seq_giorni, n_micro, giorni_max):
    """Un tentativo. seq_giorni = iterabile di liste di P&L per micro.

    Ritorna ('pass'|'fail'|'aperto', giorni_usati).
    """
    bal, picco_eod, limite = CONTO, CONTO, CONTO - MLL
    g = 0
    for g, trades in enumerate(seq_giorni, 1):
        for t, giu in trades:
            if bal + giu * n_micro <= limite:  # sfondato DENTRO il trade, non alla chiusura
                return 'fail', g
            bal += t * n_micro
            if bal <= limite:
                return 'fail', g
            if bal >= CONTO + TARGET:
                return 'pass', g
        picco_eod = max(picco_eod, bal)        # il trailing si aggiorna a fine giornata
        limite = min(picco_eod - MLL, LOCK)
        if giorni_max and g >= giorni_max:
            return 'aperto', g
    return 'aperto', g


def sim_iid(giorni, n_micro, n_sim, giorni_max, rng):
    """Ricampiona i GIORNI con reimmissione: tentativi indipendenti."""
    pool = [t for _, t in giorni]
    esiti, durate = {'pass': 0, 'fail': 0, 'aperto': 0}, []
    for _ in range(n_sim):
        seq = [rng.choice(pool) for _ in range(giorni_max or 400)]
        e, g = tentativo(seq, n_micro, giorni_max)
        esiti[e] += 1
        if e == 'pass':
            durate.append(g)
    return esiti, durate


def sim_contiguo(giorni, n_micro, giorni_max):
    """Ogni giorno dello storico come partenza: cattura la correlazione fra tentativi."""
    pool = [t for _, t in giorni]
    ultimo = max(1, len(pool) - (giorni_max or 0))   # partenze complete soltanto
    esiti, durate = {'pass': 0, 'fail': 0, 'aperto': 0}, []
    for i in range(ultimo):
        e, g = tentativo(pool[i:], n_micro, giorni_max)
        esiti[e] += 1
        if e == 'pass':
            durate.append(g)
    return esiti, durate


def dd_corrente(giorni):
    """Per ogni giorno, la distanza dal massimo a fine giornata."""
    eq, picco, out = 0.0, 0.0, []
    for _, trades in giorni:
        for t, _g in trades:
            eq += t
            picco = max(picco, eq)
        out.append(picco - eq)
    return out


def sim_condizionato(giorni, n_micro, giorni_max, soglia_dd):
    """Solo le partenze da un drawdown >= soglia: 'se partiamo adesso, cosa succede'."""
    pool = [t for _, t in giorni]
    dd = dd_corrente(giorni)
    ultimo = max(1, len(pool) - (giorni_max or 0))
    esiti, durate = {'pass': 0, 'fail': 0, 'aperto': 0}, []
    for i in range(ultimo):
        if dd[i] < soglia_dd:
            continue
        e, g = tentativo(pool[i:], n_micro, giorni_max)
        esiti[e] += 1
        if e == 'pass':
            durate.append(g)
    return esiti, durate


def sim_sequenziale(giorni, n_micro, giorni_max, tent_max):
    """Tentativi CONSECUTIVI sullo storico vero: il tentativo k parte dove ha finito k-1.

    E' la correlazione fra tentativi di Live 004, misurata invece che parametrizzata.
    Ritorna, per k = 1..tent_max, la frazione di partenze che ha passato entro k tentativi.
    """
    pool = [t for _, t in giorni]
    ultimo = max(1, len(pool) - (giorni_max or 0) * tent_max)
    conteggi = [0] * (tent_max + 1)
    n = 0
    for i in range(ultimo):
        n += 1
        pos = i
        for k in range(1, tent_max + 1):
            if pos >= len(pool):
                break
            e, g = tentativo(pool[pos:], n_micro, giorni_max)
            if e == 'pass':
                for kk in range(k, tent_max + 1):
                    conteggi[kk] += 1
                break
            pos += g
    return [c / n if n else 0.0 for c in conteggi], n


def cumulato(p, n):
    """P(almeno un successo in n tentativi) assumendo indipendenza."""
    return 1.0 - (1.0 - p) ** n


def main():
    arg = sys.argv[1:]
    if not arg:
        raise SystemExit(__doc__)
    def opt(nome, default, tipo=float):
        if nome in arg:
            i = arg.index(nome); v = tipo(arg[i + 1]); del arg[i:i + 2]; return v
        return default
    n_sim      = int(opt('--sim', 20000))
    giorni_max = int(opt('--giorni-max', 60))
    comm_micro = opt('--comm-micro', COMM_MICRO)
    tent_max   = int(opt('--tentativi', 4))
    griglia    = opt('--micro', '1,2,3,4,6,8', str)
    griglia    = [int(x) for x in griglia.split(',')]
    path = arg[0]

    cfg, giorni = per_giorno(path, comm_micro)
    rng = random.Random(20261015)

    print('=' * 78)
    print('STAGE 7 -- %s' % os.path.basename(path))
    print('=' * 78)
    d1, d2 = _data(cfg.get('Start Date')), _data(cfg.get('End Date'))
    tot = sum(len(t) for _, t in giorni)
    print('Conto $%s | target +$%s | MLL $%s trailing EOD (lock $%s) | tentativo $%s'
          % (f'{CONTO:,.0f}', f'{TARGET:,.0f}', f'{MLL:,.0f}', f'{LOCK:,.0f}', f'{COSTO_TENT:,.0f}'))
    print('Dati: %s -> %s | %d giorni | %d trade | costo micro $%.2f/round-turn'
          % (d1, d2, len(giorni), tot, comm_micro))
    avg = sum(x for _, t in giorni for x, _g in t) / tot
    print('Per 1 micro: avg trade $%.2f | %.1f trade/giorno' % (avg, tot / len(giorni)))

    s = stato_attuale(giorni)
    print('\n1. STATO ATTUALE DELLA CURVA  (Live 004: non partire da un drawdown pesante)')
    print('   distanza dal massimo, ora      $%.0f per micro' % s['dd_ora'])
    print('   drawdown massimo storico       $%.0f' % s['dd_max'])
    print('   mediana / 95esimo percentile   $%.0f / $%.0f' % (s['p50'], s['p95']))
    print('   -> siamo al %.0f%% percentile della distribuzione dei drawdown' % s['pct'])
    if s['dd_ora'] > s['p95']:
        print('   !! oltre il 95esimo percentile: e\' esattamente la situazione in cui il')
        print('      corso mette la strategia in panchina invece di partire')
    elif s['dd_ora'] > s['p50']:
        print('   !  sopra la mediana: partire ora e\' sfavorevole')
    else:
        print('   OK vicino al massimo: e\' il momento buono per partire')

    print('\n2. PASS RATE per numero di micro   (finestra max %d giorni)' % giorni_max)
    print('   %-7s %-28s %-28s' % ('', 'iid (tentativi indipendenti)', 'contiguo (storico vero)'))
    print('   %-7s %7s %7s %8s   %7s %7s %8s'
          % ('micro', 'pass%', 'fail%', 'gg mediani', 'pass%', 'fail%', 'gg mediani'))
    risultati = {}
    for n in griglia:
        ei, di = sim_iid(giorni, n, n_sim, giorni_max, rng)
        ec, dc = sim_contiguo(giorni, n, giorni_max)
        pi = 100.0 * ei['pass'] / sum(ei.values())
        pc = 100.0 * ec['pass'] / sum(ec.values())
        mi = sorted(di)[len(di) // 2] if di else 0
        mc = sorted(dc)[len(dc) // 2] if dc else 0
        risultati[n] = (pi / 100.0, pc / 100.0, mi, mc)
        print('   %-7d %7.1f %7.1f %8d   %7.1f %7.1f %8d'
              % (n, pi, 100.0 * ei['fail'] / sum(ei.values()), mi,
                 pc, 100.0 * ec['fail'] / sum(ec.values()), mc))

    migliore = max(risultati, key=lambda n: risultati[n][0])   # si scegle sullo iid
    pi, pc, mi, mc = risultati[migliore]
    print('\n   Il contiguo NON e\' una stima conservativa: le finestre si sovrappongono e')
    print('   cavalcano i cluster favorevoli dello storico, quindi sopravvaluta. Lo numero')
    print('   su cui si decide e\' lo iid; il contiguo serve solo come controllo.')

    print('\n3. SE PARTIAMO ADESSO  (%d micro, solo le partenze da drawdown >= $%.0f)'
          % (migliore, s['p95']))
    ec, dc = sim_condizionato(giorni, migliore, giorni_max, s['p95'])
    tot_c = sum(ec.values())
    indip = len(giorni) / float(giorni_max or 1)      # finestre davvero indipendenti
    # il conteggio delle partenze non conta: contano le finestre indipendenti
    if tot_c >= 30 and indip >= 20:
        print('   %d partenze storiche in quella condizione: pass %.1f%%  fail %.1f%%'
              % (tot_c, 100.0 * ec['pass'] / tot_c, 100.0 * ec['fail'] / tot_c))
    else:
        print('   %d partenze (pass %d, fail %d) = %.0f%%, MA si sovrappongono e le finestre'
              % (tot_c, ec['pass'], ec['fail'],
                 100.0 * ec['pass'] / tot_c if tot_c else 0))
        print('   indipendenti sono ~%.0f: il numero NON e\' affidabile in nessuna direzione.' % indip)
        print('   La domanda resta aperta e vale come riserva, non come via libera ne come kill.')

    print('\n4. CUMULATO SUI TENTATIVI  (%d micro)' % migliore)
    seq, n_seq = sim_sequenziale(giorni, migliore, giorni_max, tent_max)
    print('   %-12s %16s %16s %18s' % ('tentativi', 'iid (indip.)', 'sequenziale', 'differenza'))
    for k in range(1, tent_max + 1):
        print('   %-12d %15.1f%% %15.1f%% %17.1f pp'
              % (k, 100 * cumulato(pi, k), 100 * seq[k], 100 * (seq[k] - cumulato(pi, k))))
    print('   %d partenze, ma si sovrappongono: con finestre da %d giorni su %d giorni di'
          % (n_seq, giorni_max, len(giorni)))
    print('   storico le osservazioni DAVVERO indipendenti sono ~%.0f.' % indip)
    if indip < 20:
        print('   -> la colonna sequenziale e\' INDICATIVA, non una misura. Un 100% la')
        print('      diventa con una manciata di finestre fortunate. Si decide sullo iid.')

    print('\n5. COSTO PER ARRIVARE FUNDED  (%d micro)' % migliore)
    if pi > 0:
        print('   iid         tentativi attesi %.1f -> $%.0f  |  ~%.1f mesi'
              % (1 / pi, COSTO_TENT / pi, (mi * (1 / pi)) / 21.0))
    if seq[tent_max] > 0:
        print('   sequenziale %.1f%% entro %d tentativi, costo massimo $%.0f'
              % (100 * seq[tent_max], tent_max, COSTO_TENT * tent_max))
    print()


if __name__ == '__main__':
    main()
