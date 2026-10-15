#!/usr/bin/env python3
"""Verifica un Performance Report xlsx di MultiCharts contro i gate della pipeline.

Fa due cose, nell'ordine che conta:

  1. CONTROLLI PRELIMINARI -- le trappole che ci hanno gia' bruciato dei run:
     commissione a zero, Bar Magnifier disattivato, timeframe sbagliato,
     range di date diverso da quello dichiarato. Se sbaglia qui, i numeri
     sotto non valgono niente.
  2. MISURE e VERDETTO -- n, WR, avg, barra d'errore, t, R:R, PF, drawdown
     sui trade chiusi, concentrazione annuale; poi PASS/FAIL per fase.

Solo libreria standard: nessun openpyxl, nessun pandas.

Uso:
    python3 mc/docs/check_report.py report.xlsx                 # misure + preliminari
    python3 mc/docs/check_report.py report.xlsx --fase 2        # + verdetto Gate 2 (IS)
    python3 mc/docs/check_report.py report.xlsx --fase 3 --dd-is 12000
    python3 mc/docs/check_report.py reports/*.xlsx --tabella    # una riga per file
"""
import sys, os, re, html, math, zipfile, datetime

# ---------------------------------------------------------------- lettura xlsx

def _sheet(z, n):
    """Restituisce le righe del foglio n come liste di stringhe."""
    ss = []
    try:
        s = z.read('xl/sharedStrings.xml').decode('utf8', 'replace')
        for m in re.finditer(r'<si>(.*?)</si>', s, re.S):
            ss.append(html.unescape(re.sub(r'<.*?>', '', m.group(1))))
    except KeyError:
        pass
    x = z.read('xl/worksheets/sheet%d.xml' % n).decode('utf8', 'replace')
    out = []
    for rm in re.finditer(r'<row[^>]*>(.*?)</row>', x, re.S):
        cells = {}
        for cm in re.finditer(r'<c r="([A-Z]+)\d+"([^>]*)>(.*?)</c>', rm.group(1), re.S):
            col, attr, body = cm.group(1), cm.group(2), cm.group(3)
            vm = re.search(r'<v>(.*?)</v>', body, re.S)
            if not vm:
                tm = re.search(r'<t[^>]*>(.*?)</t>', body, re.S)
                cells[col] = html.unescape(tm.group(1)) if tm else ''
                continue
            v = vm.group(1)
            if 't="s"' in attr:
                v = ss[int(v)]
            cells[col] = html.unescape(v)
        if cells:
            def idx(c):
                k = 0
                for ch in c:
                    k = k * 26 + ord(ch) - 64
                return k - 1
            row = [''] * (idx(max(cells, key=idx)) + 1)
            for c, v in cells.items():
                row[idx(c)] = v
            out.append(row)
    return out


def _find(z, titolo):
    """Numero del foglio il cui titolo in A1 contiene `titolo`. MC non e' costante."""
    for n in range(1, 13):
        try:
            r = _sheet(z, n)
        except KeyError:
            continue
        if r and r[0] and titolo.lower() in r[0][0].lower():
            return n
    return None


def _data(serial):
    """Seriale Excel -> date. Epoca 1899-12-30."""
    try:
        return datetime.date(1899, 12, 30) + datetime.timedelta(days=float(serial))
    except (ValueError, TypeError, OverflowError):
        return None

# ------------------------------------------------------------------ estrazione

def leggi(path):
    z = zipfile.ZipFile(path)

    cfg = {}
    ns = _find(z, 'Settings')
    if ns:
        for r in _sheet(z, ns):
            if len(r) >= 2 and r[0]:
                cfg[r[0].strip()] = r[1].strip()

    nt = _find(z, 'List of Trades')
    if nt is None:
        raise SystemExit('%s: nessun foglio "List of Trades"' % os.path.basename(path))
    righe = _sheet(z, nt)
    hdr = next((i for i, r in enumerate(righe[:10])
                if any(c.strip() == 'Profit ($)' for c in r)), None)
    if hdr is None:
        raise SystemExit('%s: colonna "Profit ($)" non trovata' % os.path.basename(path))
    col = {c.strip(): j for j, c in enumerate(righe[hdr])}

    pl, cum, anni, cts = [], [], [], []
    for r in righe[hdr + 1:]:
        j = col['Profit ($)']
        if j >= len(r) or not r[j].strip():
            continue                      # riga di uscita: il P&L sta sull'ingresso
        try:
            v = float(r[j])
        except ValueError:
            continue
        pl.append(v)
        jc = col.get('Cum. Profit ($)')
        if jc is not None and jc < len(r) and r[jc].strip():
            try:
                cum.append(float(r[jc]))
            except ValueError:
                pass
        jd = col.get('Date')
        d = _data(r[jd]) if jd is not None and jd < len(r) else None
        anni.append(d.year if d else None)
        jk = col.get('Contracts')
        if jk is not None and jk < len(r) and r[jk].strip():
            cts.append(r[jk].strip())

    return cfg, pl, cum, anni, cts


