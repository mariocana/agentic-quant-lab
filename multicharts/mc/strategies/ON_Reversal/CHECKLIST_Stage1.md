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

---

# Esito Stage 1 (17/10/2026): meccanica verificata

Report sul 2026-06-29 → 2026-10-16, 65 trade, log `on_reversal_trades.txt` con 65 setup.

| controllo | esito |
|---|---|
| 1. un solo trade al giorno | **65 ingressi su 65 giorni distinti** |
| 2. orario di ingresso | **08:35 su 65/65** |
| 3. nessuna posizione dopo l'ora | ultima uscita **09:35**, nessuna dopo |
| 4. nomi delle uscite | solo i sei previsti: `S-tgt` 23 · `L-tgt` 11 · `L-stp` 9 · `S-stp` 8 · `S-flat` 7 · `L-flat` 7 |
| 5. direzione contraria al gap | **65/65 corrette** (38 gap positivi → 38 EntryShort) |
| 6. frequenza | 65 setup nel log = 65 trade nel report, **0,83/giorno** |

## Perche l'ingresso e alle 08:35 e non alle 08:40 come avevo scritto

Su un chart **Globex 24h** la barra timbrata **08:30** copre 08:25-08:30, cioe' e' ancora
pre-apertura. Il segnale nasce li', sulla sua chiusura — che **e' il prezzo delle 08:30, cioe'
l'apertura RTH** — e `next bar at market` riempie all'apertura della barra 08:30-08:35,
timbrata 08:35.

**Quindi il fill e' praticamente all'apertura**, piu' vicino alla misura di quanto temessi: la
mia previsione di 08:40 era sbagliata in meglio.

## Una fragilita' trovata verificando, e corretta

Il rilevamento di apertura era `Time >= SessStart and Time[1] < SessStart`. **Su un chart RTH
non avrebbe MAI funzionato**: la barra precedente alla 08:35 e' la 15:00 del giorno prima, e
`1500 < 830` e' falso. La strategia non avrebbe fatto **un solo trade, in silenzio**.

Corretto in `Time >= SessStart and ( Time[1] < SessStart or Date <> Date[1] )`, su entrambi i
file. Su Globex non cambia nulla (a mezzanotte `Date` cambia ma `Time` e' 5, che non e'
>= 830), e su RTH ora funziona.

**Il run fatto era su Globex, quindi e' valido.** Ma la misura e la strategia devono stare
sullo stesso template, e ora lo fanno su entrambi.

## Le due cose annotate, non giudicate

| | Stage 1 (2026) | misura (2016-2024) |
|---|---|---|
| uscite flat | **21,5%** (14 su 65) | 29% |
| WR sui risolti | **66,7%** (34 target / 17 stop) | 64,1% e 64,8% |

Coerenti. Il campione e' piccolo (65 trade su quattro mesi) e non decide niente.

## Cosa manca per chiudere lo Stage 1

1. **Il test x10** — non ancora fatto.
2. **Il run va rifatto con i costi e il Bar Magnifier**: questo aveva `No Commission` e
   **Bar Magnifier Disabled**. Per la meccanica non cambia nulla, **ma l'attribuzione delle
   uscite si'**: con target e stop che possono essere colpiti **dentro la stessa barra da 5
   minuti**, senza il magnifier e' MultiCharts a decidere quale scatta, non il percorso a 1
   minuto. Quindi **il 34/17 non e' affidabile** e il P&L non si legge.
