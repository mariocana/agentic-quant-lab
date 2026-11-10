# motore: backtest in Python con la semantica di MultiCharts

Serve a **scartare presto** le idee deboli: S1, IS e OOS in minuti invece che in giorni di
MultiCharts. Il report definitivo resta quello di MultiCharts, che replica la SPEC senza modifiche.

## Regole (10/11/2026)

- **Si usa su una strategia solo dopo la calibrazione**: almeno il 90% dei trade di un report MC
  ritrovati (stessa entrata, ora e lato) e net entro il 10%. Soglia scritta prima del primo confronto.
- **L'OOS in Python e' l'unico sguardo all'OOS.** Se va male, l'idea va in cimitero e non si rifa' su
  MC. Se va bene, MC lo replica: non e' un secondo sguardo.
- **Ogni idea provata qui conta nel k**, come su MC.

## Dati

In sola lettura da quantlake (`agentic-quant-lab`), variabile `QUANTLAKE_DATA`, default
`~/Documents/Repo/agentic-quant-lab/quantlake/data`. File `multicharts/<SIMBOLO>_1min.csv`: export di
MC da TradeStation, ora di Chicago, sessione 17-16 senza pause. Le barre da 5/15 minuti si
costruiscono da quelle a 1 minuto, che restano dentro ogni barra per il Bar Magnifier. Nessun dato
nel repo: la cache sta in `motore/.cache/` (ignorata).

**Gold manca**: serve l'export `GC_1min.csv` con `ExportBars`, stessa procedura di NQ.

## Semantica (MC Classic, IOG spento, Bar Magnifier 1 minuto)

- la strategia gira alla chiusura della barra; gli ordini valgono solo per la barra dopo;
- a mercato: all'apertura della barra dopo; stop e limite cercati sulle barre da 1 minuto, con il
  percorso open → estremo piu' vicino → l'altro → close;
- nessuno stop nella barra d'ingresso (la strategia li mette alla sua chiusura), come in MC;
- `SetExitOnClose`: flat alla chiusura dell'ultima barra prima della pausa di sessione.

## Calibrazione

| strategia | report MC | trade MC | ritrovati | stesse uscite | net MC → motore | esito |
|---|---|---|---|---|---|---|
| DPB | `DPB_S5_OOS_2025-2026` (fino al 07/10/2026) | 1.421 | **100%** | 1.418 | $84.220 → $85.010 (+0,9%) | ✅ |
| DPB | `DPB_S2_IS_mode0` (2020-2024) | 3.499 | **100%** | 3.499 | $194.110 → $195.440 (+0,7%) | ✅ |
| OBO | `OBO_S2_IS_2020-2024` | 455 | **100%** | **455** | $182.680 → $182.680 (0,0%) | ✅ |
| OBO | `OBO_S5_OOS_2025-2026` (fino al 07/10/2026) | 160 | **100%** | 156 | $63.185 → $63.220 (+0,1%) | ✅ |

OBO verifica cose che DPB non usa: ADX di Wilder, ATR giornaliero, EMA, ordini d'uscita messi
insieme all'ingresso (attivi gia' nella barra del fill, `OBO-L-SL0`) e l'arrotondamento al tick di
stop e target, nel verso prudente. Gli scarti OOS di OBO: due entrate dell'11/09/2026, dati riscritti.

Gli scarti di DPB: 3 trade OOS con l'entrata a 0,25-0,50 punti (dati di TradeStation riscritti dopo il
report) e un giorno, il 18/07/2024, che nel report MC non c'e' (4 trade in piu' nel motore).

```bash
python3 -m motore.calibra dpb strategies/DriftPullback/reports/DPB_S2_IS_mode0.xlsx --diff
python3 -m motore.calibra obo strategies/OvernightBiasORB/reports/OBO_S2_IS_2020-2024.xlsx --diff
```

## Nella pipeline (`lab.py`)

```bash
python3 -m motore.esegui obo s1  strategies/OvernightBiasORB/SPEC.md     # + report _x10
python3 -m motore.esegui obo is  strategies/OvernightBiasORB/SPEC.md
python3 -m motore.esegui obo oos strategies/OvernightBiasORB/SPEC.md
python3 docs/lab.py giudica <SPEC> <fase> <report _motore>               # come per MC
python3 docs/lab.py replica <SPEC> <fase> <report MC>                    # MC replica il motore
```

- Il report del motore ha la forma di quello di MC: `check_report`, i controlli dello Stage 1,
  `gate_marginale` e `book_sim` lo leggono uguale (provato su OBO: stesse misure del report MC).
- La riga `Fonte` di Settings finisce nel verdetto (`fonte: motore`).
- Il suffisso `_motore` e' un rerun per il k, non una variante.
- `replica`: soglia della calibrazione (90% dei trade, net entro il 10%). Scrive
  `verdicts/<SPEC>_<fase>_replica.md` e una riga nel log della strategia.
- Finestre: s1 = ultimi 100 giorni di dati; is = 2020-2024; oos = 2025 → ultimo giorno completo.

## Struttura

| file | cosa |
|---|---|
| `dati.py` | CSV da 1 minuto → barre con le barre da 1 minuto dentro, cache |
| `motore.py` | ordini, fill, trade (P&L in punti, escursioni), contesto con i nomi di EasyLanguage |
| `strategie/` | una strategia per file, registrata in `strategie/__init__.py` |
| `mc_report.py` | List of Trades di un report MC |
| `calibra.py` | motore contro report MC |
| `esegui.py` | una fase della pipeline: report nella cartella della strategia |
| `report.py` | il report .xlsx con la forma di quello di MC |
