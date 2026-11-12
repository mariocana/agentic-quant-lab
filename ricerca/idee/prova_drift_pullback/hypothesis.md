# prova_drift_pullback

> Porta `user`: è l'idea di Mario (DriftPullback v2.1, dal corso di Francesco Agnello), messa
> in forma senza cambiarla. Dove la sua SPEC non dice un dettaglio, la scelta è dichiarata
> come tale. Nessuna madre nel cimitero da nominare: prova alla cieca.

## Ipotesi

Su NQ, quando il prezzo a 15 minuti chiude oltre il VWAP di sessione, il VWAP sale (o scende)
nella stessa direzione e l'ultima ora ha già fatto almeno lo 0,10%, la prima barra a 5 minuti
contro quella direzione è una pausa e non un'inversione: entrando alla barra dopo, il prezzo
tocca un target corto (40 punti long, 50 short) prima di uno stop largo (80 punti) più spesso
di quanto serve per pareggiare, cioè più del 67% delle volte sui long e del 62% sugli short,
costi compresi.

È falsa se, sul 2020-2024, il risultato per trade non supera quello di ingressi casuali con
lo stesso bracket, la stessa direzione e la stessa ora, di almeno 3 errori standard.

## Meccanismo

Quello che scrive Mario: i trend intraday sui futures su indice sono spinti da flussi che non
si esauriscono in una stampata sola. Ne nomina tre: ribilanciamenti sistematici, hedging dei
book di opzioni, inseguitori di momentum che arrivano tardi. Un pullback poco profondo dentro
un drift già stabilito sarebbe presa di profitto o caccia agli stop, non un cambio di
direzione.

Detto piano: dei tre flussi, solo l'hedging dei dealer di opzioni (quando sono corti gamma
comprano dopo i rialzi e vendono dopo i ribassi) è un flusso obbligato. Gli altri due sono un
racconto comportamentale. E la regola non condiziona su nessuno dei tre: non guarda il gamma,
non guarda il calendario dei ribilanciamenti. Prende tutti i drift da 0,10% in un'ora, sia
quelli spinti da un flusso obbligato sia quelli che non lo sono. Il meccanismo quindi spiega
perché l'effetto potrebbe esistere in media, non quando esiste.

## Chi perde, e perché continua a perdere

Secondo Mario: chi va contro la prima discesa dentro un rialzo (o la prima salita dentro un
ribasso), e chi insegue tardi pagando lo spread al momentum. Noi daremmo liquidità di
continuazione a un prezzo un po' migliore di quello dell'inseguitore.

Perché non smettano, la fonte non lo dice. Il contrarian che vende la prima barra rossa in un
rialzo non è obbligato a farlo; l'inseguitore tardivo paga un tick o due, che è il costo
normale di chi vuole eseguire subito. L'unica controparte che non può smettere è il dealer
corto gamma che deve coprirsi, ma lui sta dalla nostra stessa parte, non dall'altra. Lo
scrivo così: **la controparte che perde non è nominata in modo convincente**.

## Fonti

1. **Francesco Agnello, tutorial «DriftPullback» (v2.1), materiale del corso**, file
   `mc/education/protocollo/11. Strategy Feedbacks/1. DriftPullback_Tutorial_.pdf`, 18 pagine,
   più la live 002 del corso. Strategia di un praticante. Dichiara: strategia validata e in
   live su conti funded; profilo media $77 a trade, win rate 65%, t-stat fuori campione 2,2;
   regole e parametri come nella sezione sotto. **Pagina non verificata**: il PDF non è nel
   repo e non l'ho potuto aprire; i numeri li riprendo da come Mario li ha trascritti in
   `ricerca/idee/prova_drift_pullback/fonti/idea.md`. Il sorgente originale non è
   disponibile: il codice esistente è una riscrittura dal PDF. Non è indicato se i $77 sono a
   contratto mini o micro (vedi sezione 6).
