---
esito: passa
fase: book
data: 2026-11-04
spec: strategies/OvernightBiasORB/SPEC.md
spec_commit: 78c8366f9d
report: strategies/OvernightBiasORB/reports/OBO_S5_OOS_2025-2026.xlsx
via: B
esito_script: passa
---
# strategies/OvernightBiasORB/SPEC.md — fase 3b, gate marginale: PASSA

## Il judge

**Entra per lo script: Δ iid +2,9 pp, Δ contiguo +6,5 pp, giornata peggiore -$1.104, avg $49,06 per micro.** Book DPB OOS a 2 micro, candidata a 1 micro. Controllo fuori verdetto, solo 2026: Δ iid +7,9, contiguo +17,1; il 2025 da solo vale poco (t 0,29). Risultato concentrato: senza i 10 trade migliori t 0,26. Verdetto asimmetrico: entra solo come prova dal vivo, forward pulito dal 1/9/2026. Il posto nel book si decide con le altre candidate.

## Avvisi

- blocco Pre-registrazione aggiunto dopo 98e1458: via e k si leggono anche nella prosa della SPEC a quel commit

## Comando

`gate_marginale.py docs/gate_marginale.py --book strategies/DriftPullback/reports/DPB_S5_OOS_2025-2026.xlsx:2 --cand strategies/OvernightBiasORB/reports/OBO_S5_OOS_2025-2026.xlsx:1`

## Output dello script

```
book : DPB_S5_OOS_2025-2026.xlsx x2
cand : OBO_S5_OOS_2025-2026.xlsx x1  |  166 trade OOS, avg $49.06 per micro, t 2.19
regole: LucidFlex 50k DLL 40%  |  460 giorni di calendario  |  20000 simulazioni, seed 20261029

                              iid   contiguo
book                        42.0%      58.8%
book + candidata            44.9%      65.2%
differenza (pp)             +2.9       +6.5

  ✅ 1. Δ iid >= +2.0 pp
  ✅ 2. Δ contiguo >= 0
  ✅ 3. giornata peggiore del book >= -DLL ($1200)
  ✅ 4. avg trade OOS della candidata > 0
  (giornata peggiore del book con la candidata: $-1104)

VERDETTO: ENTRA NEL BOOK
```
