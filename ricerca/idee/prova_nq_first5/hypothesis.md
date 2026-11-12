# prova_nq_first5

Porta: user (idea di Mario, `fonti/idea.md`). Prova dell'impianto alla cieca: nessuna madre
nominata in `GIA_FATTO`. Qui c'è il caso base della sua SPEC, `UseFilters 0`, senza stop,
un trade al giorno. L'idea è messa in forma, non cambiata.

## Ipotesi

Su NQ la posizione del prezzo rispetto alla sua EMA a 12 barre da 5 minuti, presa alla chiusura
della prima barra della sessione cash di New York (08:30-08:35 CT), indica la direzione del
resto della seduta. Se si entra in quella direzione alle 08:35 e si esce alle 15:00 CT, la quota
di trade vincenti è più alta di quella di un random walk con la stessa geometria, e la
differenza basta a coprire i costi.

È falsificabile così: sull'in-sample 2020-2024 l'eccesso sul caso non arriva alla soglia della
sezione 7.

## Meccanismo

Quello che scrive Mario: all'apertura arrivano tutti insieme gli ordini istituzionali accumulati
fuori sessione, cioè ordini MOO, ribilanciamenti ed esecuzioni programmate. Quel flusso dà la
direzione alla giornata, e la parte che non si esaurisce nella prima barra continua a spingere
nella stessa direzione fino alla chiusura.

Per il filtro n. 3 conta una cosa: il meccanismo citato è un flusso obbligato (ordini che devono
essere eseguiti), ma la regola non lo misura. Il segnale non è la direzione dei primi 5 minuti:
è il prezzo alle 08:35 confrontato con una media che, su un grafico Globex a 24 ore, è fatta
soprattutto di barre della notte. Che il flusso d'apertura continui è un'ipotesi in più, e la
fonte non la documenta.

## Chi perde, e perché continua a perdere

Secondo Mario, chi fa fade dell'apertura e chi entra tardi. Non so dire perché non smettano: la
fonte non lo spiega, e io non ho un nome più preciso. Un controparte strutturale possibile sono i
market maker che danno liquidità contro il flusso d'apertura, ma per loro è un costo che mettono
nel prezzo, non una perdita che si ripete. Lo segnalo come punto debole: il critico può
ucciderla qui.

## Fonti

1. **Template del corso, fonte (18), citato in `fonti/idea.md`.** Strategia di un praticante. Chi
   e quando: il file non dice né autore né data, dice solo «template del corso (18)». Dove:
   materiale didattico, non pubblicato. Cosa dichiara: la regola della sezione 5 (5 minuti,
   barra che chiude alle 08:35 CT, close contro EMA(12), uscita alle 15:00 CT) e, secondo Mario,
   l'autore stesso la dichiara **non validata**. Non riporta numeri di performance. Nessun
   numero di questo file viene da qui.
2. **Zarattini, C. e Aziz, A. (2023), «Can Day Trading Really Be Profitable? Evidence of
   Sustainable Long-term Profits from Opening Range Breakout (ORB) Day Trading Strategy vs.
   Benchmark in the US Stock Market», working paper SSRN n. 4416622, non referato.** È
   l'effetto più vicino che ho trovato: su QQQ (ETF, non future) dal 2016 al 2023 usa la
   direzione della prima candela da 5 minuti per entrare long o short e tiene fino a fine
   giornata, con uno stop. **Pagina: non verificata.** Il PDF l'ho scaricato, ma non sono
   riuscito a estrarne il testo; quindi non riporto nessuno dei suoi numeri. È citato solo come
   letteratura vicina. Non è la regola di Mario: lì il segnale è la direzione della candela
   d'apertura, qui è close contro EMA(12), e lì c'è uno stop.

Nessun numero con pagina. Il prior viene dal meccanismo, non da un effetto misurato da qualcuno.

## Regola eseguibile