2. **Zarattini, Aziz, Barbon (2024), «Beat the Market: An Effective Intraday Momentum
   Strategy for S&P500 ETF (SPY)», Swiss Finance Institute Research Paper n. 24-97 (working
   paper, non referato; SSRN 4824172).** È la fonte più vicina alla «famiglia fast alpha»
   che Mario cita come «Zarattini & Pagani»: un paper con quei due autori non l'ho trovato.
   Dall'abstract (non ho potuto aprire il testo, quindi nessuna pagina): momentum intraday
   su SPY dal 2007 all'inizio del 2024, ingresso quando il prezzo esce da una banda di
   rumore, con trailing stop; dichiara 1.985% di rendimento totale netto dei costi, 19,6%
   annuo, Sharpe 1,33, e analizza lo sbilanciamento gamma dei dealer. **I suoi numeri non
   entrano nel prior**: niente pagina, è su un ETF e non su futures, e la regola è diversa
   (insegue il breakout, non il pullback).

Nessun numero della regola viene da una fonte con pagina verificata.

## Regola eseguibile

**Mercato e dati.** NQ continuo (`@NQ`), periodo 2020-01-01 → 2024-12-31. Due serie costruite
dalle barre a 1 minuto: **data1 = 5 minuti** (esecuzione), **data2 = 15 minuti** (segnale).
Tutti gli orari in **ora di Chicago (CT)**. Un contratto per trade.

**Giornata di trading.** La sessione Globex: dalle 17:00 CT del giorno prima alle 14:55 CT
(ora del flat). *Scelta dichiarata*: Mario scrive «Globex 24h, chart CT» e «tutti i default
di sessione»; la lettura più semplice è che la giornata, il VWAP e i contatori ripartano
all'apertura Globex delle 17:00 CT, non all'apertura cash delle 08:30.

**Ancora.** VWAP di sessione calcolato sulla serie a 15 minuti: somma di (prezzo tipico ×
volume) / somma del volume, dalla prima barra delle 17:00 CT. Prezzo tipico = (H+L+C)/3.
*Scelta dichiarata*: è la definizione standard; la SPEC dice solo «VWAP di sessione»
(`AnchorType 2`).

**Armamento** (valutato solo alla chiusura di ogni barra a 15 minuti):
- **long armato** se tutte e tre:
  1. close 15m > VWAP;
  2. VWAP di questa barra > VWAP della barra 15m precedente (ancora inclinata in su);
  3. drift 1h = (close 15m − close 15m di 4 barre prima) / close 15m di 4 barre prima ≥ +0,10%.
- **short armato** se: close 15m < VWAP, VWAP < VWAP precedente, drift 1h ≤ −0,10%.
- *Scelte dichiarate*: l'inclinazione è il confronto con la sola barra precedente; il drift
  1h sono le ultime 4 barre a 15 minuti. Le prime 4 barre della sessione non possono armare
  (manca l'ora di storia nella sessione).
- Un armamento apre una finestra di **6 barre a 5 minuti** che cominciano dopo la chiusura
  della barra 15m che ha armato. Se alla chiusura 15m successiva le condizioni valgono ancora,
  la finestra riparte da capo da lì; se valgono nella direzione opposta, l'armamento si gira;
  se non valgono più, la finestra in corso resta aperta fino alla sua scadenza. *Scelta
  dichiarata*: la SPEC non dice cosa succede al riarmo; questa è la lettura più semplice.

**Trigger** (serie a 5 minuti, dentro la finestra):
- long: la prima barra 5m che chiude **rossa** (close < open);
- short: la prima barra 5m che chiude **verde** (close > open);
- una barra con close = open non è un trigger;
- al trigger: **ordine a mercato all'apertura della barra 5m successiva** (*next bar at
  market*). Il trigger consuma l'armamento: per un altro ingresso serve un nuovo armamento.

**Bracket** (fisso, dal prezzo di riempimento, piazzato subito):
- stop: **80 punti** contro (long e short);
- target: **+40 punti** sui long, **+50 punti** sugli short, ordine limite;
- slippage sullo stop: **2 tick** (0,50 punti), come `StopSlipTicks 2` della configurazione
  validata. Se nella stessa barra a 1 minuto vengono toccati stop e target, conta lo stop
  (*scelta dichiarata*: la lettura prudente).

**Flat.** Alle **14:55 CT** ogni posizione aperta si chiude a mercato e gli armamenti si
annullano. Nessun ingresso dopo le 14:50 CT (l'ultima barra 5m che può aprire un trade è
quella delle 14:50, che chiude alle 14:55: *scelta dichiarata*, un ordine sulla barra delle
14:55 uscirebbe nello stesso istante). Nessuna posizione tra le 14:55 e le 17:00.

