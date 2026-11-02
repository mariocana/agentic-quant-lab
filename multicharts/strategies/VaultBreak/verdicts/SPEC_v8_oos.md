---
esito: passa
fase: oos
data: 2026-11-02
spec: strategies/VaultBreak/SPEC_v8.md
spec_commit: fe91c17e88
report: strategies/VaultBreak/reports/VB8_S5_OOS_2025-2026.xlsx
via: A|B
esito_script: passa
t: 2.07
dd: 12965
n: 482
---
# strategies/VaultBreak/SPEC_v8.md — fase 3, OOS: PASSA

## Il judge

**Passa per lo script (t 2,07, WR 67,4%, R:R 0,59, 482 trade), ma tutto il risultato e' nel 2025.** 2025 H1 t 2,74 e H2 t 1,90; 2026 H1 t 0,40, 2026 H2 t -0,79; il 2026 intero fa -$2.050. Forward pulito dal 13/10/2026: 11 trade, -$5.165. Preliminari come da SPEC (30 min Globex, $7,50 per lato, slippage 0, 2025-01-03 -> oggi). OOS contaminato dai parametri dell'autore: verdetto asimmetrico, il passa vale solo come ingresso in prova dal vivo dopo il gate marginale.

## Avvisi

- blocco Pre-registrazione aggiunto dopo 811259fcf3: via e k si leggono anche nella prosa della SPEC a quel commit

## Output dello script

```
========================================================================
VB8_S5_OOS_2025-2026.xlsx
========================================================================

CONTROLLI PRELIMINARI  (se sbaglia qui, i numeri sotto non valgono)
  OK   Size: 1 contratto su tutti i 482 trade
  OK   Commissione: 7.50$ per Contract [Fixed 7.5$ per Contract]
  ?    Slippage: 0$ per Trade  (se e' 0, deve essere modellato nel codice)
  OK   Bar Magnifier: Enabled1 Minute
  ?    Compression: 30 Minutes   Symbol: @NQ   Point Value: $20
  ?    Range testato: 2025-01-03 -> 2026-11-02  (668 giorni)
  ?    Ultima barra 13:00 di OGGI: giorno incompleto, il session template NON si deduce. Verificalo sul grafico.

MISURE
  n trade        482
  avg trade      $93.45   +/- 45.24   (barra d'errore = sd/radice(n))
  t              2.07          <- quante barre separano l'avg dallo zero
  WR             67.4%
  R:R            0.59         (vinc. media $753 / perd. media $1272)
  PF             1.226        [criterio LIVE, informativo]
  DD chiusi      $12,965
  Net            $45,045
  per anno       2025: 105%  2026: -5%
  anno max       105%        [criterio LIVE, informativo]

Gate 3 - OOS (fase 3): l'edge regge fuori campione?
  OK   t >= 1,3         t = 2.07
  OK   WR >= 50%        WR = 67.4%
  OK   R:R 0,5-1        R:R = 0.59
  OK   DD <= 1,5x IS    DD = $12,965

  VERDETTO: PASSA
```