| | |
|---|---|
| Mercato | NQ, continuo, contratto intero (la misura riporta anche i dollari per micro, MNQ = 1/10) |
| Timeframe | barre da 5 minuti costruite dalle barre a 1 minuto del lake, allineate all'ora (:00, :05, ...). Ora di Chicago (CT), con l'ora legale gestita dal fuso |
| Convenzione del tempo | «la barra delle hh:mm» è quella che **chiude** alle hh:mm, come in MultiCharts. La barra delle 08:35 copre 08:30:00-08:34:59. *Scelta dichiarata*: se il lake marca le barre all'apertura, è la barra marcata 08:30 |
| Indicatore | EMA(12) sulle chiusure da 5 minuti, con alpha = 2/13, calcolata **in continuo su tutte le barre Globex**, notte compresa, senza azzerarla a ogni sessione (il grafico della fonte è «Globex 24h»). Si inizializza con la prima chiusura disponibile. *Scelta dichiarata*: il primo giorno dello storico si scarta come riscaldamento |
| Setup | ogni giorno di contrattazione che ha la barra delle 08:35 CT |
| Ingresso | alla chiusura della barra delle 08:35: close > EMA(12) → **long**; close < EMA(12) → **short**. Ordine al prezzo di chiusura della barra (fonte: «this bar at close»). *Scelta dichiarata*: con close = EMA non si entra |
| Stop | nessuno (caso base della fonte) |
| Target | nessuno |
| Uscita a tempo | alla chiusura della prima barra con orario ≥ **15:00 CT**, cioè la barra 14:55-15:00, al suo prezzo di chiusura |
| Giornate corte | *scelta dichiarata*, che traduce il backstop `SetExitOnClose` della fonte: se nella sessione non c'è una barra delle 15:00 (chiusure anticipate), si esce alla chiusura dell'ultima barra della sessione. Flat sempre a fine giornata |
| Finestra | ingresso solo alle 08:35; posizione aperta da 08:35 a 15:00 CT |
| Massimo al giorno | 1 trade |
| Filtri | nessuno (`UseFilters 0`) |
| Periodo | 2020-01-01 → 2024-12-31, solo in-sample |

## Frequenza e costi

- **Segnali:** uno per giorno di contrattazione, meno i rari casi con close = EMA o senza barra
  delle 08:35. Circa 250 l'anno, circa 1.250 sull'in-sample. Sta sul minimo del perimetro (1 al
  giorno) e, per `come_scegliere_un_paper.md` punto 5, vale da seconda gamba, non da prima.
- **Costo di un trade:** *assunzione dichiarata*: 1 tick di slippage per lato e la commissione
  del conto. Su NQ sono circa 2 tick, cioè $10, più la commissione; su MNQ circa $1 più la
  commissione. La misura usi i costi standard del motore.
- **Effetto contro costo:** la fonte non dichiara un effetto, quindi il confronto non si può
  fare sulla carta. Si può dire solo questo: un trade tenuto 6 ore e mezza su NQ ha un
  movimento tipico di decine o centinaia di punti, contro 2 tick di costo, quindi i costi non
  sono il collo di bottiglia. Lo è la varianza: con un solo trade al giorno e niente stop, i
  risultati per trade sono molto dispersi e servono molti anni per arrivare a t 3.

## Cosa la ucciderebbe, e la soglia della misura

**Soglia (scritta prima di qualsiasi numero):**

1. eccesso sul caso ad almeno **3,0 errori standard** sull'in-sample 2020-2024 (minimo del
   perimetro);
2. almeno **$10 al giorno per micro** al netto dei costi (minimo del perimetro);
3. *più severa del perimetro, scelta mia*: eccesso **positivo in entrambe le metà**
   dell'in-sample (2020-2022 e 2023-2024). Mario chiede le due metà per i filtri; io la chiedo
   anche al caso base, perché su un effetto d'apertura il cambio di regime dopo il 2021 (0DTE) è
   il rischio noto.

Se ne manca una, l'idea muore.

**Perché secondo me può non reggere (PORTA user: la regola resta quella di Mario):**

- **Filtro 1 (futures):** la fonte è un template di un corso, non validato, e la letteratura più
  vicina (Zarattini-Aziz) è su un ETF, con un segnale diverso e con lo stop.
- **Filtro 2 (replica):** nessuna replica indipendente che conosco con pagina.
- **Filtro 3 (meccanismo):** il flusso d'apertura è reale, ma esce in buona parte con l'asta
  delle 08:30 e quindi sta già dentro la prima barra. Che continui fino alle 15:00 non è
  dimostrato, e la regola misura una cosa diversa: prezzo contro media della notte.
- **Filtro 8 (campione dopo il 2021):** il template non ha un campione; Zarattini-Aziz arriva al
  2023, ma su QQQ.
- **Chi perde:** non nominato in modo convincente (sezione 3).
- **Senza stop non si usa in prop:** lo dice Mario stesso. Anche se la misura passasse, la
  variante con lo stop deve reggere, e il suo kill (avg trade netto < $70 o WR < 50%) resta.

**Altre ipotesi nella fonte**, da aprire eventualmente come idee nuove, una riga ciascuna:
- con stop in punti come frazione dell'ADR (`StopPts` > 0), la variante necessaria per la prop;
- con i filtri: range della barra di riferimento ≥ 0,15 × ADR(20) e ADR(20) ≥ 1,10 × ADR(100);
- solo short (`AllowLongs 0`);
- EMA a 8 o a 20 barre. Questa è una ricerca di parametro, non un'idea: sconsiglio di aprirla.
