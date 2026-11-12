---
esito: non passa
fase: is
data: 2026-11-04
spec: strategies/VWAP_Pullback/SPEC_ADX.md
spec_commit: 78c8366f9d
report: strategies/VWAP_Pullback/reports/VWAPADX_S2_IS_2020-2024.xlsx
via: B
esito_script: non passa
t: 0.58
dd: 20530
n: 605
---
# strategies/VWAP_Pullback/SPEC_ADX.md — fase 2, IS: NON PASSA

## Il judge

**Non passa ne' la via A ne' la via B: t 0,58** (soglie 2 e 1,03), 605 trade, avg $21,95 per NQ, WR 64%, R:R 0,60, trade peggiore $601 per micro (tetto $500). Dentro l'attesa bassa (t 0,5-1,5), lontano dai numeri dichiarati dall'autore (WR 82%, avg $300). 2020 negativo. Preliminari come da SPEC: @NQ 1 min, 2020-01-03 -> 2024-12-31, template 17:00-16:00, $7,50 per lato. Il report OOS arrivato insieme non e' stato aperto ne' copiato nel repo.

## Avvisi

- blocco Pre-registrazione aggiunto dopo 811259f: via e k si leggono anche nella prosa della SPEC a quel commit

## Output dello script

```
========================================================================
VWAPADX_S2_IS_2020-2024.xlsx
========================================================================

CONTROLLI PRELIMINARI  (se sbaglia qui, i numeri sotto non valgono)
  OK   Size: 1 contratto su tutti i 605 trade
  OK   Commissione: 7.50$ per Contract [Fixed 7.5$ per Contract]
  ?    Slippage: 0$ per Trade  (se e' 0, deve essere modellato nel codice)
  ?    Bar Magnifier: Disabled (grafico a 1 minuto: atteso)
  ?    Compression: 1 Minute   Symbol: @NQ   Point Value: $20
  ?    Range testato: 2020-01-03 -> 2024-12-31  (1824 giorni)
  ?    Ultima barra 16:00 -> session template **Globex 24h**

MISURE
  n trade        605
  avg trade      $21.95   +/- 37.52   (barra d'errore = sd/radice(n))
  t              0.58          <- quante barre separano l'avg dallo zero
  WR             64.0%
  R:R            0.60         (vinc. media $520 / perd. media $863)
  PF             1.071        [criterio LIVE, informativo]
  DD chiusi      $20,530
  Net            $13,280
  per anno       2020: -72%  2021: 20%  2022: 20%  2023: 67%  2024: 65%
  anno max       67%        [criterio LIVE, informativo]

Gate 2 - IS (fase 2): l'edge esiste?
  NO   t >= 2           t = 0.58
  OK   WR >= 55%        WR = 64.0%
  OK   R:R 0,5-1        R:R = 0.60

  VERDETTO: NON PASSA -> cimitero


Via A|B: la via A non passa, si giudica con la via B.

Via B (pipeline_semplice.md, fase 2):
  NO   t > 1.03  (max(0,5, edge zero con k = 4))   t = 0.58
  NO   trade peggiore <= $500 per micro (report / 10)   $601
  (meccanica corretta: la dice il verdetto s1)

  VERDETTO: NON PASSA -> cimitero
```
