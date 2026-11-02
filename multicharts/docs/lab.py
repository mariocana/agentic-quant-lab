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
  - la via B usa la soglia t del massimo di k strategie a edge zero;
  - una riga NO nei controlli preliminari rende il report invalido.

Fasi: s1 (meccanica, 100 giorni), is (2020-2024), oos (2025->oggi), book (gate marginale).

Uso:
    python3 docs/lab.py stato
    python3 docs/lab.py prereg strategies/X/SPEC.md
    python3 docs/lab.py nuova "Nome" strategies/X/SPEC.md --famiglia "..." --strumento "..."
    python3 docs/lab.py collega "Nome gia' in pipeline_status" strategies/X/SPEC.md
    python3 docs/lab.py giudica strategies/X/SPEC.md is strategies/X/reports/X_IS.xlsx
    python3 docs/lab.py giudica strategies/X/SPEC.md book strategies/X/reports/X_OOS.xlsx \\
        --micro 1 --book strategies/DriftPullback/reports/DPB_S5_OOS_2025-2026.xlsx:2
    python3 docs/lab.py verbale strategies/X/SPEC.md is --nota "..."
    python3 docs/lab.py verbale strategies/X/SPEC.md oos --esito invalido --nota "commissione a zero"

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
VIA_B_MIN_T = 0.5
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
    via = re.search(r'^\s*[-*]?\s*via:\s*([AB])\b', testo, re.M | re.I)
    k = re.search(r'^\s*[-*]?\s*k-varianti:\s*(\d+)', testo, re.M | re.I)
    return {'via': via.group(1).upper() if via else 'A', 'k': int(k.group(1)) if k else 1,
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
        json.dump(d, f, ensure_ascii=False, indent=2)
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
    k_contato = len({s for (s, f) in v if f == 'is'})
    print(json.dumps({'spec': rel(a.spec), 'commit': sha[:10], 'data': quando, 'via': info['via'],
                      'k_dichiarato': info['k'], 'k_contato': k_contato,
                      'soglia_t_via_B': round(max(VIA_B_MIN_T, soglia_k(max(info['k'], k_contato))), 2),
                      'blocco_pre_registrazione': info['blocco']}, ensure_ascii=False))
    if not info['blocco']:
        print('ATTENZIONE: manca il blocco "## Pre-registrazione" (via, k-varianti, attesa, kill)')


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


def gira_check_report(report, fase_cr, dd_is):
    import check_report as cr
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        m = cr.rapporto(report, fase_cr, dd_is)
    _, pl, _, _, _ = cr.leggi(report)
    testo = buf.getvalue()
    prelim = re.findall(r'^\s{2}(NO|\?)\s+(.*)$', testo, re.M)
    metr = {k: m[k] for k in ('n', 'avg', 't', 'wr', 'rr', 'pf', 'dd', 'net') if k in m}
    metr['peggiore'] = min(pl) if pl else 0.0
    esito = None
    if fase_cr:
        esito = 'passa' if re.search(r'VERDETTO: PASSA', testo) else 'non passa'
    return testo, metr, prelim, esito


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
    t_spec = dt.datetime.fromisoformat(quando)
    code, primo = git('log', '--diff-filter=A', '--follow', '--format=%cI', '--', rel(report))
    if primo:
        t_rep, origine = dt.datetime.fromisoformat(primo.splitlines()[-1]), 'commit del report'
    else:
        t_rep, origine = dt.datetime.fromtimestamp(os.path.getmtime(report)).astimezone(), 'data del file'
    if t_rep < t_spec:
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
            fail('l\'OOS di %s e\' gia\' stato giudicato (%s): non si rigira' % (stem(spec), mio.get('esito')))
        if mio:
            avvisi.append('OOS gia\' visto in un run invalido: se passa, vale solo come prova dal vivo')
        sorelle = [s for (s, f) in v if f == 'oos' and s != stem(spec)]
        if sorelle:
            avvisi.append('OOS gia\' visto su SPEC sorelle (%s): verdetto asimmetrico, fallire conta pieno, '
                          'passare vale solo come prova dal vivo' % ', '.join(sorelle))

    # 5. lo script della fase
    dati = {'fase': fase, 'spec': rel(spec), 'spec_commit': sha[:10], 'report': rel(report),
            'via': info['via'], 'avvisi': avvisi}
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
        if fase == 'oos' and dd_is is None:
            is_v = v.get((stem(spec), 'is'))
            if is_v and is_v.get('dd'):
                dd_is = float(is_v['dd'])
            else:
                fail('oos: manca il DD dell\'IS (nessun verdetto IS con dd): passa --dd-is')
        fase_cr = {'s1': None, 'is': 2 if info['via'] == 'A' else None, 'oos': 3}[fase]
        testo, metr, prelim, esito = gira_check_report(report, fase_cr, dd_is)
        if fase == 'is' and info['via'] == 'B':
            k = max(info['k'], len({s for (s, f) in v if f == 'is'} | {stem(spec)}))
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
    print('ESITO DELLO SCRIPT: %s' % (dati['esito_script'] or 'nessuno (s1: lo decide il judge, passa o bug)'))
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
        if fase == 's1':
            fail('s1: l\'esito lo decide il judge: --esito passa o --esito bug')
        if bloccato:
            fail('un preliminare e\' NO: --esito invalido')
        esito = script
    elif esito in ('passa', 'non passa') and fase != 's1' and esito != script:
        fail('l\'esito e\' quello dello script (%s), non si cambia. Alternative: invalido, sospeso' % script)
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
          'esito_script: %s' % (script or '-')]
    if metr:
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
        if metr and esito in ('passa', 'non passa'):
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
    s = sub.add_parser('prereg'); s.add_argument('spec'); s.set_defaults(fn=cmd_prereg)
    s = sub.add_parser('nuova'); s.add_argument('nome'); s.add_argument('spec')
    s.add_argument('--famiglia'); s.add_argument('--strumento'); s.set_defaults(fn=cmd_nuova)
    s = sub.add_parser('collega'); s.add_argument('nome'); s.add_argument('spec'); s.set_defaults(fn=cmd_collega)
    s = sub.add_parser('giudica'); s.add_argument('spec'); s.add_argument('fase', choices=FASI)
    s.add_argument('report'); s.add_argument('--dd-is', type=float)
    s.add_argument('--book', action='append'); s.add_argument('--micro', default='1'); s.add_argument('--dal')
    s.set_defaults(fn=cmd_giudica)
    s = sub.add_parser('verbale'); s.add_argument('spec'); s.add_argument('fase', choices=FASI)
    s.add_argument('--esito', choices=['passa', 'non passa', 'bug', 'invalido', 'sospeso'])
    s.add_argument('--nota'); s.set_defaults(fn=cmd_verbale)
    a = p.parse_args()
    a.fn(a)


if __name__ == '__main__':
    main()
