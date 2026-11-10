"""Barre da quantlake (agentic-quant-lab) in sola lettura.

Il file e' l'export di MultiCharts a 1 minuto (`<SIMBOLO>_1min.csv`): ora di Chicago, `time` = ora di
CHIUSURA della barra (HHMM), sessione 17:00-16:00 senza pause, continuous back-adjusted di
TradeStation. Le barre piu' lunghe si costruiscono come le costruisce MultiCharts: etichetta = ora
di chiusura, confini allineati all'orologio (1701-1705 -> barra delle 17:05). Ogni barra tiene le
sue barre da 1 minuto per il Bar Magnifier.

Percorso dei dati: variabile QUANTLAKE_DATA, default il repo agentic-quant-lab accanto a questo.
Cache delle barre lette in motore/.cache (ignorata da git): si rifa' quando il CSV cambia.
"""
import csv, os, pickle, datetime as dt

DATI = os.environ.get('QUANTLAKE_DATA',
                      os.path.expanduser('~/Documents/Repo/agentic-quant-lab/quantlake/data'))
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.cache')


class Barra:
    __slots__ = ('t', 'o', 'h', 'l', 'c', 'v', 'sub')

    def __init__(self, t, o, h, l, c, v, sub):
        self.t, self.o, self.h, self.l, self.c, self.v, self.sub = t, o, h, l, c, v, sub

    @property
    def data(self):
        return self.t.date()

    @property
    def ora(self):                          # HHMM come Time di EasyLanguage
        return self.t.hour * 100 + self.t.minute

    def __repr__(self):
        return 'Barra(%s o=%.2f h=%.2f l=%.2f c=%.2f v=%d)' % (self.t, self.o, self.h, self.l, self.c, self.v)


def file_1min(simbolo):
    return os.path.join(DATI, 'multicharts', '%s_1min.csv' % simbolo)


def minuti(simbolo, dal, al):
    """Barre da 1 minuto fra dal e al (date, inclusi): (datetime chiusura, o, h, l, c, volume)."""
    p = file_1min(simbolo)
    if not os.path.exists(p):
        raise SystemExit('mancano i dati: %s (QUANTLAKE_DATA=%s)' % (p, DATI))
    d0, d1 = int(dal.strftime('%Y%m%d')), int(al.strftime('%Y%m%d'))
    out = []
    with open(p, newline='') as f:
        r = csv.reader(f)
        next(r)
        for riga in r:
            d = int(riga[0])
            if d < d0 or d > d1:
                continue
            hm = int(riga[1])
            t = dt.datetime(d // 10000, d // 100 % 100, d % 100, hm // 100, hm % 100)
            out.append((t, float(riga[2]), float(riga[3]), float(riga[4]), float(riga[5]), int(riga[6])))
    return out


def aggrega(mins, tf):
    """Barre da tf minuti con etichetta all'ora di chiusura e le barre da 1 minuto dentro."""
    out, cur, chiave = [], None, None
    for t, o, h, l, c, v in mins:
        m = t.hour * 60 + t.minute
        r = m % tf
        k = t + dt.timedelta(minutes=tf - r) if r else t
        if k != chiave:
            if cur:
                out.append(cur)
            cur = Barra(k, o, h, l, c, v, [(o, h, l, c)])
            chiave = k
        else:
            cur.h = max(cur.h, h)
            cur.l = min(cur.l, l)
            cur.c = c
            cur.v += v
            cur.sub.append((o, h, l, c))
    if cur:
        out.append(cur)
    return out


def barre(simbolo, tf, dal, al):
    """Barre da tf minuti, con cache. dal/al: date."""
    p = file_1min(simbolo)
    st = os.stat(p)
    nome = '%s_%d_%s_%s_%d_%d.pkl' % (simbolo, tf, dal, al, int(st.st_mtime), st.st_size)
    cp = os.path.join(CACHE, nome)
    if os.path.exists(cp):
        with open(cp, 'rb') as f:
            return pickle.load(f)
    b = aggrega(minuti(simbolo, dal, al), tf)
    os.makedirs(CACHE, exist_ok=True)
    with open(cp, 'wb') as f:
        pickle.dump(b, f, protocol=pickle.HIGHEST_PROTOCOL)
    return b


def ultimo_giorno(simbolo):
    with open(file_1min(simbolo), 'rb') as f:
        f.seek(-200, 2)
        riga = f.read().decode().strip().splitlines()[-1]
    d = int(riga.split(',')[0])
    return dt.date(d // 10000, d // 100 % 100, d % 100)
