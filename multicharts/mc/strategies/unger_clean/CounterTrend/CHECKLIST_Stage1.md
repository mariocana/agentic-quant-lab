# CHECKLIST Stage 1 — Counter Trend di Unger su GC

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