**Guardrail giornalieri** (per giornata Globex):
- una posizione alla volta: mentre si è in posizione, i trigger si ignorano;
- al massimo **4 ingressi** al giorno;
- dopo **2 trade chiusi in perdita** nel giorno, nessun nuovo ingresso fino alle 17:00 CT.
  Un trade chiuso al flat delle 14:55 con risultato negativo conta come perdita.

**Varianti escluse.** Mario dichiara validata anche l'ancora SMA(20) a 15 minuti
(`AnchorType 0`); qui si misura solo il VWAP, che è la configurazione di riferimento. Nessun
parametro è da ottimizzare: 0,10%, 6 barre, 80/40/50 punti, 4 ingressi, 2 perdite sono
quelli della SPEC.

## Frequenza e costi

**Segnali al giorno.** La SPEC dichiara 1-4 trade al giorno. Mi aspetto **circa 1,5-2 al
giorno** in media: su una sessione di 22 ore un drift da 0,10% in un'ora capita più volte, e
in quasi tutte una barra a 5 minuti contraria arriva entro mezz'ora; il tetto di 4 e lo stop
dopo 2 perdite tagliano le giornate più attive. Sopra il minimo del perimetro (1 al giorno).

**Costi.** Tick NQ = 0,25 punti = $5 sul mini, $0,50 sul micro. Ingresso a mercato (circa 1
tick), stop con 2 tick di slippage, target a limite senza slippage, più la commissione. In
tutto circa 1-3 tick a trade, 0,25-0,75 punti.

**Effetto contro costo.** Con stop a 80,5 punti, il pareggio richiede un tasso di successo del
66,8% sui long (80,5 / 120,5) e del 61,7% sugli short (80,5 / 130,5), prima delle uscite al
flat. Il 65% dichiarato sta sotto il pareggio dei long e poco sopra quello degli short: il
margine è di pochi punti percentuali. I $77 a trade dichiarati, se sono a contratto mini,
valgono circa 3,9 punti: cinque-quindici volte il costo, ma su un bracket da 80 punti, quindi
uno o due stop in più ogni cento trade li cancellano. Se fossero a micro (38 punti a trade su
un target da 40) sarebbero implausibili: li leggo come mini.

## Cosa la ucciderebbe, e la soglia della misura

**Soglia (scritta prima di qualsiasi numero), sul 2020-01-01 → 2024-12-31, costi inclusi:**
- eccesso sul caso ≥ **3,0 errori standard** (il minimo del perimetro, non più basso);
- ≥ **$10 al giorno per micro**;
- ≥ **1 setup al giorno** in media.

Basta che una delle tre manchi e l'idea muore.

**Cosa la ucciderebbe anche passando la soglia:**
- l'eccesso viene tutto da un lato (solo long) e il lato short è negativo: allora è il drift
  rialzista del Nasdaq 2020-2024, non la continuazione dopo il pullback;
- l'eccesso viene tutto da un anno (2020 o 2022, gli anni con le tendenze più forti);
- l'eccesso viene dalle uscite al flat delle 14:55 e non dai target: allora il bracket non sta
  facendo quello che dice il meccanismo.

**Perché secondo me può non reggere** (porta `user`: lo scrivo qui senza cambiare l'idea):
- l'autore stesso dichiara un t fuori campione di **2,2**, sotto la nostra soglia di 3: già il
  suo numero, preso per buono, non basterebbe;
- la fonte è un praticante, non un paper; i suoi numeri non sono verificabili a pagina e il
  sorgente non c'è: misuriamo una riscrittura;
- la famiglia «fast alpha» citata come base è su SPY, non su futures, e insegue il breakout
  invece del pullback (filtro 1 di `come_scegliere_un_paper.md`);
- il meccanismo ha un solo flusso obbligato (hedging dei dealer) e la regola non lo usa; chi
  perde dall'altra parte non è nominato in modo convincente (filtro 3);
- un bracket 80/40 vive di tasso di successo: con un pareggio al 67% sui long, uno scarto di
  pochi punti nel win rate cambia il segno del risultato.

Altre ipotesi nella fonte, da aprire eventualmente come idee nuove:
- la stessa regola con ancora SMA(20) a 15 minuti al posto del VWAP (`AnchorType 0`).
