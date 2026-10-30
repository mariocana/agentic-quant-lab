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
