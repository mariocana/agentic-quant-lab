# CHECKLIST Stage 1 — Overnight Bias ORB

## Primo giro (03/11/2026) — `OBO_S1_x1.xlsx`, meccanica giusta dove verificabile

@NQ 15 min, 1 contratto, 7.5$, Bar Magnifier 1 min, input di default, `TradeStartEL 1260701`.
33 trade dal 07/07 al 30/10/2026 (29 giornate).

| # | controllo (SPEC) | esito |
|---|---|---|
| 1 | ingressi fra 08:45 e 12:00 CT | ✅ dalle 09:14 alle 11:29 (MC timbra l'ingresso a fine barra: segnale alle 09:00 → 09:14/09:15) |
| 2 | ingressi solo nel verso del bias | ⏳ nessun giorno con direzioni miste (29/29), ma il bias non si vede nel report → serve il log |
| 3 | stop = 0,3 × ATR, target = 3 × stop, dalla close del segnale | ✅ in parte: nello stesso giorno gli stop sono uguali (25/09: 113,0 e 112,5 pt; 11/09: 90,5 e 90,5) e il 16/10 lo stop è 114,75 pt e il target 347,5 = 3 × 115,8. ⏳ il valore dell'ATR → serve il log |
| 4 | flat alle 14:30 | ✅ 20 uscite `OBO-XL`/`OBO-XS`, tutte timbrate 14:45 (barra 14:30–14:45) |
| 5 | max 4 ingressi al giorno, mai due posizioni | ✅ 25 giorni con 1, 4 con 2; nessuna sovrapposizione |
| 6 | stop nella barra d'ingresso | ✅ `OBO-L-SL0`/`OBO-S-SL0` 3 volte, come da codice |
| 7 | scaling ×10 | ⏳ serve il run a 10 contratti |

Trade peggiore −$3.720 (= $372 per micro). Lo stop è 90–185 punti: con NQ a ~30.000 l'ATR
giornaliero RTH è più alto dei 250–450 pt stimati nella SPEC, ma resta sotto i $500 per micro.

**Aggiunto `ShowLog`** (03/11): `OBO DAY` stampa ogni giorno range overnight, open, posizione nel
range, bias, OR e ATR; `OBO ENT` ogni ingresso con close del segnale, SL, TP e ADX. Non tocca
la logica.

## Per il secondo giro
Stesso chart e stessa finestra: **A** a 1 contratto con `ShowLog 1` (log da salvare) e **B** a
**10 contratti** con `ShowLog 0`.
