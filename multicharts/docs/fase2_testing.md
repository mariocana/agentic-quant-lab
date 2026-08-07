# Fase 2 — Processo di test nel Tester di MetaTrader 5

Obiettivo: portare ogni EA dal codice a un giudizio "profittevole / da scartare",
e per i sopravvissuti verificare la compatibilità **prop** (con `Include/PropGuard.mqh`).

Il flusso segue il diagramma: *Idea → Data → Implementation → Backtest → Robustness → Diversification → Incubation → Live/Prop*.

---

## 0. Setup del Tester (una volta)

- **Dati**: scaricare lo storico del simbolo (Symbols → Bars/Ticks). Per gli EA
  tick-based/pending usare **"Every tick based on real ticks"**; per gli EA che
  lavorano solo a fine barra basta **"1 minute OHLC"** (più veloce).
- **Spread**: usare **spread reale** (o fisso realistico), mai "current".
- **Commissioni/Slippage**: impostarle nel simbolo o nel test (es. indici/forex
  del tuo broker). Molti EA nostri ne risentono: vanno incluse.
- **Deposito/Valuta/Leva**: coerenti con il conto prop target (es. 10.000, USD).
- **Modello di ottimizzazione**: genetico per spazi grandi, completo per pochi input.

---

## 1. Split In-Sample / Out-of-Sample

- **In-Sample (IS)**: ottimizzazione (es. 2015–2021).
- **Out-of-Sample (OOS)**: verifica su dati mai usati (es. 2022–oggi).
- Usare il **Forward** automatico del Tester (es. 1/3 forward) per avere l'OOS
  senza rifare a mano.
- Regola d'oro: se il forward crolla rispetto all'IS → **overfit**, si scarta.

---

## 2. Criteri di ottimizzazione

Non massimizzare solo il **Net Profit**. Preferire criteri robusti:
- **Profit Factor** ≥ 1.3 (meglio ≥ 1.5)
- **Custom**: es. `Net Profit × (1 − DD%)` o Sharpe, per penalizzare il drawdown.
- **# trade** sufficiente (statistica): almeno ~100 trade nel periodo IS.

## 3. Metriche minime di accettazione (soglie di partenza, da tarare)

| Metrica | Soglia |
|---|---|
| Profit Factor | ≥ 1.3 |
| Max Drawdown % | ≤ 20–25% |
| # trade (IS) | ≥ 100 |
| Forward PF / IS PF | ≥ 0.6 (tiene fuori IS) |
| Recovery Factor | ≥ 3 |

---

## 4. Robustezza (per chi passa IS+OOS)

- **Walk-Forward Analysis** (ri-ottimizzazione a finestre mobili).
- **Monte Carlo** sui trade (randomizzazione ordine/skip) → distribuzione del DD.
- **Stress test**: +spread, +slippage, +commissioni; shift degli orari ±1h
  (i nostri EA usano ora server → verificare la sensibilità al fuso).
- **Stabilità dei parametri**: il profitto deve reggere anche con input **vicini**
  a quelli ottimi (mappa 3D del Tester "liscia", non a picchi).
- **Multi-mercato / multi-TF** dove ha senso.

## 5. Diversificazione

- Tenere solo EA con **bassa correlazione** tra le equity.
- Comporre un piccolo portafoglio (simboli/logiche diverse).

## 6. Incubazione → Live/Prop

- **Forward demo** (paper) per qualche settimana.
- Solo poi: attivare `PropGuard` (`InpUseProp=true`) e verificare in backtest che
  **non violi** daily loss / max DD della prop scelta, e che il **target** sia
  raggiungibile nei giorni richiesti.

---

## 7. Matrice per-EA (punto di partenza per i test)

> "Ottimizzare" = input principali da far variare nel Tester. I valori fine-tuned
> documentati nel codice sono un **seme**, non un vincolo.

| EA | Simbolo | TF | Da ottimizzare | Note |
|---|---|---|---|---|
| m7dr/DR_IDR_Breakout | NAS100/US30 | M5 | InpLevel, InpRR, sessioni | DST-aware, chiusura intraday |
| unger/nasdaq/Strategy1 | NAS100 | M15 | SMA, offset punti, orari | SL/TP monetari |
| unger/nasdaq/Strategy2 | NAS100 | M15 | ATR mult, momentum, finestre | breakeven |
| vitro/analitic_spread_trading/R110 | coppie corr. | H1 | soglia %, lookback | serve Symbol B |
| vitro/fractal_rsi_scalping | EURUSD/USDJPY | M1–M5 | RSI, fractal wing, lookback | calibrare RVO-like |
| vitro/renko RenkoEMA_CCI | EURUSD/USDJPY | (M1 base) | brick, EMA, CCI, SL/TP | Renko sintetico |
| vitro/trend_following_neutral_zone R109 | EURUSD/GBPUSD | M5 | zona 144, orari, SL/TP | zona statica |
| bb_2bands_mr | forex | vari | periodi/dev bande, RSI | tick vs new-bar |
| us30_rvo | US30 | M1 | RVO, HawkEye, guardie | calibrare RVO su TV |
| turtle_breakout | vari | H1/D1 | canali, ATR mult | trend following |
| trap_12pm | EURUSD | M15 | orari cattura/breakout | fuso broker |
| death_cross | vari | D1/intraday | medie, modo, filtro volume | trend/contrarian |
| range_breakout/MultiRange | indici/FX | intraday | range attivi, orari, TP | multi-sessione |
| seven_trigger | vari | vari | trigger 1-7, mode, exit | breakout/reversal |
| ivb | forex/indici | M5 | box orari, entryMode, TP | opening range |
| **unger/trading_system_supremacy/** (SA) | vedi sotto | vedi sotto | pattern LY/LN/SY/SN + orari | usare i 42 pattern |

### Famiglia SA (pattern) — semi documentati
| EA | Simbolo/TF suggeriti | Semi (dai commenti) |
|---|---|---|
| TrendFollowing_SA | EU M15 | LY=6 SY=4 LN=18 SN=19; orari 4/13:30 |
| CounterTrend_SA | GBPUSD M30 | LY=14 SY=15 LN=40 SN=40; duration=8 |
| Bias_SA | EU H1 | barre LE/LX/SE/SX da ottimizzare |
| DaxFirstHour_SA | DAX M5 | dailyfactor<0.75; 09:00-09:55 |
| FXFader_SA | GBPUSD H1 | BarOfDay 3-21; SL 100 tick |
| GapFade_SA | Gold/indici | soglia gap, flat a fine sessione |
| NightFIB_SA | FTSEMIB | 17:30→09:20; gap/nuovo minimo |
| WeeklyBump_SA | future | W1; wf/cong/perc/ATR |
| Stop Progressivi | vari | Gain/Loss + fattori decadimento |
| IntraToOverNight_SA | vari | check 16:45; tieni se in profitto |
| ESCounter_SA | ES | overnight; nuovo minimo N giorni |

---

## Priorità suggerita di test

1. **Breakout/trend con logica solida e pochi input**: Turtle, DR/IDR, MultiRange,
   Trap12PM, DaxFirstHour — veloci da validare.
2. **Famiglia SA a pattern**: alto potenziale ma richiede ottimizzazione ampia
   (usare il genetico + i semi documentati).
3. **Mean-reversion / scalping**: BB2Bands, NeutralZone, FXFader, FractalRSI —
   sensibili a spread/commissioni: testare con costi realistici.
4. **Da calibrare prima**: US30-RVO (allineare l'RVO a TradingView), Renko
   (convenzione brick), R110 spread (Symbol B).
