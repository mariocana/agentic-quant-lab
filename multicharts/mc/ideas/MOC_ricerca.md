# MOC e ultimi 10 minuti — scheda di ricerca

Materiale di partenza raccolto da Stucchi (podcast Savius ep. 8, Masterclass parte 2,
Liquidity Bootcamp), più una traccia di ricerca. Le parti marcate **[da verificare]**
sono informazioni di contesto che non vengono da Stucchi: controllale sulle fonti
ufficiali prima di usarle.

---

## 1. Cosa dice Stucchi

### Trascrizione (podcast Savius Traders Talk ep. 8, 45:42–48:40)

Fonte: `transcripts/7_Savius_Traders_Talk_ep8_grande_ritorno_stucchi.txt`. Trascrizione
automatica (whisper), ripulita solo della punteggiatura. "mock in balance" = MOC imbalance.

> […] uno di questi importanti che per me è fondamentale è l'orologio. Io faccio trading
> con l'orologio, nel senso che per me un orario o un altro fanno completamente cambiare
> il mio modo di lavorare, perché so che ci sono dei momenti della giornata in cui c'è
> una maggiore partecipazione degli operatori, e questa la vedo semplicemente analizzando
> i volumi. So che all'apertura dei mercati c'è un grosso volume, c'è un grosso volume
> alla chiusura dei mercati: 15:30 Wall Street, parlo di orari italiani, 22 Wall Street
> sono due momenti di grossi picchi di volume. L'ultima ora, quella che viene detta anche
> power hour o rush hour come la chiamo io, è un periodo in cui concentro la maggior parte
> della mia operatività. Faccio trading nelle ultime due o tre ore della giornata, perché
> so che lì per me è più facile, è più prevedibile, ho più movimenti, ho più volumi, ho
> più aiuti, ho più edge.
>
> Anche questo è un altro esempio importante: gli ultimi 10 minuti sono critici, perché ci
> sono tutti gli arbitraggi sui market on close imbalance. Cosa significa? Significa che
> gli operatori possono fino alle 21:50 italiane mettere gli ordini di chiusura, che
> verranno eseguiti sul mercato dall'exchange alle 22, nei pressi delle 22. Alle 21:50 si
> chiude la possibilità di mettere e di cancellare questi tipi di ordine. Alle 21:50
> precise esiste un valore che viene fornito, che si chiama MOC imbalance, market on close
> imbalance, e ti dice quante sono le persone che vogliono fare un buy e quante vogliono
> fare un sell alla chiusura del mercato. Ci sono degli algoritmi che leggono questa cosa
> e spostano il prezzo per cercare di riequilibrare, perché sanno che alla chiusura ci
> sarà questo imbalance. Questo è un esempio di movimento degli ultimi 10 minuti, che io
> tempo fa, nei miei video sul canale, avevo chiamato "il palin" [nome non chiaro nella
> trascrizione]. È un movimento che nasce da questa logica e va conosciuto come una
> statistica importante.

### Punti chiave

