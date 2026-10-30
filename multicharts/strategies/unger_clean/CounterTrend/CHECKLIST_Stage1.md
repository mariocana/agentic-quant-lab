# CHECKLIST Stage 1 — Counter Trend di Unger su GC — **Gate 1 passato** (23/10/2026, secondo giro)

## Primo giro (19/10/2026) — **invalido**: impostazioni del chart

Periodo 2026‑06‑25 → 2026‑10‑18, @GC, $12,50/contratto, Bar Magnifier 1 min. 12 trade.
Report non conservati.

| problema | prova | effetto |
|---|---|---|
| **chart a 5 min** invece di 30 | `Compression: 5 Minutes`; segnali alle 02:05, 02:10, 02:25 | la finestra di 8 barre dura 40 min invece di 4 ore, Bollinger su 100 min invece di 10 ore: un'altra strategia |
| **session template a giorno di calendario** (00:00–24:00) | uscite `End of Day Exit` alle **23:59** (12:59 il 03/07) | `Mario_PtnBaseSA` legge "ieri" come giorno di calendario, non come sessione CME: filtri 14/15/40 sbagliati |
| **run A con `FlatEOD` acceso** | 6 uscite `End of Day Exit` nel run A | il run A era in realtà una B; A10 non è 10 × A perché fatto con input diversi |

### Cosa questo giro ha comunque verificato
- **Stop**: le 6 uscite `Stop Loss` sono a **0,651–0,654%** dall'entrata = 0,65% del close
  del segnale (l'entrata è all'open della barra dopo). `stop$` nel log corretto
  (4.054,40 × 0,65% × $100 = $2.635,36).
- **Segnali nella direzione della posizione aperta** (`mp=1` su un `CT L`, `mp=-1` su un
  `CT S`): ignorati, come deve essere.

## Per il secondo giro
@GC **30 min**, template **17:00–16:00 CT senza pause** (quello di ESCounter). Run A
(`FlatEOD 0`, `ShowLog 1`), A10 (stessi input, 10 contratti), B (`FlatEOD 1`). Annotare il
close di @GC al 02/01/2020 (prezzo reale ~1.525).

---

## Secondo giro (23/10/2026) — **Gate 1 passato**

@GC **30 min**, template 17:00–16:00 CT, $12,50/contratto, Bar Magnifier 1 min, periodo
2026‑07‑09 → 2026‑10‑23 (106 giorni). Report in `reports/`: `CT_S1_GC_A_x1.xlsx` (A),
`CT_S1_GC_A_x10.xlsx` (A a 10 contratti; sul Desktop si chiamava "B"),
`CT_S1_GC_B_x1.xlsx` (variante B, `FlatEOD 1`; sul Desktop "C"). Log non inviato.

| # | controllo | esito |
|---|---|---|
| 1 | finestra | ✅ entrate timbrate fra 03:00 e 05:00 CT = segnali sulle barre che chiudono fra 02:30 e 04:30 (`cnt` 2–6), mai di domenica |
| 2 | filtri 14/15/40 | **non verificato riga per riga**: manca il log. La funzione `Mario_PtnBaseSA` è verificata (Gate 1, 95 sessioni) e gli input sono collegati direttamente (L → 14, S → 15, entrambi → no 40) |
| 3 | stop 0,65% | ✅ tutte le 23 uscite `Stop Loss` (A e B) a **0,650–0,653%** dall'entrata |
| 4 | inversioni | **non osservate**: in 106 giorni nessun segnale opposto con posizione aperta. La logica (`buy` / `sellshort` su posizione opposta) è standard e resta da vedere nell'IS |
| 5 | variante B | ✅ 4 `End of Day Exit` alle 15:59 (sessione che chiude alle 16:00), nessuna posizione overnight |
| — | variante A | tiene oltre la sessione e nel weekend (stop del 17/07 scattato domenica 19/07 alle 23:00); posizioni fino a 2 giorni e 19 ore |
| 6 | scala ×10 | ✅ A10 = 10 × A su tutti i 13 trade |
| 7 | back‑adjustment (close @GC al 02/01/2020) | **non annotato**: da fare prima di leggere lo Stage 2 |

### Il dato da tenere: nella variante A **13 trade su 13 a stop**

Non è un difetto: è la costruzione di Unger. Senza target e senza uscita a tempo una posizione
esce solo **a stop** (sempre in perdita) o **per inversione** su un segnale opposto. In 106
giorni nessuna inversione, quindi WR 0% e −$2.807 per trade. Su GBPUSD le inversioni erano
frequenti (il cambio oscilla); sull'oro in trend forte del 2026 no. **Il porting dipende da
quante inversioni produce l'oro**: lo misura lo Stage 2.

| run | n | WR | avg | net |
|---|---|---|---|---|
| A (originale) | 13 | 0% | −$2.807 | −$36.485 |
| B (flat a fine sessione) | 14 | 14,3% | −$2.068 | −$28.950 |

Periodo OOS e 14 trade: informativo, non decide nulla.

## Stage 2 — cosa lanciare
IS **2020‑01‑01 → 2024‑12‑31**, 1 contratto, senza log: **GC** A e B ($12,50); **ES** A e B
($15); **YM** A e B ($7,50). Prima, il close di @GC al 02/01/2020.
