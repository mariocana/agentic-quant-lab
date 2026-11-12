#!/usr/bin/env python3
"""Le regole della pipeline prop, in codice: le usa il judge di /lab prima di ogni verdetto.

Il judge non scrive file. Lancia `giudica`, che controlla le regole e fa girare lo script
della fase (check_report.py o gate_marginale.py), poi `verbale`, che scrive il verdetto in
strategies/<X>/verdicts/ e aggiorna pipeline_status.json. L'esito e' quello dello script:
il judge puo' solo dichiarare un report invalido (impostazioni sbagliate) o sospenderlo
con una domanda per Mario.

Regole controllate (docs/factory_trading.md, §3):
  - la SPEC e' committata, pulita, e non e' cambiata dopo un verdetto gia' dato;
  - il report non e' piu' vecchio del commit della SPEC;
  - l'OOS si gira una volta sola; un OOS gia' visto rende il verdetto asimmetrico;
  - la via B usa la soglia t del massimo di k strategie a edge zero; in OOS non ha soglie
    proprie: il suo giudizio e' il gate marginale;
  - una riga NO nei controlli preliminari rende il report invalido;
  - Stage 1: controlli meccanici sulla List of Trades (uscite, orari, trade al giorno,
    overnight, scaling x10), l'esito e' quello dei controlli.

Il k conta le VARIANTI, non i file: i report IS della cartella si raggruppano togliendo i
suffissi di rerun (meta1/meta2, costi-onesti, IS-intero, anni). La SPEC puo' dichiarare
`via: A|B` (via A, altrimenti via B). Un blocco "## Pre-registrazione" aggiunto dopo, a una
SPEC che non lo aveva, si dichiara con `registrata: <sha>`: lab.py verifica che dopo quel
commit siano state solo AGGIUNTE righe nel blocco, e usa la data di <sha>.
La data del report e' l'Export Time scritto da MultiCharts nel foglio Settings.

Fasi: s1 (meccanica, 100 giorni), is (2020-2024), oos (2025->oggi), book (gate marginale).

Uso:
    python3 docs/lab.py cerca vwap pullback adx          # cosa e' gia' stato fatto su un'idea
    python3 docs/lab.py annota strategies/X/SPEC.md "SPEC scritta" --next "Stage 1: ..."
    python3 docs/lab.py annota - "idea scartata: ..."     # log generale
    python3 docs/lab.py stato
    python3 docs/lab.py prereg strategies/X/SPEC.md
    python3 docs/lab.py nuova "Nome" strategies/X/SPEC.md --famiglia "..." --strumento "..."
    python3 docs/lab.py collega "Nome gia' in pipeline_status" strategies/X/SPEC.md
    python3 docs/lab.py giudica strategies/X/SPEC.md s1 strategies/X/reports/X_S1_100gg.xlsx \\
        --x10 strategies/X/reports/X_S1_100gg_x10.xlsx --entrata 1030-1430 --max-giorno 3 --flat
    python3 docs/lab.py giudica strategies/X/SPEC.md is strategies/X/reports/X_IS.xlsx
    python3 docs/lab.py giudica strategies/X/SPEC.md book strategies/X/reports/X_OOS.xlsx \\
        --micro 1 --book strategies/DriftPullback/reports/DPB_S5_OOS_2025-2026.xlsx:2
    python3 docs/lab.py verbale strategies/X/SPEC.md is --nota "..."
    python3 docs/lab.py verbale strategies/X/SPEC.md oos --esito invalido --nota "commissione a zero"
    python3 docs/lab.py replica strategies/X/SPEC.md oos strategies/X/reports/X_OOS.xlsx   # MC replica il motore

Report del motore Python (python3 -m motore.esegui ...): stessa forma di quelli di MC, si giudicano
uguali; la riga Fonte di Settings finisce nel verdetto. Il suffisso _motore e' un rerun per il k.
Dopo un verdetto sul motore, il report di MultiCharts e' una replica (lab.py replica), non un nuovo
sguardo: stessa soglia della calibrazione, 90% dei trade e net entro il 10%.

Solo libreria standard.
"""
import argparse, contextlib, datetime as dt, io, json, math, os, re, subprocess, sys

DOCS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(DOCS)
STATUS = os.path.join(DOCS, 'pipeline_status.json')
REGISTRO = os.path.join(DOCS, 'pipeline_semplice.md')
sys.path.insert(0, DOCS)

FASI = ['s1', 'is', 'oos', 'book']
STAGE = {'s1': '1', 'is': '2', 'oos': '5', 'book': '8'}     # chiavi di pipeline_status.json
PRIMA = {'is': 's1', 'oos': 'is', 'book': 'oos'}
NOME = {'s1': 'Stage 1, meccanica', 'is': 'fase 2, IS', 'oos': 'fase 3, OOS', 'book': 'fase 3b, gate marginale'}
PROSSIMO = {
    ('s1', 'passa'): 'IS 2020-2024 in MultiCharts, poi /lab report',
    ('s1', 'bug'): 'il coder corregge il codice, poi si rigira lo Stage 1',
    ('is', 'passa'): 'OOS 2025->oggi in MultiCharts, una volta sola, poi /lab report',
    ('is', 'non passa'): 'Chiusa. Cimitero (fase 2, IS).',
    ('oos', 'passa'): 'gate marginale contro il book live: /lab book',
    ('oos', 'non passa'): 'Chiusa. Cimitero definitivo (fase 3, OOS).',
    ('book', 'passa'): 'entra nel book: paper almeno una settimana, poi eval col budget dichiarato',
    ('book', 'non passa'): 'Chiusa. Cimitero (gate marginale).',
}
VIA_B_MIN_T = 0.5
FUSO_ORE = 14               # margine sull'Export Time, scritto nell'ora locale del PC che esporta
VIA_B_PEGGIORE = 500.0      # trade peggiore per micro, in $


def fail(msg):
    raise SystemExit('lab: ' + msg)


def rel(path):
    return os.path.relpath(os.path.abspath(path), ROOT)


def git(*args):
    r = subprocess.run(['git', '-C', ROOT] + list(args), capture_output=True, text=True)
    return r.returncode, r.stdout.strip()


# ------------------------------------------------------------------ SPEC e verdetti