def misura(pl, cum, anni):
    n = len(pl)
    if n < 3:
        raise SystemExit('solo %d trade: niente da misurare' % n)
    avg = sum(pl) / n
    sd = math.sqrt(sum((x - avg) ** 2 for x in pl) / (n - 1))
    se = sd / math.sqrt(n)                       # la barra d'errore
    vin = [x for x in pl if x > 0]
    per = [x for x in pl if x <= 0]
    wr = 100.0 * len(vin) / n
    aw = sum(vin) / len(vin) if vin else 0.0
    al = sum(per) / len(per) if per else 0.0
    rr = (aw / -al) if al else float('inf')
    pf = (sum(vin) / -sum(per)) if per and sum(per) else float('inf')

    dd = 0.0                                      # drawdown sui trade chiusi
    if cum:
        picco = cum[0]
        for c in cum:
            picco = max(picco, c)
            dd = max(dd, picco - c)

    per_anno = {}
    for a, v in zip(anni, pl):
        if a:
            per_anno[a] = per_anno.get(a, 0.0) + v
    net = sum(pl)
    quota = max((100.0 * v / net for v in per_anno.values()), default=0.0) if net > 0 else 0.0

    return dict(n=n, avg=avg, sd=sd, se=se, t=avg / se if se else 0.0, wr=wr,
                aw=aw, al=al, rr=rr, pf=pf, dd=dd, net=net,
                per_anno=per_anno, quota=quota)

# ------------------------------------------------------------------- stampa

OK, NO, EH = 'OK  ', 'NO  ', '?   '


def preliminari(cfg, cts):
    """Le trappole. Ritorna la lista (esito, testo)."""
    out = []

    # size variabile: il P&L per trade non e' piu' confrontabile fra IS e OOS
    distinti = sorted(set(cts))
    if distinti and distinti != ['1']:
        from collections import Counter
        det = '  '.join('%sct: %d' % (k, v) for k, v in sorted(Counter(cts).items()))
        out.append((NO, 'Size VARIABILE (%s) -> avg trade e t non confrontabili con una '
                        'serie a 1 contratto. Metti SizeMode 0.' % det))
    elif distinti:
        out.append((OK, 'Size: 1 contratto su tutti i %d trade' % len(cts)))

    comm = cfg.get('Commission', '')
    zero = (not comm) or re.match(r'^\s*(0\$?|no commission)', comm, re.I)
    out.append((NO if zero else OK, 'Commissione: %s' % (comm or 'ASSENTE')))

    out.append((EH, 'Slippage: %s  (se e\' 0, deve essere modellato nel codice)'
                % cfg.get('Slippage', '?')))

    bm = cfg.get('Bar Magnifier', '')
    out.append((OK if 'enabled' in bm.lower() else NO, 'Bar Magnifier: %s' % (bm or 'ASSENTE')))

    out.append((EH, 'Compression: %s   Symbol: %s   Point Value: %s'
                % (cfg.get('Compression', '?'), cfg.get('Symbol Name', '?'),
                   cfg.get('Point Value', '?'))))

    d1, d2 = _data(cfg.get('Start Date')), _data(cfg.get('End Date'))
    if d1 and d2:
        out.append((EH, 'Range testato: %s -> %s  (%d giorni)'
                    % (d1, d2, (d2 - d1).days)))
    return out


