# CHECKLIST Stage 1 — GoldAsianRange

Chart: `@GC` · 15 min · Bar Magnifier 1 min · commissione **$12,50 per contratto**
(slippage ripiegata dentro, campo slippage 0) · Point Value $100 · Backtesting Mode Classic.
Periodo del chart: **2026‑06‑16 04:00 → 2026‑10‑08 20:00** (83 finestre di range,
78 giorni con trade).

Report in `reports/`:

| run | `TP_RR` | `Num_Contracts` | file |
|---|---|---|---|
| A | 0 | 1 | `GAR_S1_A_tp0_x1.xlsx` |
| B | 0 | 10 | `GAR_S1_B_tp0_x10.xlsx` |
| C | 1 | 1 | `GAR_S1_C_tp1_x1.xlsx` |
| D | 1 | 10 | `GAR_S1_D_tp1_x10.xlsx` |

Tutti gli altri input ai default di spec: `RangeStart 2000`, `RangeEnd 0`,
`ExitTime 1000`, `StopFrac 1.0`, `TradeLongs 1`, `TradeShorts 1`,
`MinRangePts 0`, `MaxRangePts 0`.

---

## Primo giro (08/10/2026) — **invalido**, sessione sbagliata

Template sessione `COMEX: Metals Futures (Electronic)`. Il chart **non conteneva le barre
fra 07:45 e 14:15**: il time exit, che cerca la prima barra con `Time >= 1000`, finiva
sulle 14:15. Quattro trade artefatto (entra 14:15, esce 14:29) e tutte le altre uscite a
tempo fuori posto. Run scartato, nessun report conservato.

Il log `GAR RNG` di quel giro ha però **validato la finestra del range**: `barre= 16` e
`armTime= 0` su tutte le 83 giornate, cioè esattamente 20:00 → 00:00 a 15 minuti. Risolta
anche l'ambiguità della barra di mezzanotte: MC la timbra `0`, non `2400`, quindi il wrap
`Time >= 2000 or Time < 0` chiude la finestra sulla barra giusta. La domanda aperta nella
spec («verificare che con il chart CT le finestre coincidano») è chiusa.

## Secondo giro (09/10/2026) — sessione 24/7, **Gate 1 passato**

### Check 1 — trade dove previsto ✅
Entrate distribuite da **00:30 a 09:45**, cioè tutte dopo la chiusura del range (00:00) e
tutte prima di `ExitTime` (10:00). Nessuna entrata fuori finestra. Il buco 07:45→14:15 e i
quattro trade a 14:15 sono spariti.

Moda sulle prime barre dopo la chiusura del range, come atteso da una strategia di
breakout: 16 entrate a 00:30, 6 a 00:45, 9 a 01:15.

### Check 2 — un trade al giorno ✅
`giorni con >1 trade: []` su 78 giorni. L'OCO via `tradeDone` + `MarketPosition = 0`
funziona.

