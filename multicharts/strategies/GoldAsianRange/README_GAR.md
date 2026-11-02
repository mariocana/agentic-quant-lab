# Gold Asian Range — istruzioni Stage 1

Codice: `GoldAsianRange.txt` (signal).

## Chart
- **@GC · 15 min · Globex**, timezone **Exchange** (CT). Orari in ora del chart:
  range **20:00 → 00:00 CT** (= 21:00–01:00 NY), flat **10:00 CT** (= 11:00 NY).
  Se il tuo chart fosse in ora NY, usa 2100 / 0100 / 1100.
- Costi: $2.50/lato + 1 tick (GC tick 0.10 = $10). Max bars back 50.
- GC = $100/punto. Range tipico $10–25 → **rischio $1.000–2.500 per contratto GC**,
  cioè $100–250 su MGC: è questo il numero che conta per la prop.

## Verifica meccanica (Gate 1)
- Il range si forma fra le 20:00 e la mezzanotte; **nel momento in cui chiude** compaiono
  i due ordini stop ai bordi. Con `ShowLog 1` il log stampa range, high, low e se il
  giorno è armato.
- Il primo ordine che riempie prende il trade, l'altro sparisce (il codice li ri‑emette
  solo da posizione piatta) → **un trade al giorno**, mai due posizioni.
- Stop = ampiezza del range (`StopFrac 1.0`) dal prezzo d'ingresso; con `TP_RR 0` non
  c'è target e la posizione corre fino alle 10:00 CT.
- Controlla che le uscite `EXIT-L/S` cadano alle 10:00 e che nessuna posizione sopravviva
  oltre.
- **La posizione è overnight per costruzione**: segna nella lista trade i giorni di
  rollover del continuous (dati non back‑adjusted) — un salto di prezzo lì è artefatto,
  non P&L.

## Varianti
| | `TP_RR` | Profilo | Uso |
|---|---|---|---|
| **A** (originale) | 0 | WR ~34%, R:R > 1 | **non** rispetta il profilo prop → solo diversificatore nel basket funded (Stage 8) |
| **B** | 1.0 poi 0.5 | WR atteso più alto | candidata per l'eval |

Altri input pre‑registrati (Stage 4): `StopFrac` 0.5/0.75 · long only · finestra
22:00–00:00 CT · `MinRangePts`/`MaxRangePts` per saltare i giorni degeneri.

## Nota sull'ipotesi
Il motivo per cui regge fill realistici è che **non c'è gap fra livello e ordine**: gli
stop vengono piazzati nell'istante in cui il range chiude. È la differenza con i breakout
"del giorno prima", dove il prezzo può attraversare il livello prima che l'ordine esista.

## Fase 3b — gate marginale (29/10/2026): OOS della variante A, una volta sola

Candidata 2 della coda in `mc/docs/pipeline_semplice.md`. **Stesso chart e stessi input
dell'IS** (`GAR_S2_IS_A_tp0.xlsx`), cambia solo il periodo:

- `Mario_GoldAsianRange` su @GC 15 min, template **24/7**, time zone **Exchange** (come l'IS),
  Bar Magnifier 1 min, commissione **12.5$ per Contract**, slippage 0, **1 contratto**.
- Input: `RangeStart 2000`, `RangeEnd 0`, `ExitTime 1000`, `StopFrac 1.0`, **`TP_RR 0`**,
  `TradeLongs 1`, `TradeShorts 1`, `MinRangePts 0`, `MaxRangePts 0`, `Num_Contracts 1`,
  `ShowLog 0`.
- Chart dal **20/12/2024** a oggi (i trade prima del 2025-01-01 si tolgono nel verdetto).
- File: `GAR_S5_OOS_A_2025-2026.xlsx`.

**A verbale sul fuso.** Per TradeStation l'exchange di @GC è il COMEX di **New York** (scoperto
il 24/10 su Counter Trend). Il codice e la spec assumono che "Exchange" sia CT; se il chart era
in ora di New York, l'IS ha misurato range 19:45–00:00 e uscita alle 10:00 **di New York**, un'ora
prima della spec. L'OOS replica il chart dell'IS, qualunque fosse: si testa la regola misurata,
non quella scritta.

### Esito (02/11/2026): **non entra. Cimitero, definitivo.**

Report `GAR_S5_OOS_A_2025-2026.xlsx` (chart dal 23/12/2024 al 30/10/2026; nel verdetto i trade
del 2024 sono tolti). Meccanica uguale all'IS: stessi input, ultima barra alle 17:00 come
nell'IS, ingressi fra 00:00 e 09:59, 338 uscite su 456 alle 10:15.

| | n | avg | t | WR | trade peggiore | per anno |
|---|---|---|---|---|---|---|
| IS 2020–2024 | 1.280 | +$60 | 1,89 | 42,6% | −$4.975 | |
| OOS dal 2025 | 450 | **+$389** | **2,20** | 50,7% | **−$22.895** | 2025 +$61.355 · 2026 +$114.385 |

L'edge fuori campione c'è ed è più forte che nell'IS: il rialzo dell'oro 2025–2026 (da ~2.600 a
oltre 5.000). Ma lo stop è l'ampiezza del range asiatico, che col prezzo e la volatilità del 2026
è esploso: 10 trade perdono più di $5.000 sul contratto intero, il peggiore (02/02/2026, short
4.729,6 → stop 4.958,3) **$22.895 = $2.290 per micro, più dell'intero MLL**.

`gate_marginale.py --dal 2025-01-01`, book DPB a 2 micro, GAR a 1 MGC, costi GC $25 nel
report e $2,60 per MGC:

| | iid | contiguo |
|---|---|---|
| book | 41,3% | 57,0% |
| book + GAR A | 48,7% | 64,1% |
| Δ | **+7,4 pp** | **+7,0 pp** |

Criteri 1, 2 e 4 ✅; **3 ❌: giornata peggiore −$2.301 contro −$1.200 (DLL)**. Per le regole del
gate non si rigira: un tetto allo stop (`MaxRangePts`) sarebbe una variante nuova scelta dopo
aver visto l'OOS.