FASI = {
    2: ('Gate 2 - IS (fase 2): l\'edge esiste?', [
        ('t >= 2',         lambda m, o: m['t'] >= 2,   lambda m: 't = %.2f' % m['t']),
        ('WR >= 55%',      lambda m, o: m['wr'] >= 55, lambda m: 'WR = %.1f%%' % m['wr']),
        ('R:R 0,5-1',      lambda m, o: 0.5 <= m['rr'] <= 1.0,
                           lambda m: 'R:R = %.2f' % m['rr']),
    ]),
    3: ('Gate 3 - OOS (fase 3): l\'edge regge fuori campione?', [
        ('t >= 1,3',       lambda m, o: m['t'] >= 1.3, lambda m: 't = %.2f' % m['t']),
        ('WR >= 50%',      lambda m, o: m['wr'] >= 50, lambda m: 'WR = %.1f%%' % m['wr']),
        ('R:R 0,5-1',      lambda m, o: 0.5 <= m['rr'] <= 1.0,
                           lambda m: 'R:R = %.2f' % m['rr']),
        ('DD <= 1,5x IS',  lambda m, o: o.get('dd_is') is None or m['dd'] <= 1.5 * o['dd_is'],
                           lambda m: 'DD = $%s' % f"{m['dd']:,.0f}"),
    ]),
}


def rapporto(path, fase, dd_is):
    cfg, pl, cum, anni, cts = leggi(path)
    m = misura(pl, cum, anni)
    nome = os.path.basename(path)

    print('=' * 72)
    print(nome)
    print('=' * 72)
    print('\nCONTROLLI PRELIMINARI  (se sbaglia qui, i numeri sotto non valgono)')
    for esito, testo in preliminari(cfg, cts):
        print('  %s %s' % (esito, testo))

    print('\nMISURE')
    print('  n trade        %d' % m['n'])
    print('  avg trade      $%.2f   +/- %.2f   (barra d\'errore = sd/radice(n))' % (m['avg'], m['se']))
    print('  t              %.2f          <- quante barre separano l\'avg dallo zero' % m['t'])
    print('  WR             %.1f%%' % m['wr'])
    print('  R:R            %.2f         (vinc. media $%.0f / perd. media $%.0f)'
          % (m['rr'], m['aw'], -m['al']))
    print('  PF             %.3f        [criterio LIVE, informativo]' % m['pf'])
    print('  DD chiusi      $%s' % f"{m['dd']:,.0f}")
    print('  Net            $%s' % f"{m['net']:,.0f}")
    if m['per_anno']:
        # con net negativo le percentuali sul net sono prive di senso: si stampano i $
        if m['net'] > 0:
            det = '  '.join('%d: %.0f%%' % (a, 100.0 * v / m['net'])
                            for a, v in sorted(m['per_anno'].items()))
            print('  per anno       %s' % det)
            print('  anno max       %.0f%%        [criterio LIVE, informativo]' % m['quota'])
        else:
            det = '  '.join('%d: $%s' % (a, f'{v:,.0f}')
                            for a, v in sorted(m['per_anno'].items()))
            print('  per anno       %s   (net <= 0: percentuali omesse)' % det)

    if fase in FASI:
        titolo, criteri = FASI[fase]
        print('\n%s' % titolo)
        tutti = True
        for nomec, test, mostra in criteri:
            passa = test(m, {'dd_is': dd_is})
            tutti = tutti and passa
            print('  %s %-16s %s' % (OK if passa else NO, nomec, mostra(m)))
        print('\n  VERDETTO: %s' % ('PASSA' if tutti else 'NON PASSA -> cimitero'))
        if fase == 3 and dd_is is None:
            print('  (DD non confrontato: passa --dd-is <drawdown dell\'IS>)')
    print()
    return m


def tabella(paths):
    print('%-44s %6s %7s %7s %7s %7s %9s' %
          ('file', 'n', 'WR%', 'R:R', 't', 'PF', 'avg'))
    for p in paths:
        try:
            cfg, pl, cum, anni, _ = leggi(p)
            m = misura(pl, cum, anni)
        except SystemExit as e:
            print('%-44s %s' % (os.path.basename(p)[:44], e))
            continue
        print('%-44s %6d %7.1f %7.2f %7.2f %7.3f %9.2f'
              % (os.path.basename(p)[:44], m['n'], m['wr'], m['rr'], m['t'], m['pf'], m['avg']))


def main():
    arg = sys.argv[1:]
    if not arg:
        raise SystemExit(__doc__)
    fase = dd_is = None
    if '--fase' in arg:
        i = arg.index('--fase'); fase = int(arg[i + 1]); del arg[i:i + 2]
    if '--dd-is' in arg:
        i = arg.index('--dd-is'); dd_is = float(arg[i + 1]); del arg[i:i + 2]
    tab = '--tabella' in arg
    if tab:
        arg.remove('--tabella')
    if tab:
        tabella(arg)
    else:
        for p in arg:
            rapporto(p, fase, dd_is)


if __name__ == '__main__':
    main()