def leggi_spec(spec):
    """via e k-varianti dal blocco '## Pre-registrazione' (righe 'chiave: valore')."""
    if not os.path.isfile(spec):
        fail('SPEC non trovata: %s' % spec)
    testo = open(spec, encoding='utf8').read()
    via = re.search(r'^\s*[-*]?\s*via:\s*(A\s*\|\s*B|[AB])\b', testo, re.M | re.I)
    k = re.search(r'^\s*[-*]?\s*k-varianti:\s*(\d+)', testo, re.M | re.I)
    reg = re.search(r'^\s*[-*]?\s*registrata:\s*([0-9a-f]{7,40})\b', testo, re.M | re.I)
    v = re.sub(r'\s', '', via.group(1).upper()) if via else 'A'
    return {'via': 'A|B' if v == 'A|B' else v, 'k': int(k.group(1)) if k else 1,
            'registrata': reg.group(1) if reg else None,
            'blocco': bool(re.search(r'^##\s*Pre-registrazione', testo, re.M | re.I))}


def commit_spec(spec):
    """(sha, data ISO) dell'ultimo commit che ha toccato la SPEC; fallisce se non e' committata o e' sporca."""
    # --follow e diff-filter=AM: conta l'ultimo cambio di contenuto, non gli spostamenti di file
    code, out = git('log', '-1', '--follow', '--diff-filter=AM', '--format=%H %cI', '--', rel(spec))
    if code or not out:
        fail('%s non e\' committata: la pre-registrazione e\' il commit, va fatto prima del run' % rel(spec))
    code, _ = git('diff', '--quiet', 'HEAD', '--', rel(spec))
    if code:
        fail('%s ha modifiche non committate: o si committano prima del run, o e\' una variante nuova' % rel(spec))
    sha, quando = out.split(' ', 1)
    return sha, quando


def data_preregistrazione(spec, info, sha, quando):
    """(data, nota) della pre-registrazione. Con `registrata: <sha>` vale la data di <sha>, ma solo
    se dopo quel commit la SPEC ha avuto soltanto righe AGGIUNTE dentro il blocco Pre-registrazione."""
    if not info['registrata']:
        return quando, None
    base = info['registrata']
    code, out = git('log', '-1', '--format=%H %cI', base)
    if code or not out:
        fail('registrata: %s non e\' un commit di questo repo' % base)
    base_sha, base_data = out.split(' ', 1)
    code, nomi = git('log', '--follow', '--format=%H', '--', rel(spec))
    if base_sha not in nomi.split():
        fail('registrata: %s non ha toccato %s' % (base[:10], rel(spec)))
    code, vecchio = git('show', '%s:%s' % (base_sha, path_al_commit(spec, base_sha)))
    if code:
        fail('registrata: non trovo %s al commit %s' % (rel(spec), base[:10]))
    nuovo = open(spec, encoding='utf8').read()
    import difflib
    blocco, dentro, tolte, fuori = re.compile(r'^##\s*Pre-registrazione', re.I), False, [], []
    righe_nuove = nuovo.split('\n')
    in_blocco = []
    for r in righe_nuove:
        if r.startswith('## '):
            dentro = bool(blocco.match(r))
        in_blocco.append(dentro or bool(blocco.match(r)))
    for op in difflib.SequenceMatcher(None, vecchio.split('\n'), righe_nuove, autojunk=False).get_opcodes():
        tag, i1, i2, j1, j2 = op
        if tag in ('replace', 'delete'):
            tolte.append(i1 + 1)
        if tag in ('replace', 'insert') and not all(in_blocco[j] or not righe_nuove[j].strip() for j in range(j1, j2)):
            fuori.append(j1 + 1)
    if tolte or fuori:
        fail('registrata: dopo %s la SPEC non ha solo aggiunto il blocco Pre-registrazione '
             '(righe cambiate o tolte: %s; aggiunte fuori dal blocco: %s). E\' una variante nuova'
             % (base[:10], tolte[:5] or '-', fuori[:5] or '-'))
    return base_data, ('blocco Pre-registrazione aggiunto dopo %s: via e k si leggono anche nella prosa '
                       'della SPEC a quel commit' % base[:10])


def path_al_commit(spec, sha):
    """Il percorso della SPEC al commit sha (il repo e' stato riorganizzato: git --follow)."""
    code, out = git('log', '--follow', '--name-only', '--format=@%H', '--', rel(spec))
    cur = None
    for riga in out.splitlines():
        if riga.startswith('@'):
            cur = riga[1:]
        elif riga.strip() and cur == sha:
            return riga.strip()
    return rel(spec)


def cartella_verdetti(spec):
    return os.path.join(os.path.dirname(os.path.abspath(spec)), 'verdicts')


def stem(spec):
    return os.path.splitext(os.path.basename(spec))[0]


def file_verdetto(spec, fase):
    return os.path.join(cartella_verdetti(spec), '%s_%s.md' % (stem(spec), fase))


def leggi_verdetto(path):
    if not os.path.isfile(path):
        return None
    testo = open(path, encoding='utf8').read()
    m = re.match(r'^---\n(.*?)\n---\n', testo, re.S)
    dati = {}
    for riga in (m.group(1).splitlines() if m else []):
        if ':' in riga:
            k, v = riga.split(':', 1)
            dati[k.strip()] = v.strip()
    return dati


def verdetti_cartella(spec):
    """Tutti i verdetti delle SPEC sorelle (stessa cartella): {(stem, fase): dati}."""
    d, out = cartella_verdetti(spec), {}
    if os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            m = re.fullmatch(r'(.+)_(s1|is|oos|book)\.md', f)
            if m:
                out[(m.group(1), m.group(2))] = leggi_verdetto(os.path.join(d, f))
    return out


IS_REPORT = re.compile(r'(^|[_-])(S2|S4|Stage2|IS)([_-]|\.xlsx$)', re.I)
# parti del nome che indicano un rerun della stessa variante, non una variante nuova
RERUN = re.compile(r'(^|[_-])(S2|S4|Stage2|IS|IS-intero|intero|meta\d|costi-onesti|range-corto|'
                   r'non-valido|motore|x10|\d{4}(-\d{4})?)(?=[_-]|$)', re.I)


def report_is_passati(spec):
    """Report IS gia' girati nella cartella (anche prima di /lab)."""
    d = os.path.join(os.path.dirname(os.path.abspath(spec)), 'reports')
    if not os.path.isdir(d):
        return []
    return sorted(f for f in os.listdir(d) if f.lower().endswith('.xlsx') and IS_REPORT.search(f)
                  and not re.search(r'oos|100gg|(^|_)S1_', f, re.I) and not re.search(r'_x\d+\.xlsx$', f, re.I))


def variante_di(f):
    """Il nome della variante di un report: il nome senza i suffissi di rerun."""
    base = os.path.splitext(f)[0]
    prima = None
    while prima != base:
        prima, base = base, RERUN.sub('', base)
    return re.sub(r'[_-]+', '_', base).strip('_').lower() or f.lower()


