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
