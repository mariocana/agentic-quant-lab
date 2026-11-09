---
esito: passa
fase: s1
data: 2026-11-09
spec: strategies/First5PreOpen/SPEC.md
spec_commit: 862759ff66
report: strategies/First5PreOpen/reports/F5P_S1_A_x1.xlsx
via: B
esito_script: passa
t: 1.81
dd: 6020
n: 62
---
# strategies/First5PreOpen/SPEC.md — Stage 1, meccanica: PASSA

## Il judge

Stage 1 secondo giro, con Bar Magnifier 1 min: **passa**. Preliminari controllati sul report: @NQ 5 min, BM 1 min acceso, commissione 7,5$ per contratto e slippage 0 come da SPEC (slippage dentro la commissione); trade fra 2024-08-07 e 2024-12-27, dentro la finestra di fase 1 della SPEC (2024-08-01 -> 2024-12-31), nessuno dopo il 2024 anche se il Range testato arriva al 2026-11-09 perche' il grafico e' piu' lungo (TradeEndEL 1241231). Session template non leggibile dal report (ultima barra di oggi), ma gli ingressi alle 08:40 richiedono la barra 830, e l'uscita alle 12:00 del Ringraziamento (28/11, festivo col Globex fino alle 12:00 CT) torna con un grafico Globex in CT. Controlli di lab.py: 62 ingressi tutti alle 08:40, max 1 trade al giorno, nessun trade a cavallo di due date, x10 esatto su 62 trade. Uscite: 41 stop (L/S-SL e 9 -SL0 sulla barra d'ingresso) a punti variabili come prevede la SPEC (stop sul livello della prima candela, non a distanza fissa), allo stesso livello del log di ShowLog del primo giro secondo il desk; 20 uscite a tempo tutte alle 15:05, una End of Day Exit alle 12:00 del 28/11; nessun target, come da TP_RR 0. A titolo informativo: t 1,81, WR 30,6%, R:R 4,56 su 62 trade.'

## Output dello script

```
========================================================================
F5P_S1_A_x1.xlsx
========================================================================

CONTROLLI PRELIMINARI  (se sbaglia qui, i numeri sotto non valgono)
  OK   Size: 1 contratto su tutti i 62 trade
  OK   Commissione: 7.50$ per Contract [Fixed 7.5$ per Contract]
  ?    Slippage: 0$ per Trade  (se e' 0, deve essere modellato nel codice)
  OK   Bar Magnifier: Enabled1 Minute
  ?    Compression: 5 Minutes   Symbol: @NQ   Point Value: $20
  ?    Range testato: 2024-08-07 -> 2026-11-09  (824 giorni)
  ?    Ultima barra 14:15 di OGGI: giorno incompleto, il session template NON si deduce. Verificalo sul grafico.

MISURE
  n trade        62
  avg trade      $537.42   +/- 296.35   (barra d'errore = sd/radice(n))
  t              1.81          <- quante barre separano l'avg dallo zero
  WR             30.6%
  R:R            4.56         (vinc. media $3480 / perd. media $763)
  PF             2.016        [criterio LIVE, informativo]
  DD chiusi      $6,020
  Net            $33,320
  per anno       2024: 100%
  anno max       100%        [criterio LIVE, informativo]


STAGE 1 — controlli meccanici sulla List of Trades (62 trade, 2024-08-07 -> 2024-12-27)
  ?    periodo: 142 giorni di calendario fra il primo e l'ultimo trade (checklist: ~100)
  OK   contratti per trade: 1
  uscite, con i punti realizzati (confrontali con stop e target della SPEC):
       F5P-L-SL           17 trade   punti: da -111.5 a -21.75 (15 valori)
       F5P-S-SL           15 trade   punti: da -71.25 a -13.75 (14 valori)
       F5P-XS             13 trade   punti: da -27.5 a 458.25 (13 valori)
       F5P-XL              7 trade   punti: da 89.75 a 223 (7 valori)
       F5P-L-SL0           5 trade   punti: -43, -36.25, -14.5, -14, -7
       F5P-S-SL0           4 trade   punti: -30.5, -30, -21.25, -20.75
       End of Day Exit     1 trade   punti: 0.75
    (uno stop o un target fisso deve avere un solo valore; con slippage negli stop il valore e' lo stop piu' lo slippage)
  orari d'ingresso (come li scrive MC: chiusura della barra del fill): 08:40×62
  OK   ingressi dentro 0840-0840: 0 fuori
  OK   trade al giorno: massimo 1 (SPEC: 1), 62 giorni con trade
  OK   flat la sera: 0 trade a cavallo di due date
  OK   scaling x10 (strategies/First5PreOpen/reports/F5P_S1_B_x10.xlsx): 62 trade contro 62, stessi ingressi e uscite si, P&L x10 diverso su 0 trade

  ESITO DEI CONTROLLI: passa (le uscite in punti vanno confrontate a mano con la SPEC)
```