def varianti_is_passate(spec):
    """{variante: [report]}: contano nel k della famiglia, una volta per variante."""
    out = {}
    for f in report_is_passati(spec):
        out.setdefault(variante_di(f), []).append(f)
    return out


def k_effettivo(spec, info, v):
    """Il piu' alto fra k dichiarato, IS giudicati da /lab e varianti IS gia' nella cartella."""
    giudicati = {s for (s, f) in v if f == 'is'} | {stem(spec)}
    return max(info['k'], len(giudicati), len(varianti_is_passate(spec)))


def soglia_k(k):
    """t atteso del massimo di k strategie a edge zero: E[max di k normali standard]."""
    if k <= 1:
        return 0.0
    phi = lambda x: math.exp(-x * x / 2) / math.sqrt(2 * math.pi)
    Phi = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))
    passo, x, tot = 0.001, -8.0, 0.0
    while x < 8.0:
        tot += x * k * phi(x) * Phi(x) ** (k - 1) * passo
        x += passo
    return tot


# ------------------------------------------------------------------ pipeline_status.json

def carica_status():
    with open(STATUS, encoding='utf8') as f:
        return json.load(f)


def salva_status(d):
    d['updated'] = dt.date.today().isoformat()
    tmp = STATUS + '.tmp'
    with open(tmp, 'w', encoding='utf8') as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
        f.write('\n')
    os.replace(tmp, STATUS)


def voce(d, spec):
    for s in d['strategies']:
        if s.get('spec') == rel(spec):
            return s
    return None


# ------------------------------------------------------------------ comandi

def cmd_prereg(a):
    info = leggi_spec(a.spec)
    sha, quando = commit_spec(a.spec)
    v = verdetti_cartella(a.spec)
    data_reg, nota_reg = data_preregistrazione(a.spec, info, sha, quando)
    passati = varianti_is_passate(a.spec)
    k = k_effettivo(a.spec, info, v)
    print(json.dumps({'spec': rel(a.spec), 'commit': sha[:10], 'data': data_reg, 'via': info['via'],
                      'k_dichiarato': info['k'], 'k_effettivo': k, 'varianti_is_nella_cartella': len(passati),
                      'soglia_t_via_B': round(max(VIA_B_MIN_T, soglia_k(k)), 2),
                      'blocco_pre_registrazione': info['blocco']}, ensure_ascii=False))
    if nota_reg:
        print('NOTA: ' + nota_reg)
    if not info['blocco']:
        print('ATTENZIONE: manca il blocco "## Pre-registrazione" (via, k-varianti, attesa, kill)')
    if info['k'] < k:
        print('ATTENZIONE: k-varianti dichiarato %d, ma nella cartella ci sono gia\' %d varianti IS e %d '
              'giudizi IS: per la via B vale k = %d' % (info['k'], len(passati),
                                                        len({s for (s, f) in v if f == 'is'}), k))
        for var, files in sorted(passati.items()):
            print('  - %s: %s' % (var, ', '.join(files)))


def cmd_nuova(a):
    commit_spec(a.spec)
    d = carica_status()
    if voce(d, a.spec):
        fail('%s e\' gia\' in pipeline_status.json' % rel(a.spec))
    if any(s['name'] == a.nome for s in d['strategies']):
        fail('il nome "%s" esiste gia\': usa collega, o un nome diverso per la variante' % a.nome)
    d['strategies'].append({
        'name': a.nome, 'family': a.famiglia or '', 'instrument': a.strumento or '',
        'path': rel(os.path.dirname(os.path.abspath(a.spec))), 'spec': rel(a.spec),
        'stages': {'0': 'pass'}, 'metrics': {}, 'next': 'Stage 1: 100 giorni in MultiCharts',
        'note': '', 'log': [{'date': dt.date.today().isoformat(),
                             'text': '**Pre-registrata** in `%s`.' % rel(a.spec)}]})
    salva_status(d)
    print('aggiunta: %s -> %s' % (a.nome, rel(a.spec)))


def cmd_collega(a):
    d = carica_status()
    trovate = [s for s in d['strategies'] if s['name'] == a.nome]
    if not trovate:
        fail('nessuna strategia chiamata "%s"; nomi: %s' % (a.nome, ', '.join(s['name'] for s in d['strategies'])))
    trovate[0]['spec'] = rel(a.spec)
    salva_status(d)
    print('collegata: %s -> %s' % (a.nome, rel(a.spec)))


def data_report(report):
    """Quando il report e' stato prodotto: l'Export Time di MultiCharts (foglio Settings), se c'e'.
    Altrimenti il primo commit del file, poi la data del file (che un cp senza -p rinnova)."""
    import check_report as cr, zipfile
    try:
        z = zipfile.ZipFile(report)
        n = cr._find(z, 'Settings')
        for r in (cr._sheet(z, n) if n else []):
            if len(r) >= 2 and r[0].strip() == 'Export Time':
                # ora locale del PC che ha esportato (il VPS e' a Chicago): fuso ignoto, si usa
                # come se fosse UTC e il confronto tiene un margine di FUSO_ORE
                t = dt.datetime(1899, 12, 30) + dt.timedelta(days=float(r[1]))
                return t.replace(tzinfo=dt.timezone.utc), 'Export Time di MultiCharts, fuso ignoto'
    except (zipfile.BadZipFile, ValueError, KeyError):
        pass
    code, primo = git('log', '--diff-filter=A', '--follow', '--format=%cI', '--', rel(report))
    if primo:
        return dt.datetime.fromisoformat(primo.splitlines()[-1]), 'commit del report'
    return dt.datetime.fromtimestamp(os.path.getmtime(report)).astimezone(), 'data del file'


def fonte_report(report):
    """'motore' se il report l'ha scritto motore/ (riga Fonte di Settings), altrimenti 'MultiCharts'."""
    import check_report as cr, zipfile
    try:
        z = zipfile.ZipFile(report)
        n = cr._find(z, 'Settings')
        for r in (cr._sheet(z, n) if n else []):
            if len(r) >= 2 and r[0].strip() == 'Fonte' and 'motore' in r[1]:
                return 'motore'
    except (zipfile.BadZipFile, KeyError):
        pass
    return 'MultiCharts'


def gira_check_report(report, fase_cr, dd_is):
    import check_report as cr
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        m = cr.rapporto(report, fase_cr, dd_is)
    _, pl, _, _, _ = cr.leggi(report)
    testo = buf.getvalue()
    # solo la sezione dei preliminari: i NO dei gate sono esiti, non impostazioni sbagliate
    sezione = testo.split('CONTROLLI PRELIMINARI', 1)[-1].split('MISURE', 1)[0]
    prelim = re.findall(r'^\s{2}(NO|\?)\s+(.*)$', sezione, re.M)
    metr = {k: m[k] for k in ('n', 'avg', 't', 'wr', 'rr', 'pf', 'dd', 'net') if k in m}
    metr['peggiore'] = min(pl) if pl else 0.0
    esito = None
    if fase_cr:
        esito = 'passa' if re.search(r'VERDETTO: PASSA', testo) else 'non passa'
    return testo, metr, prelim, esito


