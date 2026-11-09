---
esito: non passa
fase: book
data: 2026-11-09
spec: strategies/First5PreOpen/SPEC.md
spec_commit: 862759ff66
report: strategies/First5PreOpen/reports/F5P_S5_OOS_2025-2026.xlsx
via: B
esito_script: non passa
---
# strategies/First5PreOpen/SPEC.md — fase 3b, gate marginale: NON PASSA

## Il judge

Gate marginale, OOS 2025-2026: **non passa**. Book di riferimento quello della decisione di Mario del 04/11/2026 in pipeline_semplice.md (DPB 1 + Gold Asian Range pct1 1 + Overnight Bias ORB 1 micro; Gold con i costi del report e di MGC 25:2.60 come nel suo gate), che supera il 'DPB a 2 micro' della sezione dei criteri; candidata a 1 micro, dal 2025-01-01, 477 giorni, LucidFlex 50k. Book 59,6% iid e 67,1% contiguo, con la candidata 57,6% e 67,4%: Δ iid -2,0 pp contro la soglia di +2,0 (criterio 1 fallisce), Δ contiguo +0,2, giornata peggiore -$1.099 sopra la DLL di $1.200, avg OOS +$39 per micro con t 1,55. Il kill della fase 3 della SPEC scatta: cimitero, definitivo. Il verdetto OOS era asimmetrico per il run con input a 0 sul 22/06 -> 06/11/2026 (a verbale nel diario), ma un fallimento conta pieno; il tetto di 3 strategie del book non entra in gioco perche' il gate non passa.

## Comando

`gate_marginale.py docs/gate_marginale.py --book strategies/DriftPullback/reports/DPB_S5_OOS_2025-2026.xlsx:1 --book strategies/GoldAsianRange/reports/GAR_S5_OOS_A_pct1_2025-2026.xlsx:1:25:2.60 --book strategies/OvernightBiasORB/reports/OBO_S5_OOS_2025-2026.xlsx:1 --cand strategies/First5PreOpen/reports/F5P_S5_OOS_2025-2026.xlsx:1 --dal 2025-01-01`

## Output dello script

```
book : DPB_S5_OOS_2025-2026.xlsx x1 + GAR_S5_OOS_A_pct1_2025-2026.xlsx x1 + OBO_S5_OOS_2025-2026.xlsx x1
cand : F5P_S5_OOS_2025-2026.xlsx x1  |  251 trade OOS, avg $39.38 per micro, t 1.55
regole: LucidFlex 50k DLL 40%  |  477 giorni di calendario  |  20000 simulazioni, seed 20261029

                              iid   contiguo
book                        59.6%      67.1%
book + candidata            57.6%      67.4%
differenza (pp)             -2.0       +0.2

  ❌ 1. Δ iid >= +2.0 pp
  ✅ 2. Δ contiguo >= 0
  ✅ 3. giornata peggiore del book >= -DLL ($1200)
  ✅ 4. avg trade OOS della candidata > 0
  (giornata peggiore del book con la candidata: $-1099)

VERDETTO: NON ENTRA
```
