---
esito: passa
fase: s1
data: 2026-11-03
spec: strategies/OvernightBiasORB/SPEC.md
spec_commit: 78c8366f9d
report: strategies/OvernightBiasORB/reports/OBO_S1_100gg.xlsx
via: B
esito_script: passa
t: 0.92
dd: 9655
n: 33
---
# strategies/OvernightBiasORB/SPEC.md — Stage 1, meccanica: PASSA

## Il judge

**Meccanica come da SPEC.** Preliminari: @NQ 15 min come da SPEC; sessione Globex (il report ha una barra alle 03:30 CT, impossibile su RTH); slippage 0 con $7,50 per lato nella commissione come dice la SPEC. Ingressi fra le barre delle 9:15 e delle 11:30 (finestra 8:45-12:00 CT), max 2 al giorno contro 4, flat a tempo alla barra delle 14:45, nessun overnight, x10 identico. Stop fra -90 e -185 pt (0,3 x ATR) e target fra +294 e +348 pt (3 x stop); 20 trade su 33 escono a tempo. Trade peggiore $372 per micro.

## Avvisi

- blocco Pre-registrazione aggiunto dopo 98e1458: via e k si leggono anche nella prosa della SPEC a quel commit

## Output dello script

```
========================================================================
OBO_S1_100gg.xlsx
========================================================================

CONTROLLI PRELIMINARI  (se sbaglia qui, i numeri sotto non valgono)
  OK   Size: 1 contratto su tutti i 33 trade
  OK   Commissione: 7.50$ per Contract [Fixed 7.5$ per Contract]
  ?    Slippage: 0$ per Trade  (se e' 0, deve essere modellato nel codice)
  OK   Bar Magnifier: Enabled1 Minute
  ?    Compression: 15 Minutes   Symbol: @NQ   Point Value: $20
  ?    Range testato: 2026-07-07 -> 2026-11-03  (119 giorni)
  ?    Ultima barra 03:30 di OGGI: giorno incompleto, il session template NON si deduce. Verificalo sul grafico.

MISURE
  n trade        33
  avg trade      $515.15   +/- 561.92   (barra d'errore = sd/radice(n))
  t              0.92          <- quante barre separano l'avg dallo zero
  WR             48.5%
  R:R            1.62         (vinc. media $3092 / perd. media $1910)
  PF             1.523        [criterio LIVE, informativo]
  DD chiusi      $9,655
  Net            $17,000
  per anno       2026: 100%
  anno max       100%        [criterio LIVE, informativo]


STAGE 1 — controlli meccanici sulla List of Trades (33 trade, 2026-07-07 -> 2026-10-30)
  ?    periodo: 115 giorni di calendario fra il primo e l'ultimo trade (checklist: ~100)
  OK   contratti per trade: 1
  uscite, con i punti realizzati (confrontali con stop e target della SPEC):
       OBO-XL             12 trade   punti: da -50.25 a 435.75 (12 valori)
       OBO-XS              8 trade   punti: da -117.75 a 236 (8 valori)
       OBO-S-SL            5 trade   punti: -184.25, -159.25, -123.75, -113, -112.5
       OBO-L-SL            2 trade   punti: -185.25, -121.75
       OBO-L-SL0           2 trade   punti: -90.5
       OBO-S-TP            2 trade   punti: 313.25, 347.5
       OBO-L-TP            1 trade   punti: 294.25
       OBO-S-SL0           1 trade   punti: -114.75
    (uno stop o un target fisso deve avere un solo valore; con slippage negli stop il valore e' lo stop piu' lo slippage)
  orari d'ingresso (come li scrive MC: chiusura della barra del fill): 09:15×6 09:30×4 09:45×8 10:00×3 10:15×2 10:30×3 10:45×2 11:00×3 11:15×1 11:30×1
  OK   ingressi dentro 0900-1215: 0 fuori
  OK   trade al giorno: massimo 2 (SPEC: 4), 29 giorni con trade
  OK   flat la sera: 0 trade a cavallo di due date
  OK   scaling x10 (strategies/OvernightBiasORB/reports/OBO_S1_100gg_x10.xlsx): 33 trade contro 33, stessi ingressi e uscite si, P&L x10 diverso su 0 trade

  ESITO DEI CONTROLLI: passa (le uscite in punti vanno confrontate a mano con la SPEC)
```
