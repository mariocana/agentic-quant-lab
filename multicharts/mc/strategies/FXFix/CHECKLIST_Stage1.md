# FX Fix — Stage 1, meccanica

**La domanda: il codice entra ed esce agli orari dei fixing, ora legale compresa?** Il P&L non
si guarda.

## Setup del run

| | |
|---|---|
| tipo di studio | **Signal**, non Indicator — contiene ordini |
| strumento | **6E, 5 min**, Globex 24h, timezone **Exchange (CT)** |
| Bar Magnifier | **1 min** (solo ordini a mercato, ma teniamo la convenzione) |
| contratti | **1** |
| commissione | **$8,65/lato** ($2,40 Lucid + 1 tick di slippage), slippage MC **0** |
| periodo | `TradeStartEL 1240201`, `TradeEndEL 1240515`, `ShowLog 1` |
| input | tutti gli altri ai default (A e B accese insieme) |

**Perché il 2024 e non i giorni recenti:** il periodo deve contenere un disallineamento
dell'ora legale (10/03 → 30/03/2024), e così l'OOS 2025-26 resta intatto. L'IS lo vedremo
comunque allo Stage 2.

Il codice va copiato come `C:\mc_out\FXFix_code.txt`; il log esce su `fxfix_log.txt`. Nomi
diversi anche ignorando le maiuscole.

## Cosa deve risultare

MultiCharts timbra il trade alla chiusura della barra in cui viene eseguito, quindi 5 minuti
dopo l'ordine.

| | settimane normali | 11/03 → 29/03/2024 |
|---|---|---|
| B ingresso `FX-B-S` | **01:05** | 01:05 |
| B uscita `FX-B-x` | **07:20** | **08:20** |
| A ingresso `FX-A-L` | **10:05** | **11:05** |
| A uscita `FX-A-x` | **15:45** | 15:45 |

1. **Al massimo un trade A e un trade B al giorno**, mai sovrapposti.
2. **Gli orari della tabella su tutti i trade.** Uno fuori orario = errore di codice.
3. **`disallineamento=si` nel log esattamente dall'11/03 al 29/03/2024**, e su nessun altro
   giorno.
4. **Solo i nomi `FX-A-L`, `FX-A-x`, `FX-B-S`, `FX-B-x`.** `FX-safe-*` solo su un giorno a
   chiusura anticipata; altrove vuol dire che un'uscita non è scattata.
5. **Frequenza:** circa 74 giorni di sessione → **circa 148 trade**.
6. **Venerdì Santo 29/03/2024:** guardare cosa succede. Se il mercato era chiuso o ridotto, il
   trade manca o esce con `FX-safe`; va bene, basta che non resti aperto fino a lunedì.

## Test x10

Rigirare con `Num_Contracts 10` e:

```bash
python3 mc/docs/check_report.py mc/strategies/FXFix/reports/*_S1_*.xlsx --tabella
```

`n`, `WR%`, `R:R` identici, `avg` a x10.

## Kill dello Stage 1

Nessuno. Se la meccanica sbaglia si corregge il codice. Il primo kill è il Gate 2 sull'IS
2020-2024, **una finestra alla volta** (`TradeWinA 1 / TradeWinB 0`, poi il contrario), con t
atteso ~3,4 (A) e ~3,6 (B) a edge intatto, ~1,7-1,8 a edge dimezzato.
