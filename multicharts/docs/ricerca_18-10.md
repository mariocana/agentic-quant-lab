# Ricerca del 18/10/2026: il profilo che cerchiamo non esiste in letteratura

Due ricerche sul web aperto, su intraday mean reversion e su intraday momentum/pullback nei
futures su indice. **Risultato negativo, ma informativo.**

## 1. Nessun edge intraday frequente sopravvive ai costi, nelle fonti

Nessun backtest credibile mostra un edge strutturale intraday durevole su ES/NQ/YM per
operativita' frequente **dopo costi realistici**. L'esempio piu' chiaro e' uno studio 2026 su
cripto: reversal da **1,3 punti base per trade** contro un round-turn piu' economico da **5
punti base**. L'edge c'e' e **vale un quarto del costo**.

> E esattamente il nostro pattern: eccesso misurato fra −0,6 e +5,3 pp, e i costi che se lo
> mangiano.

## 2. E la cosa che conta: **il profilo prop non e' un profilo di segnale**

Il corso chiede **WR 54-72% con R:R 0,5-1**. La letteratura sul momentum intraday replicato
seriamente dice l'opposto:

| fonte | WR | payoff |
|---|---|---|
| replica Quantitativo su ES/NQ | **36-39%** | **2,09** |
| linee guida generiche | — | «minimo 2:1» |
| backtest vendor con WR alto (82%, 78%) | alto | **ma perdite medie piu' grandi delle vincite**, DD 30% |

**Il profilo ad alto win rate e basso R:R non si trova come proprieta' di un segnale.** Dove
compare, o non e' verificato, o arriva con drawdown profondi.

### Perche', e cosa cambia per noi

Perche' **quel profilo lo impone l'uscita, non l'ingresso**. Prendi un segnale con un edge
modesto, metti il target vicino e lo stop lontano, e ottieni WR alto e R:R basso. L'**eccesso
sul caso resta identico** — e invariante alla geometria, e' il principio che usiamo da due
giorni — ma la **forma** cambia.

> **Cercare in letteratura «una strategia ad alto win rate e basso R:R» e' cercare una cosa
> che non esiste come tale.** Esistono segnali con un eccesso misurabile. Il profilo lo
> costruisci tu col bracket.

**Conseguenza operativa**: smettere di cercare *strategie* con quel profilo e cercare
**segnali con un eccesso sul caso misurabile**, di qualunque forma. Poi la forma la si impone.

## 3. Cosa resta da provare, in ordine di costo

| | costo | nota |
|---|---|---|
| **DriftPullback portata su @YM** | **un run** | stessa logica, stop riscalato per ATR (129 pt). E' l'unico segnale con eccesso dimostrato che abbiamo |
| Reversal pomeridiano (Xu-Zhu) | ~mezza giornata | si sovrappone a DriftPullback: la correlazione va misurata, non assunta |
| Evento macro (8:30 CT) | ~un giorno | gia' sul board, mai sviluppato. Strutturale (liquidita' che si ritira e torna su un rilascio noto) e **cade nell'ora libera**. Ma 2-3 volte a settimana, non 2 al giorno |

## Fonti

- [Does Overnight News Explain Overnight Returns?](https://arxiv.org/pdf/2507.04481)
- [Short-horizon mean reversion in cryptocurrency markets](https://arxiv.org/pdf/2608.21888)
- [Intraday Momentum for ES and NQ — Quantitativo](https://www.quantitativo.com/p/intraday-momentum-for-es-and-nq)
- [Mean Reversion Trading Strategy: 565 Weeks of NQ Data](https://tradingstats.net/mean-reversion-trading-strategy/)
- [Pullback Trading Strategies — QuantifiedStrategies](https://www.quantifiedstrategies.com/pullback-trading-strategy/)
- [NQ vs ES: Why They Move Together, Until They Don't — Bookmap](https://bookmap.com/blog/nq-vs-es-why-they-move-together-until-they-dont)
