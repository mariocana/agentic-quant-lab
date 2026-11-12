---
esito: passa
fase: is
data: 2026-11-09
spec: strategies/First5PreOpen/SPEC.md
spec_commit: 862759ff66
report: strategies/First5PreOpen/reports/F5P_S2_IS_2020-2024.xlsx
via: B
esito_script: passa
t: 2.38
dd: 17115
n: 642
---
# strategies/First5PreOpen/SPEC.md — fase 2, IS: PASSA

## Il judge

IS 2020-2024, via B: **passa**. Prima era sospeso: check_report segnava NO perche' il primo trade e' del 2020-01-09 e TradeStartEL e' 1200101. A Mario e' stato chiesto se il Data Range del grafico parte il 2020-01-01 o prima, e lui ha risposto di si'. Lo Start Date di Settings e' il primo ingresso (2020-01-09 08:40), non l'inizio del grafico, e il desk ha corretto check_report (commit 1d6829e): uno scarto di 8-31 giorni ora e' un avviso. Gli altri preliminari sono come da SPEC: @NQ 5 min, BM 1 min, 7,5$ per contratto e slippage 0. Ci sono 642 ingressi tutti alle 08:40, uscite a stop o alle 15:05, e l'ultimo trade e' del 2024-12-27, dentro TradeEndEL 1241231. Risultato: t 2,38 > 1,16 (k = 5) e trade peggiore $273 per micro <= $500, quindi il kill non scatta. n 642 e WR 24,5% stanno nelle bande del proxy, e t 2,38 sta nell'attesa della SPEC (1,5-2,4).

## Output dello script

```
========================================================================
F5P_S2_IS_2020-2024.xlsx
========================================================================

CONTROLLI PRELIMINARI  (se sbaglia qui, i numeri sotto non valgono)
  OK   Size: 1 contratto su tutti i 642 trade
  OK   Commissione: 7.50$ per Contract [Fixed 7.5$ per Contract]
  ?    Slippage: 0$ per Trade  (se e' 0, deve essere modellato nel codice)
  OK   Bar Magnifier: Enabled1 Minute
  ?    Compression: 5 Minutes   Symbol: @NQ   Point Value: $20
  ?    Range testato: 2020-01-09 -> 2026-11-09  (2496 giorni)
  ?    TradeStartEL chiede 2020-01-01 ma il primo trade e' del 2020-01-09 (8 giorni): controlla sul grafico che il Data Range copra la finestra.
  ?    Ultima barra 15:40 di OGGI: giorno incompleto, il session template NON si deduce. Verificalo sul grafico.

MISURE
  n trade        642
  avg trade      $185.63   +/- 77.84   (barra d'errore = sd/radice(n))
  t              2.38          <- quante barre separano l'avg dallo zero
  WR             24.5%
  R:R            4.11         (vinc. media $3046 / perd. media $740)
  PF             1.332        [criterio LIVE, informativo]
  DD chiusi      $17,115
  Net            $119,175
  per anno       2020: 2%  2021: 17%  2022: 36%  2023: 4%  2024: 41%
  anno max       41%        [criterio LIVE, informativo]


Via B (pipeline_semplice.md, fase 2):
  OK   t > 1.16  (max(0,5, edge zero con k = 5))   t = 2.38
  OK   trade peggiore <= $500 per micro (report / 10)   $273
  (meccanica corretta: la dice il verdetto s1)

  VERDETTO: PASSA
```
