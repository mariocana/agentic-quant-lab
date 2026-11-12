---
esito: passa
fase: oos
data: 2026-11-09
spec: strategies/First5PreOpen/SPEC.md
spec_commit: 862759ff66
report: strategies/First5PreOpen/reports/F5P_S5_OOS_2025-2026.xlsx
via: B
esito_script: passa
t: 1.55
dd: 25385
n: 251
---
# strategies/First5PreOpen/SPEC.md — fase 3, OOS: PASSA

## Il judge

OOS 2025-2026, via B: **passa** (lo script registra le misure, il giudizio e' il gate marginale). Preliminari controllati sul report: @NQ 5 min, BM 1 min, 1 contratto, 7,5$ per contratto e slippage 0 come da SPEC (slippage dentro la commissione); trade dal 2025-01-02 al 2026-11-09, dentro l'OOS della SPEC (2025-01-01 -> oggi). Session template non leggibile dal report (ultima barra di oggi), ma i 251 ingressi sono tutti alle 08:40, le uscite a tempo tutte alle 15:05 e l'unica End of Day Exit e' alle 12:15 del 03/07/2025 (mezza giornata), coerenti con Globex in CT. Misure: 251 trade, t 1,55, WR 29,9%, R:R 3,38, trade peggiore $3.895 nel report ($390 per micro, sotto i $500), sopra l'attesa della SPEC (edge dimezzato, t 0,6-0,7). Verdetto asimmetrico, anche se lab.py non lo segnala: un run con TradeStartEL e TradeEndEL a 0 ha girato per errore sul 22/06 -> 06/11/2026, dentro questo OOS, ed e' a verbale nel diario (F5P_S1_run0_OOS2026_input-a-0_non-valido.xlsx, mai giudicato); fallire contava pieno, passare vale solo come prova dal vivo. Il report giudicato ha input corretti (TradeStartEL 1250101, TradeEndEL 0, 1 contratto, BM 1 min, 7,5$) secondo il desk.

## Output dello script

```
========================================================================
F5P_S5_OOS_2025-2026.xlsx
========================================================================

CONTROLLI PRELIMINARI  (se sbaglia qui, i numeri sotto non valgono)
  OK   Size: 1 contratto su tutti i 251 trade
  OK   Commissione: 7.50$ per Contract [Fixed 7.5$ per Contract]
  ?    Slippage: 0$ per Trade  (se e' 0, deve essere modellato nel codice)
  OK   Bar Magnifier: Enabled1 Minute
  ?    Compression: 5 Minutes   Symbol: @NQ   Point Value: $20
  ?    Range testato: 2025-01-02 -> 2026-11-09  (676 giorni)
  ?    Ultima barra 15:55 di OGGI: giorno incompleto, il session template NON si deduce. Verificalo sul grafico.

MISURE
  n trade        251
  avg trade      $393.78   +/- 254.01   (barra d'errore = sd/radice(n))
  t              1.55          <- quante barre separano l'avg dallo zero
  WR             29.9%
  R:R            3.38         (vinc. media $4320 / perd. media $1279)
  PF             1.439        [criterio LIVE, informativo]
  DD chiusi      $25,385
  Net            $98,840
  per anno       2025: 51%  2026: 49%
  anno max       51%        [criterio LIVE, informativo]


Via B: l'OOS non ha soglie proprie, qui si registrano le misure. Il giudizio e' il gate marginale (book); se fallisce, cimitero definitivo.
```
