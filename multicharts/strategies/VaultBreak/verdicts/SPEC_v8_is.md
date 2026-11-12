---
esito: passa
fase: is
data: 2026-11-02
spec: strategies/VaultBreak/SPEC_v8.md
spec_commit: fe91c17e88
report: strategies/VaultBreak/reports/VB8_S2_IS_2020-2024.xlsx
via: A
esito_script: passa
t: 2.78
dd: 17490
n: 1125
---
# strategies/VaultBreak/SPEC_v8.md — fase 2, IS: PASSA

## Il judge

**Passa la via A**: t 2,78, WR 65,3%, R:R 0,64 su 1.125 trade, sopra l'attesa (t 1-2,5). Preliminari come da SPEC: @NQ 30 min Globex (ultima barra 16:00), 2020-01-02 -> 2024-12-31, $7,50 per lato con slippage 0. Edge in calo ogni anno: 2024 t 0,45, seconda meta' dell'IS t 1,33 contro 2,64. OOS 2025-26 contaminato (parametri dell'autore): verdetto asimmetrico, forward pulito dal 13/10/2026.

## Avvisi

- blocco Pre-registrazione aggiunto dopo 811259fcf3: via e k si leggono anche nella prosa della SPEC a quel commit

## Output dello script

```
========================================================================
VB8_S2_IS_2020-2024.xlsx
========================================================================

CONTROLLI PRELIMINARI  (se sbaglia qui, i numeri sotto non valgono)
  OK   Size: 1 contratto su tutti i 1125 trade
  OK   Commissione: 7.50$ per Contract [Fixed 7.5$ per Contract]
  ?    Slippage: 0$ per Trade  (se e' 0, deve essere modellato nel codice)
  OK   Bar Magnifier: Enabled1 Minute
  ?    Compression: 30 Minutes   Symbol: @NQ   Point Value: $20
  ?    Range testato: 2020-01-02 -> 2024-12-31  (1825 giorni)
  ?    Ultima barra 16:00 -> session template **Globex 24h**

MISURE
  n trade        1125
  avg trade      $76.76   +/- 27.65   (barra d'errore = sd/radice(n))
  t              2.78          <- quante barre separano l'avg dallo zero
  WR             65.3%
  R:R            0.64         (vinc. media $694 / perd. media $1086)
  PF             1.204        [criterio LIVE, informativo]
  DD chiusi      $17,490
  Net            $86,350
  per anno       2020: 35%  2021: 22%  2022: 15%  2023: 20%  2024: 8%
  anno max       35%        [criterio LIVE, informativo]

Gate 2 - IS (fase 2): l'edge esiste?
  OK   t >= 2           t = 2.78
  OK   WR >= 55%        WR = 65.3%
  OK   R:R 0,5-1        R:R = 0.64

  VERDETTO: PASSA


Via A|B: passa la via A, la via B non serve.
```
