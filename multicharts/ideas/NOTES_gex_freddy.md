# GEX / GEXBot — *Class summary Freddy 19.05* · valutazione

File: `mc/ideas/Class summary Freddy 19.05.pdf` (22 pp., note di studio di una lezione).
Tema: usare la **gamma exposure** e GEXBot come mappa operativa su NQ / NDX / QQQ.

## Verdetto: **playbook**, non pipeline algo

Decisione di Mario, e i contenuti la confermano. Sotto: la sintesi utile al playbook e le
ragioni per cui non entra nel protocollo.

---

## Sintesi per il playbook

### L'idea centrale
GEX **non è un segnale, è una mappa**. I market maker di opzioni devono restare
delta‑neutrali: quando il prezzo entra in zone di forte open interest, il loro hedging
produce flusso sui futures. La lezione insegna a leggere dove quel flusso è concentrato,
non a entrare perché compare un livello.

Sequenza dichiarata: **livello prima, reazione poi, ingresso per ultimo.**

### Il flusso decisionale
1. **Regime di volatilità** — alta o bassa.
2. **Struttura macro** — trend rialzista, ribassista, o range.
3. **Contesto intraday** — apertura, primi 30 minuti, metà giornata, vicinanza ai livelli.
4. **Nodi** — max gamma, call wall, put wall, grandi concentrazioni di open interest.
5. **Aspetta** che il prezzo arrivi alla zona: non si insegue.
6. **Conferma** con tape, delta, volume, big trade.
7. **Gestisci** con rischio piccolo vicino al livello; si aggiunge **solo dopo** conferma.

### La meccanica del gamma (la parte che spiega il "perché")
- **Dealer long gamma → attrito.** L'hedging rallenta il prezzo, che tende a oscillare
  attorno al livello. Vicino al **max gamma** la zona si comporta da calamita (pin).
- **Gamma che sparisce → accelerazione.** Tolto il freno, il movimento può correre.
- **Call wall**: avvicinandosi, i dealer tendono a vendere futures per coprire il delta →
  possibile zona di offerta. **Put wall**: specularmente, tendono a comprare → possibile
  zona di domanda. In entrambi i casi **solo se la reazione conferma**.

### Volatilità
La superficie di volatilità (strike × scadenza × IV) serve a vedere dove la volatilità è
cara o a buon mercato e come la struttura cambia. Lo skew indica zone di pressione. Lo
schema riassuntivo: **superficie/skew → zone di pressione · GEX → mappa dei livelli ·
order flow → conferma reale**.

Regime alto: più range e più velocità, inversioni più pulite dalle zone gamma quando
confermate. Regime basso: comportamento da range, mean reversion, setup distributivi.

### Rischio
Rischio definito e vicino al livello, stop chiaro se la reazione fallisce, incrementi solo
dopo conferma, e ricerca di **asimmetria** (perdita fissa contenuta, upside lasciato correre).

### Il calendario che cambia il profilo gamma
Date da avere segnate, perché modificano volatilità e flussi di hedging:
- **OPEX**: terzo venerdì di ogni mese.
- **Triple witching**: terzo venerdì di marzo, giugno, settembre, dicembre.
- **VIXperation**: mensile, ~30 giorni prima della scadenza opzioni S&P del mese successivo.
- **JHEQX** (JPMorgan Hedged Equity Fund): esecuzione della copertura a fine trimestre.

---

## Perché resta fuori dalla pipeline algo

1. **Dati che non abbiamo.** Servono open interest e livelli di gamma sulle opzioni
   (GEXBot è un abbonamento a parte) **più** tape e order flow per la conferma. Nessuno dei
   due è nel feed futures TradeStation né in dxFeed CME. Il secondo è lo stesso problema
   L2/L3 del Bridge — vedi `institutional_protocol_digest.md` §7.
2. **La regola non è meccanica.** Il cuore del metodo è «leggere la reazione» e «sviluppare
   sensibilità per il flusso». Come è scritto non è falsificabile: fallisce lo Stage 0, e
   per codificarlo dovremmo inventare noi ogni definizione — a quel punto la strategia
   sarebbe nostra e il documento solo ispirazione.
3. **Profilo di payoff opposto al nostro.** Cerca asimmetria con upside lasciato correre;
   il profilo prop vuole R:R 0.5–1 e WR alto. Sono due mestieri diversi.
4. **Incrementi dopo conferma.** Aggiungere size su un trade che va bene è ragionevole a
   capitale proprio; sotto trailing drawdown Apex è un'altra disciplina, e noi sviluppiamo
   a lotti fissi per scelta.

## L'unica cosa che potrebbe attraversare (non adottata)

Le **date del calendario** sopra sono oggettive e non richiedono dati opzioni: si possono
codificare da un calendario. Si potrebbero testare come filtro di giornata sulle strategie
esistenti — *l'ORB si comporta diversamente nei giorni di OPEX o di triple witching?*

Non è pre‑registrato in nessuna SPEC: sarebbe un filtro in più, e valgono le regole di
sempre (split‑sample sulle due metà dell'IS, e il corso avverte che i filtri con valore
reale sono pochissimi). Se un giorno servirà, l'idea è annotata qui.