# ------------------------------------------------------------------ Stage 1

def trade_s1(report):
    """I trade della List of Trades: ingresso, uscita, lato, nome dell'uscita, punti, P&L, contratti."""
    import check_report as cr, zipfile
    z = zipfile.ZipFile(report)
    righe = cr._sheet(z, cr._find(z, 'List of Trades'))
    h = next(i for i, r in enumerate(righe[:10]) if any(c.strip() == 'Profit ($)' for c in r))
    col = {c.strip(): j for j, c in enumerate(righe[h])}
    cella = lambda r, k: r[col[k]].strip() if col.get(k) is not None and col[k] < len(r) else ''
    quando = lambda r: (dt.datetime(1899, 12, 30) + dt.timedelta(days=float(cella(r, 'Date')))
                        + dt.timedelta(seconds=30)).replace(second=0, microsecond=0)
    out, corpo = [], righe[h + 1:]
    for i, r in enumerate(corpo):
        if not cella(r, 'Trade #') or i + 1 >= len(corpo):
            continue
        x = corpo[i + 1]
        lato = 1 if 'long' in cella(r, 'Type').lower() else -1
        ep, xp = float(cella(r, 'Price')), float(cella(x, 'Price'))
        out.append({'in': quando(r), 'out': quando(x), 'lato': lato, 'uscita': cella(x, 'Signal'),
                    'punti': round((xp - ep) * lato, 2), 'pl': float(cella(r, 'Profit ($)')),
                    'cts': cella(r, 'Contracts')})
    return out


def controlli_s1(report, x10, entrata, max_giorno, flat):
    """Controlli meccanici dello Stage 1. Ritorna (testo, esito, metriche)."""
    T = trade_s1(report)
    if not T:
        fail('s1: nessun trade nella List of Trades di %s' % rel(report))
    righe, bug = ['', 'STAGE 1 — controlli meccanici sulla List of Trades (%d trade, %s -> %s)'
                  % (len(T), T[0]['in'].date(), T[-1]['in'].date())], []

    def riga(ok, testo):
        righe.append('  %s %s' % ({True: 'OK  ', False: 'NO  ', None: '?   '}[ok], testo))
        if ok is False:
            bug.append(testo)

    giorni = (T[-1]['in'].date() - T[0]['in'].date()).days
    riga(None if giorni >= 90 else False, 'periodo: %d giorni di calendario fra il primo e l\'ultimo trade (checklist: ~100)' % giorni)
    cts = sorted({t['cts'] for t in T})
    riga(len(cts) == 1, 'contratti per trade: %s' % ', '.join(cts))

    righe.append('  uscite, con i punti realizzati (confrontali con stop e target della SPEC):')
    per = {}
    for t in T:
        per.setdefault(t['uscita'], []).append(t['punti'])
    for nome, pts in sorted(per.items(), key=lambda kv: -len(kv[1])):
        distinti = sorted(set(pts))
        valori = ', '.join('%g' % p for p in distinti) if len(distinti) <= 6 else \
            'da %g a %g (%d valori)' % (distinti[0], distinti[-1], len(distinti))
        righe.append('       %-16s %4d trade   punti: %s' % (nome, len(pts), valori))
    righe.append('    (uno stop o un target fisso deve avere un solo valore; con slippage negli stop '
                 'il valore e\' lo stop piu\' lo slippage)')

    orari = {}
    for t in T:
        orari[t['in'].strftime('%H:%M')] = orari.get(t['in'].strftime('%H:%M'), 0) + 1
    righe.append('  orari d\'ingresso (come li scrive MC: chiusura della barra del fill): '
                 + ' '.join('%s×%d' % kv for kv in sorted(orari.items())))
    if entrata:
        da, a_ = [int(x) for x in entrata.split('-')]
        fuori = [t for t in T if not (da <= int(t['in'].strftime('%H%M')) <= a_)]
        riga(not fuori, 'ingressi dentro %04d-%04d: %d fuori%s' % (
            da, a_, len(fuori), (' (' + ', '.join(str(t['in']) for t in fuori[:5]) + ')') if fuori else ''))
    else:
        riga(None, 'finestra d\'ingresso non passata (--entrata HHMM-HHMM): controllala sugli orari sopra')

    per_giorno = {}
    for t in T:
        per_giorno[t['in'].date()] = per_giorno.get(t['in'].date(), 0) + 1
    mx = max(per_giorno.values())
    if max_giorno:
        riga(mx <= max_giorno, 'trade al giorno: massimo %d (SPEC: %d), %d giorni con trade' % (mx, max_giorno, len(per_giorno)))
    else:
        riga(None, 'trade al giorno: massimo %d, %d giorni con trade (--max-giorno per controllarlo)' % (mx, len(per_giorno)))

    notte = [t for t in T if t['out'].date() != t['in'].date()]
    if flat:
        riga(not notte, 'flat la sera: %d trade a cavallo di due date%s' % (
            len(notte), (' (' + ', '.join('%s -> %s %s' % (t['in'], t['out'], t['uscita']) for t in notte[:5]) + ')') if notte else ''))
    elif notte:
        riga(None, '%d trade a cavallo di due date (se la SPEC dice flat la sera, passa --flat)' % len(notte))

    if x10:
        X = trade_s1(x10)
        uguali = len(X) == len(T) and all(a['in'] == b['in'] and a['out'] == b['out'] and a['uscita'] == b['uscita']
                                         for a, b in zip(T, X))
        n = sum(1 for a, b in zip(T, X) if abs(a['pl'] * 10 - b['pl']) > 0.01)
        riga(uguali and not n, 'scaling x10 (%s): %d trade contro %d, stessi ingressi e uscite %s, P&L x10 '
             'diverso su %d trade' % (rel(x10), len(X), len(T), 'si' if uguali else 'NO', n))
    else:
        riga(None, 'scaling x10 non controllato (--x10 report_x10.xlsx)')

    righe += ['', '  ESITO DEI CONTROLLI: %s' % ('BUG — ' + '; '.join(bug) if bug else
              'passa (le uscite in punti vanno confrontate a mano con la SPEC)'), '']
    pl = [t['pl'] for t in T]
    metr = {'n': len(T), 'peggiore': min(pl)}
    return '\n'.join(righe), ('bug' if bug else 'passa'), metr


