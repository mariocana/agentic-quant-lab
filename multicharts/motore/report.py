"""Un report .xlsx con la forma di quello di MultiCharts, da una lista di trade del motore.

Stessi fogli e colonne che leggono check_report.py, lab.py, gate_marginale.py e book_sim.py: la
pipeline non distingue un report del motore da uno di MC, se non per la riga `Fonte` di Settings.
P&L come MC: contratti NQ full-size, valore del punto e commissione per lato nel P&L di ogni trade.
"""
import datetime as dt, subprocess, os
import openpyxl

FONTE = 'motore Python (motore/)'


def _sha():
    try:
        return subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], capture_output=True, text=True,
                              cwd=os.path.dirname(os.path.abspath(__file__))).stdout.strip()
    except OSError:
        return '?'


def scrivi(path, trades, st, inp, nome_strategia, compressione, dal, al):
    punto, comm = st['punto'], st['comm_lato']
    wb = openpyxl.Workbook()
    wb.active.title = 'Strategy Analysis'
    wb.active.append(['Strategy Performance Summary'])
    wb.active.append([])
    net = sum(t.dollari(punto, comm) for t in trades)
    wb.active.append(['', 'All Trades'])
    wb.active.append(['Net Profit', net])
    wb.active.append(['Total # of Trades', len(trades)])

    lt = wb.create_sheet('List of Trades')
    lt.append(['List of Trades'])
    lt.append([])
    lt.append(['Trade #', 'Order #', 'Type', 'Signal', 'Date', 'Time', 'Price', 'Contracts', 'Profit ($)',
               'Profit (%)', 'Cum. Profit ($)', 'Cum. Profit (%)', 'Run-up ($)', 'Run-up (%)',
               'Drawdown ($)', 'Drawdown (%)'])
    cum = 0.0
    for n, t in enumerate(trades, 1):
        pl = t.dollari(punto, comm)
        cum += pl
        lato = 'Long' if t.lato > 0 else 'Short'
        lt.append([n, 2 * n - 1, 'Entry' + lato, t.nome_in, t.t_in, t.t_in, t.p_in, t.qta, pl, None, cum,
                   None, t.su * punto * t.qta - comm * t.qta, None, t.giu * punto * t.qta - comm * t.qta, None])
        lt.append([None, 2 * n, 'Exit' + lato, t.nome_out, t.t_out, t.t_out, t.p_out, t.qta])

    se = wb.create_sheet('Settings')
    se.append(['Settings'])
    se.append([])
    se.append([nome_strategia])
    for k, v in inp.items():
        se.append([k, str(v)])
    cts = sorted({t.qta for t in trades})
    se.append(['Fonte', '%s, commit %s' % (FONTE, _sha())])
    se.append(['Finestra', '%s -> %s' % (dal, al)])
    se.append(['Symbol Name', '@' + st['simbolo']])
    se.append(['Commission', '%g$ per Contract [Fixed %g$ per Contract]' % (comm, comm)])
    se.append(['Backtesting Assumptions', 'Fill Limit price or better (Classic mode)'])
    se.append(['Slippage', '0$ per Trade'])
    se.append(['Compression', compressione])
    se.append(['Bar Magnifier', 'Enabled1 Minute'])
    se.append(['Point Value', '$%g' % punto])
    if trades:
        se.append(['Start Date', trades[0].t_in])
        # come MC: Start Date = primo trade, End Date = ultima barra del grafico (Globex: 16:00)
        se.append(['End Date', dt.datetime.combine(al, dt.time(16, 0))])
    se.append(['Backtesting Mode', 'Classic'])
    se.append(['Contratti', ', '.join(map(str, cts))])
    se.append(['Export Time', dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)])
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    wb.save(path)
    return net
