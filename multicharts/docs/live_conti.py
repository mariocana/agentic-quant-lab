#!/usr/bin/env python3
"""Pass rate e costi reali dei conti in live/conti.csv, contro quelli del simulatore.

Uso:  python3 docs/live_conti.py
"""
import csv, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prop_sim as ps

CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'live', 'conti.csv')
PASS = ('pass', 'funded', 'funded chiuso')


def num(x):
    return float(x) if x.strip() else 0.0


def main():
    righe = list(csv.DictReader(open(CSV, encoding='utf8')))
    print('%-32s %-5s %-5s %-20s %6s %10s %8s' % ('conto', 'book', 'micro', 'esito', 'trade', 'netto $', 'costo $'))
    for r in righe:
        print('%-32s %-5s %-5s %-20s %6s %10.2f %8.2f' % (
            r['conto'][:32], r['book'][:5], r['micro'][:5], r['esito'][:20], r['trade'],
            num(r['pnl_netto_usd']), num(r['costo_usd'])))
    chiusi = [r for r in righe if r['esito'] != 'aperto']
    passati = [r for r in chiusi if r['esito'] in PASS]
    spesa = sum(num(r['costo_usd']) + num(r['attivazione_usd']) for r in righe)
    payout = sum(num(r['payout_usd']) for r in righe)
    print('\nconti chiusi %d · passati %d · spesa $%.2f · payout $%.2f · saldo $%.2f' % (
        len(chiusi), len(passati), spesa, payout, payout - spesa))
    if chiusi:
        lo, hi = ps.wilson(len(passati), len(chiusi))
        print('pass rate reale %.0f%%, intervallo 95%% %.0f%%-%.0f%%' % (
            100.0 * len(passati) / len(chiusi), 100 * lo, 100 * hi))
    if passati:
        print('costo reale per funded $%.2f' % (spesa / len(passati)))
    else:
        print('costo reale per funded: n/d, nessun pass')
    print('(i conti con book o size diversi non sono lo stesso esperimento: pochi conti non dicono nulla)')


if __name__ == '__main__':
    main()
