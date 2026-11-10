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
  5. SIZE A GRADINI -- pochi micro finche' il conto non ha un cuscinetto, poi la size
     piena (Colab della Live 003, cella 8b: la domanda di Francesco).

Le regole delle prop stanno in `prop_firms.ini`, una sezione per conto; il default e'
LucidFlex 50k. Solo le regole dell'eval: il funded ha regole sue e non entra qui.

Uso:
    python3 mc/docs/prop_sim.py reports/DPB_S5_OOS_2025-2026.xlsx
    python3 mc/docs/prop_sim.py report.xlsx --micro 1,2,3,4,6,8 --sim 20000
    python3 mc/docs/prop_sim.py report.xlsx --comm-micro 2.50     # sensibilita' ai costi
    python3 mc/docs/prop_sim.py report.xlsx --prop apex_50k_eod   # un'altra prop
    python3 mc/docs/prop_sim.py report.xlsx --confronta           # tutte le prop del file
    python3 mc/docs/prop_sim.py report.xlsx --buffer 1000 --ratchet
"""
import sys, os, math, random, datetime, configparser
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_report import leggi, _data   # riuso del parser, niente duplicazione

# ----------------------------------------------------------- conto e strumento
PROP_FILE    = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'prop_firms.ini')
PROP_DEFAULT = 'lucidflex_50k'
COMM_FULL    = 15.00   # $/round-turn gia' dentro il P&L del report (NQ: 7,50 per lato)
GUARDIA_GG   = 60      # senza scadenza, un tentativo ancora aperto dopo 60 giorni conta come non passato

# regole del conto in uso: le imposta usa_prop()
CONTO = TARGET = MLL = LOCK = COMM_MICRO = DLL = CONSISTENCY = TARGET2 = 0.0
DLL_HARD = False
MIN_GIORNI = 0
COSTO_TENT = ATTIVAZIONE = None
PROP = {}


class Trade(tuple):
    """(P&L, minimo dentro il trade) per micro, piu' il massimo dentro il trade in .su: serve solo
    al trailing intraday. Si spacchetta come una coppia."""
    def __new__(cls, t, giu, su=0.0):
        o = tuple.__new__(cls, (t, giu))
        o.su = su
        return o


def leggi_prop():
    """Tutte le prop di prop_firms.ini, come {sezione: dict}."""
    cp = configparser.ConfigParser(inline_comment_prefixes=('#',), interpolation=None)
    if not cp.read(PROP_FILE, encoding='utf8'):
        raise SystemExit('manca %s' % PROP_FILE)
    def num(v):
        return None if v.strip().lower() == 'none' else float(v)
    out = {}
    for s in cp.sections():
        c = cp[s]
        out[s] = dict(sezione=s, nome=c['nome'], conto=num(c['conto']), target=num(c['target']),
                      mll=num(c['mll']), trailing=c['trailing'].strip().lower(),
                      lock_sopra_conto=num(c['lock_sopra_conto']), dll=num(c['dll']) or 0.0,
                      consistency=num(c['consistency']) or 0.0,
                      giorni_max=int(num(c['giorni_max']) or 0),
                      costo_tentativo=num(c['costo_tentativo']), attivazione=num(c['attivazione']),
                      comm_micro_rt=num(c['comm_micro_rt']), max_micro=num(c['max_micro']),
                      comm={k[5:-3].upper(): num(v) for k, v in c.items()
                            if k.startswith('comm_') and k.endswith('_rt') and k != 'comm_micro_rt'},
                      automazione=c.get('automazione', 'none').strip().lower(),
                      dll_tipo=c.get('dll_tipo', 'soft').strip().lower(),
                      min_giorni=int(num(c.get('min_giorni', '0')) or 0),
                      target_fase2=num(c.get('target_fase2', '0')) or 0.0,
                      fonte=c.get('fonte', ''), verificato=c.get('verificato', 'none'))
    return out


def usa_prop(p):
    """Imposta le regole del conto su cui girano tentativo() e il resto."""
    global CONTO, TARGET, MLL, LOCK, COMM_MICRO, DLL, CONSISTENCY, COSTO_TENT, ATTIVAZIONE, PROP
    global TARGET2, DLL_HARD, MIN_GIORNI
    if p['trailing'] not in ('eod', 'intraday', 'static'):
        raise SystemExit('%s: trailing %r non supportato' % (p['nome'], p['trailing']))
    PROP = p
    CONTO, TARGET, MLL = p['conto'], p['target'], p['mll']
    if p['trailing'] == 'static':
        LOCK = CONTO - MLL                  # limite fermo dal primo giorno (FTMO)
    else:
        LOCK = CONTO + p['lock_sopra_conto']    # il trailing si ferma qui
    TARGET2 = p.get('target_fase2', 0.0)
    DLL_HARD = p.get('dll_tipo', 'soft') == 'hard'
    MIN_GIORNI = p.get('min_giorni', 0)
    COMM_MICRO = p['comm_micro_rt']
    COSTO_TENT = p['costo_tentativo']
    ATTIVAZIONE = p['attivazione']
    DLL = p['dll']
    CONSISTENCY = p['consistency']


def wilson(k, n, z=1.96):
    """Intervallo di confidenza 95% su una proporzione k/n (come il Colab del corso)."""
    if n == 0:
        return float('nan'), float('nan')
    p = k / float(n)
    den = 1 + z * z / n
    centro = (p + z * z / (2 * n)) / den
    marg = (z / den) * math.sqrt(p * (1 - p) / n + z * z / (4.0 * n * n))
    return max(0.0, centro - marg), min(1.0, centro + marg)


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
    jru = col.get('Run-up ($)')       # massimo DENTRO il trade, per il trailing intraday

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
        su = 0.0
        if jru is not None and jru < len(r) and r[jru].strip():
            try:
                su = max(0.0, float(r[jru]) / 10.0)
            except ValueError:
                su = 0.0
        if d not in giorni:
            giorni[d] = []
            ordine.append(d)
        giorni[d].append(Trade(micro, giu, su))
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


def tentativo(seq_giorni, n_micro, giorni_max, gradini=None):
    """Un tentativo, in una o due fasi (target_fase2 > 0: FTMO 2-Step). La seconda fase
    riparte da CONTO con gli stessi limiti e usa i giorni che seguono la prima; i giorni
    ritornati sono la somma. Senza scadenza, le due fasi stanno nella stessa guardia di giorni."""
    it = iter(seq_giorni)
    e, g1 = _fase(it, n_micro, giorni_max, gradini, TARGET)
    if e != 'pass' or not TARGET2:
        return e, g1
    resto = giorni_max - g1 if giorni_max else 0
    if giorni_max and resto <= 0:
        return 'aperto', g1
    e, g2 = _fase(it, n_micro, resto, gradini, TARGET2)
    return e, g1 + g2


def _fase(seq_giorni, n_micro, giorni_max, gradini, target):
    """Una fase. seq_giorni = iterabile di liste di P&L per micro.

    gradini = (micro_iniziali, buffer, ratchet): si tradano micro_iniziali finche' il
    profitto e' sotto +buffer, poi n_micro. La size si decide all'ingresso di ogni trade.
    Con ratchet=False si torna piccoli se il profitto riscende sotto il buffer.

    Consistency (> 0): al target si passa solo se la giornata migliore vale al massimo
    quella quota del profitto; se no si continua (LucidFlex 40%).

    Trailing intraday: il limite sale anche sul massimo toccato dentro il trade. L'ordine fra
    massimo e minimo non e' nei report: si assume prima il massimo, il caso prudente.

    Daily loss limit (DLL > 0): se la perdita della giornata, aperti inclusi, arriva al
    DLL, la posizione si chiude li' e la giornata finisce; il conto resta vivo (Apex).
    Si assume l'uscita esattamente sulla soglia: dal vivo e' a mercato, un po' sopra o sotto.
    Con dll_tipo hard (FTMO) toccare il DLL boccia il tentativo.

    Giorni minimi (min_giorni > 0): al target si passa solo dopo almeno quei giorni con trade;
    prima si continua a tradare.

    Ritorna ('pass'|'fail'|'aperto', giorni_usati).
    """
    bal, picco_eod, limite = CONTO, CONTO, CONTO - MLL
    grande = gradini is None
    intraday = PROP.get('trailing') == 'intraday'
    giorno_max = 0.0                           # miglior giornata chiusa, per la consistency
    g = attivi = 0
    for g, trades in enumerate(seq_giorni, 1):
        inizio = bal
        if trades:
            attivi += 1
        stop_dll = bal - DLL if DLL else None
        for tr in trades:
            t, giu = tr
            n = n_micro
            if gradini is not None:
                piccolo, buffer, ratchet = gradini
                sopra = bal - CONTO >= buffer
                grande = (grande or sopra) if ratchet else sopra
                n = n_micro if grande else piccolo
            if intraday:
                picco_eod = max(picco_eod, bal + getattr(tr, 'su', 0.0) * n)
                limite = min(picco_eod - MLL, LOCK)
            fondo = bal + giu * n
            if stop_dll is not None and fondo <= stop_dll and stop_dll > limite:
                if DLL_HARD:
                    return 'fail', g           # FTMO: la perdita giornaliera chiude il conto
                bal = stop_dll                 # il DLL arriva prima dell'MLL: giornata chiusa
                break
            if fondo <= limite:                # sfondato DENTRO il trade, non alla chiusura
                return 'fail', g
            bal += t * n
            if intraday:
                picco_eod = max(picco_eod, bal)
                limite = min(picco_eod - MLL, LOCK)
            if bal <= limite:
                return 'fail', g
            if bal >= CONTO + target and attivi >= MIN_GIORNI:
                # consistency: il giorno migliore (oggi compreso) <= quota del profitto,
                # altrimenti si continua a tradare (Lucid: "keep trading until...")
                if not CONSISTENCY or max(giorno_max, bal - inizio) <= CONSISTENCY * (bal - CONTO):
                    return 'pass', g
        giorno_max = max(giorno_max, bal - inizio)
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


def sim_gradini(giorni, n_micro, iniziali, buffer, n_sim, giorni_max, seed, ratchet):
    """Size piena contro partenze ridotte, sulle STESSE sequenze di giorni.

    Stesse sequenze per tutte le varianti (numeri casuali comuni): la differenza fra
    le righe e' l'effetto dei gradini, non del campionamento.
    Ritorna [(micro_iniziali, pass, n, giorni mediani al pass), ...], la prima riga e' la
    size piena.
    """
    pool = [t for _, t in giorni]
    rng = random.Random(seed)
    seqs = [[pool[rng.randrange(len(pool))] for _ in range(giorni_max or GUARDIA_GG)]
            for _ in range(n_sim)]
    out = []
    for m in [n_micro] + iniziali:
        grad = None if m == n_micro else (m, buffer, ratchet)
        gg = [g for e, g in (tentativo(s, n_micro, giorni_max, grad) for s in seqs) if e == 'pass']
        out.append((m, len(gg), n_sim, sorted(gg)[len(gg) // 2] if gg else 0))
    return out


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


def degrada(giorni, wr_adj, shrink, rng):
    """Rigira la lista di trade come se dal vivo rendesse meno del backtest.

    `wr_adj` e' in PUNTI di win rate da togliere: una frazione dei trade vincenti
    viene trasformata in perdite, pescando dalla distribuzione delle perdite vere.
    `shrink` riduce tutti i P&L di quella frazione. Sono gli scenari che il Colab
    del corso chiama "degradation": la domanda e' «e se dal vivo va peggio».
    """
    vinc = [t for _, tr in giorni for t, _g in tr if t > 0]
    perd = [(t, g) for _, tr in giorni for t, g in tr if t <= 0]
    n = sum(len(tr) for _, tr in giorni)
    if not vinc or not perd or n == 0:
        return giorni
    wr = len(vinc) / float(n)
    # quota di vincenti da ribaltare perche' il WR scenda di wr_adj punti
    quota = (wr_adj / 100.0) / wr if wr > 0 else 0.0
    out = []
    for d, tr in giorni:
        nuovi = []
        for t, g in tr:
            if t > 0 and quota > 0 and rng.random() < quota:
                t, g = perd[rng.randrange(len(perd))]      # diventa una perdita vera
            nuovi.append((t * (1 - shrink), g * (1 - shrink)))
        out.append((d, nuovi))
    return out


SCENARI = [
    ("come da backtest",        0.0, 0.00),
    ("WR -3 pp, P&L -10%",      3.0, 0.10),
    ("WR -5 pp, P&L -15%",      5.0, 0.15),
    ("WR -5 pp, P&L -25%",      5.0, 0.25),
    ("WR -8 pp, P&L -30%",      8.0, 0.30),
]


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
    def flag(nome):
        if nome in arg:
            arg.remove(nome); return True
        return False
    n_sim      = int(opt('--sim', 20000))
    giorni_opt = opt('--giorni-max', None)
    comm_opt   = opt('--comm-micro', None)
    tent_max   = int(opt('--tentativi', 4))
    griglia    = opt('--micro', '1,2,3,4,6,8', str)
    griglia    = [int(x) for x in griglia.split(',')]
    nome_prop  = opt('--prop', PROP_DEFAULT, str)
    buffer     = opt('--buffer', 1000.0)
    ratchet    = flag('--ratchet')
    confronta  = flag('--confronta')
    path = arg[0]

    props = leggi_prop()
    if confronta:
        return confronto(path, props, griglia, n_sim, comm_opt, giorni_opt)
    if nome_prop not in props:
        raise SystemExit('prop %r non in %s (ci sono: %s)'
                         % (nome_prop, os.path.basename(PROP_FILE), ', '.join(props)))
    usa_prop(props[nome_prop])
    comm_micro = COMM_MICRO if comm_opt is None else comm_opt
    giorni_max = int(giorni_opt) if giorni_opt is not None else (PROP['giorni_max'] or GUARDIA_GG)

    cfg, giorni = per_giorno(path, comm_micro)
    rng = random.Random(20261015)

    print('=' * 78)
    print('STAGE 7 -- %s -- %s' % (os.path.basename(path), PROP['nome']))
    print('=' * 78)
    d1, d2 = _data(cfg.get('Start Date')), _data(cfg.get('End Date'))
    tot = sum(len(t) for _, t in giorni)
    print('Conto $%s | target +$%s | MLL $%s trailing EOD (lock $%s) | tentativo %s'
          % (f'{CONTO:,.0f}', f'{TARGET:,.0f}', f'{MLL:,.0f}', f'{LOCK:,.0f}', _dollari(COSTO_TENT)))
    print('Scadenza: %s | DLL %s | consistency %s | regole verificate: %s'
          % ('%d giorni' % PROP['giorni_max'] if PROP['giorni_max']
             else 'nessuna (tentativo aperto dopo %d giorni = non passato)' % giorni_max,
             '$%s (chiude la giornata, non il conto)' % f'{DLL:,.0f}' if DLL else 'nessuno',
             '%.0f%%' % (100 * CONSISTENCY) if CONSISTENCY else 'nessuna',
             PROP['verificato']))
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
    print('   %-7s %-40s %-28s' % ('', 'iid (tentativi indipendenti)', 'contiguo (storico vero)'))
    print('   %-7s %7s %11s %7s %8s   %7s %7s %8s'
          % ('micro', 'pass%', 'IC 95%', 'fail%', 'gg mediani', 'pass%', 'fail%', 'gg mediani'))
    risultati = {}
    for n in griglia:
        ei, di = sim_iid(giorni, n, n_sim, giorni_max, rng)
        ec, dc = sim_contiguo(giorni, n, giorni_max)
        pi = 100.0 * ei['pass'] / sum(ei.values())
        pc = 100.0 * ec['pass'] / sum(ec.values())
        lo, hi = wilson(ei['pass'], sum(ei.values()))
        mi = sorted(di)[len(di) // 2] if di else 0
        mc = sorted(dc)[len(dc) // 2] if dc else 0
        risultati[n] = (pi / 100.0, pc / 100.0, mi, mc)
        fuori = PROP['max_micro'] is not None and n > PROP['max_micro']
        print('   %-7d %7.1f %5.1f-%-5.1f %7.1f %8d   %7.1f %7.1f %8d%s'
              % (n, pi, 100 * lo, 100 * hi, 100.0 * ei['fail'] / sum(ei.values()), mi,
                 pc, 100.0 * ec['fail'] / sum(ec.values()), mc,
                 '   oltre il limite di contratti' if fuori else ''))
    print('   IC 95%%: l\'incertezza della SIMULAZIONE (%d giri), non quella dei dati.' % n_sim)
    print('   Quella dei dati e\' piu\' larga: lo storico e\' uno solo.')

    ammessi = [n for n in risultati
               if PROP['max_micro'] is None or n <= PROP['max_micro']] or list(risultati)
    migliore = max(ammessi, key=lambda n: risultati[n][0])     # si scegle sullo iid
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

    print('\n5. SE DAL VIVO VA PEGGIO DEL BACKTEST  (%d micro, iid)' % migliore)
    print('   %-24s %8s %12s' % ('scenario', 'pass%', 'entro 4 tent.'))
    for nome, wa, sh in SCENARI:
        g2 = giorni if wa == 0 and sh == 0 else degrada(giorni, wa, sh, rng)
        e2, _d2 = sim_iid(g2, migliore, max(2000, n_sim // 4), giorni_max, rng)
        p2 = e2['pass'] / float(sum(e2.values()))
        print('   %-24s %7.1f%% %11.1f%%' % (nome, 100 * p2, 100 * cumulato(p2, 4)))

    print('\n6. SIZE A GRADINI  (meno micro finche\' il profitto e\' sotto +$%.0f, poi %d)'
          % (buffer, migliore))
    print('   %s' % ('ratchet: superato il buffer una volta, si resta pieni' if ratchet
                     else 'dinamico: se il profitto riscende sotto il buffer si torna piccoli'))
    iniziali = sorted({max(1, int(round(f * migliore))) for f in (0.25, 0.50, 0.75)} - {migliore})
    if not iniziali:
        print('   con %d micro non c\'e\' una size piu\' piccola da provare' % migliore)
    else:
        righe = sim_gradini(giorni, migliore, iniziali, buffer, n_sim, giorni_max, 20261024, ratchet)
        _m0, k0, n0, gg0 = righe[0]
        lo0, hi0 = wilson(k0, n0)
        print('   %-14s %7s %11s %9s %11s' % ('partenza', 'pass%', 'IC 95%', 'vs pieni', 'gg mediani'))
        print('   %-14s %7.1f %5.1f-%-5.1f %9s %11d' % ('%d pieni' % migliore, 100.0 * k0 / n0,
                                                       100 * lo0, 100 * hi0, 'base', gg0))
        meglio = peggio = False
        for m, k, n, gg in righe[1:]:
            lo, hi = wilson(k, n)
            print('   %-14s %7.1f %5.1f-%-5.1f %+8.1f pp %11d' % ('%d -> %d' % (m, migliore), 100.0 * k / n,
                                                              100 * lo, 100 * hi, 100.0 * (k - k0) / n, gg))
            meglio = meglio or lo > hi0
            peggio = peggio or hi < lo0
        if meglio:
            print('   -> partire piccoli AIUTA, fuori dagli intervalli di confidenza')
        elif peggio and not meglio:
            print('   -> partire piccoli PEGGIORA: il tempo speso piccoli costa piu\' della protezione')
        else:
            print('   -> nessuna differenza distinguibile: partire piccoli non aiuta ne\' danneggia')
        print('   Stesse sequenze di giorni per tutte le righe: la differenza e\' solo dei gradini.')
        if not PROP['giorni_max']:
            print('   Senza scadenza la partenza lenta costa poco, ma la guardia a %d giorni la penalizza.'
                  % giorni_max)

    print('\n7. COSTO PER ARRIVARE FUNDED  (%d micro)' % migliore)
    if COSTO_TENT is None:
        print('   costo del tentativo non verificato in %s' % os.path.basename(PROP_FILE))
    else:
        if pi > 0:
            print('   iid         tentativi attesi %.1f -> $%.0f  |  ~%.1f mesi'
                  % (1 / pi, COSTO_TENT / pi, (mi * (1 / pi)) / 21.0))
            if ATTIVAZIONE:
                print('               + attivazione del funded $%.0f = $%.0f'
                      % (ATTIVAZIONE, COSTO_TENT / pi + ATTIVAZIONE))
        if seq[tent_max] > 0:
            print('   sequenziale %.1f%% entro %d tentativi, costo massimo $%.0f'
                  % (100 * seq[tent_max], tent_max, COSTO_TENT * tent_max))
    print()


def _dollari(v):
    return 'n/d' if v is None else '$%s' % f'{v:,.0f}'


def confronto(path, props, griglia, n_sim, comm_opt, giorni_opt):
    """Lo stesso report su tutte le prop del file: pass rate iid per micro e costo atteso."""
    print('=' * 78)
    print('CONFRONTO FRA PROP -- %s' % os.path.basename(path))
    print('=' * 78)
    print('Pass rate iid (%d giri per cella). Stesse sequenze casuali per ogni prop.' % n_sim)
    print('   %-24s %-10s' % ('prop', 'scadenza') + ''.join('%8s' % ('%d mic' % n) for n in griglia)
          + '%14s' % 'costo atteso')
    for s, p in props.items():
        usa_prop(p)
        comm = COMM_MICRO if comm_opt is None else comm_opt
        gmax = int(giorni_opt) if giorni_opt is not None else (p['giorni_max'] or GUARDIA_GG)
        _cfg, giorni = per_giorno(path, comm)
        celle, migliore = [], None
        for n in griglia:
            rng = random.Random(20261015)
            e, _d = sim_iid(giorni, n, n_sim, gmax, rng)
            pr = e['pass'] / float(sum(e.values()))
            fuori = p['max_micro'] is not None and n > p['max_micro']
            celle.append('%8s' % ('oltre' if fuori else '%.1f' % (100 * pr)))
            if not fuori and (migliore is None or pr > migliore[1]):
                migliore = (n, pr)
        costo = ('n/d' if COSTO_TENT is None or not migliore or migliore[1] == 0
                 else '$%.0f (%d mic)' % (COSTO_TENT / migliore[1] + (ATTIVAZIONE or 0),
                                          migliore[0]))
        scad = '%d gg' % p['giorni_max'] if p['giorni_max'] else 'nessuna'
        print('   %-24s %-10s' % (p['nome'][:24], scad) + ''.join(celle) + '%14s' % costo)
    print('\nNon verificate: ' + (', '.join(p['nome'] for p in props.values()
                                            if p['verificato'] in ('none', '')) or 'nessuna'))
    print('Una prop con scadenza conta i giorni CON trade, non i feriali: e\' un po\' ottimista.')
    print()


if __name__ == '__main__':
    main()
