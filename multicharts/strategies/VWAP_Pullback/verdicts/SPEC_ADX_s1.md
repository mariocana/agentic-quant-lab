---
esito: passa
fase: s1
data: 2026-11-04
spec: strategies/VWAP_Pullback/SPEC_ADX.md
spec_commit: 78c8366f9d
report: strategies/VWAP_Pullback/reports/VWAPADX_S1_100gg.xlsx
via: A|B
esito_script: passa
t: 0.79
dd: 7725
n: 60
---
# strategies/VWAP_Pullback/SPEC_ADX.md — Stage 1, meccanica: PASSA

## Il judge

**Meccanica come da SPEC_ADX.** Preliminari: @NQ 1 min, Bar Magnifier spento come atteso su 1 minuto, $7,50 per lato con slippage 0, template 17:00-16:00 senza pause (il flat scatta alle 15:56 anche di venerdi'). Log contro List of Trades 60 su 60: ADX sempre >= 20 e in calo, ingressi alla barra dopo il segnale, TP e SL ai livelli del log. Solo long, max 1 al giorno, nessun overnight, x10 identico. Distanza dello stop misurata come chiede la SPEC: da 2,5 a 721,5 punti, 7 trade su 60 oltre 250 punti, trade peggiore $558 per micro.

## Avvisi

- blocco Pre-registrazione aggiunto dopo 811259f: via e k si leggono anche nella prosa della SPEC a quel commit

## Output dello script

```
========================================================================
VWAPADX_S1_100gg.xlsx
========================================================================

CONTROLLI PRELIMINARI  (se sbaglia qui, i numeri sotto non valgono)
  OK   Size: 1 contratto su tutti i 60 trade
  OK   Commissione: 7.50$ per Contract [Fixed 7.5$ per Contract]
  ?    Slippage: 0$ per Trade  (se e' 0, deve essere modellato nel codice)
  ?    Bar Magnifier: Disabled (grafico a 1 minuto: atteso)
  ?    Compression: 1 Minute   Symbol: @NQ   Point Value: $20
  ?    Range testato: 2026-05-01 -> 2026-11-04  (187 giorni)
  ?    Ultima barra 02:44 di OGGI: giorno incompleto, il session template NON si deduce. Verificalo sul grafico.

MISURE
  n trade        60
  avg trade      $150.75   +/- 190.28   (barra d'errore = sd/radice(n))
  t              0.79          <- quante barre separano l'avg dallo zero
  WR             70.0%
  R:R            0.57         (vinc. media $871 / perd. media $1530)
  PF             1.328        [criterio LIVE, informativo]
  DD chiusi      $7,725
  Net            $9,045
  per anno       2026: 100%
  anno max       100%        [criterio LIVE, informativo]


STAGE 1 — controlli meccanici sulla List of Trades (60 trade, 2026-05-01 -> 2026-11-03)
  ?    periodo: 186 giorni di calendario fra il primo e l'ultimo trade (checklist: ~100)
  OK   contratti per trade: 1
  uscite, con i punti realizzati (confrontali con stop e target della SPEC):
       L-TP               41 trade   punti: da 1 a 141.25 (37 valori)
       L-SL               15 trade   punti: da -278.5 a -1.5 (15 valori)
       EOD-L               4 trade   punti: -120.5, -60.25, -18, 31.5
    (uno stop o un target fisso deve avere un solo valore; con slippage negli stop il valore e' lo stop piu' lo slippage)
  orari d'ingresso (come li scrive MC: chiusura della barra del fill): 09:12×1 09:17×1 09:18×1 09:30×1 09:31×1 09:37×1 09:39×1 09:41×1 09:44×1 09:45×1 09:52×1 09:54×2 09:57×1 10:00×2 10:01×1 10:02×1 10:05×2 10:10×1 10:20×1 10:24×1 10:26×1 10:29×1 10:32×1 10:48×1 10:49×3 10:50×1 10:52×1 10:57×1 10:59×1 11:01×1 11:07×2 11:14×1 11:15×1 11:20×1 11:22×1 11:25×1 11:26×1 11:27×1 11:36×1 11:38×1 11:43×1 11:48×1 11:53×1 12:00×1 12:02×1 12:14×1 12:16×1 13:13×1 13:41×1 14:08×1 14:32×1 15:00×1 15:35×1 15:48×1
  OK   ingressi dentro 0900-1700: 0 fuori
  OK   trade al giorno: massimo 1 (SPEC: 1), 60 giorni con trade
  OK   flat la sera: 0 trade a cavallo di due date
  OK   scaling x10 (strategies/VWAP_Pullback/reports/VWAPADX_S1_100gg_x10.xlsx): 60 trade contro 60, stessi ingressi e uscite si, P&L x10 diverso su 0 trade

  ESITO DEI CONTROLLI: passa (le uscite in punti vanno confrontate a mano con la SPEC)
```
