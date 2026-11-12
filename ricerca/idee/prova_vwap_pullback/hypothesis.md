# prova_vwap_pullback

Idea di Mario (porta `user`), messa in forma senza cambiarla. Il testo originale è in
`fonti/idea.md`. Questa è la regola base: niente gate ADX, un trade al giorno, flat alle 14:55 CT.
Non è variante di un'idea morta nota a questo giro (prova alla cieca: `GIA_FATTO` vuoto).

## Ipotesi

Nei giorni in cui NQ chiude una barra da 1 minuto fuori dal range 08:30–09:00 CT, il primo
ritorno del prezzo sul VWAP della sessione regolare, seguito da una chiusura di nuovo dalla parte
del breakout, è seguito più spesso del caso da una ripresa nella direzione del breakout fino al
massimo (o minimo) di swing precedente, prima che venga toccato lo swing opposto.
Falsificabile così: se gli ingressi presi con questa regola non battono, oltre i costi, ingressi
nella stessa direzione e nelle stesse ore presi a caso, l'ipotesi è falsa.

## Meccanismo

Mario lo scrive così: gran parte del flusso istituzionale viene eseguito da algoritmi che hanno il
VWAP come benchmark, quindi il VWAP è la zona in cui il flusso passivo si attiva e il prezzo reagisce.

Detto per esteso, le parti sono due.
1. Il breakout del range d'apertura dice da che parte sta lo squilibrio della giornata (chi deve
   comprare o vendere per forza, ad esempio per ribilanciamenti o grandi ordini spezzati nella giornata).
2. Chi esegue un ordine grande con benchmark VWAP viene giudicato sul prezzo medio rispetto al
   VWAP. Un compratore che deve finire l'ordine trova conveniente comprare di più quando il prezzo
   torna al benchmark o sotto, e meno quando è sopra. Se lo squilibrio del breakout è vero, il
   ritorno al VWAP richiama proprio quel flusso, che spinge il prezzo di nuovo nella direzione del bias.

Onestà sul meccanismo: il benchmark di esecuzione è un flusso obbligato, e questo pesa a favore
(filtro 3). Ma gli algoritmi VWAP standard partecipano in proporzione al volume, non a un livello di
prezzo. Che il VWAP sia un livello a cui il prezzo «reagisce» è un passaggio in più, in parte
comportamentale (tanti lo guardano). Il critico deve trattarlo come un punto debole.

## Chi perde, e perché continua a perdere

Secondo Mario sono due.
- **Chi insegue il breakout**: compra sopra il range a prezzo peggiore, con lo stop più lontano,
  e viene scosso nel pullback. Continua perché il breakout è l'ingresso più visibile e più insegnato.
- **Chi sfuma il primo pullback**: vende il ritorno al VWAP pensando che il breakout sia fallito,
  e paga quando il flusso del giorno riprende. Continua perché nella metà dei giorni senza
  squilibrio vero la stessa mossa paga, e il rinforzo intermittente è quello che tiene vivo un errore.

Debolezza: sono due figure comportamentali, non un flusso obbligato che perde per forza. Gli
esecutori VWAP non «perdono» per noi: pagano un costo di impatto che spendono comunque. Se il critico
non accetta queste due figure, l'idea non ha un perdente nominato in modo solido.

## Fonti

1. **Strategia di un praticante (il corso citato da Mario).** Chi: il corso da cui viene il template
   `13. VWAP Pullback NQ Margin Vol 1min TF.txt`. Il nome dell'autore e del corso non è nel materiale
   (si nomina solo «Agnello» per la variante ADX). Dove: materiale del corso, riportato da Mario in
   `fonti/idea.md`. Quando: backtest su NQ 1 minuto dal 2021. Cosa dichiara: trade medio circa
   $80 per contratto NQ intero, profit factor 1,2, 58% di trade vincenti, con la versione che tiene
   overnight (la nostra è flat a fine giornata, quindi i numeri non valgono direttamente per noi).
   Variante ADX: 82% vincenti e trade medio $300 fuori campione. **Non verificata**: il codice ADX
   non è nel materiale. Non ci sono pagine: sono dichiarazioni del corso, da prendere come tali.
2. **«Il 90%+ del flusso istituzionale è benchmarked al VWAP».** Non entra come numero. Ho cercato
   una fonte con pagina (Madhavan, «VWAP Strategies», *Transaction Performance*, primavera 2002,
   pp. 32-38). Il PDF esiste, ma non sono riuscito a leggerne il testo, quindi non posso mettere il
   numero su una pagina. Resta l'affermazione qualitativa, standard nella letteratura di esecuzione:
   il VWAP è un benchmark di esecuzione molto diffuso. Nessuna percentuale.

