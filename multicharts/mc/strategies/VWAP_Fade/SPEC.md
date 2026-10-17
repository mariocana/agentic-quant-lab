# VWAP Fade — Stage 0

**Aperta il 17/10/2026.** Prima strategia **mean reverting** della pipeline: tutte e sei le
precedenti erano momentum o breakout (vedi la correzione del 17/10 su VWAP Pullback).

> *"the minimum that you need to have is through having a trend following strategy **and a
> mean reverting strategy**"* — Live 001, 421

## Ipotesi

Dentro la sessione il prezzo oscilla attorno al VWAP, che e il prezzo medio a cui si e
scambiato il volume. Quando se ne allontana di abbastanza **senza una ragione direzionale**,
la pressione degli esecutori che lavorano contro il VWAP — algoritmi di esecuzione
istituzionali che devono riempire al VWAP o meglio — tende a riportarlo indietro.

**Il perche strutturale**, che e la parte che conta: il VWAP non e una media qualsiasi, e il
**benchmark di esecuzione** della maggior parte degli ordini istituzionali. Chi deve comprare
viene valutato sul VWAP, quindi quando il prezzo sta sopra ha un incentivo ad aspettare, e
quando sta sotto ad accelerare. E un flusso che esiste per un motivo contabile, non per una
regolarita statistica che potrebbe svanire.

**E l'esatto contrario di VWAP Pullback**, che e momentum: quella entra sul **reclaim** del
VWAP nella direzione di un breakout. Questa **vende la deviazione** e punta al VWAP.

## Geometria, pre-registrata e non ottimizzabile

| | valore | perche |
|---|---|---|
| ingresso | chiusura oltre **VWAP ± 1,0 σ** | |
| target | **il VWAP** | e il punto di attrazione dell'ipotesi, non un livello scelto |
| stop | **VWAP ± 2,5 σ**, σ congelata all'ingresso | |
| **R:R** | 1,0 / 1,5 = **0,67** | dentro la banda 0,5-1 del profilo prop |

La σ e la deviazione standard **pesata per volume** del prezzo tipico attorno al VWAP: la
banda classica, non una deviazione sui rendimenti.

## Il test che la falsifica, scritto prima di qualunque codice di strategia

In un random walk senza drift, partendo da +1σ con barriere a 0 e +2,5σ:

> **P(tocca il VWAP prima dello stop) = (2,5 − 1,0) / 2,5 = 60%**

Per arrivare a PF 1,3 con R:R 0,67 serve `WR = PF/(PF+R:R)` = 1,3/1,97 = **66%**.

> **Soglia: eccesso sul caso ≥ +6 punti percentuali. Cioe WR ≥ 66% al primo tocco.**

E lo stesso metro con cui le sei morte hanno dato da **+0,4** (VWAP base) a **+5,3**
(VaultBreak), e la letteratura documenta +1,5…+5. **Se questa non arriva a +6, e morta prima
di nascere e non si scrive la strategia.**

## E il secondo test, quello che ha ucciso le candidate dell'agente

> **Serve ≥ 2 setup al giorno.**

Con meno, l'economia della eval non regge: DriftPullback passa perche fa $18,34 al giorno per
micro (3,2 trade/giorno × $5,73); le candidate IB-C erano a $3,24 e volevano 462 giorni per
fare $3.000. La frequenza non e un dettaglio, e il vincolo che decide.

## Come si misura, prima di scrivere la strategia

`VWAP_Fade_Study.txt` e un **indicatore**, non una strategia: conta i setup, li risolve al
primo tocco e stampa frequenza, win rate osservato, win rate del caso ed eccesso. Non serve
nessun backtest.

- chart **5 min**, timezone **Exchange (CT)**, Bar Magnifier 1 min
- la sessione la impone il **codice** (`SessStart 830`, `SessEnd 1455`), non il template: e
  la lezione dei due run buttati su `ATR_Window_Study`
- girare su **@NQ** e su **@YM**, periodo 2020-2024 (l'IS), `ShowLog 1`
- mandare il contenuto di `C:\mc_out\vwap_fade.txt`

## Strumento: @YM e il candidato, @NQ il controllo

Al budget di rischio che il drawdown consente, **R/ATR** vale **0,29-0,52 su MYM** contro
**0,12-0,21 su MNQ**: su MNQ lo stop sta dentro il rumore, ed e il motivo strutturale per cui
tre strategie su NQ sono morte sullo stesso numero. Si misurano entrambi e si sceglie col
dato, ma l'aspettativa e dichiarata: **YM dovrebbe reggere meglio**.

## Cosa NON c'e, deliberatamente

**Nessun filtro di regime.** Il fade sul VWAP muore nei giorni di trend, e la tentazione e
aggiungere subito un filtro che escluda quei giorni. Non si fa adesso: *"start simple, prove
there is a signal, then add degrees of sophistication"* (Lesson 2, 09:41). Se la misura base
da un eccesso vicino alla soglia, il filtro di regime e la **prima** variante dello Stage 4 —
e dovra passare lo split-sample come tutte le altre.

## Aspettativa dichiarata

L'eccesso sara **positivo ma piccolo**, fra +2 e +5 pp, cioe sotto soglia. Motivo: e la stessa
banda in cui e caduto tutto quello che abbiamo misurato finora, e un fade senza filtro di
regime paga i giorni di trend. **Se esce sopra +6 senza filtri, sono io ad avere sbagliato
previsione, e va verificato due volte prima di festeggiare.**

## Strumento deciso: **@YM**. Col dato, non con l'aspettativa.

Misurati i range RTH 2020-2024 (`mc/docs/lucid_strumenti.md`): **MCL e MYM hanno lo stesso
identico range per micro, $170 contro $169**, quindi lo stesso R/ATR — **0,47** a R = $80.
Come unita di rischio sono intercambiabili, e la scelta si sposta su altro:

- **costo**: MYM $1,50 per round-turn contro $2,00 di MCL (1,9% di R contro 2,5%);
- **granularita**: tick da $0,50 contro $1,00, cioe 160 tick di stop contro 80;
- **stabilita di regime**: anno peggiore / anno migliore **1,68** contro **2,42** (il crude
  nel 2022 raddoppia il range per la crisi energetica).

E soprattutto una ragione che riguarda **questa** strategia e non il rischio:

> L'ipotesi del VWAP Fade e che il VWAP sia il **benchmark di esecuzione istituzionale**.
> Quell'argomento e nato sull'azionario ed e li che e piu forte. Sul crude il flusso che
> lavora contro il VWAP e piu debole: la ragione strutturale si annacqua.

**Quindi: VWAP Fade su @YM.** @NQ resta come controllo nello stesso run — costa un grafico e
dice se il problema di MNQ (R/ATR 0,19) si vede anche qui.

**MCL non e scartato, e messo da parte per la cosa giusta**: e l'unico non-indice a $0,50 per
lato e l'unica vera diversificazione di classe disponibile. Ma merita una strategia pensata
sui driver del crude, non un VWAP fade trapiantato.
