"""List of Trades di un report MultiCharts (.xlsx) come lista di trade del motore."""
import datetime as dt
import openpyxl

from .motore import Trade


def _quando(d, t):
    if isinstance(d, dt.datetime) and isinstance(t, dt.datetime):
        return dt.datetime.combine(d.date(), t.time())
    return d if isinstance(d, dt.datetime) else None


def trade(path):
    wb = openpyxl.load_workbook(path, read_only=True)
    righe = list(wb['List of Trades'].iter_rows(values_only=True))
    hdr = next(i for i, r in enumerate(righe[:10]) if r and 'Signal' in r)
    col = {c: j for j, c in enumerate(righe[hdr]) if c}
    jt, js, jd, jo, jp, jc = (col[k] for k in ('Type', 'Signal', 'Date', 'Time', 'Price', 'Contracts'))
    out, aperto = [], None
    for r in righe[hdr + 1:]:
        if not r or len(r) <= jp or r[jt] is None:
            continue
        tipo = str(r[jt])
        t = _quando(r[jd], r[jo])
        if tipo.startswith('Entry'):
            aperto = Trade(1 if 'Long' in tipo else -1, int(r[jc] or 1), t, float(r[jp]), r[js])
        elif tipo.startswith('Exit') and aperto:
            aperto.t_out, aperto.p_out, aperto.nome_out = t, float(r[jp]), r[js]
            out.append(aperto)
            aperto = None
    return out