### Check 3 — flat all'ora prevista ✅
Variante A: **63 uscite su 78 alle 10:15**, le altre 15 sono stop (`L-SL`/`S-SL`).
Variante B (C): 41 a tempo, 22 a target, 15 a stop. Le uscite a tempo cadono sulla barra
delle 10:15 perché `Time >= 1000` scatta sulla barra timbrata 10:00 e l'ordine `next bar
at market` riempie sulla successiva — comportamento corretto, non un difetto.

**Zero posizioni overnight** (0/78: entrata e uscita sempre nello stesso giorno di
calendario). Questo **annulla il rischio di rollover** segnalato nella spec: la posizione
non attraversa mai un break di sessione, quindi i giorni di rollover del continuous non
vanno annotati.

### Check 4 — SL/TP = quelli della spec ✅
Prova diretta sul trade peggiore: **massima distanza di stop 43,90 punti**,
43,90 × $100 = $4.390, più $25 di commissione andata/ritorno = **$4.415**, che è
esattamente il trade peggiore riportato da MC. Lo stop viene colpito al prezzo, senza gap:
in questo campione **nessuna uscita ha superato il livello di stop**.

Le 15 uscite a stop sono identiche fra A e C (n=15, min 20,60, mediana 31,30, max 43,90
punti), come deve essere: `TP_RR` non tocca lo stop.

Con `TP_RR = 1` la distanza di target **è** l'ampiezza del range: i 22 target raggiunti
danno mediana **37,75 punti**, che coincide con la mediana del range misurata dal log
`GAR RNG` del primo giro (**≈ 37,8**). Due misure indipendenti, stesso numero.

### Check 5 — con 10 contratti P&L ×10 ✅
Rapporto esatto su ogni metrica in dollari, invarianza esatta su ogni rapporto:

| metrica | ×1 | ×10 | rapporto |
|---|---|---|---|
| **A → B** (`TP_RR 0`) | | | |
| Net Profit | $69.660 | $696.600 | **10,000000** |
| Gross Profit | $136.465 | $1.364.650 | **10,000000** |
| Gross Loss | −$66.805 | −$668.050 | **10,000000** |
| Max Strategy Drawdown | −$14.295 | −$142.950 | **10,000000** |
| Max Close To Close DD | −$9.920 | −$99.200 | **10,000000** |
| Commission Paid | $1.950 | $19.500 | **10,000000** |
| Profit Factor | 2,04 | 2,04 | 1,000000 |
| Total # of Trades | 78 | 78 | 1,000000 |
| % Profitable | 57,69% | 57,69% | 1,000000 |
| Max # Contracts Held | 1 | 10 | 10,000000 |
| **C → D** (`TP_RR 1`) | | | |
| Net Profit | $58.920 | $589.200 | **10,000000** |
| Gross Profit | $123.990 | $1.239.900 | **10,000000** |
| Gross Loss | −$65.070 | −$650.700 | **10,000000** |
| Max Strategy Drawdown | −$10.420 | −$104.200 | **10,000000** |
| Max Close To Close DD | −$8.560 | −$85.600 | **10,000000** |
| Profit Factor | 1,91 | 1,91 | 1,000000 |
| % Profitable | 58,97% | 58,97% | 1,000000 |

Nota: GoldAsianRange usa bracket a livello di prezzo (`next bar at posSL stop`), non
`SetStopLoss`, quindi **non è esposta al difetto `CurrentContracts` sulla barra d'ingresso**
che ha richiesto due giri su NQ First5. Il test ×10 lo conferma e basta.

### Check 6 — nessun trade nel weekend non voluto ✅
Entrate e uscite **solo lun–ven**, zero sabato/domenica:
Lun 13 · Mar 17 · Mer 17 · Gio 16 · Ven 15.

Il venerdì sera non esiste una finestra 20:00–00:00 (il mercato chiude alle 16:00 CT),
quindi non si generano trade il sabato. Corretto per costruzione.

**Giorni lavorativi senza trade: 4.**

| giorno | causa |
|---|---|
| 2026‑07‑03 | venerdì prima del 4 luglio — **half‑day/festivo US**, annotato |
| 2026‑06‑22 | lunedì, nessun lato del range toccato prima delle 10:00 |
| 2026‑08‑17 | idem |
| 2026‑08‑31 | idem |

I tre lunedì senza trade spiegano il conteggio del lunedì più basso (13 vs 15–17): il
range costruito la domenica sera incorpora il gap del weekend, è più largo e viene rotto
meno spesso. Osservazione, non difetto.

---

## ✅ Gate 1 — **passato** (09/10/2026)

Meccanica corretta al 100% su tutti e sei i controlli del protocollo. Report in `reports/`.

## Numeri indicativi (NON un giudizio di Gate 2)

Gate 2 si giudica sull'IS 2020‑2024 con n ≥ 200. Questi sono 78 trade su 4 mesi e servono
solo a sapere se vale la pena spendere lo Stage 2.

| | variante A (`TP_RR 0`) | variante B (`TP_RR 1`) |
|---|---|---|
| trade | 78 | 78 |
| Net Profit (GC) | $69.660 | $58.920 |
| avg trade (GC) | $893 | $755 |
| → **avg trade per MGC** | **$89** | **$75** |
| WR | 57,7% | 59,0% |
| Profit Factor | 2,04 | 1,91 |
| avg win / avg loss | 1,50 | 1,33 |
| Max Strategy DD (GC) | −$14.295 | −$10.420 |
| → **DD per MGC** | **$1.429** | **$1.042** |
| trade peggiore (GC) | −$4.415 | −$4.415 |
| → **peggiore per MGC** | **$442** | **$442** |

### Il dato che conta: l'unità di rischio entra nel budget

Soglia Gate 2 sul trade peggiore: **÷10 ≤ $500**. Qui è **$442**. **Passa.**

È la prima volta nella pipeline. Le tre strategie su @NQ morivano proprio qui
(First5: DD/micro $5.784, trade peggiore/micro $1.044). Il muro «l'edge esiste ma l'unità
di rischio non sta nell'MLL» **non si presenta su MGC**.

### Due cose da registrare come scostamenti dalla spec

1. **Il range è più largo di quanto la spec assumeva.** La spec diceva «range tipico
   $10–25 → $100–250 per MGC». Misurato: **mediana ≈ 37,8 punti ≈ $378 per MGC**, media
   ≈ 42 pt ≈ $425. Da 1,5 a 3,8 volte l'assunzione. Resta sotto la soglia di gate
   ($500), ma l'assunzione della spec era sbagliata e va corretta lì.
2. **La variante A non ha il profilo che la spec le attribuiva.** Spec: «WR 34%,
   R:R > 1, non rispetta il profilo prop». Misurato: **WR 57,7%** con avg win/avg loss
   **1,50**. La ricerca del corso riportava WR ~34%; su questi dati non si riproduce.
   Possibile causa: il time exit a 10:00 CT chiude molte posizioni in piccolo utile che
   in un'altra configurazione sarebbero diventate perdite. Da verificare nello Stage 2,
   dove il campione è 5 anni invece di 4 mesi.

   Conseguenza pratica: **entrambe le varianti vanno allo Stage 2**, non solo la B. La
   pre-registrazione «Gate 2 si giudica sulla variante B» era motivata dall'attesa
   WR 34% della variante A; quell'attesa è smentita dal dato, non da una scelta a
   posteriori sui risultati.

### Punti aperti prima/dentro lo Stage 2

- **ADR dell'oro non misurata.** Un range asiatico di 37,8 punti su un sottostante a
  $4.100–4.400 va rapportato al range giornaliero medio del periodo. Se il range asiatico
  fosse una frazione dominante dell'ADR, lo stop «tutto il range» sarebbe strutturalmente
  sovradimensionato. Da misurare.
- **Gate date non ancora eseguito** (il controllo pre-registrato su una finestra di date
  ristretta, come fatto per First5).

---

## ADR — misurata (13/10/2026), punto aperto chiuso

Indicatore `GAR_ADR_Study.txt` sullo stesso chart. **n = 84 giornate**, 17/06 → 12/10/2026.
Tutte le misure in punti @GC.

| | mediana | media | p10 | p90 | min | max |
|---|---|---|---|---|---|---|
| `asia` — finestra del range | **39,05** | 42,88 | 27,15 | 66,16 | 20,60 | 85,20 |
| `trade` — finestra 00:00→10:00 | **57,00** | 64,70 | 39,22 | 98,13 | 26,00 | 149,60 |
| `h24` — 24 ore precedenti | **92,90** | 99,97 | 58,80 | 150,77 | 42,80 | 242,40 |

### La domanda pre-registrata e la sua risposta

La regola era scritta prima di misurare, in `SPEC.md`: «*se il range asiatico è una frazione
dominante dell'ADR, lo stop «tutto il range» è strutturalmente sovradimensionato e la
variante `StopFrac` < 1 diventa il caso base, non un'alternativa*».

**`asia / h24` = 0,447 mediano** (media 0,462; p10 0,263; p90 0,643).

Il range asiatico è **meno della metà** del movimento giornaliero. La condizione
pre-registrata **non è soddisfatta**: più di metà dell'escursione della giornata avviene
fuori dalla finestra asiatica, quindi c'è spazio perché la rottura prosegua.

**Conseguenza: `StopFrac 1.0` resta il caso base dello Stage 2.** La regola ha sparato e la
risposta è «non cambiare niente». Le varianti `StopFrac` 0.5/0.75 restano dove erano
pre-registrate, allo Stage 4.

### Il target a 1R è raggiungibile

`trade / asia` = **1,531 mediano** (media 1,668): nella giornata tipica la finestra di
trading è una volta e mezza il range asiatico, quindi un target a 1R ci sta con margine.

| | giorni | % |
|---|---|---|
| `trade` < `asia` → **1R irraggiungibile anche in teoria** | 18 / 84 | **21,4%** |
| `trade` < 0,5 × `asia` → **nemmeno 0,5R** | 1 / 84 | **1,2%** |

Il 21,4% combacia con il comportamento osservato della variante B: 22 target su 78 trade
(28%) sono stati raggiunti. Numeri indipendenti, stessa storia.

Nota per lo Stage 4: a `TP_RR 0.5` il target diventa irraggiungibile solo nell'1,2% dei
giorni invece che nel 21,4%. Era già pre-registrata; ora si sa **perché** dovrebbe aiutare.

### Il rischio per MGC, per `StopFrac`

| `StopFrac` | mediana | p90 | max |
|---|---|---|---|
| **1.00** (base) | **$390** | **$662** | **$852** |
| 0.75 | $293 | $496 | $639 |
| 0.50 | $195 | $331 | $426 |
| 0.35 | $137 | $232 | $298 |

Soglia Gate 2 sul trade peggiore: **÷10 ≤ $500**.

Con `StopFrac 1.0` la **mediana passa ($390) ma il 90° percentile no ($662)**, e il caso
peggiore del campione è $852. Il trade peggiore *realizzato* nel run era $442 — molto
meglio del massimo teorico. Il motivo non è fortuna:

### Meccanismo di autolimitazione (nuovo, da registrare)

I giorni con il range più largo **tendono a non generare nessun trade**, perché un range
largo è più difficile da rompere entro le 10 ore della finestra.

Nel decile più largo del periodo confrontabile (8 giorni, `asia` > 67 punti):

| giorno | `asia` | trade? |
|---|---|---|
| 1260622 | 85,20 | **no** |
| 1260825 | 84,50 | sì |
| 1260630 | 76,70 | sì |
| 1260831 | 75,90 | **no** |
| 1260928 | 75,20 | sì |
| 1260703 | 72,40 | **no** — ma è la vigilia del 4 luglio, half‑day |
| 1260805 | 68,60 | sì |
| 1260623 | 67,60 | sì |

**3 su 8 senza trade (38%) contro un 4,9% complessivo.** Scontando 1260703, che si spiega
col calendario e non con l'ampiezza, restano 2 su 8 (25%): comunque **cinque volte** il
tasso di base.

Quindi l'esposizione effettiva è più vicina alla mediana che al massimo. Ma è una proprietà
del campione, non una garanzia: su cinque anni di Stage 2 qualche giornata larga entrerà.
**Da sorvegliare al Gate 2, non da correggere adesso.**

### Contesto: l'oro in questo periodo

`h24` mediano 92,90 punti su un sottostante a $4.100–4.400 = **~2,2% di escursione
giornaliera**. È un periodo volatile, e va ricordato quando si leggeranno i numeri dello
Stage 2 sul 2020–2024.
