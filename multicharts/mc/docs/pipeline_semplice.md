# La pipeline in una pagina

**Aggiornato:** 15/10/2026 · **In corso:** DriftPullback, fase 3

Nove stage, ma sono **cinque domande**. Una strategia alla volta.

| | fase | la domanda | il criterio | se fallisce |
|---|---|---|---|---|
| **1** | Scrivi (Stage 0-1) | *il codice fa quello che credo?* | 100 giorni: trade dove previsto, flat la sera, P&L x10 con 10 contratti | si corregge il codice, non e un kill |
| **2** | Misura (Stage 2) | *l'edge **esiste**?* | su 2020-2024: **t >= 2 · WR >= 55% · R:R 0,5-1** | cimitero |
| **3** | Falsifica (Stage 5-6) | *l'edge **regge fuori campione**?* | 2025-2026, **una volta sola**: **t >= 1,3** · WR dello stesso ordine | cimitero, definitivo |
| **4** | Decidi (Stage 7) | *l'edge **basta** per questo conto?* | simulatore: **pass rate cumulato sui tentativi** + quanti contratti | cimitero |
| **5** | Deploy (Stage 8-9) | *regge in esercizio?* | paper 1 settimana, poi eval con budget dichiarato | si spegne |

Lo **Stage 4** (migliorie) e opzionale e sta fra la 2 e la 3: solo in-sample, max 3 input,
ogni filtro deve passare lo split-sample. Lo **Stage 8** (basket) serve quando le strategie
vive sono piu di una.

## Le due regole che contano piu dei criteri

1. **L'OOS si gira una volta sola.** Se lo rigiri con parametri diversi non e piu un OOS, e
   un secondo in-sample. VaultBreak e morta cosi e va bene cosi: e l'unica morta nel modo
   giusto.
2. **Tutto si scrive prima del run.** Soglia, attesa e kill in `SPEC.md` **prima** di
   guardare il risultato. Altrimenti il numero lo si spiega sempre.

## Cosa non sta piu in pipeline

- **PF >= 1,2 · avg trade >= $70 · nessun anno > 50%** → `metodologia_live.md`, stand-by fino
  ai payout. Sono criteri da soldi propri. *«Your biggest enemy is the trailing drawdown and
  not the profit factor»* (Live 002).
- **Il RATIO** → sostituito dal simulatore dello Stage 7. Trattava la eval come
  «sopravvivere a cinque anni» invece che come **primo passaggio ripetibile**: il corso
  lavora col 39% di pass rate per tentativo, che su quattro tentativi fa 92,6%.
- **Il vecchio Gate 3** (drawdown Monte Carlo contro l'MLL) → ritirato, stesso errore.

## Le due frasi da ricordare

> **`t` dice se l'edge esiste. Non dice se basta.**

> **Il rischio e un output, non un input.** Quanti contratti lo decide il simulatore, non noi.

## Lo script che controlla i report

Non si leggono piu gli xlsx a mano. `mc/docs/check_report.py` (solo libreria standard,
nessuna installazione):

```bash
# misure + controlli preliminari
python3 mc/docs/check_report.py report.xlsx

# verdetto fase 2 (IS): t >= 2 . WR >= 55% . R:R 0,5-1
python3 mc/docs/check_report.py report.xlsx --fase 2

# verdetto fase 3 (OOS): t >= 1,3 . WR >= 50% . R:R 0,5-1 . DD <= 1,5x IS
python3 mc/docs/check_report.py report.xlsx --fase 3 --dd-is 31670

# confronto rapido di piu report
python3 mc/docs/check_report.py mc/strategies/*/reports/*.xlsx --tabella
```

**La parte che conta davvero sono i CONTROLLI PRELIMINARI**, stampati prima delle misure:
commissione a zero, Bar Magnifier disattivato, timeframe, simbolo, point value e range di
date effettivo. Sono le trappole che ci hanno gia' bruciato dei run — un ORB girato con
`No Commission` e Bar Magnifier `Disabled`, un VWAP girato su grafico 15 minuti invece di 1.
Se sbaglia li, i numeri sotto non valgono niente.

PF e concentrazione annuale vengono stampati ma **marcati come criteri live**: informativi,
non fanno parte del verdetto.

## Stato

| strategia | dove | nota |
|---|---|---|
| **DriftPullback** | **fase 3, OOS da girare** | t 3,01 su 3.499 trade, WR 63,5% |
| VaultBreak `MaxTrades1` | in coda | t 2,97, mai vista fuori campione |
| ORB `cutoff11` | in coda | t 2,95, chiusa dal Gate 3 ritirato |
| VWAP · Gold · First5 | cimitero | t 0,87 · 1,89 (WR 42,6%) · 1,63, su tutte le varianti |
| VaultBreak base | cimitero | OOS t −0,03, morta nel modo giusto |

## Decisioni del 15/10/2026

**Tetto a 3 strategie per la prop.** Non si cerca oltre. Il corso dice di non deployare una
singola strategia nemmeno in eval (Live 004) e coi suoi numeri un basket da 45,8% al primo
tentativo contro 38% di una singola, 84,3% contro 77,2% entro sei. Tre bastano per avere
quell'effetto; oltre, si moltiplica il lavoro senza moltiplicare l'informazione.

**Test live appena c'e qualcosa in mano.** Non si aspetta il basket perfetto. Paper almeno
una settimana (Stage 9), poi un tentativo vero col budget dichiarato.

## Stesso asset o asset diversi?

**Misurato, non teorizzato.** DriftPullback e VaultBreak, entrambe NQ intraday, sullo stesso
periodo OOS 2025-2026:

| | valore |
|---|---|
| correlazione P&L giornaliero, giorni in comune (137) | **0,367** |
| correlazione sull'unione dei giorni, assenza = 0 (456) | **0,210** |
| copertura: Drift 100% dei giorni, VaultBreak 30% | giorni con solo VaultBreak: **0** |

**La correlazione la fanno la famiglia e l'ora, non il ticker.** Due logiche diverse sullo
stesso future danno 0,21. E al contrario NQ/ES/YM/RTY sono fra loro **0,8-0,95 correlati**
intraday: spostare la stessa logica su ES compra molta meno diversificazione di quanto sembri.

**Quindi cercare sullo stesso asset ha senso.** Il vincolo vero non e il ticker, sono due
altre cose:

1. **la copertura** — VaultBreak opera 137 giorni su 456 e Drift copre tutto: non aggiunge
   giorni, aggiunge dimensione su un terzo di essi. Quello che serve al basket e una strategia
   positiva **nei giorni in cui Drift perde**, e si misura;
2. **l'unita di rischio** — e questo si, e un argomento per cambiare strumento: al budget
   $60-110 per micro, R/ATR da **M2K 0,37-0,68** e **MNQ 0,14-0,26, il peggiore**. Su MNQ lo
   stop sta dentro il rumore. Se un terzo candidato nasce su M2K o MYM, e un vantaggio
   strutturale, non una diversificazione di facciata.
