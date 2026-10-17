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

## Run del 17/10 su @YM: NON VALIDO, bug nell'indicatore

Log archiviato come `mc/docs/measures/vwap_fade_YM_2020-2024_RUN-ROTTO.txt`.

**Il risultato sembrava una stroncatura:** 20.217 setup su 1.292 giorni, WR 25,34% contro un
caso del 60%, **eccesso −34,66 pp**. Non e un verdetto: e uno strumento rotto, e lo si vede
senza interpretare niente.

**Il tell sta nelle ultime due righe del log:**

| | misurato | di progetto |
|---|---|---|
| distanza media al target | **101,39 punti** | 1,0 σ |
| distanza media allo stop | **21,94 punti** | 1,5 σ |
| **R:R realizzato** | **4,62** | **0,67** |

Il target era **4,6 volte piu lontano dello stop**, cioe l'esatto contrario di come e
costruita la geometria. Da li si ricava che **gli ingressi avvenivano a 2,06 σ sopra il VWAP
invece che a 1,00**.

### La causa

Mancava la **condizione di riarmo**. Appena un setup si risolveva, `armed` tornava a 0 e la
barra successiva poteva aprirne subito un altro — **senza che il prezzo fosse mai rientrato
dentro la banda**. Dentro un trend questo riapre il setup a ogni barra, ogni volta piu lontano
dal VWAP, con lo stop (fisso a 2,5 σ dal VWAP) sempre piu vicino e il target sempre piu
lontano.

Lo conferma la frequenza: **15,65 setup al giorno**, cioe **uno ogni 5 barre** su una
giornata da 78. Non e un mercato che oscilla, e un contatore impazzito.

### Le correzioni

1. **Riarmo**: un nuovo setup puo nascere solo dopo che il prezzo e **rientrato** dentro
   `± EntrySD · σ`. E la meccanica standard di un fade, non un filtro.
2. **`MinBars 12`**: con poche barre la σ non e ancora definita e il primo tocco e rumore.
   Un'ora a 5 minuti.
3. **Diagnostica aggiunta**: il log ora stampa **`sigma all'ingresso`**, che **deve valere
   ~1,00**. Se esce piu alto, il riarmo e di nuovo rotto e il resto del log non si legge
   nemmeno.
4. Corretta la riga giornaliera, che stampava `nSetup` due volte.

### Cosa NON si puo concludere dal run rotto

Niente sull'ipotesi. **L'eccesso di −34,66 pp non falsifica il VWAP Fade**: misura un
meccanismo che nessuna strategia implementerebbe mai. L'aspettativa dichiarata prima del run
(**+2…+5 pp, sotto soglia**) resta in piedi e non e stata ne confermata ne smentita.

## Esito: NON PASSA. Eccesso +0,41 pp contro i +6 richiesti.

Log: `mc/docs/measures/vwap_fade_YM_2020-2024.txt`. @YM, 1.292 giorni, 2020-2024.

### Il primo test lo passa

**3,33 setup al giorno**, sopra la soglia di 2. La famiglia non muore di frequenza — e
l'unica delle ultime quattro candidate a superare questo scoglio.

### Il secondo no, e il numero giusto non e quello stampato

Il log stampava **eccesso −15,47 pp**, e anche quello era un difetto dell'indicatore:
confrontava il win rate col caso della geometria **di progetto** invece che di quella
**realizzata**.

Entrando alla **chiusura** della barra che rompe la banda si sfora: l'ingresso medio cade a
**1,397 σ** invece che a 1,000. E il caso dipende da dove entri davvero:

| | ingresso | caso | WR misurato | eccesso |
|---|---|---|---|---|
| geometria di progetto | 1,00 σ | 60,00% | 44,53% | −15,47 pp **(sbagliato)** |
| **geometria realizzata** | **1,397 σ** | **44,12%** | **44,53%** | **+0,41 pp** |

> **Il fade al VWAP su YM e un random walk.** WR 44,53% contro un caso di 44,12%.

