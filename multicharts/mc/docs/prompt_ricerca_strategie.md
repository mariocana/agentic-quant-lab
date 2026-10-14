# Prompt per la ricerca di strategie candidate

Da incollare in una sessione nuova (o a un agente di ricerca). Serve a far **proporre
candidate**, non a far valutare: la valutazione resta la pipeline in `pipeline_prop.md`.

**Perché esiste questo file.** Un agente senza contesto riporta le stesse strategie che
abbiamo già ucciso, perché la letteratura pubblica non riporta mai il numero che ci uccide:
il **rischio per trade per contratto micro**. Il valore del prompt sta nei vincoli, che sono
il risultato di quattro strategie morte.

Aggiornare questo file quando muore una strategia o cambia un vincolo.

---

## Il prompt

```
Devi propormi strategie di trading sistematico candidate a un obiettivo molto specifico.
Non devi valutarle a fondo né backtestarle: devi proporle e dirmi, per ciascuna, se
sopravvive ai vincoli che trovi sotto. Se non puoi stabilirlo, dillo invece di indovinare.

# L'OBIETTIVO, UNICO

Passare la valutazione di una prop firm (LucidFlex, conto da 50k) e incassare i payout.
Non "fare trading", non "capire i mercati": passare l'eval. Una strategia profittevole che
non passa l'eval non serve.

# I VINCOLI DEL CONTO — questi sono rigidi

- Target: +$3.000
- Massima perdita (MLL): $2.000, trailing su base EOD, si blocca a $52.100
- Regola di consistenza: nessun giorno può valere più del 50% del profitto totale
- Nessun daily loss limit
- Size massima: 4 contratti mini o 40 micro
- Automazione permessa
- FLAT A FINE GIORNATA OBBLIGATORIO. Nessuna posizione overnight, mai.
  Questo esclude in blocco: strategie da calendario con hold multi-giorno, anomalie
  overnight, swing, pair trading a più giorni.
- Esiste una REGOLA DI INATTIVITÀ: un conto funded si perde anche per non aver operato.
  Una strategia che fa 20 trade l'anno è inutilizzabile anche se è profittevole.

# IL VINCOLO CHE UCCIDE — leggilo due volte

Lo sviluppo avviene su 1 contratto grande, l'operatività su micro (1/10 del grande).
Il numero che decide tutto è:

    RISCHIO PER TRADE, IN DOLLARI, SU UN CONTRATTO MICRO

Deve stare sotto $500. Con un MLL di $2.000 significa quattro perdite piene di margine.

Tradotto in punti, per gli strumenti plausibili:
  - MNQ (Nasdaq micro), $2 per punto   -> stop massimo 250 punti
  - MES (S&P micro),    $5 per punto   -> stop massimo 100 punti
  - MGC (oro micro),    $10 per punto  -> stop massimo  50 punti
  - M2K (Russell micro),$5 per punto   -> stop massimo 100 punti

E il drawdown su cinque anni, sempre per micro, deve stare sotto $1.000 (storico) e sotto
$2.000 al 95° percentile di un Monte Carlo con riordinamento.

Quattro strategie sono già morte qui. Tre su @NQ con drawdown per micro di $3.121, $3.109
e $5.784 contro un tetto di $1.000. La quarta ha passato il vincolo di rischio e è morta
per mancanza di edge.

QUINDI: se una candidata non ti permette di stimare il rischio per trade in punti, non
proporla, o proponila dicendo esplicitamente che quel numero manca. È il primo filtro,
non l'ultimo.

# IL SECONDO VINCOLO CHE UCCIDE: il pavimento dei costi

I costi, con lo slippage ripiegato dentro la commissione:
  - NQ: $7,50 per lato = $15 andata-ritorno
  - GC: $12,50 per lato = $25 andata-ritorno
  - ES: $15,00 per lato = $30 andata-ritorno

Il trade medio NETTO richiesto è >= $70 su NQ e >= $140 su GC, per contratto grande.
Significa che serve un edge LORDO di almeno 3 volte il costo andata-ritorno.

Una strategia è già morta con un edge lordo di $46 per trade su GC: l'edge esisteva ma
i costi se ne mangiavano metà. Valuta sempre l'edge atteso per trade CONTRO il costo, non
in assoluto e non in percentuale.

# IL PROFILO RICHIESTO — non negoziabile, è la forma dell'eval

  - Win rate >= 55%
  - Rapporto vincita media / perdita media fra 0,5 e 1
  - Almeno 200 trade su cinque anni (2020-2024), cioè >= 40 all'anno
  - Profit factor >= 1,2
  - Nessun anno che valga più del 50% del profitto totale

Nota bene la combinazione: ALTO win rate con R:R PICCOLO. Questo esclude per costruzione
l'intera famiglia trend following / breakout con R:R 2-3 e win rate 35-40%, che è la
maggior parte di quello che trovi pubblicato. Non propormela "perché è robusta": non
rispetta il profilo e non passa il gate.

# TRE ANTI-PATTERN, imparati sul campo. Non riproporli.

1. BREAKOUT DIREZIONALE INTRADAY SU @NQ.
   Tre strategie indipendenti, logiche diverse, tutte morte sullo stesso numero. Il
   nozionale del Nasdaq è troppo grande perché il rischio per trade entri in un MLL da
   $2.000, anche in micro. Serve una ragione forte e specifica per tornarci.

2. UNITÀ DI RISCHIO CHE SCALA CON LA VOLATILITÀ REALIZZATA SENZA UN TETTO.
   Una strategia con "stop = ampiezza del range di sessione" sembrava eccellente su quattro
   mesi recenti e si è disintegrata su cinque anni, perché in quei quattro mesi la
   volatilità era eccezionale. L'edge per trade scala con la volatilità, i costi no.
   Se proponi uno stop in ATR o in frazioni di un range, deve avere un TETTO in punti.

3. UNITÀ DI RISCHIO NON DICHIARATA.
   Una strategia con stop "all'ultimo pivot swing" produce stop da 0,25 punti a 386 punti:
   un rapporto di 1.500 volte, con il 10% dei trade che ha uno stop indistinguibile dal
   rumore. Lo stop deve essere DICHIARATO PRIMA (punti fissi, o ATR con tetto e pavimento),
   non scoperto dopo.

# VINCOLI TECNICI

- Piattaforma: MultiCharts, linguaggio PowerLanguage (dialetto EasyLanguage).
- I dati continuous (@NQ, @GC) sono BACK-ADJUSTED: i livelli storici sono traslati. Quindi
  qualunque logica in percentuale di prezzo su un continuous è inaffidabile. Preferisci
  logiche in punti o in ATR.
- Non abbiamo: dati di order flow o profondità del book, dati di opzioni/gamma, dati COT in
  tempo reale, dati non back-adjusted, strumenti Eurex.
- Serve codificabilità in regole deterministiche. Niente che richieda giudizio umano,
  lettura di news o output di un LLM.

# REGOLA DI PROCESSO — vale anche per te

Il materiale esterno produce STRATEGIE E VARIANTI, mai modifiche ai criteri di
valutazione. Se concludi che i gate sono troppo severi, scrivilo come osservazione
separata e vai avanti a proporre dentro i vincoli. Non riscrivere i vincoli per far
entrare una candidata: è il modo in cui si costruiscono backtest che non sopravvivono.

# COSA CONSEGNARE

Prima una tabella di sintesi, ordinata da migliore a peggiore:

| # | Nome | Strumento · TF | Famiglia | Stop dichiarato (punti -> $/micro) | n/anno attesi | WR atteso | R:R atteso | Fonte | Verdetto |

Poi, per ogni candidata che sopravvive ai filtri, mezza pagina con:

  - IPOTESI: cosa dovrebbe accadere nei prezzi, in una frase.
  - PERCHÉ DOVREBBE FUNZIONARE: il meccanismo, e soprattutto CHI PERDE i soldi che
    guadagneremmo. Se non sai dire chi sta dall'altra parte, dillo: è un segnale debole.
  - REGOLE: sessione e orari, condizione d'ingresso, stop, target, uscita a tempo. Precise
    abbastanza da essere codificate, non descrizioni vaghe.
  - RISCHIO PER TRADE: in punti e in dollari per micro. È il numero che guardo per primo.
  - PERCHÉ RISPETTA IL PROFILO: come ottiene WR >= 55% con R:R fra 0,5 e 1.
  - COSA LA FALSIFICA: quale misura, fatta prima del backtest, la ucciderebbe. Questo è
    il campo più utile di tutti, perché è quello che ci fa spendere un'ora invece di tre
    giorni.
  - FONTE: paper, libro, articolo, forum, con link se esiste. Distingui fra "testato da
    qualcuno con dati" e "affermato".
  - COSA NON SO: i dati che la fonte non riporta. Quasi nessuno pubblica il drawdown per
    contratto, quindi questo campo sarà quasi sempre pieno.

Chiudi con una lista di candidate SCARTATE e il motivo in una riga, così non le
ripropone nessuno la prossima volta.

# QUANTE

Da cinque a otto candidate serie, non venti superficiali. Preferisco tre proposte dove so
cosa misurare domani mattina, che quindici nomi da cercare.

Se la tua ricerca converge su "non esiste niente che rispetti questi vincoli", è un
risultato legittimo e lo voglio sapere: significa che il problema è il conto da 50k e non
le strategie.
```

---

## Dopo che l'agente ha risposto

Le candidate **non entrano in pipeline automaticamente**. Il percorso resta:

1. Una riga nel journal degli ingest (`ingest_journal.md`) con il verdetto.
2. Per quelle che passano: `SPEC.md` in `mc/strategies/<Nome>/` = Stage 0, con ipotesi,
   perché, date IS/OOS, varianti pre-registrate e condizione di kill.
3. **Prima dello Stage 1**, per ogni candidata: misurare la distribuzione del rischio per
   trade sull'**IS**, non su un campione recente. È la lezione di Gold Asian Range.
