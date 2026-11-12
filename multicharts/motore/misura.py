"""La misura preliminare: l'eccesso sul caso di una regola, dai trade del motore.

    PYTHONPATH=multicharts python3 -m motore.misura dpb
    PYTHONPATH=multicharts python3 -m motore.misura dpb DriftMode=1 --json

Cosa misura. Il caso e' il win rate di pareggio al R:R realizzato: null = 1 / (1 + R:R), con
R:R = vincita media / perdita media, al netto dei costi. L'eccesso e' WR - null. E' la
definizione delle SPEC (DriftPullback: WR 63,5%, R:R 0,640, null 61,0%, eccesso +2,6 pp), e non
dipende dal rapporto target/stop: cambiarlo sposta WR e null insieme.

Perche' dai trade del motore e non da un indicatore. I tre bug del 17/10/2026
(docs/bug_misura_primo_tocco.md) stavano tutti negli indicatori di misura: tie-break dentro la
barra, non risolti esclusi, caso calcolato sulla geometria di progetto. Qui non esistono:
  - il motore risolve stop e target sul percorso a 1 minuto, come il Bar Magnifier;
  - ogni trade conta, anche quelli chiusi a tempo: niente "non risolti";
  - il R:R e' quello realizzato, costi compresi.

Regole.
  - Solo in-sample (2020-2024). Il comando non ha un'opzione per altri periodi: l'OOS si guarda
    una volta sola, in pipeline, non qui.
  - Ogni misura e' uno sguardo ai dati e conta nel totale delle idee.
  - Una misura non autorizza una strategia: al massimo la propone.
"""
import argparse, datetime as dt, json, math, statistics as st

MICRO = 10          # un contratto pieno = 10 micro, per punto e per commissione


def misura(dollari, giorni_di_mercato):
    """dollari: il P&L netto di ogni trade, per contratto. giorni_di_mercato: i giorni della
    finestra in cui il mercato era aperto (non solo quelli con un trade)."""
    n = len(dollari)
    vinti = [x for x in dollari if x > 0]
    persi = [-x for x in dollari if x <= 0]
    if n < 2 or not vinti or not persi:
        raise ValueError('servono almeno due trade, uno vinto e uno perso (n=%d)' % n)
    w, l = st.mean(vinti), st.mean(persi)
    wr, null = len(vinti) / n, l / (w + l)
    es = math.sqrt(null * (1 - null) / n)                 # errore standard del WR sotto il caso
    media, dev = st.mean(dollari), st.stdev(dollari)
    return {
        'trade': n,
        'giorni': giorni_di_mercato,
        'trade_al_giorno': n / giorni_di_mercato,
        'wr': wr,
        'rr': w / l,
        'null': null,
        'eccesso_pp': 100 * (wr - null),
        'errore_standard_pp': 100 * es,
        'errori_standard': (wr - null) / es,
        'media_per_trade': media,
        't': media / dev * math.sqrt(n) if dev > 0 else float('nan'),
        'dollari_al_giorno_per_micro': media * n / giorni_di_mercato / MICRO,
    }


def misura_strategia(nome, inp=None):
    """La strategia `nome` del registro del motore, sull'in-sample."""
    from . import dati, esegui
    dal, al = esegui.IS
    trade, parametri, reg = esegui.gira(nome, dal, al, inp or {})
    giorni = {b.t.date() for b in dati.barre(reg['simbolo'], reg['tf'][0], dal, al) if b.t.weekday() < 5}
    m = misura([t.dollari(reg['punto'], reg['comm_lato']) for t in trade], len(giorni))
    m.update(strategia=nome, simbolo=reg['simbolo'], periodo=[dal.isoformat(), al.isoformat()],
             commissione_per_lato=reg['comm_lato'], parametri=parametri)
    return m


def stampa(m):
    print('%s su %s, %s -> %s, $%.2f per lato' % (m['strategia'], m['simbolo'], *m['periodo'], m['commissione_per_lato']))
    print('  trade                 %d  (%.2f al giorno su %d giorni)' % (m['trade'], m['trade_al_giorno'], m['giorni']))
    print('  WR                    %.2f%%' % (100 * m['wr']))
    print('  R:R realizzato        %.3f' % m['rr'])
    print('  il caso (null)        %.2f%%' % (100 * m['null']))
    print('  ECCESSO               %+.2f pp' % m['eccesso_pp'])
    print('  errore standard       %.2f pp' % m['errore_standard_pp'])
    print('  errori standard       %.2f   <- serve >= 3 per crederci' % m['errori_standard'])
    print('  t della media         %.2f' % m['t'])
    print('  $ al giorno per micro %.2f   <- sotto $10 non si parte' % m['dollari_al_giorno_per_micro'])


def main():
    from . import esegui
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('nome', help='la strategia nel registro del motore (motore/strategie/__init__.py)')
    ap.add_argument('input', nargs='*', help='input della strategia, chiave=valore')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    inp = {k: esegui.valore(v) for k, v in (x.split('=', 1) for x in a.input)}
    m = misura_strategia(a.nome, inp)
    m['misurata_il'] = dt.date.today().isoformat()
    print(json.dumps(m, indent=2, default=str)) if a.json else stampa(m)


if __name__ == '__main__':
    main()