Fonti con pagina verificata: zero. Il critico ne terrà conto. Filtri: è su futures (NQ) e il
campione è oltre il 2021, ma non è replicato né referato e non riporta i costi in modo esplicito.

## Regola eseguibile

**Mercato e dati.** NQ, barre da 1 minuto, serie continua del motore, 1 contratto (nella misura:
1 micro). Orari in ora di Chicago (CT). Convenzione: ogni barra porta l'orario di **chiusura**, come
in MultiCharts. La barra «08:31» copre 08:30:00–08:30:59. Giorni: tutte le sessioni regolari
lun-ven presenti nei dati.

**VWAP di sessione.** Si azzera all'apertura della sessione regolare, 08:30 CT. La prima barra è
quella delle 08:31. Per ogni barra: prezzo tipico = (massimo + minimo + chiusura) / 3.
VWAP(t) = somma(prezzo tipico × volume) / somma(volume), sulle barre da 08:31 a t comprese.
*Scelta dichiarata*: Mario scrive «VWAP di sessione» su un grafico Globex 24 ore. Ho scelto
l'ancoraggio alle 08:30 e non alle 17:00 perché il meccanismo che invoca è il benchmark delle
esecuzioni istituzionali, che si misura sulla sessione regolare. Il prezzo tipico è la lettura
più comune del VWAP su barre.

**Range d'apertura.** RH = massimo dei massimi e RL = minimo dei minimi delle barre da 08:31 a
09:00 comprese (30 barre).

**Bias (latched).** Dalla barra 09:01 in poi, la prima barra che chiude sopra RH fissa il bias
**long**, la prima che chiude sotto RL fissa il bias **short**. Una volta fissato il bias non cambia
più per il resto del giorno, anche se il prezzo poi rompe il lato opposto. Se nessuna barra chiude
fuori dal range entro le 14:00, quel giorno non c'è trade. Chiamo B la barra che fissa il bias.

**Retest e reclaim (long; per lo short tutto a specchio).** Si guardano solo le barre successive a B.
- *Retest*: la prima barra dopo B con minimo ≤ VWAP di quella barra.
- *Reclaim*: se la barra di retest chiude ≥ VWAP, è essa stessa il reclaim (tocco e tenuta). Se
  chiude sotto il VWAP, il reclaim è la prima barra successiva che chiude > VWAP.
- Conta solo il primo retest del giorno: dopo un retest si aspetta il suo reclaim, non se ne
  cercano altri.

Short: retest = prima barra dopo B con massimo ≥ VWAP; reclaim = la stessa barra se chiude ≤ VWAP,
altrimenti la prima successiva che chiude < VWAP.

**Ingresso.** Ordine a mercato nella direzione del bias, eseguito all'apertura della barra dopo il
reclaim («buy next bar at market», cioè alla chiusura del reclaim). La barra di reclaim deve avere
orario tra 09:01 e 14:00 compresi. Se il reclaim arriva dopo le 14:00, quel giorno non c'è trade.

**Pivot (definizione unica, usata per stop e target).** Una barra i è *pivot low di forza N* se il
suo minimo è strettamente minore dei minimi delle N barre prima e minore o uguale ai minimi delle
N barre dopo. Il pivot high è a specchio: massimo strettamente maggiore delle N barre prima e
maggiore o uguale alle N barre dopo. Un pivot è *confermato* alla chiusura della barra i+N, e si può
usare solo da lì in poi. Si usano barre della sessione Globex corrente, cioè dalle 17:00 CT del
giorno di calendario precedente, fino alla barra di reclaim compresa.
*Scelta dichiarata*: «StopSwingLen 20» e «TargetSwingLen 5» li leggo come forza N del pivot,
alla maniera di SwingLow/SwingHigh di MultiCharts. È coerente con il MaxBarsBack ≥ 42 del template
(2 × 20 + 1 barre).

**Stop (long).** Il pivot low di forza 20 confermato più recente con prezzo < prezzo d'ingresso.
Ordine stop a mercato esattamente a quel prezzo, senza margine. Fissato all'ingresso, non si
sposta. Short: pivot high di forza 20 confermato più recente con prezzo > ingresso.

**Target (long).** Il pivot high di forza 5 confermato più recente con prezzo > prezzo d'ingresso.
Ordine limite a quel prezzo, fissato all'ingresso. Short: pivot low di forza 5 confermato più
recente con prezzo < ingresso.

**Se manca lo stop o il target** (nessun pivot valido nella sessione Globex corrente): niente trade
quel giorno, e il setup è consumato. *Scelta dichiarata*: è la lettura più semplice. Ripiegare
sull'estremo del pullback (StopMode 2) sarebbe una regola in più.

