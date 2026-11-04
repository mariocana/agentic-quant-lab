---
esito: passa
fase: oos
data: 2026-11-04
spec: strategies/OvernightBiasORB/SPEC.md
spec_commit: 78c8366f9d
report: strategies/OvernightBiasORB/reports/OBO_S5_OOS_2025-2026.xlsx
via: B
esito_script: passa
t: 2.19
dd: 18420
n: 166
---
# strategies/OvernightBiasORB/SPEC.md — fase 3, OOS: PASSA

## Il judge

**Misure registrate, il giudizio e' il gate marginale (via B).** 166 trade, avg $491 per NQ, t 2,19, WR 54,8%, R:R 1,27, DD $18.420. Disomogeneo: 2025 t 0,29, 2026 t 2,60; senza i 10 trade migliori t 0,26; trade peggiore $542,50 per micro, sopra i $500 della fase 2 (non e' un criterio di fase 3). Forward pulito dal 1/9/2026: 19 trade, +$14.290, t 1,00. Primo giudizio di lab.py errato (NON PASSA e report invalido): applicava alla via B i criteri della via A e leggeva i NO dei gate come preliminari. Corretto sulla regola del 29/10 in pipeline_semplice.md, dopo aver visto questo risultato.

## Avvisi

- blocco Pre-registrazione aggiunto dopo 98e1458: via e k si leggono anche nella prosa della SPEC a quel commit

## Output dello script

```
========================================================================
OBO_S5_OOS_2025-2026.xlsx
========================================================================

CONTROLLI PRELIMINARI  (se sbaglia qui, i numeri sotto non valgono)
  OK   Size: 1 contratto su tutti i 166 trade
  OK   Commissione: 7.50$ per Contract [Fixed 7.5$ per Contract]
  ?    Slippage: 0$ per Trade  (se e' 0, deve essere modellato nel codice)
  OK   Bar Magnifier: Enabled1 Minute
  ?    Compression: 15 Minutes   Symbol: @NQ   Point Value: $20
  ?    Range testato: 2025-01-03 -> 2026-11-04  (670 giorni)
  ?    Ultima barra 02:30 di OGGI: giorno incompleto, il session template NON si deduce. Verificalo sul grafico.

MISURE
  n trade        166
  avg trade      $490.60   +/- 223.67   (barra d'errore = sd/radice(n))
  t              2.19          <- quante barre separano l'avg dallo zero
  WR             54.8%
  R:R            1.27         (vinc. media $2533 / perd. media $1987)
  PF             1.547        [criterio LIVE, informativo]
  DD chiusi      $18,420
  Net            $81,440
  per anno       2025: 8%  2026: 92%
  anno max       92%        [criterio LIVE, informativo]


Via B: l'OOS non ha soglie proprie, qui si registrano le misure. Il giudizio e' il gate marginale (book); se fallisce, cimitero definitivo.
```
