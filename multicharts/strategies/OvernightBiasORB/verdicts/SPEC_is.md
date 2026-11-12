---
esito: passa
fase: is
data: 2026-11-03
spec: strategies/OvernightBiasORB/SPEC.md
spec_commit: 78c8366f9d
report: strategies/OvernightBiasORB/reports/OBO_S2_IS_2020-2024.xlsx
via: B
esito_script: passa
t: 4.51
dd: 16555
n: 455
---
# strategies/OvernightBiasORB/SPEC.md — fase 2, IS: PASSA

## Il judge

**Passa la via B con margine: t 4,51** (soglia 0,5), 455 trade, avg $401 per NQ ($40 per micro), WR 53,8%, R:R 1,45, trade peggiore $328 per micro (tetto $500). Molto sopra l'attesa (t 1-2,5). Robusto: cinque anni su cinque con t fra 1,48 e 2,99, long t 3,14 e short t 3,23, senza i 10 trade migliori t 3,39. 12 uscite End of Day (SetExitOnClose nelle sedute corte). Preliminari come da SPEC: @NQ 15 min Globex, 2020-01-08 -> 2024-12-31, $7,50 per lato. Il 2020-2024 sta nell'OOS dichiarato dall'autore, pubblicato dopo averlo visto: verdetto OOS asimmetrico, forward pulito dal 1/9/2026.

## Avvisi

- blocco Pre-registrazione aggiunto dopo 98e1458: via e k si leggono anche nella prosa della SPEC a quel commit

## Output dello script

```
========================================================================
OBO_S2_IS_2020-2024.xlsx
========================================================================

CONTROLLI PRELIMINARI  (se sbaglia qui, i numeri sotto non valgono)
  OK   Size: 1 contratto su tutti i 455 trade
  OK   Commissione: 7.50$ per Contract [Fixed 7.5$ per Contract]
  ?    Slippage: 0$ per Trade  (se e' 0, deve essere modellato nel codice)
  OK   Bar Magnifier: Enabled1 Minute
  ?    Compression: 15 Minutes   Symbol: @NQ   Point Value: $20
  ?    Range testato: 2020-01-08 -> 2024-12-31  (1819 giorni)
  ?    Ultima barra 16:00 -> session template **Globex 24h**

MISURE
  n trade        455
  avg trade      $401.49   +/- 89.08   (barra d'errore = sd/radice(n))
  t              4.51          <- quante barre separano l'avg dallo zero
  WR             53.8%
  R:R            1.45         (vinc. media $1832 / perd. media $1267)
  PF             1.686        [criterio LIVE, informativo]
  DD chiusi      $16,555
  Net            $182,680
  per anno       2020: 14%  2021: 13%  2022: 26%  2023: 11%  2024: 36%
  anno max       36%        [criterio LIVE, informativo]


Via B (pipeline_semplice.md, fase 2):
  OK   t > 0.50  (max(0,5, edge zero con k = 1))   t = 4.51
  OK   trade peggiore <= $500 per micro (report / 10)   $328
  (meccanica corretta: la dice il verdetto s1)

  VERDETTO: PASSA
```
