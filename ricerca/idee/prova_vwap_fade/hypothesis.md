# prova_vwap_fade

> **Possibile variante di un'idea morta.** Mario stesso cita fra i casi misurati un «VWAP base»
> (eccesso +0,4 punti) e mette questa idea come l'opposto di «VWAP Pullback». Inoltre
> `docs/desk_ricerca.md` nomina un «VWAP Fade» che non si è potuto ricalibrare nel motore. Per
> questa prova alla cieca non ho letto il cimitero, quindi non so dire se la madre sia «VWAP
> base» o «VWAP Fade»: lo decide il desk, che deve collegarla nel registro se è così.

## Ipotesi

Su NQ, nella sessione regolare, quando una barra da 5 minuti chiude oltre VWAP ± 1σ (σ = la
deviazione standard pesata per volume attorno al VWAP), il prezzo torna al VWAP prima di toccare
VWAP ± 2,5σ più spesso di quanto farebbe un random walk con la stessa geometria. Con barriere
fisse a 0 e 2,5σ partendo da 1σ il caso dà il 60%. L'ipotesi è falsa se l'eccesso sul caso è
sotto +6 punti, cioè se il win rate al primo tocco non arriva al 66%.

## Meccanismo

Il VWAP è il benchmark di esecuzione di molti ordini istituzionali: chi deve comprare viene
giudicato sul prezzo medio pesato della giornata. Quando il prezzo sta sopra il VWAP, a chi
compra conviene rallentare. Quando sta sotto, conviene accelerare. Per chi vende vale il
contrario. Questi flussi, per come sono costruiti, frenano le deviazioni grandi dal VWAP e
spingono il prezzo indietro. È un incentivo contabile, non un pattern statistico. Nella scala
del filtro è un flusso legato a un benchmark di esecuzione (domanda 3 di
`come_scegliere_un_paper.md`).

Due cose da dire chiaramente, perché le guarderà il critico:
- Il meccanismo riguarda soprattutto chi esegue **azioni** sul VWAP. Su NQ il passaggio è
  indiretto: dalle azioni del Nasdaq-100 e dall'arbitraggio indice-future. Nessuna fonte che ho
  aperto lo misura sul future.
- Un algoritmo VWAP puro partecipa in proporzione al volume, senza guardare il prezzo. Il freno
  descritto da Mario vale per chi ha margine di discrezione sul timing (algoritmi «VWAP o
  meglio», trader con il VWAP come benchmark), non per i VWAP passivi.

## Chi perde, e perché continua a perdere

Dall'altra parte stanno quelli che spingono il prezzo lontano dal VWAP senza una notizia:
ordini direzionali impazienti, stop e liquidazioni a cascata, momentum di breve. Continuano
a perdere perché la loro urgenza non dipende dal prezzo: devono eseguire adesso (gestione del
rischio, margini, flussi ETF), e chi ha tempo fino a fine giornata gli fornisce liquidità a
un prezzo migliore della media.

Il punto debole è proprio qui: nei giorni di trend chi spinge ha ragione, e allora a perdere
è il fade. L'idea vive solo se i giorni «senza ragione direzionale» pesano più di quelli di
trend. Senza un filtro di regime (escluso apposta da Mario) non so nominare un perdente
che perda **sempre**. Lo nomino come ipotesi: il flusso impaziente intragiornaliero.

## Fonti

L'idea è di Mario (`ricerca/idee/prova_vwap_fade/fonti/idea.md`), con parole e numeri suoi. Il
60% e il 66% non vengono da un paper: sono il calcolo della rovina del giocatore e la
formula `WR = PF/(PF+R:R)` con PF 1,3 e R:R 0,67, scritti da lui prima di qualunque misura.

Fonti esterne. Nessun numero entra da qui, perché non sono riuscito a mettere nessun numero
su una pagina verificata:

1. **Berkowitz, Logue, Noser (1988)**, *The Total Cost of Transactions on the NYSE*, *Journal of
   Finance* 43(1), pp. 97-112. È il lavoro che introduce il VWAP della giornata come benchmark
   per misurare il costo d'esecuzione degli ordini istituzionali. La pagina 97 (abstract) l'ho
   vista solo in un catalogo bibliografico, non nel testo. **Non verificata**: il critico la
   controlli. Il numero di costo che riporta (circa 23 punti base) non lo uso.
2. **Madhavan (2002)**, *VWAP Strategies*, in *Transaction Performance*, Institutional Investor,
   Spring 2002, pp. 32-38. Dice che il VWAP è molto usato per valutare i trader e avverte che
   inseguire il benchmark può cambiare il comportamento d'esecuzione. Il PDF non l'ho potuto
   leggere, ho visto solo una sintesi di terzi. **Pagina non verificata**: vale solo come
   riferimento qualitativo del meccanismo.