**Stop e target nella stessa barra.** Si assume che sia stato toccato prima lo stop. È la lettura
prudente; su barre da 1 minuto non si può sapere.

**Uscita a tempo.** Se la posizione è ancora aperta, si chiude a mercato alla chiusura della barra
delle 14:55. Nei giorni a chiusura anticipata si chiude a mercato alla chiusura dell'ultima barra
della sessione regolare.

**Massimo trade al giorno: 1.** Il primo ingresso consuma la giornata, comunque finisca.

**Parametri liberi: nessuno.** 08:30–09:00, 09:00–14:00, 14:55, 20, 5 e 1 trade sono tutti di
Mario. Le scelte mie sono quelle dichiarate sopra: ancoraggio del VWAP, prezzo tipico, definizione
di pivot e di conferma, finestra di ricerca dei pivot, regola «niente pivot, niente trade», stop
prima del target nella stessa barra.

## Frequenza e costi

**Segnali al giorno.** Per costruzione al massimo 1. Mi aspetto il bias quasi ogni giorno e un
ritorno al VWAP con reclaim entro le 14:00 in poco più della metà dei giorni. Qualche setup cade
in più per pivot mancanti. Stima: **0,5–0,7 trade al giorno**. È una stima mia, non un numero di una fonte.

**Effetto contro costo.** Il corso dichiara circa $80 di trade medio su NQ intero, ma con
posizioni tenute overnight. Il costo di un trade su NQ intero: ingresso a mercato e stop a mercato
con circa 1 tick di slippage ciascuno ($5 a tick), il target è un limite, più la commissione di
andata e ritorno. Totale circa $10–20. Sul micro (un decimo) il trade medio lordo diventa circa
$8, contro circa $2–3 di costi.
L'effetto dichiarato supera il costo per trade. Ma vedi la sezione 7: non basta per la soglia in
dollari al giorno.

## Cosa la ucciderebbe, e la soglia della misura

Scritto prima di qualsiasi numero.

**Soglie (quelle del perimetro, nessuna più bassa):**
- eccesso sul caso / errore standard **≥ 3,0**;
- **≥ $10 al giorno per micro**, al netto dei costi, sul periodo 2020-01-01 → 2024-12-31. Mario
  scriveva IS dal 2021; la misura accetta solo il periodo del perimetro;
- in più la soglia di Mario, più severa sul singolo trade: **se con flat a fine giornata il trade
  medio sul contratto intero scende sotto $70 (sotto $7 per micro), l'idea è morta**.

**Cosa la ucciderebbe, e cosa mi aspetto già ora:**
1. **Frequenza sotto il minimo del perimetro.** Il perimetro chiede ≥ 1 segnale al giorno per
   l'intraday. Con il tetto di 1 trade al giorno, la regola arriva a 1 solo se ogni giorno dà un
   setup, e non succede. Mi aspetto 0,5–0,7: **per costruzione, la regola base sta sotto il
   minimo**. Il desk deve decidere se misurarla comunque come prova dell'impianto. Non ho cambiato
   la regola per rientrarci, perché la porta è `user`.
2. **I dollari al giorno non tornano nemmeno con i numeri del corso.** $10 al giorno per micro
   con 0,6 trade al giorno vogliono circa $17 netti per trade sul micro, cioè circa $170 sul
   contratto intero. Il corso dichiara $80 lordi, e con la posizione overnight. Anche se l'effetto
   fosse esattamente quello dichiarato, la soglia in dollari non si raggiunge. Me lo aspetto, e
   lo scrivo ora.
3. Il flat alle 14:55 taglia la parte del guadagno che nel corso veniva dalla tenuta overnight. Se
   era quella a fare il trade medio, l'idea è morta.
4. L'eccesso sul caso, misurato contro ingressi casuali nella stessa direzione del bias e nella
   stessa finestra, non supera 3 errori standard. In quel caso il VWAP non aggiunge niente al
   semplice breakout d'apertura.
5. I numeri del corso non sono verificati e non hanno una fonte con pagina. Se il prior viene
   solo da lì, va trattato come vicino a zero.

**Altre ipotesi nella fonte** (varianti di Mario per lo Stage 4, non aperte qui; il desk decide):
- gate ADX(14) > 20 o > 25 sul grafico a 5 minuti (la variante «Agnello», non verificata);
- StopMode 2: stop all'estremo del pullback invece che al pivot di forza 20;
- filtro MinRR 1: si entra solo se la distanza dal target è almeno pari alla distanza dallo stop;
- target fisso in R (0,5–1R) al posto del pivot;
- solo long.
