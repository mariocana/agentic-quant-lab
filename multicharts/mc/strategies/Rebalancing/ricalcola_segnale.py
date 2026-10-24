"""Ricalcola il segnale di Rebalancing dai prezzi nel log e lo confronta con quello di MultiCharts.

Uso:  python3 mc/strategies/Rebalancing/ricalcola_segnale.py reports/RB_S1_log.txt

Indipendente dal codice PowerLanguage: stesse regole del paper (Appendice B, sezione 4),
riscritte da zero. Se thr, cal, calMod o dir differiscono, uno dei due ha un errore.
"""
import calendar
import datetime as dt
import sys


def giorni_lavorativi_dopo(d):
    ultimo = calendar.monthrange(d.year, d.month)[1]
    return sum(1 for g in range(d.day + 1, ultimo + 1)
               if dt.date(d.year, d.month, g).weekday() < 5)


def segno(x):
    return (x > 0) - (x < 0)


def leggi(path):
    righe = []
    for r in open(path, encoding='latin-1'):
        t = r.split()
        if not t or t[0] != 'RB':
            continue
        v = dict(zip(t[2::2], t[3::2]))
        n = int(float(t[1]))
        righe.append((dt.date(1900 + n // 10000, n // 100 % 100, n % 100),
                      {k: float(x) for k, x in v.items()}))
    return righe


def main(path):
    righe = leggi(path)
    wT = [0.6] * 26
    wC = 0.6
    thr = cal = calT4 = 0.0
    prev = None
    diff = {'thr': 0, 'cal': 0, 'calMod': 0, 'dir': 0}
    for d, mc in righe:
        primo = prev is not None and prev[0].month != d.month
        if prev is not None:
            rs = mc['ES'] / prev[1]['ES'] - 1
            rb = mc['TY'] / prev[1]['TY'] - 1
            for k in range(26):
                base = 0.6 if abs(wT[k] - 0.6) >= k * 0.001 else wT[k]
                wT[k] = base * (1 + rs) / (base * (1 + rs) + (1 - base) * (1 + rb))
            thr = sum(w - 0.6 for w in wT) / 26
            base = 0.6 if primo else wC
            wC = base * (1 + rs) / (base * (1 + rs) + (1 - base) * (1 + rb))
            cal = wC - 0.6
        rest = giorni_lavorativi_dopo(d)
        if rest == 4:
            calT4 = cal
        calMod = -segno(cal) if rest <= 4 else (segno(calT4) if primo else 0)
        peso = 0.5 * (-thr / 0.015) + 0.5 * calMod
        mio = {'thr': thr, 'cal': cal, 'calMod': calMod, 'dir': segno(peso)}
        for k, tol in (('thr', 2e-6), ('cal', 2e-6), ('calMod', 0), ('dir', 0)):
            if abs(mio[k] - mc[k]) > tol:
                diff[k] += 1
                if diff[k] <= 3:
                    print('  %s  %-6s  python %.6f  MC %.6f' % (d, k, mio[k], mc[k]))
        prev = (d, mc)

    print('%d giorni, %s -> %s' % (len(righe), righe[0][0], righe[-1][0]))
    for k, n in diff.items():
        print('  %-6s  %s' % (k, 'identico' if n == 0 else '%d differenze' % n))
    lunghi = sum(1 for _, mc in righe if mc['dir'] > 0)
    print('  long %d · short %d · zero %d' % (lunghi, sum(1 for _, mc in righe if mc['dir'] < 0),
                                            sum(1 for _, mc in righe if mc['dir'] == 0)))


if __name__ == '__main__':
    main(sys.argv[1])
