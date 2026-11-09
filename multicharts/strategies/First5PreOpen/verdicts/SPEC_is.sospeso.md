---
esito: sospeso
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
# strategies/First5PreOpen/SPEC.md — fase 2, IS: SOSPESO

## Il judge

IS 2020-2024, via B: resta **sospeso**, ma ora per un limite dello strumento e non per una domanda aperta. Domanda a Mario: il Data Range del grafico parte il 2020-01-01 o prima? Risposta di Mario: si'. Il NO di check_report (dati dal 2020-01-09 contro TradeStartEL 1200101) e' quindi un falso allarme: lo Start Date del foglio Settings e' il primo ingresso (2020-01-09 08:40), come in tutti i report di First5PreOpen, s1 compreso. lab.py pero' rifiuta passa con un preliminare NO ('un preliminare e' NO: --esito invalido'), e un rigiro darebbe lo stesso NO. Il verbale resta sospeso finche' il controllo di check_report non viene corretto o la regola non si sblocca a mano. Esito dello script: passa, con t 2,38 > 1,16 (k = 5), trade peggiore $273 per micro <= $500, n 642 e WR 24,5%; ultimo trade il 2024-12-27, dentro TradeEndEL 1241231.

## Avvisi

- un controllo preliminare e' NO: il report e' invalido, va rigirato con le impostazioni giuste (esito obbligato: invalido)

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
  NO   TradeStartEL chiede 2020-01-01 ma i dati partono il 2020-01-09: 8 giorni mancanti. Il range del GRAFICO vince, allargalo e rigira.
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