def cmd_giudica(a):
    fase, spec, report = a.fase, a.spec, a.report
    if not os.path.isfile(report):
        fail('report non trovato: %s' % report)
    info = leggi_spec(spec)
    sha, quando = commit_spec(spec)
    avvisi, v = [], verdetti_cartella(spec)
    d = carica_status()
    entry = voce(d, spec)

    # 1. la SPEC non e' cambiata dopo un verdetto gia' dato
    for (s, f), dati in v.items():
        if s == stem(spec) and dati.get('spec_commit') and not sha.startswith(dati['spec_commit']):
            fail('la SPEC e\' cambiata dopo il verdetto %s (commit %s, ora %s): e\' una variante, '
                 'va scritta in una SPEC nuova' % (f, dati['spec_commit'], sha[:10]))

    # 2. il report non e' piu' vecchio della pre-registrazione
    quando_reg, nota_reg = data_preregistrazione(spec, info, sha, quando)
    if nota_reg:
        avvisi.append(nota_reg)
    t_spec = dt.datetime.fromisoformat(quando_reg)
    t_rep, origine = data_report(report)
    margine = dt.timedelta(hours=FUSO_ORE if 'fuso ignoto' in origine else 0)
    if t_spec - margine <= t_rep < t_spec + margine:
        avvisi.append('report (%s) e pre-registrazione a meno di %d ore: con il fuso ignoto dell\'Export '
                      'Time l\'ordine non e\' certo, controllalo' % (origine, FUSO_ORE))
    elif t_rep < t_spec:
        fail('il report (%s %s) e\' piu\' vecchio del commit della SPEC (%s): il run e\' venuto prima '
             'della pre-registrazione' % (origine, t_rep.isoformat(timespec='minutes'), t_spec.isoformat(timespec='minutes')))

    # 3. ordine delle fasi
    if fase in PRIMA:
        prec = v.get((stem(spec), PRIMA[fase]))
        gia = entry and entry.get('stages', {}).get(STAGE[PRIMA[fase]]) == 'pass'
        if not (prec and prec.get('esito') == 'passa') and not gia:
            fail('%s richiede prima %s con esito passa' % (fase, PRIMA[fase]))

    # 4. l'OOS una volta sola
    if fase == 'oos':
        mio = v.get((stem(spec), 'oos'))
        if mio and mio.get('esito') != 'invalido':
            extra = (' Se questo e\' il report MC che replica l\'OOS del motore: lab.py replica %s oos %s'
                     % (rel(spec), rel(report))) if mio.get('fonte') == 'motore' else ''
            fail('l\'OOS di %s e\' gia\' stato giudicato (%s): non si rigira.%s' % (stem(spec), mio.get('esito'), extra))
        if mio:
            avvisi.append('OOS gia\' visto in un run invalido: se passa, vale solo come prova dal vivo')
        sorelle = [s for (s, f) in v if f == 'oos' and s != stem(spec)]
        if sorelle:
            avvisi.append('OOS gia\' visto su SPEC sorelle (%s): verdetto asimmetrico, fallire conta pieno, '
                          'passare vale solo come prova dal vivo' % ', '.join(sorelle))

    # 5. lo script della fase
    fonte = fonte_report(report)
    if fonte == 'motore':
        avvisi.append('report del motore Python (motore/): il report definitivo e\' la replica in MultiCharts, '
                      'con lab.py replica dopo il verdetto')
    dati = {'fase': fase, 'spec': rel(spec), 'spec_commit': sha[:10], 'report': rel(report),
            'via': info['via'], 'fonte': fonte, 'avvisi': avvisi}
    if fase == 'book':
        if not a.book:
            fail('book: serve almeno un --book report.xlsx:micro (il book live di riferimento)')
        cmd = [sys.executable, os.path.join(DOCS, 'gate_marginale.py')]
        for b in a.book:
            cmd += ['--book', b]
        cmd += ['--cand', '%s:%s' % (report, a.micro)]
        if a.dal:
            cmd += ['--dal', a.dal]
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
        testo = r.stdout + r.stderr
        if r.returncode:
            fail('gate_marginale.py e\' uscito con errore:\n' + testo)
        dati['esito_script'] = 'passa' if 'VERDETTO: ENTRA NEL BOOK' in testo else 'non passa'
        diff = re.search(r'differenza \(pp\)\s+([+-]?[\d.]+)\s+([+-]?[\d.]+)', testo)
        pegg = re.search(r'giornata peggiore del book con la candidata: \$(-?[\d.]+)', testo)
        cand = re.search(r'avg \$(-?[\d.]+) per micro', testo)
        dati['registro'] = {'iid': diff.group(1) if diff else '?', 'contiguo': diff.group(2) if diff else '?',
                            'peggiore': pegg.group(1) if pegg else '?', 'avg': cand.group(1) if cand else '?'}
        dati['comando'] = ' '.join(os.path.relpath(c, ROOT) if os.path.isabs(c) else c for c in cmd[1:])
        dati['prelim'] = []
    else:
        dd_is = a.dd_is
        # A|B: in OOS vale la via con cui la strategia ha passato l'IS
        via_oos = info['via']
        if via_oos == 'A|B':
            via_oos = v.get((stem(spec), 'is'), {}).get('via', 'A')
        if fase == 'oos' and via_oos == 'A' and dd_is is None:
            is_v = v.get((stem(spec), 'is'))
            if is_v and is_v.get('dd'):
                dd_is = float(is_v['dd'])
            else:
                fail('oos: manca il DD dell\'IS (nessun verdetto IS con dd): passa --dd-is')
        fase_cr = {'s1': None, 'is': 2 if info['via'] in ('A', 'A|B') else None,
                   'oos': 3 if via_oos == 'A' else None}[fase]
        testo, metr, prelim, esito = gira_check_report(report, fase_cr, dd_is)
        if fase == 'oos' and via_oos == 'B':
            # pipeline_semplice.md: per la via B la fase 3 sono i quattro criteri del gate marginale
            testo += ('\nVia B: l\'OOS non ha soglie proprie, qui si registrano le misure. Il giudizio '
                      'e\' il gate marginale (book); se fallisce, cimitero definitivo.\n')
            esito = 'passa'
            dati['via'] = 'B'
        if fase == 's1':
            t1, esito, m1 = controlli_s1(report, a.x10, a.entrata, a.max_giorno, a.flat)
            testo += t1
            metr.update(m1)
        if fase == 'is' and info['via'] == 'A|B' and esito == 'passa':
            testo += '\nVia A|B: passa la via A, la via B non serve.\n'
            dati['via'] = 'A'
        elif fase == 'is' and info['via'] in ('B', 'A|B'):
            if info['via'] == 'A|B':
                testo += '\nVia A|B: la via A non passa, si giudica con la via B.\n'
                dati['via'] = 'B'
            k = k_effettivo(spec, info, v)
            if k > info['k']:
                avvisi.append('k-varianti dichiarato %d, usato k = %d (varianti IS gia\' nella cartella: %d)'
                              % (info['k'], k, len(varianti_is_passate(spec))))
            soglia = max(VIA_B_MIN_T, soglia_k(k))
            pegg_micro = -metr['peggiore'] / 10.0
            ok_t, ok_p = metr['t'] > soglia, pegg_micro <= VIA_B_PEGGIORE
            testo += ('\nVia B (pipeline_semplice.md, fase 2):\n'
                      '  %s t > %.2f  (max(0,5, edge zero con k = %d))   t = %.2f\n'
                      '  %s trade peggiore <= $%.0f per micro (report / 10)   $%.0f\n'
                      '  (meccanica corretta: la dice il verdetto s1)\n\n  VERDETTO: %s\n'
                      % ('OK  ' if ok_t else 'NO  ', soglia, k, metr['t'],
                         'OK  ' if ok_p else 'NO  ', VIA_B_PEGGIORE, pegg_micro,
                         'PASSA' if ok_t and ok_p else 'NON PASSA -> cimitero'))
            esito = 'passa' if ok_t and ok_p else 'non passa'
            dati['soglia_t'] = round(soglia, 2)
        dati.update({'esito_script': esito, 'metriche': metr, 'prelim': prelim, 'dd_is': dd_is})
        if any(p[0] == 'NO' for p in prelim):
            avvisi.append('un controllo preliminare e\' NO: il report e\' invalido, va rigirato con le '
                          'impostazioni giuste (esito obbligato: invalido)')
    dati['output'] = testo
    os.makedirs(cartella_verdetti(spec), exist_ok=True)
    with open(file_verdetto(spec, fase) + '.pending.json', 'w', encoding='utf8') as f:
        json.dump(dati, f, ensure_ascii=False, indent=2)

    print(testo)
    print('-' * 72)
    print('REGOLE: SPEC %s committata il %s, via %s' % (sha[:10], quando, info['via']))
    for x in avvisi:
        print('AVVISO: ' + x)
    for p in dati['prelim']:
        if p[0] == '?':
            print('DA CONFERMARE CON MARIO: ' + p[1])
    print('ESITO DELLO SCRIPT: %s' % dati['esito_script'])
    print('Ora: lab.py verbale %s %s --nota "..."' % (rel(spec), fase))


