#!/usr/bin/env python3
"""Lancia il Monte Carlo del corso (Live 5) fuori da Colab, senza toccarne il codice.

Cambia solo gli input della cella 2: pesi per strategia, OOS_START_DATE, costi.
I report di MultiCharts hanno gia' $15 andata e ritorno dentro, quindi i costi dello
script vanno a 0 (se no si contano due volte). Le regole sono quelle di Apex 50K,
scritte nello script.

Uso (dalla root del repo):
    docs/colab_corso/run_colab.sh --pesi '{"dpb": 0.2, "vb_": 0.2}' \
        strategies/DriftPullback/reports/DPB_S5_OOS_2025-2026.xlsx \
        strategies/VaultBreak/reports/VB_S5_OOS_2025-2026.xlsx
    opzioni: --oos 2023-01-01 (default: nessun filtro) · --comm 2.25 --slip 5.0
"""
import os, sys, json

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..',
                      'protocollo', '8. Livestreaming', 'PropFirm_MonteCarlo_Apex50K_1708_MultiStrats.py')

arg = sys.argv[1:]
def opt(nome, default):
    if nome in arg:
        i = arg.index(nome); v = arg[i + 1]; del arg[i:i + 2]; return v
    return default
pesi = json.loads(opt('--pesi', '{}'))
oos  = opt('--oos', None)
comm = float(opt('--comm', 0.0))
slip = float(opt('--slip', 0.0))
if not arg:
    raise SystemExit(__doc__)
os.environ['MC_FILES'] = ','.join(arg)

src = open(SCRIPT, encoding='utf8').read()
for old, new in [('STRATEGY_WEIGHTS = {}', 'STRATEGY_WEIGHTS = %r' % pesi),
                 ('OOS_START_DATE = "2023-01-01"', 'OOS_START_DATE = %r' % oos),
                 ('COMMISSION_PER_CONTRACT = 2.25', 'COMMISSION_PER_CONTRACT = %r' % comm),
                 ('SLIPPAGE_PER_CONTRACT = 5.0', 'SLIPPAGE_PER_CONTRACT = %r' % slip)]:
    assert src.count(old) == 1, 'cella 2 cambiata nello script del corso: %s' % old
    src = src.replace(old, new)
exec(compile(src, SCRIPT, 'exec'), {'__name__': '__main__'})
