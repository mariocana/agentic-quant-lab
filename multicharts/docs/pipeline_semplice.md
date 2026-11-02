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

---

# Pre-registrazione — gate marginale (fase 3b), 29/10/2026

**Scritta prima di girare qualsiasi candidata.** Nasce da una domanda di Mario: *«una strategia
non ha bisogno di un edge forte per funzionare in un contesto prop» (Live 002, 51:07), quindi
stiamo uccidendo strategie che in prop servirebbero?* Risposta misurata (`book_DPB_VB.md`):
in parte sì. Edge zero passa il ~24% su Lucid, DPB il 42%: un edge debole vale. Ma una
strategia a edge zero **abbassa** il pass rate del book (VaultBreak: −1,2 pp iid, −5,6 pp
contiguo). Quindi non si tolgono le morti: si cambia la domanda della fase 3 per chi ha un
edge debole.

## Due vie dopo la fase 2

| | via A — standalone (invariata) | **via B — marginale (nuova)** |
|---|---|---|
| fase 2, IS | t ≥ 2 · WR ≥ 55% · R:R 0,5-1 | **t > 0,5** · meccanica corretta · trade peggiore ≤ $500 per micro |
| fase 3, OOS una volta | t ≥ 1,3 | **i quattro criteri sotto** |
| se fallisce | cimitero | cimitero, definitivo |

Una strategia che passa la via A passa anche dal gate marginale prima di entrare nel book: la
domanda finale è sempre *alza il pass rate del book?*

## I criteri (fase 3b)

Strumento: `mc/docs/gate_marginale.py`. Regole `lucidflex_50k` di `prop_firms.ini`. Book di
riferimento: **quello live** (oggi DPB `DPB_S5_OOS_2025-2026` a 2 micro). Candidata a
**1 micro**, nessuna ricerca della size. 20.000 simulazioni, seed 20261029, numeri casuali comuni.

1. **Δ pass rate iid ≥ +2,0 pp** rispetto al book da solo. Soglia fissata sopra il rumore
   visto finora (ORB NQ +0,4 pp, VaultBreak −1,2 pp).
2. **Δ pass rate contiguo ≥ 0**: non deve peggiorare sulle finestre cronologiche vere.
3. **Giornata peggiore del book con la candidata ≥ −DLL ($1.200).**
4. **Avg trade OOS della candidata > 0.** Una moneta non entra nemmeno se il rumore la aiuta.

Tutti e quattro. Se ne manca uno: cimitero, senza rigirare con altri micro o altri parametri.

## Regole contro la ricerca a tentativi

- **Una candidata, un run.** Il risultato si scrive nella tabella sotto, anche se è negativo.
- **L'ordine è fissato qui.** Se una candidata entra, il book di riferimento per le
  successive diventa il nuovo book.
- **Tetto di 3 strategie nel book** (decisione del 15/10).
- Il book che esce dal gate **non è validato**: è un'ipotesi da confermare dal vivo. Si
  aggiunge una strategia alla volta, con almeno 2 settimane di live fra un'aggiunta e l'altra.

## Candidate, in quest'ordine (rivisto il 29/10, prima di qualsiasi run; Trend Following NQ B messa prima su richiesta di Mario, sempre prima di qualsiasi run)

**Regola aggiunta per le varianti scelte a posteriori:** se una variante e' la migliore fra
k provate, il suo t IS deve superare il **t atteso del massimo di k strategie a edge zero**,
non 0,5: k = 2 → 0,56 · k = 3 → 0,85 · k = 4 → 1,03 · k = 6 → 1,27.

| # | candidata | t IS | trade peggiore / micro | nota |
|---|---|---|---|---|
| 1 | **Trend Following (Unger) B su NQ** (MNQ) | 1,73 | $264 | B pre-registrata per strumento; il migliore di 4 strumenti, soglia k = 4 → 1,03: passa. Cinque anni su cinque positivi. IS girato senza commissione, corretto a −$15/trade. OOS mai toccato |
| 2 | **Gold Asian Range A** (MGC) | 1,89 | $498 | variante base pre-registrata, strumento diverso da NQ. OOS mai toccato |
| 3 | ORB NQ `cutoff11` | 2,80 | | OOS visto da solo (t 0,63), mai nel book |
| 4 | VaultBreak `MaxTrades1` | 2,88 | | OOS visto da solo (t 0,23), mai nel book. **A verbale**: logica gia' morta su NQ |
| 5 | ORB NQ senza cutoff | 2,74 | | **a verbale**: gia' misurato nel book il 29/10 prima della regola (+0,4 pp iid) |
| 6 | VWAP Pullback filtrata (MNQ) | 0,69 | $444 | scelta fra 2 versioni: soglia 0,56, passa. OOS mai toccato |

**Escluse:**
- **VaultBreak su ES**: la stessa logica e' fallita fuori campione su NQ nello stesso periodo (t −0,03), ES/NQ correlati 0,8-0,95. Rigirarla sarebbe una variante dopo un gate fallito.
- **Counter Trend YM B**: migliore di 6 run, t 1,01 contro 1,27 atteso dal caso.
- First5 (serve un IS nuovo con lo stop), Last Half-Hour e Rebalancing (trade peggiore oltre $500), Trend Following 6E (causa B: l'edge fuori campione c'era, B t 1,98, ma lo stop vale $938 a contratto e su Lucid non ci sono micro), Trend Following B su ES (t 0,52 sotto la soglia k = 4 di 1,03) e su GC (t −0,16), tutte le altre (t ≤ 0,5).

**Fuori da questa coda, con la pipeline normale** (Stage 0 il 29/10, prima di qualsiasi run): le
versioni del corso che non avevamo mai testato. **VaultBreak v8** (`VaultBreak/SPEC_v8.md`, via B
t IS > 0,85, k = 3), **VWAP Pullback + ADX v4** (`VWAP_Pullback/SPEC_ADX.md`, via B t IS > 1,03,
k = 4, fuori campione pulito dal 3/7/2026), **Overnight Bias ORB** (`OvernightBiasORB/SPEC.md`,
solo via B, t IS > 0,5). Se passano la fase 2 entrano in coda dopo la candidata 6, con verdetto
OOS asimmetrico: fallire conta pieno, passare vale solo come prova dal vivo.

## Registro

| data | candidata | Δ iid | Δ contiguo | peggior giorno | avg OOS | verdetto |
|---|---|---|---|---|---|---|
| 29/10 | VaultBreak base (prova dello script) | −1,2 | −5,6 | −$1.098 | −$0,19 | non entra |
| 29/10 | Trend Following (Unger) B su NQ, candidata 1 | −3,8 | −7,5 | −$998 | +$6,02 | **non entra**: cimitero |
| 02/11 | Gold Asian Range A (MGC), candidata 2 | +7,4 | +7,0 | −$2.301 | +$38,95 | **non entra** (criterio 3): un trade da −$2.290 per micro, più dell'MLL. Cimitero |
| 02/11 | VaultBreak v8 (corso) | +3,0 | +7,7 | −$1.104 | +$9,35 | **entra** |