3. **Evidenza contraria: Zarattini e Aziz (2023)**, *Volume Weighted Average Price (VWAP): The
   Holy Grail for Day Trading Systems*, working paper SSRN (Concretum Research). Su QQQ e TQQQ,
   2018-2023, dichiarano un risultato con la regola opposta: lungo sopra il VWAP, corto sotto.
   È un ETF e non un future, non è referato, e non ho visto la pagina. Lo cito solo perché, se
   regge, il fade lavora contro un trend documentato sullo stesso indice dopo il 2021.

Riassunto onesto per il critico: **nessuna fonte con pagina verificata**. Il meccanismo del
benchmark è letteratura standard sull'esecuzione, ma nessun paper misura il fade del VWAP su
futures. Le domande 1, 2, 7 e 8 del filtro restano senza risposta.

## Regola eseguibile

Motore: barre da 5 minuti su NQ, stop e target risolti sul percorso a 1 minuto. Orari in
Central Time.

**Sessione.** Sessione regolare 08:30-15:00 CT. Barre da 5 minuti allineate a 08:30. Overnight
escluso dal calcolo e dal trading. *Scelta*: è la sessione in cui opera il flusso azionario
del meccanismo.

**VWAP e σ.** Si ancorano alle 08:30 di ogni giorno e si azzerano ogni giorno. Si calcolano
dalle barre da 1 minuto della sessione:
- prezzo tipico `p = (H+L+C)/3`, volume `v`
- `VWAP = Σ v·p / Σ v`
- `σ = sqrt( Σ v·(p − VWAP)² / Σ v )`, la banda classica pesata per volume (definizione di Mario)

Per il segnale si usano VWAP e σ aggiornati alla chiusura della barra da 5 minuti, con tutti i
minuti fino a quella chiusura compresa.

**Setup.**
- Corto: una barra da 5 minuti chiude sopra `VWAP + 1,0σ` e la barra precedente aveva chiuso
  a `VWAP + 1,0σ` o sotto (attraversamento fresco).
- Lungo: lo specchio, chiusura sotto `VWAP − 1,0σ` dopo una chiusura a `VWAP − 1,0σ` o sopra.
- La prima barra della giornata (chiusura 08:35) confronta la propria chiusura con la banda.
  Non avendo una barra precedente nella sessione, vale come attraversamento fresco.
- *Scelta*: nessun periodo di riscaldamento. È la lettura più semplice del testo di Mario,
  che non ne prevede. Il rischio che ne viene (σ minuscola nei primi minuti) è nella sezione 7.

**Riarmo.** Una posizione per volta. I setup che arrivano mentre si è in posizione si
ignorano. Dopo l'uscita ci si riarma per un lato solo quando una barra da 5 minuti chiude di
nuovo dentro la banda di quel lato (`≤ VWAP + 1σ` per il corto, `≥ VWAP − 1σ` per il lungo).
Ci vuole poi un attraversamento fresco. *Scelta*: impedisce di rientrare subito, a ogni barra,
dopo uno stop con il prezzo ancora oltre la banda. È la condizione di «attraversamento» già
scritta sopra, senza parametri nuovi.

**Ingresso.** A mercato all'apertura della barra da 5 minuti successiva a quella del segnale.

**Target e stop**, fissati all'ingresso con VWAP e σ della barra del segnale (`VWAP₀`, `σ₀`):
- target: `VWAP₀`, ordine limite
- stop: `VWAP₀ + 2,5σ₀` per il corto, `VWAP₀ − 2,5σ₀` per il lungo, ordine stop
- *Scelta*: Mario congela σ. Congelo anche il VWAP, perché il suo 60% presuppone barriere fisse.
  Il target mobile sul VWAP corrente sarebbe un'altra idea.
- Se stop e target cadono nella stessa barra da 1 minuto, vince lo stop (lettura prudente).
- Il R:R realizzato non sarà esattamente 0,67, perché l'ingresso è all'apertura della barra
  successiva e non sulla banda. La misura usa la geometria realizzata, quindi va bene così.

**Uscita a fine sessione.** Se la posizione è ancora aperta, si chiude a mercato alla chiusura
della barra delle 14:55-15:00. I segnali possono arrivare fino alla barra che chiude alle 14:55.
L'ingresso più tardo è quindi all'apertura delle 14:55. Il segnale sulla barra che chiude alle
15:00 non ha ingresso.

