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

Gli scarti: 3 trade OOS con l'entrata a 0,25-0,50 punti (dati di TradeStation riscritti dopo il
report) e un giorno, il 18/07/2024, che nel report MC non c'e' (4 trade in piu' nel motore).

```bash
python3 -m motore.calibra dpb strategies/DriftPullback/reports/DPB_S2_IS_mode0.xlsx --diff
```

## Struttura

| file | cosa |
|---|---|
| `dati.py` | CSV da 1 minuto → barre con le barre da 1 minuto dentro, cache |
| `motore.py` | ordini, fill, trade (P&L in punti, escursioni), contesto con i nomi di EasyLanguage |
| `strategie/` | una strategia per file, registrata in `strategie/__init__.py` |
| `mc_report.py` | List of Trades di un report MC |
| `calibra.py` | motore contro report MC |