1. Picchi di volume all'apertura (15:30 CET) e alla chiusura (22:00 CET) di Wall Street.
2. Stucchi concentra la sua operatività nelle **ultime 2–3 ore** della sessione USA su ES.
3. **21:50 CET**: ultimo momento per inserire o cancellare ordini MOC; esce il dato di
   MOC imbalance (quanto c'è da comprare e da vendere in chiusura).
4. Negli ultimi 10 minuti gli algoritmi leggono l'imbalance e muovono il prezzo per
   "riequilibrarlo" prima dell'asta di chiusura.
5. Lo considera una statistica ricorrente da conoscere. Il nome che gli dava nei vecchi
   video non si capisce dalla trascrizione: cercalo sul suo vecchio canale YouTube.
6. Nel Bootcamp (*LB 41*) cita il MOC tra gli strumenti con cui i grandi operatori
   eseguono size senza muovere il mercato ("special order types: MOC, block trades,
   intermarket sweep, MTF, dark pools").

### Il collegamento con il GEX (Masterclass parte 2, slide 139–140)

<img src="img/moc/gexbot_spx_1556.jpg" width="49%"> <img src="img/moc/gexbot_spx_close_attrattori.jpg" width="49%">

*SPX il 12/12/25 alle 15:56 ET e in chiusura. Nota sulla slide: "Negli ultimi 10 minuti i
livelli più colmi fanno da attrattori del prezzo". Gli strike 0DTE con più gamma tirano
il prezzo in chiusura, quando il gamma delle opzioni in scadenza è massimo.*

### Lo stesso fenomeno su un altro mercato: il settlement del petrolio (Bootcamp 165–166)

<img src="img/moc/cl_settlement_pattern_cet.jpg" width="49%"> <img src="img/moc/cl_settlement_range_per_minute_et.jpg" width="49%">

*Sinistra: CL, movimento iniziale alle 14:15 ET e continuazione fino al settlement delle
14:30 ET. Destra: range medio per minuto del CL negli ultimi 16 anni (ET), con picchi
agli orari fissi e nella finestra di settlement. È il tipo di statistica "con
l'orologio" che Stucchi usa: la stessa analisi si può fare per ES tra 15:50 e 16:00 ET.*

---

## 2. Contesto di mercato [da verificare]

Informazioni generali sull'asta di chiusura USA, da confermare sui documenti ufficiali
(NYSE "Closing Auction", Nasdaq "Closing Cross" e "Net Order Imbalance Indicator",
specifiche CME dei future E-mini).

| Cosa | Orario ET | Orario CET normale | Settimane di sfasamento ora legale |
|---|---|---|---|
| Stop inserimento/cancellazione ordini MOC e LOC (NYSE e Nasdaq) | 15:50 | 21:50 | 20:50 |
| Inizio pubblicazione dei dati di imbalance | 15:50 | 21:50 | 20:50 |
| Asta di chiusura cash | 16:00 | 22:00 | 21:00 |
| Settlement giornaliero ES (VWAP dell'ultimo mezzo minuto prima delle 15:00 CT) | 15:59:30–16:00 | 21:59:30–22:00 | 20:59:30–21:00 |

Altre cose da sapere:
- Dopo le 15:50 ET, su NYSE sono ammessi di norma solo ordini che **compensano**
  l'imbalance pubblicato (closing offset). Per questo il dato delle 15:50 è
  informativo: chi arriva dopo può solo stare dalla parte opposta.
- L'imbalance è enorme nei giorni di **ribilanciamento degli indici** (S&P trimestrale, il
  terzo venerdì di marzo, giugno, settembre e dicembre, lo stesso giorno della scadenza
  trimestrale delle opzioni; ricostituzione Russell a fine giugno) e spesso a **fine
  mese**. In quei giorni è la variabile che conta di più negli ultimi 10 minuti.
- Il dato di imbalance in tempo reale è a pagamento (feed di borsa). Una stima del totale
  (es. "$X miliardi da comprare") viene spesso riportata da Bloomberg, newsletter o
  account social verso le 15:50 ET: va trattata come indicativa.

---

## 3. Domande di ricerca

Ordinate dalla più semplice (bastano i tuoi dati ES/NQ a 1 minuto) alla più complessa.

1. **Volatilità per minuto 15:00–16:00 ET su ES.** C'è un salto di range e di volume
   dopo le 15:50, come nel grafico del CL? Quanto vale in punti?
2. **Direzione degli ultimi 10 minuti rispetto alla giornata.** Il rendimento
   15:50–16:00 continua o inverte quello 09:30–15:50? Cambia nei trend day (giornate
   con chiusura vicino a massimo o minimo)?
   **Ipotesi di Stucchi** (Liquidity Bootcamp, Day 1, 0:11:17): «quando arriva il market
   on close, 10 minuti prima della chiusura, il 75% delle volte la direzione è la stessa
   della direzione principale della giornata: è una continuazione». Da verificare: cosa
   si intende per "direzione principale" (apertura→15:50? VWAP?) e se il 75% regge su ES.
3. **Giorni speciali.** Fine mese, scadenza trimestrale e ribilanciamento, ricostituzione
   Russell rispetto ai giorni normali: range e direzione degli ultimi 10 minuti.
4. **Imbalance noto.** Con il segno e la dimensione del MOC imbalance delle 15:50 (se
   trovi una fonte storica), il prezzo va nella direzione dell'imbalance fino alle 16:00?
   Oppure lo sconta prima, tra 15:50 e 15:55, e poi torna indietro?
5. **Attrazione verso gli strike.** Negli ultimi 10 minuti il prezzo si avvicina allo
   strike 0DTE con più gamma (dato gexbot)? Con che frequenza chiude entro pochi punti
   da quello strike?
6. **Settlement ES.** Il VWAP di settlement (15:59:30–16:00 ET) crea movimenti propri
   rispetto all'asta cash?

---

### Altre statistiche dette a voce da Stucchi (Bootcamp Day 1, da verificare)

- I gap si chiudono il **65%** delle volte nella stessa sessione.
- L'oro tende a salire il venerdì pomeriggio; il petrolio a scendere il lunedì mattina.
- CL: movimento iniziale circa 15 minuti prima del settlement delle 14:30 ET,
  accelerazione negli ultimi 5 minuti (Day 3, 0:38:56; slide *LB 165–166*).

Fonte: `mc/education/enrico_stucchi/transcripts/8_Liquidity_Bootcamp_Day1.txt` e
`BOOTCAMP_video_vs_slide.md`.

## 4. Come usarla oggi

- **Nel discrezionale**: è il motivo della regola "niente ingressi dopo le 21:50"
  nella power hour (playbook §5.3). Dopo quell'ora il prezzo lo muovono algoritmi che
  vedono un dato che tu non hai in tempo reale.
- **Nel sistematico**: se le domande 1–3 mostrano un comportamento stabile, diventa una
  candidata per la pipeline prop (Stage 0: spec con ipotesi, finestra 15:50–16:00 ET,
  date IS/OOS e criteri di kill decisi prima). È il tipo di edge "con l'orologio" che si
  testa meglio con un sistema che a occhio.

---

## 5. Fonti da cercare

- NYSE: documento "NYSE Closing Auction" (fact sheet) e regole su MOC/LOC e closing
  offset.
- Nasdaq: "Nasdaq Closing Cross" e "Net Order Imbalance Indicator (NOII)".
- CME: "E-mini S&P 500 daily settlement procedure".
- S&P Dow Jones Indices: calendario dei ribilanciamenti trimestrali.
- FTSE Russell: calendario della ricostituzione.
- Vecchi video di Stucchi sul suo canale YouTube: il pattern degli ultimi 10 minuti.
