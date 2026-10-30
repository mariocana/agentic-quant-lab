#!/usr/bin/env python3
"""Legge un Optimization Report di MultiCharts (.MCReport).

Il file e' un INI: quasi tutto e' stile del grafico, ma la sezione
[MCReport\\OptimizationReport\\OptReport] contiene la griglia vera, con i
valori degli input in `Inp` e la matrice dei risultati in `Vals`, entrambi
array di float64 little-endian compressi gzip e codificati base64.

Uso:  python3 mc/docs/read_mcreport.py <file.MCReport> [altri...]
"""
import sys, re, base64, gzip, struct

# colonne mostrate in tabella, nell'ordine; le altre restano disponibili in --all
SHORT = ['Total Trades', '% Profitable', 'Avg Trade', 'Profit Factor',
         'Net Profit', 'Max Intraday Drawdown', 'Win/Loss Ratio',
         'Max Consecutive Losers']


def parse(path):
    t = open(path, encoding='utf8', errors='replace').read()
    m = re.search(r'\[MCReport\\OptimizationReport\\OptReport\]\n(.*?)(?=\n\[|\Z)', t, re.S)
    if not m:
        raise SystemExit("%s: nessuna sezione OptReport (e' un report di ottimizzazione?)" % path)
    b = m.group(1)

    def key(k):
        mm = re.search(r"^\s*%s\s*=\s*'(.*?)'\s*$" % re.escape(k), b, re.S | re.M)
        return re.sub(r'\s+', '', mm.group(1)) if mm else None

    caps = {int(x.group(1)): x.group(2)
            for x in re.finditer(r"Caption_(\d+)\s*=\s*'([^']*)'", b)}
    cols, rows = int(key('Cols')), int(key('Rows'))
    blob = lambda k: gzip.decompress(base64.b64decode(key(k)))
    inp = struct.unpack('<%dd' % rows, blob('Inp'))
    vals = struct.unpack('<%dd' % (rows * cols), blob('Vals'))
    names = [caps[i] for i in range(cols)]

    # nome dell'input ottimizzato, se presente
    im = re.search(r"InputName\s*=\s*'([^']*)'", t)
    label = im.group(1).split(' (')[0] if im else 'input'
    return label, inp, names, [vals[r * cols:(r + 1) * cols] for r in range(rows)]


def show(path, allcols=False):
    label, inp, names, rows = parse(path)
    print("\n=== %s" % path.split('/')[-1])
    cols = names if allcols else [c for c in SHORT if c in names]
    idx = [names.index(c) for c in cols]
    hdr = "%-10s" % label[:10] + "".join("%14s" % c[:14] for c in cols)
    print(hdr)
    print("-" * len(hdr))
    for v, row in zip(inp, rows):
        print("%-10g" % v + "".join("%14.2f" % row[i] for i in idx))


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    if not args:
        raise SystemExit(__doc__)
    for p in args:
        show(p, allcols='--all' in sys.argv)