def cmd_verbale(a):
    spec, fase = a.spec, a.fase
    pend = file_verdetto(spec, fase) + '.pending.json'
    if not os.path.isfile(pend):
        fail('nessun giudizio in sospeso per %s %s: prima lab.py giudica' % (rel(spec), fase))
    dati = json.load(open(pend, encoding='utf8'))
    script = dati.get('esito_script')
    bloccato = any(p[0] == 'NO' for p in dati.get('prelim', []))
    esito = a.esito
    if esito is None:
        if bloccato:
            fail('un preliminare e\' NO: --esito invalido')
        esito = script
    elif esito in ('passa', 'non passa') and fase != 's1' and esito != script:
        fail('l\'esito e\' quello dello script (%s), non si cambia. Alternative: invalido, sospeso' % script)
    elif fase == 's1' and esito == 'passa' and script == 'bug':
        fail('s1: i controlli dicono bug. Se un\'opzione era sbagliata (finestra, max al giorno, --flat), '
             'rilancia giudica con quella giusta; altrimenti --esito bug')
    elif esito == 'passa' and bloccato:
        fail('un preliminare e\' NO: --esito invalido')
    elif esito == 'bug' and fase != 's1':
        fail('bug vale solo per s1')
    if esito in ('invalido', 'sospeso', 'bug') and not a.nota:
        fail('%s richiede --nota con il motivo' % esito)

    oggi = dt.date.today().isoformat()
    metr = dati.get('metriche', {})
    fm = ['esito: %s' % esito, 'fase: %s' % fase, 'data: %s' % oggi, 'spec: %s' % dati['spec'],
          'spec_commit: %s' % dati['spec_commit'], 'report: %s' % dati['report'], 'via: %s' % dati['via'],
          'esito_script: %s' % (script or '-'), 'fonte: %s' % dati.get('fonte', 'MultiCharts')]
    if metr and 't' in metr:
        fm += ['t: %.2f' % metr['t'], 'dd: %.0f' % metr['dd'], 'n: %d' % metr['n']]
    corpo = ['# %s — %s: %s' % (dati['spec'], NOME[fase], esito.upper()), '']
    if a.nota:
        corpo += ['## Il judge', '', a.nota, '']
    if dati.get('avvisi'):
        corpo += ['## Avvisi', ''] + ['- ' + x for x in dati['avvisi']] + ['']
    if dati.get('comando'):
        corpo += ['## Comando', '', '`gate_marginale.py %s`' % dati['comando'], '']
    corpo += ['## Output dello script', '', '```', dati['output'].rstrip(), '```', '']
    path = file_verdetto(spec, fase)
    if esito == 'sospeso':
        path = path[:-3] + '.sospeso.md'
    with open(path, 'w', encoding='utf8') as f:
        f.write('---\n%s\n---\n%s' % ('\n'.join(fm), '\n'.join(corpo)))
    if esito != 'sospeso':
        os.remove(pend)
        sosp = file_verdetto(spec, fase)[:-3] + '.sospeso.md'
        if os.path.isfile(sosp):
            os.remove(sosp)

    # stato e registro
    d = carica_status()
    entry = voce(d, spec)
    if esito == 'sospeso':
        pass
    elif entry is None:
        print('ATTENZIONE: %s non e\' collegata a pipeline_status.json (lab.py collega o nuova)' % rel(spec))
    else:
        val = {'passa': 'pass', 'non passa': 'fail'}.get(esito)
        if val:
            entry.setdefault('stages', {})[STAGE[fase]] = val
        entry['next'] = PROSSIMO.get((fase, esito), entry.get('next', ''))
        if metr and 'wr' in metr and fase != 's1' and esito in ('passa', 'non passa'):
            entry.setdefault('metrics', {})[NOME[fase]] = '%d trade · t %.2f · WR %.1f%% · R:R %.2f' % (
                metr['n'], metr['t'], metr['wr'], metr['rr'])
        nota = (a.nota or '').strip()
        if nota and not nota.endswith(('.', '!', '?')):
            nota += '.'
        testo = '**%s: %s.** %s Verdetto in `%s`.' % (NOME[fase], esito, nota, rel(path))
        entry.setdefault('log', []).append({'date': oggi, 'text': testo.replace('  ', ' ')})
        salva_status(d)
    if fase == 'book' and esito in ('passa', 'non passa'):
        aggiungi_registro(entry['name'] if entry else rel(spec), dati['registro'], esito)
    print('verbale: %s (%s)' % (rel(path), esito))