**Massimo di trade al giorno.** Nessun tetto oltre il riarmo. *Scelta*: Mario non ne indica
uno, e il riarmo limita già la frequenza. Il numero effettivo di trade al giorno va riportato
dalla misura.

**Nessun filtro** di regime, di volatilità, di giorno della settimana o di calendario.
Escluso apposta da Mario.

## Frequenza e costi

**Segnali.** La mia stima, non misurata e da non usare come prior forte, è di **2-4 trade al
giorno**. Un prezzo che oscilla attorno al VWAP attraversa più volte ±1σ in sei ore e mezza, e
il riarmo dimezza grosso modo gli ingressi possibili. Nei giorni di trend forte sarà 1, chiuso
dallo stop o a fine sessione.

**Effetto contro costo.** La fonte non dichiara un effetto: l'unico numero è la soglia di
Mario. Con target 1σ e stop 1,5σ, un trade rende in media `WR·1σ − (1−WR)·1,5σ`:
- al 66% (soglia): +0,15σ
- al 63% (eccesso +3, il centro dell'aspettativa di Mario): +0,075σ
- al 60% (caso): 0

Su MNQ (2 dollari al punto), con σ di 20 punti, 0,15σ sono 3 punti, cioè 6 dollari a
trade per micro. A +3 punti di eccesso diventano 3 dollari. Il costo andata e ritorno che
assumo è circa 1,5-2 dollari a micro: commissione più un tick di slippage in ingresso a
mercato e sullo stop. È un'*assunzione dichiarata*, non presa da una fonte. Il target è un
limite, quindi senza slippage. Quindi alla soglia l'effetto copre i costi tre volte; a metà
aspettativa, una e mezza.

Non conosco il valore tipico di σ su NQ nel 2020-2024. Il 20 è un'ipotesi di lavoro, e il
conto scala in proporzione. A σ piccola (mattina presto, giorni calmi) il costo mangia tutto.

## Cosa la ucciderebbe, e la soglia della misura

Scritto prima di ogni numero. La misura è sul periodo in-sample 2020-01-01 / 2024-12-31 del
perimetro.

**Soglie, tutte necessarie.** Più severe del perimetro dove Mario lo è:
1. **Eccesso sul caso ≥ +6 punti percentuali**, con il caso calcolato sulla geometria
   realizzata. È la soglia di Mario (WR ≥ 66% sulla geometria nominale), e vale più dei minimi
   del perimetro.
2. **Errori standard ≥ 3,0** sull'eccesso (minimo del perimetro).
3. **≥ 2 setup al giorno** in media. È la soglia di Mario, più severa del minimo di 1 del
   perimetro.
4. **≥ 10 dollari al giorno per micro**, netti di costi (minimo del perimetro).

Se ne manca una, l'idea è morta in questa forma. Il filtro di regime **non** è un modo per
salvarla: Mario lo ha scritto come variante successiva, da aprire come idea nuova e contare.

**Cosa la ucciderebbe, in concreto:**
- **I giorni di trend.** Un fade senza filtro paga per intero i giorni in cui il prezzo si
  allontana dal VWAP e non torna. Mario stesso si aspetta un eccesso **fra +2 e +5**, sotto la
  sua soglia. Sono d'accordo: il mio prior è che non passi. Se esce sopra +6 senza filtri,
  prima di crederci va controllato il calcolo (Mario lo dice: «va verificato due volte»).
- **σ minuscola a inizio sessione.** Senza riscaldamento, nei primi minuti σ è calcolata su
  pochi minuti ed è piccola. Attraversamenti facili, target e stop vicini, costo in proporzione
  enorme. Se i dollari al giorno sono negativi, la prima cosa da guardare è questa. Ma un
  riscaldamento aggiunto dopo sarebbe un parametro scelto sui dati, quindi un'idea nuova.
- **Meccanismo indiretto.** Il benchmark VWAP è delle azioni, non del future. Se il flusso non
  passa su NQ, l'eccesso è zero per costruzione.
- **Evidenza contraria sullo stesso indice.** Il lavoro di Zarattini e Aziz (QQQ, 2018-2023)
  trova un trend rispetto al VWAP, non un ritorno. Se ha ragione, l'eccesso può essere
  negativo.
- **Domanda 8 del filtro.** Nessuna fonte mostra l'effetto vivo dopo il 2021, perché nessuna
  fonte lo misura.

---

Altre idee nella fonte, da aprire eventualmente come idee nuove:
- Lo stesso fade con un filtro di regime che escluda i giorni di trend (Mario: «prima variante
  dello Stage 4», se la base esce vicina alla soglia).
