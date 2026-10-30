#!/usr/bin/env python3
"""Converte un Performance Report xlsx di MultiCharts nel CSV che vuole il Colab del corso.

Il notebook `PropFirm_MonteCarlo_Apex50K_funded_IP.ipynb` pretende colonne in minuscolo con
nomi suoi: `trade_id`, `contracts`, `profit_usd`, `direction`, piu una colonna data fra
`datetime`, `excel_date` o `date`. Il foglio "List of Trades" di MultiCharts ha gli stessi
dati con nomi diversi, e per di piu sta nel terzo foglio: `pd.read_excel` da solo leggerebbe
il primo, che e il sommario.

Emette **una riga per trade** (solo le righe di ingresso, che portano il P&L), come il file
di esempio del corso.

Uso:
    python3 mc/docs/to_colab_csv.py report.xlsx              # -> report_colab.csv
    python3 mc/docs/to_colab_csv.py report.xlsx out.csv
    python3 mc/docs/to_colab_csv.py report.xlsx --lordo      # toglie i costi gia applicati
"""
import sys, os, csv, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_report import _sheet, _find

# MultiCharts -> Colab
MAPPA = [
    ('Trade #',          'trade_id'),
    ('Order #',          'order_id'),
    ('Type',             'type'),
    ('Signal',           'signal'),
    ('Date',             'excel_date'),
    ('Time',             'excel_time'),
    ('Price',            'price'),
    ('Contracts',        'contracts'),
    ('Profit ($)',       'profit_usd'),
    ('Profit (%)',       'profit_pct'),
    ('Cum. Profit ($)',  'cum_profit_usd'),
    ('Cum. Profit (%)',  'cum_profit_pct'),
    ('Run-up ($)',       'runup_usd'),
    ('Run-up (%)',       'runup_pct'),
    ('Drawdown ($)',     'drawdown_usd'),
    ('Drawdown (%)',     'drawdown_pct'),
]


def converti(path, out, lordo_per_lato=None):
    z = zipfile.ZipFile(path)
    n = _find(z, 'List of Trades')
    if n is None:
        raise SystemExit('%s: nessun foglio "List of Trades"' % os.path.basename(path))
    righe = _sheet(z, n)
    hdr = next((i for i, r in enumerate(righe[:10])
                if any(c.strip() == 'Profit ($)' for c in r)), None)
    if hdr is None:
        raise SystemExit('colonna "Profit ($)" non trovata')
    col = {c.strip(): j for j, c in enumerate(righe[hdr])}

    manca = [a for a, _ in MAPPA if a not in col]
    if manca:
        print('nota: colonne assenti nel report, lasciate vuote: %s' % ', '.join(manca))

    fuori = [b for _, b in MAPPA] + ['direction']
    n_righe = 0
    with open(out, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(fuori)
        for r in righe[hdr + 1:]:
            jp = col['Profit ($)']
            if jp >= len(r) or not r[jp].strip():
                continue                      # riga di uscita: una riga per trade
            riga = []
            for a, _ in MAPPA:
                j = col.get(a)
                v = r[j] if (j is not None and j < len(r)) else ''
                if a == 'Profit ($)' and lordo_per_lato:
                    try:
                        jc = col.get('Contracts')
                        cts = float(r[jc]) if jc is not None and jc < len(r) and r[jc].strip() else 1.0
                        v = '%.2f' % (float(v) + 2 * lordo_per_lato * cts)
                    except ValueError:
                        pass
                riga.append(v)
            tipo = (r[col['Type']] if 'Type' in col and col['Type'] < len(r) else '').upper()
            riga.append('SHORT' if 'SHORT' in tipo else 'LONG')
            w.writerow(riga)
            n_righe += 1
    return n_righe


def main():
    arg = sys.argv[1:]
    if not arg:
        raise SystemExit(__doc__)
    lordo = None
    if '--lordo' in arg:
        i = arg.index('--lordo')
        del arg[i]
        lordo = 7.50                       # $/contratto/lato gia dentro il P&L su NQ
        if arg and arg[-1].replace('.', '', 1).isdigit():
            lordo = float(arg.pop())
    src = arg[0]
    out = arg[1] if len(arg) > 1 else os.path.splitext(src)[0] + '_colab.csv'
    n = converti(src, out, lordo)
    print('%d trade -> %s' % (n, out))
    if lordo:
        print('P&L riportato al LORDO togliendo $%.2f/contratto/lato: nel Colab metti '
              'COMMISSION_PER_CONTRACT e SLIPPAGE_PER_CONTRACT ai tuoi valori veri.' % lordo)
    else:
        print('P&L NETTO (costi gia dentro): nel Colab metti COMMISSION_PER_CONTRACT = 0 e '
              'SLIPPAGE_PER_CONTRACT = 0, altrimenti li conta due volte.')


if __name__ == '__main__':
    main()