SOGLIA_REPLICA_TRADE, SOGLIA_REPLICA_NET = 0.90, 0.10      # come la calibrazione di motore/


def cmd_replica(a):
    """Il report MC che replica una fase giudicata sul report del motore: stessi trade, stesso net?"""
    spec, fase = a.spec, a.fase
    v = verdetti_cartella(spec).get((stem(spec), fase))
    if not v:
        fail('nessun verdetto %s per %s' % (fase, rel(spec)))
    if v.get('fonte') != 'motore':
        fail('il verdetto %s di %s non viene dal motore: non c\'e\' niente da replicare' % (fase, rel(spec)))
    if fonte_report(a.report) != 'MultiCharts':
        fail('%s e\' un report del motore: la replica va fatta in MultiCharts' % rel(a.report))
    sys.path.insert(0, ROOT)
    from motore import mc_report
    py = mc_report.trade(os.path.join(ROOT, v['report']))
    mc = mc_report.trade(a.report)
    if not mc:
        fail('nessun trade nel report MC')
    # solo i giorni coperti da tutti e due: i dati del motore possono finire prima
    fine = min(py[-1].t_out, mc[-1].t_out).date() if py else mc[-1].t_out.date()
    mc = [t for t in mc if t.t_out.date() <= fine]
    py = [t for t in py if t.t_out.date() <= fine]
    k = lambda t: (t.t_in, t.lato)
    ip, im = {k(t): t for t in py}, {k(t): t for t in mc}
    comuni = [x for x in im if x in ip]
    net = lambda ts: sum((t.p_out - t.p_in) * t.lato * t.qta for t in ts)
    n_mc, n_py = net(mc), net(py)
    quota = len(comuni) / len(mc)
    scarto = (n_py - n_mc) / abs(n_mc) if n_mc else float('inf')
    ok = quota >= SOGLIA_REPLICA_TRADE and abs(scarto) <= SOGLIA_REPLICA_NET
    righe = ['REPLICA %s di %s fino al %s' % (fase, rel(spec), fine),
             '  motore: %s' % v['report'], '  MultiCharts: %s' % rel(a.report),
             '  trade MC %d, motore %d, in comune %d (%.1f%% di MC; soglia %.0f%%)'
             % (len(mc), len(py), len(comuni), 100 * quota, 100 * SOGLIA_REPLICA_TRADE),
             '  punti netti MC %.2f, motore %.2f: scarto %+.1f%% (soglia %.0f%%)'
             % (n_mc, n_py, 100 * scarto, 100 * SOGLIA_REPLICA_NET),
             '  ESITO: %s' % ('REPLICA OK: il verdetto del motore resta' if ok else
                             'REPLICA NON OK: la strategia si ferma finche\' non si capisce la differenza')]
    testo = '\n'.join(righe)
    path = file_verdetto(spec, fase)[:-3] + '_replica.md'
    with open(path, 'w', encoding='utf8') as f:
        f.write('---\nesito: %s\nfase: %s\ndata: %s\nreport_mc: %s\nreport_motore: %s\n---\n```\n%s\n```\n'
                % ('ok' if ok else 'non ok', fase, dt.date.today().isoformat(), rel(a.report), v['report'], testo))
    d = carica_status()
    entry = voce(d, spec)
    if entry is not None:
        entry.setdefault('log', []).append({'date': dt.date.today().isoformat(), 'text':
            '**Replica MC di %s: %s** (%d/%d trade, net %+.1f%%). Verbale in `%s`.'
            % (NOME[fase], 'ok' if ok else 'NON ok', len(comuni), len(mc), 100 * scarto, rel(path))})
        salva_status(d)
    print(testo)
    print('verbale: %s' % rel(path))


def aggiungi_registro(nome, r, esito):
    righe = open(REGISTRO, encoding='utf8').read().split('\n')
    try:
        i = next(n for n, l in enumerate(righe) if l.startswith('| data | candidata'))
    except StopIteration:
        print('ATTENZIONE: tabella del registro non trovata in pipeline_semplice.md')
        return
    j = i + 2
    while j < len(righe) and righe[j].startswith('|'):
        j += 1
    num = lambda x: x.replace('-', '−').replace('.', ',')
    pegg = '−$' + '{:,}'.format(abs(int(float(r['peggiore'])))).replace(',', '.') if r['peggiore'] != '?' else '?'
    avg = ('−' if r['avg'].startswith('-') else '+') + '$' + r['avg'].lstrip('-').replace('.', ',')
    riga = '| %s | %s | %s | %s | %s | %s | %s |' % (
        dt.date.today().strftime('%d/%m'), nome, num(r['iid']), num(r['contiguo']), pegg, avg,
        '**entra**' if esito == 'passa' else 'non entra')
    righe.insert(j, riga)
    open(REGISTRO, 'w', encoding='utf8').write('\n'.join(righe))


def cmd_annota(a):
    """Il diario: ogni passo del laboratorio finisce in pipeline_status.json, come fanno le sessioni."""
    d = carica_status()
    voce_log = {'date': dt.date.today().isoformat(), 'text': a.testo}
    if a.spec == '-':
        d.setdefault('log', []).insert(0, voce_log)      # il log generale e' dal piu' recente
        dove = 'log generale'
    else:
        entry = voce(d, a.spec)
        if entry is None:
            fail('%s non e\' collegata a pipeline_status.json (lab.py nuova o collega)' % rel(a.spec))
        entry.setdefault('log', []).append(voce_log)
        if a.next is not None:
            entry['next'] = a.next
        if a.note is not None:
            entry['note'] = a.note
        dove = entry['name']
    salva_status(d)
    print('annotato in %s' % dove)


