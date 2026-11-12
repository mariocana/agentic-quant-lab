---
esito: passa
fase: book
data: 2026-11-02
spec: strategies/VaultBreak/SPEC_v8.md
spec_commit: fe91c17e88
report: strategies/VaultBreak/reports/VB8_S5_OOS_2025-2026.xlsx
via: A|B
esito_script: passa
---
# strategies/VaultBreak/SPEC_v8.md — fase 3b, gate marginale: PASSA

## Il judge

**Entra per lo script: Δ iid +3,0 pp, Δ contiguo +7,7 pp, giornata peggiore -$1.104, avg $9,35 per micro.** Book DPB OOS a 2 micro, candidata a 1 micro, nessun --dal. Diagnostica fuori verdetto, solo 2026 (--dal 2026-01-01, dopo la correzione del bug di --dal): Δ iid -1,9 pp, Δ contiguo +1,4, avg -$0,84 per micro: l'aumento viene dal 2025. Verdetto asimmetrico: entra solo come prova dal vivo, e il live e' il vero OOS.

## Avvisi

- blocco Pre-registrazione aggiunto dopo 811259fcf3: via e k si leggono anche nella prosa della SPEC a quel commit

## Comando

`gate_marginale.py docs/gate_marginale.py --book strategies/DriftPullback/reports/DPB_S5_OOS_2025-2026.xlsx:2 --cand strategies/VaultBreak/reports/VB8_S5_OOS_2025-2026.xlsx:1`

## Output dello script

```
book : DPB_S5_OOS_2025-2026.xlsx x2
cand : VB8_S5_OOS_2025-2026.xlsx x1  |  482 trade OOS, avg $9.35 per micro, t 2.07
regole: LucidFlex 50k DLL 40%  |  461 giorni di calendario  |  20000 simulazioni, seed 20261029

                              iid   contiguo
book                        42.1%      58.4%
book + candidata            45.1%      66.1%
differenza (pp)             +3.0       +7.7

  ✅ 1. Δ iid >= +2.0 pp
  ✅ 2. Δ contiguo >= 0
  ✅ 3. giornata peggiore del book >= -DLL ($1200)
  ✅ 4. avg trade OOS della candidata > 0
  (giornata peggiore del book con la candidata: $-1104)

VERDETTO: ENTRA NEL BOOK
```