### E il test aveva potenza da vendere

Su **3.804 setup risolti**, l'errore standard sull'eccesso e **0,81 pp**:

- misurato **+0,41 pp**, cioe **0,51 errori standard da zero**;
- intervallo di confidenza 95%: **da −1,17 a +1,99 pp**;
- la soglia di **+6,0 pp** sarebbe stata a **7,5 errori standard**.

**Non e un campione piccolo, non e un regime sfortunato: non c'e niente.** L'aspettativa
dichiarata prima del run era +2…+5 pp e sotto soglia; il misurato e persino sotto quella.

### La nota sulla geometria, che non salva niente

Lo sforamento di 0,40 σ degrada anche il R:R da **0,67 a 1,27**, fuori dalla banda prop. Si
correggerebbe entrando con un **limite alla banda** invece che alla chiusura. **Ma non
cambierebbe il verdetto**: l'eccesso sul caso e costruito apposta per essere invariante alla
geometria — spostare target e stop rietichetta l'edge, non lo crea. Un fill migliore sposta
il caso dal 44% al 60% e la soglia dal 44% al 66%: la distanza resta la stessa.

### Cosa resta da fare prima di chiudere la famiglia

Il controllo su **@NQ**, che e nella SPEC e costa dieci minuti. Serve a sapere se il nulla e
dello strumento o del meccanismo. **L'aspettativa e che sia identico.**

## Controllo su @NQ: confermato. La famiglia si chiude.

Log: `mc/docs/measures/vwap_fade_NQ_2020-2024.txt`. 1.293 giorni, 2020-2024.

Il log stampa ancora **−17,27 pp** perche e girato con la versione dell'indicatore **prima**
della correzione sul caso. Il numero corretto si ricava dalle stesse righe:

| | setup/giorno | σ all'ingresso | caso | WR | **eccesso** | n risolti |
|---|---|---|---|---|---|---|
| **@YM** | 3,33 | 1,397 | 44,12% | 44,53% | **+0,41 pp** | 3.804 |
| **@NQ** | 3,26 | 1,390 | 44,40% | 42,73% | **−1,67 pp** | 3.712 |
| **combinato** | | | | | **−0,62 pp ± 0,57** | **7.516** |

Intervallo di confidenza 95% sul combinato: **da −1,74 a +0,51 pp**. La soglia di **+6,0**
sarebbe a **10,5 errori standard**.

> **Non c'e edge nel fade della deviazione dal VWAP, su nessuno dei due strumenti.**
> Due campioni indipendenti, 7.516 setup risolti, e lo zero ci sta comodamente dentro.

### Cosa si porta via questa misura

1. **La famiglia «fade della deviazione dal VWAP» e chiusa.** Non e lo strumento: NQ e YM
   danno lo stesso nulla pur avendo range per micro diversi di 2,5 volte.
2. **Il meccanismo pero produce materiale**: **3,3 setup al giorno su entrambi**, sopra la
   soglia di 2, unica delle ultime candidate a passare il test di frequenza. Se un giorno si
   trova un edge mean reverting, **la banda a 1 σ sul VWAP e un trigger valido**: manca il
   segnale, non il contatore.
3. **Il mean reversion in generale NON e falsificato.** Lo e *un* meccanismo. Restano da
   provare: reversal pomeridiano dopo momentum mattutino (Xu-Zhu 2022), reversal
   overnight-intraday (Liu et al. 2025), gap fade.

### Il costo di questa misura

Tre run e **due bug miei** nello stesso indicatore: il riarmo mancante (15,65 setup/giorno,
R:R 4,62) e il caso calcolato sulla geometria di progetto invece che su quella realizzata
(−15,47 dove c'era +0,41). **Entrambi erano visibili senza guardare il win rate** — il primo
nella frequenza assurda, il secondo nel R:R fuori scala. La regola da tenere: **prima si
controlla che lo strumento misuri quello che deve, poi si legge il risultato.**
