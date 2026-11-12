"""Il motore contro un report MultiCharts: quanti trade coincidono, e di quanto differisce il net.

    python3 -m motore.calibra dpb strategies/DriftPullback/reports/DPB_S5_OOS_2025-2026.xlsx

Soglia per approvare il motore su una strategia (scritta prima del primo confronto, 10/11/2026):
almeno il 90% dei trade MC ritrovati con stessa entrata (ora e lato), e net entro il 10%.
Si confronta solo sui giorni coperti da tutti e due: il report e i dati di quantlake.
"""
import sys, datetime as dt
from collections import Counter

from . import dati, mc_report
from .motore import Motore
from .strategie import STRATEGIE

SOGLIA_TRADE, SOGLIA_NET = 0.90, 0.10


def gira(nome, dal, al, **inp):
    st = STRATEGIE[nome]
    caldo = dal - dt.timedelta(days=st['riscaldamento'])
    serie = [dati.barre(st['simbolo'], tf, caldo, al) for tf in st['tf']]
    s = st['classe'](*serie[1:], **inp)
    m = Motore(serie[0], s, punto=st['punto'], comm_lato=st['comm_lato'])
    return m.gira(dt.datetime.combine(dal, dt.time(0, 0))), st


def main():
    arg = sys.argv[1:]
    if len(arg) < 2:
        raise SystemExit(__doc__)
    nome, report = arg[0], arg[1]
    mc = mc_report.trade(report)
    fine_dati = dati.ultimo_giorno(STRATEGIE[nome]['simbolo'])
    dal = mc[0].t_in.date()
    al = min(mc[-1].t_out.date(), fine_dati - dt.timedelta(days=1))
    mc = [t for t in mc if t.t_out.date() <= al]
    py, st = gira(nome, dal, al)
    py = [t for t in py if t.t_out.date() <= al and t.nome_out != 'FINE']

    chiave = lambda t: (t.t_in, t.lato)
    ip = {chiave(t): t for t in py}
    im = {chiave(t): t for t in mc}
    comuni = [k for k in im if k in ip]
    stesso_prezzo_in = sum(abs(im[k].p_in - ip[k].p_in) < 1e-6 for k in comuni)
    stessa_uscita = sum(im[k].t_out == ip[k].t_out and abs(im[k].p_out - ip[k].p_out) < 1e-6 for k in comuni)
    usd = lambda ts: sum(t.dollari(st['punto'], st['comm_lato']) for t in ts)
    net_mc, net_py = usd(mc), usd(py)

    print('%s · %s → %s · report %s' % (nome, dal, al, report))
    print('trade MC %d · motore %d · in comune %d (%.1f%% di MC, %.1f%% del motore)' % (
        len(mc), len(py), len(comuni), 100 * len(comuni) / len(mc), 100 * len(comuni) / max(1, len(py))))
    print('fra quelli in comune: stesso prezzo d\'entrata %d · stessa uscita (ora e prezzo) %d' % (
        stesso_prezzo_in, stessa_uscita))
    print('net MC $%.0f · motore $%.0f · scarto %.1f%%' % (net_mc, net_py, 100 * (net_py - net_mc) / abs(net_mc)))
    print('uscite MC %s' % dict(Counter(t.nome_out for t in mc)))
    print('uscite motore %s' % dict(Counter(t.nome_out for t in py)))
    ok = len(comuni) / len(mc) >= SOGLIA_TRADE and abs(net_py - net_mc) <= SOGLIA_NET * abs(net_mc)
    print('ESITO: %s' % ('motore APPROVATO su questa strategia' if ok else 'NON approvato'))

    if '--diff' in arg:
        solo_mc = sorted((k for k in im if k not in ip))[:15]
        solo_py = sorted((k for k in ip if k not in im))[:15]
        print('\nsolo MC:'); [print('  ', im[k]) for k in solo_mc]
        print('solo motore:'); [print('  ', ip[k]) for k in solo_py]
        diverse = [k for k in comuni if im[k].t_out != ip[k].t_out or abs(im[k].p_out - ip[k].p_out) > 1e-6][:15]
        print('uscite diverse:')
        for k in diverse:
            print('   MC', im[k]); print('   py', ip[k])


if __name__ == '__main__':
    main()
