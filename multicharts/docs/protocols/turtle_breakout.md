# Protocollo di test — Turtle Breakout

EA: `turtle_breakout/TurtleBreakout_EA.mq5`
Tipo: trend-following, breakout di canale (Donchian) + filtro SMA200 + stop ATR.

---

## 1. Simboli e timeframe

Il Turtle rende su strumenti che **trendano**. Test consigliati (in ordine):
- **XAUUSD (Gold)** — H1 e D1
- **NAS100 / US100** — H1
- **EURUSD** — H1 (per vedere se regge anche su FX major)

TF primario: **H1**. Poi ripetere su **D1** (Turtle "classico").

## 2. Periodo dati (IS / OOS)

- **In-Sample**: 2016-01 → 2021-12 (ottimizzazione)
- **Out-of-Sample**: 2022-01 → oggi (verifica)
- In alternativa: tutto 2016→oggi con **Forward = 1/3** (il Tester fa lo split da solo).
- Modello: **1 minute OHLC** va bene (l'EA lavora a fine barra). Real ticks solo per conferma finale.

## 3. Costi (obbligatori)

- Spread reale + **commissione** del tuo broker (Gold/indici/FX).
- Slippage realistico. Senza costi il breakout sembra sempre migliore di quanto sia.

## 4. Ottimizzazione — 2 fasi

**Rischio fisso durante l'ottimizzazione**: `InpRiskPercent = 1.0`, `InpUseFixedLots = false`
(non ottimizzare il rischio: scala linearmente e falsa il confronto).
Fissa anche `InpATRPeriod = 20` e `InpTrendMAPeriod = 200` in fase 1.

### Fase 1 — coarse (3 input)
| Input | Da | A | Step |
|---|---|---|---|
| InpEntryBars | 20 | 60 | 5 |
| InpExitBars  | 10 | 40 | 5 |
| InpATRmult   | 1.5 | 4.0 | 0.5 |

Modello ottimizzazione: **genetico**, criterio **Recovery Factor** (o Sharpe).

### Fase 2 — fine (attorno ai migliori)
- Restringere i range attorno ai valori vincenti (es. EntryBars ±5, ATRmult ±0.5).
- Aggiungere `InpTrendMAPeriod` 100→300 step 50 e `InpATRPeriod` 14→28 step 7
  **solo se** la Fase 1 ha dato qualcosa di solido.

## 5. Cosa guardare nel report

Accetta l'EA per il passo successivo solo se, **in Out-of-Sample**:
- **Profit Factor** ≥ 1.3
- **Max Drawdown** ≤ ~20–25%
- **# trade** ≥ 100 (nel periodo IS)
- **Forward/IS**: il forward NON deve crollare (PF forward ≥ ~0.6 × PF IS)
- Mappa dei parametri **liscia** (profitto stabile con input vicini, non un picco isolato)

## 6. Note specifiche del Turtle

- L'uscita è sul **canale opposto** (`InpExitBars`) + stop **ATR×mult**: exit più corto
  dell'entry (es. 40/20) = stile System 1 classico.
- Su D1 servono molti anni di dati per avere abbastanza trade.
- Se i trade sono pochissimi su FX, è normale: il Turtle è nato su future/commodities.

---

## 7. Prossimo passo

Lancia la **Fase 1** su **XAUUSD H1** (2016→2021, forward 1/3) e incollami il report
(o gli screenshot): i migliori set + PF/DD/#trade IS e forward. Da lì decidiamo se
passare alla Fase 2 o cambiare simbolo/TF.
