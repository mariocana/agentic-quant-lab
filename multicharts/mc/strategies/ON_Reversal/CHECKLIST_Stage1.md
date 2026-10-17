# ON Reversal — Stage 1, meccanica

**La domanda dello Stage 1 e una sola: il codice fa quello che credo?** Non si guarda il P&L.

## Setup del run

| | |
|---|---|
| strumento | **@YM**, 5 min |
| timezone | **Exchange (CT)** — gli orari negli input sono in ora del chart |
| Bar Magnifier | **1 min, Enabled** |
| contratti | **1** |
| commissione | **$6,75 per lato** ($1,75 Lucid + 1 tick da $5 di slippage) |
| slippage MC | **0** (e' dentro la commissione) |
| periodo | **100 giorni**, con almeno **20 sessioni di lead-in prima** |
| input | tutti ai default |

**Il lead-in non e' opzionale**: `avgRng` resta a 0 finche' non ha `AtrLen` = 20 sessioni, e
con `avgRng = 0` il gate non arma nulla. Se il grafico parte esattamente al primo giorno da
valutare, i primi 20 giorni non produrranno trade — e corretto, non e' un bug.

## Cosa deve risultare

1. **Al massimo un trade al giorno.** `tradedToday` lo impone. Se ne vedi due, il flag non
   si azzera dove deve.
2. **Tutti gli ingressi nella prima barra utile dopo l'apertura**, cioe' timbrati **08:40**
   su un chart a 5 minuti (il segnale nasce alla chiusura della barra 08:35, l'ordine e'
   `next bar at market`).
3. **Zero posizioni dopo le 09:30.** Il flat e' obbligatorio.
4. **Le uscite hanno i nomi previsti**: `L-tgt`, `L-stp`, `L-flat`, `S-tgt`, `S-stp`,
   `S-flat`. Se compare qualcos'altro, c'e' un ordine che non ho previsto.
5. **La direzione e' sempre contraria al gap.** Con `ShowLog 1` il log stampa `gap=`: se e'
   positivo il trade deve essere **short**.
6. **Frequenza attesa ~0,7 trade al giorno**, cioe' **~70 trade su 100 giorni**. Se sono
   molti di piu' il gate non sta filtrando; se molti di meno, `avgRng` e' sbagliato.

## Il test x10

Rigirare identico con `Num_Contracts 10` ed esportare i due report:

```bash
python3 mc/docs/check_report.py mc/strategies/ON_Reversal/reports/*_S1_*.xlsx --tabella
```

**`n`, `WR%` e `R:R` devono essere identici**; **`avg` deve stare a x10**. Uno scarto sul
Gross Loss entro lo 0,1% e' noto e accettato (vedi la nota di DriftPullback).

## Le due cose da guardare che NON sono la meccanica

Si annotano, non si giudicano — il giudizio e' allo Stage 2.

1. **Quanti trade escono con `L-flat` / `S-flat`.** Nella misura erano il **29%** dei setup,
   e il loro P&L **non e' mai stato misurato**: e' la prima volta che lo vediamo.
2. **L'avg trade.** La misura dava un eccesso di +4,40 pp sul caso, ma con l'ingresso alla
   chiusura della prima barra. Qui si entra alla barra dopo, a mercato: **l'avg trade sara'
   piu' basso**, e quanto piu' basso e' esattamente il costo del fill realistico.

## Kill dello Stage 1

**Nessuno.** Qui non si uccide niente: se la meccanica e' sbagliata si corregge il codice e si
rigira. Il primo kill e' al Gate 2.
