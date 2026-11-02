---
esito: passa
fase: s1
data: 2026-11-02
spec: strategies/VaultBreak/SPEC_v8.md
spec_commit: fe91c17e88
report: strategies/VaultBreak/reports/VB8_S1_100gg.xlsx
via: A|B
esito_script: passa
t: -0.07
dd: 11705
n: 102
---
# strategies/VaultBreak/SPEC_v8.md — Stage 1, meccanica: PASSA

## Il judge

**Meccanica come da SPEC_v8.** Preliminari: @NQ 30 min come da SPEC, slippage 0 con i $7,50 per lato nella commissione come dice la SPEC, sessione Globex confermata dall'ultima barra alle 16:00 del report IS con lo stesso grafico. Stop -75 pt e target +40 pt esatti, ingressi fra le barre delle 10:30 e delle 14:30 (segnali 10:00-14:00 CT), max 3 al giorno, nessun overnight, x10 identico. L'uscita VWAP a 7 barre e VB-Carry non scattano mai nei 100 giorni.

## Avvisi

- blocco Pre-registrazione aggiunto dopo 811259fcf3: via e k si leggono anche nella prosa della SPEC a quel commit

## Output dello script

```
========================================================================
VB8_S1_100gg.xlsx
========================================================================

CONTROLLI PRELIMINARI  (se sbaglia qui, i numeri sotto non valgono)
  OK   Size: 1 contratto su tutti i 102 trade
  OK   Commissione: 7.50$ per Contract [Fixed 7.5$ per Contract]
  ?    Slippage: 0$ per Trade  (se e' 0, deve essere modellato nel codice)
  OK   Bar Magnifier: Enabled1 Minute
  ?    Compression: 30 Minutes   Symbol: @NQ   Point Value: $20
  ?    Range testato: 2026-06-02 -> 2026-11-02  (153 giorni)
  ?    Ultima barra 07:30 di OGGI: giorno incompleto, il session template NON si deduce. Verificalo sul grafico.

MISURE
  n trade        102
  avg trade      $-7.65   +/- 104.50   (barra d'errore = sd/radice(n))
  t              -0.07          <- quante barre separano l'avg dallo zero
  WR             62.7%
  R:R            0.58         (vinc. media $781 / perd. media $1336)
  PF             0.985        [criterio LIVE, informativo]
  DD chiusi      $11,705
  Net            $-780
  per anno       2026: $-780   (net <= 0: percentuali omesse)


STAGE 1 — controlli meccanici sulla List of Trades (102 trade, 2026-06-02 -> 2026-10-27)
  ?    periodo: 147 giorni di calendario fra il primo e l'ultimo trade (checklist: ~100)
  OK   contratti per trade: 1
  uscite, con i punti realizzati (confrontali con stop e target della SPEC):
       Profit Target      63 trade   punti: 40
       Stop Loss          30 trade   punti: -75
       VB-TIMEX            9 trade   punti: da -59.5 a 26.5 (9 valori)
    (uno stop o un target fisso deve avere un solo valore; con slippage negli stop il valore e' lo stop piu' lo slippage)
  orari d'ingresso (come li scrive MC: chiusura della barra del fill): 10:30×26 11:00×20 11:30×17 12:00×11 12:30×8 13:00×8 13:30×6 14:00×4 14:30×2
  OK   ingressi dentro 1030-1430: 0 fuori
  OK   trade al giorno: massimo 3 (SPEC: 3), 46 giorni con trade
  OK   flat la sera: 0 trade a cavallo di due date
  OK   scaling x10 (strategies/VaultBreak/reports/VB8_S1_100gg_x10.xlsx): 102 trade contro 102, stessi ingressi e uscite si, P&L x10 diverso su 0 trade

  ESITO DEI CONTROLLI: passa (le uscite in punti vanno confrontate a mano con la SPEC)
```