def cmd_cerca(a):
    """Tutto quello che e' gia' stato fatto su un'idea: strategie, documenti, studi, report."""
    termini = [t.lower() for t in a.termini]
    punti = lambda testo: sum(1 for t in termini if t in testo.lower())
    minimo = a.min or (2 if len(termini) > 2 else 1)
    corto = lambda x, n=220: re.sub(r'\s+', ' ', x)[:n]

    d = carica_status()
    trovate = []
    for s in d['strategies']:
        testo = ' '.join([s.get('name', ''), s.get('family', ''), s.get('instrument', ''), s.get('path', ''),
                          s.get('note', ''), s.get('next', ''), json.dumps(s.get('metrics', {}), ensure_ascii=False)]
                         + [l.get('text', '') for l in s.get('log', [])])
        p = punti(testo)
        if p >= minimo:
            trovate.append((p, s))
    print('== STRATEGIE in pipeline_status.json (%d)' % len(trovate))
    for p, s in sorted(trovate, key=lambda x: -x[0]):
        print('- %s  [%s · %s]  stages %s' % (s['name'], s.get('family', ''), s.get('instrument', ''),
                                              json.dumps(s.get('stages', {}))))
        print('    next: %s' % corto(s.get('next', ''), 160))
        if s.get('note'):
            print('    note: %s' % corto(s['note']))
        for l in s.get('log', [])[-2:]:
            print('    %s: %s' % (l.get('date', ''), corto(l.get('text', ''))))

    generale = [l for l in d.get('log', []) if punti(l.get('text', '')) >= minimo]
    print('\n== LOG GENERALE (%d)' % len(generale))
    for l in generale[:a.max]:
        print('- %s: %s' % (l.get('date', ''), corto(l.get('text', ''))))

    print('\n== DOCUMENTI E STRATEGIE (.md, .txt)')
    radici = [os.path.join(ROOT, 'docs'), os.path.join(ROOT, 'strategies')]
    n_doc = 0
    for radice in radici:
        for cart, _, files in sorted(os.walk(radice)):
            if os.sep + 'verdicts' in cart:
                continue
            for f in sorted(files):
                if not f.endswith(('.md', '.txt')) or f in ('factory_trading.md',):
                    continue
                path = os.path.join(cart, f)
                try:
                    righe = open(path, encoding='utf8', errors='replace').read().split('\n')
                except OSError:
                    continue
                colpi = [(i + 1, r) for i, r in enumerate(righe) if punti(r) >= minimo]
                if punti(f + ' ' + rel(cart)) >= minimo and not colpi:
                    colpi = [(1, righe[0] if righe else '')]
                if colpi:
                    n_doc += 1
                    print('- %s  (%d righe)' % (rel(path), len(colpi)))
                    for num, r in colpi[:3]:
                        print('    %d: %s' % (num, corto(r, 180)))
    if not n_doc:
        print('(nessuno)')

    print('\n== REPORT GIA\' GIRATI')
    n_rep = 0
    for cart, _, files in sorted(os.walk(os.path.join(ROOT, 'strategies'))):
        if os.path.basename(cart) != 'reports':
            continue
        nomi = [f for f in sorted(files) if punti(f + ' ' + rel(cart)) >= minimo]
        if nomi:
            n_rep += len(nomi)
            print('- %s: %s' % (rel(cart), ', '.join(nomi)))
    if not n_rep:
        print('(nessuno)')
    print('\n(termini: %s · una voce compare se ne contiene almeno %d)' % (', '.join(termini), minimo))


def cmd_stato(a):
    d = carica_status()
    out = []
    for s in d['strategies']:
        if not s.get('spec'):
            continue
        spec = os.path.join(ROOT, s['spec'])
        v = verdetti_cartella(spec)
        fatti = {f: v[(stem(spec), f)].get('esito') for f in FASI if (stem(spec), f) in v}
        sospesi = [f for f in FASI if os.path.isfile(file_verdetto(spec, f)[:-3] + '.sospeso.md')]
        pend = [f for f in FASI if os.path.isfile(file_verdetto(spec, f) + '.pending.json')]
        out.append({'nome': s['name'], 'spec': s['spec'], 'stages': s.get('stages', {}),
                    'verdetti': fatti, 'sospesi': sospesi, 'da_verbalizzare': pend, 'next': s.get('next', '')})
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return
    if not out:
        print('nessuna strategia collegata a una SPEC (lab.py collega / nuova)')
    for o in out:
        extra = ''.join([' · sospeso: ' + ','.join(o['sospesi']) if o['sospesi'] else '',
                         ' · da verbalizzare: ' + ','.join(o['da_verbalizzare']) if o['da_verbalizzare'] else ''])
        print('%-34s %-40s %s%s' % (o['nome'][:34], o['spec'][:40],
                                    ' '.join('%s=%s' % kv for kv in o['verdetti'].items()) or '-', extra))


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('stato'); s.add_argument('--json', action='store_true'); s.set_defaults(fn=cmd_stato)
    s = sub.add_parser('cerca'); s.add_argument('termini', nargs='+')
    s.add_argument('--min', type=int, help='quanti termini deve contenere una voce (default 1, 2 se piu\' di 2)')
    s.add_argument('--max', type=int, default=8); s.set_defaults(fn=cmd_cerca)
    s = sub.add_parser('annota'); s.add_argument('spec', help="la SPEC, o - per il log generale")
    s.add_argument('testo'); s.add_argument('--next'); s.add_argument('--note'); s.set_defaults(fn=cmd_annota)
    s = sub.add_parser('prereg'); s.add_argument('spec'); s.set_defaults(fn=cmd_prereg)
    s = sub.add_parser('nuova'); s.add_argument('nome'); s.add_argument('spec')
    s.add_argument('--famiglia'); s.add_argument('--strumento'); s.set_defaults(fn=cmd_nuova)
    s = sub.add_parser('collega'); s.add_argument('nome'); s.add_argument('spec'); s.set_defaults(fn=cmd_collega)
    s = sub.add_parser('giudica'); s.add_argument('spec'); s.add_argument('fase', choices=FASI)
    s.add_argument('report'); s.add_argument('--dd-is', type=float)
    s.add_argument('--book', action='append'); s.add_argument('--micro', default='1'); s.add_argument('--dal')
    s.add_argument('--x10', help='s1: il report con 10 contratti, per lo scaling')
    s.add_argument('--entrata', help='s1: finestra HHMM-HHMM degli orari d\'ingresso come li scrive MC')
    s.add_argument('--max-giorno', type=int, help='s1: trade al giorno dichiarati nella SPEC')
    s.add_argument('--flat', action='store_true', help='s1: la SPEC dice flat la sera')
    s.set_defaults(fn=cmd_giudica)
    s = sub.add_parser('verbale'); s.add_argument('spec'); s.add_argument('fase', choices=FASI)
    s.add_argument('--esito', choices=['passa', 'non passa', 'bug', 'invalido', 'sospeso'])
    s.add_argument('--nota'); s.set_defaults(fn=cmd_verbale)
    s = sub.add_parser('replica', help='il report MC che replica una fase giudicata col motore')
    s.add_argument('spec'); s.add_argument('fase', choices=['s1', 'is', 'oos']); s.add_argument('report')
    s.set_defaults(fn=cmd_replica)
    a = p.parse_args()
    a.fn(a)


if __name__ == '__main__':
    main()
