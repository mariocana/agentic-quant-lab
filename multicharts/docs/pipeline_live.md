# La pipeline live (soldi propri): BOZZA del 12/11/2026

**Stato: bozza, non in vigore.** Resta in stand-by come [metodologia_live.md](metodologia_live.md):
si applica quando c'è il conto. Scritta ora perché le regole esistano prima dei numeri.

**Due regole sono già decise (Mario, 12/11/2026): il conto minimo è $100.000**, sotto non si
parte, **e il programma si ferma a −15%.** Tutte le altre soglie sono proposte, segnate con `?` finché Mario non le conferma.

## Perché non è la pipeline prop con soglie più alte

| | prop | live |
|---|---|---|
| La domanda | tocco +$3.000 prima di −$2.000? | il capitale cresce senza un drawdown che mi ferma? |
| Se va male | un'altra eval a $80 | soldi veri, nessun reset |
| Orizzonte | settimane | anni |
| Il nemico | il trailing drawdown | i costi, il cambio di regime, il drawdown lungo |
| Forma che premia | WR alto, R:R basso, tanti trade | edge spesso per trade, anche con pochi trade |
| Vincoli | flat a fine giornata, consistency, MLL | nessuno: overnight, swing e barre giornaliere sono permessi |

La pipeline prop seleziona strategie sottili per trade. Le candidate live si cercano anche fuori
dall'intraday; una strategia del book prop può candidarsi, ma rifà il percorso da capo con questi
criteri.

## Il bilancio di rischio, fissato prima di qualsiasi strategia

| | valore | da dove viene |
|---|---|---|
| Conto minimo | **$100.000** | Mario, 12/11/2026 |
| Drawdown che ferma il programma | **15%** = $15.000 | Mario, 12/11/2026: a quel punto si spegne tutto e si rivede |
| Drawdown atteso del book, 95° percentile a 12 mesi | **≤ 7,5%** `?` = $7.500 | metà del limite: il drawdown futuro è peggiore di quello simulato |
| Perdita massima di un trade | **≤ 0,5%** `?` = $500 | ai prezzi di oggi, non a quelli dell'IS |
| Perdita massima di un giorno, tutto il book | **≤ 1,5%** `?` = $1.500 | |
| Costi fissi (VPS, piattaforma, dati) | **≤ 2%** l'anno `?` | oggi circa $1.740: su $100.000 è l'1,7% |

**La size è un output anche qui.** Non si decide quanti contratti: si cerca la size più grande
che rispetta le tre righe di rischio. Se a 1 micro una strategia le supera, non entra.

## Le sette domande

Una strategia alla volta. Soglia, attesa e kill scritti nella SPEC prima del run, come in prop.

| | fase | la domanda | il criterio | se fallisce |
|---|---|---|---|---|
| **0** | SPEC | *perché dovrebbe esistere, e continuare?* | ragione strutturale scritta: chi sta dall'altra parte, perché non sparisce, cosa la farebbe sparire. Storico cercato con `lab.py cerca` | non si scrive codice |
| **1** | Meccanica | *il codice fa quello che credo?* | come lo Stage 1 prop, più: **trade peggiore in dollari ai prezzi di oggi** ≤ 0,5% del conto a 1 micro | si corregge, non è un kill |
| **2** | Edge | *l'edge esiste ed è spesso?* | i quattro criteri sotto | cimitero |
| **3** | Fragilità | *regge se sposto qualcosa?* | i tre criteri sotto, solo in-sample | cimitero |
| **4** | Fuori campione | *regge su dati mai visti?* | una volta sola, sulla riserva: **t ≥ 1,5** `?` · avg ≥ metà dell'IS · drawdown ≤ 1,5 volte l'IS | cimitero, definitivo |
| **5** | Size e book | *quanto, e migliora il book?* | size dal bilancio di rischio; gate marginale live | non entra |
| **6** | Forward | *l'esecuzione segue il grafico?* | almeno **30 trade** `?` e 3 mesi, in paper o su un conto funded | si ferma finché non si capisce |
| **7** | Live a scalini | *regge in esercizio?* | parte a un terzo della size; soglie di spegnimento | si spegne |

### Fase 2: l'edge esiste ed è spesso

1. **t ≥ 2,5** `?`, e comunque sopra il t massimo atteso dal caso per il numero **totale** di idee
   provate nel programma, non solo per le varianti di questa (20 idee → 1,9 · 50 → 2,25).
2. **Edge lordo ≥ 4 volte il costo per trade** `?` (commissione più slippage misurato). Sostituisce
   PF ≥ 1,2 e avg ≥ $70, che dicono quasi la stessa cosa con soglie arbitrarie. PF e avg si
   stampano ancora, informativi.
3. **Peggiori 12 mesi consecutivi ≥ −metà dell'anno medio** `?`, e al massimo un anno di calendario
   negativo. Sostituisce «nessun anno oltre il 50%».
4. **Campione:** almeno 5 anni e 200 trade `?`; per strategie su barre giornaliere almeno 10 anni
   dove i dati ci sono.

### Fase 3: fragilità (solo in-sample, niente ottimizzazione)

1. **Vicinato dei parametri:** ogni input spostato del ±20%, uno alla volta, lascia t ≥ 1,5 `?`.
   Un picco isolato è un adattamento.
2. **Costi doppi:** il netto resta positivo.
3. **Due metà:** entrambe le metà dell'IS positive, con avg dello stesso ordine.

I run di questa fase non contano nel k perché non scelgono niente: se la strategia passa resta
con i parametri della SPEC, se non passa muore.

### Fase 4: la riserva

L'OOS 2025-2026 è già stato guardato dal programma prop. Per il live serve una riserva che nessun
run ha toccato: **i dati dal 01/07/2026 in poi** `?`, che crescono col tempo. Ogni sguardo alla
riserva si scrive in un registro unico del programma, con la data.

Una strategia che arriva dal book prop ha già visto il 2025-2026: quel periodo per lei vale come
in-sample, e l'OOS è solo la riserva.

### Fase 5: size e gate marginale live

- **Size:** la più grande con drawdown al 95° percentile a 12 mesi (ricampionamento a blocchi)
  dentro la quota del book, trade peggiore ≤ 0,5% e giorno peggiore del book ≤ 1,5%.
- **Gate marginale:** la candidata entra se migliora il rapporto rendimento annuo / drawdown al
  95° percentile del book, con il **5° percentile del miglioramento sopra zero** (lo stesso
  ricampionamento di `gate_marginale.py --intervallo`).
- **Stress:** il book regge con la candidata riportata a metà del suo edge. Se il book sta in
  piedi solo con la candidata al suo meglio, non entra.

### Fase 6: forward

- **Replica dell'esecuzione** con la soglia del motore: almeno il 90% dei trade del grafico
  ritrovati sul conto, netto entro il 10%.
- **Slippage misurato**, e la fase 2 ricalcolata con quello: se l'edge scende sotto 4 volte il
  costo, la strategia si ferma.
- Un conto funded prop vale come forward dell'esecuzione, non dell'edge.

### Fase 7: live a scalini e spegnimento

| scalino | size | si sale quando |
|---|---|---|
| 1 | un terzo (almeno 1 micro) | 30 trade `?` con avg dentro l'intervallo atteso |
| 2 | due terzi | altri 30 trade |
| 3 | piena | |

| si spegne la strategia quando | |
|---|---|
| il suo drawdown supera il 95° percentile simulato | |
| l'avg sugli ultimi 50 trade è sotto zero `?` | |
| un trade è sul grafico e non sul conto, o viceversa | subito |
| lo scarto conto-grafico medio su 30 trade supera metà dell'edge | |
| **si spegne il programma quando il conto è a −15%** | deciso |

Una strategia spenta non si riaccende con altri parametri: è una variante, e rifà il percorso.

## Prima della fase 7: i requisiti dell'infrastruttura

Non sono criteri di una strategia: valgono per il conto. Dall'[audit del 12/11](audit_2026-11-12.md):

1. stop d'emergenza al broker per ogni posizione;
2. tetto di quantità lato broker;
3. confronto automatico grafico-conto con allarme;
4. allarmi a calendario per rollover e scadenza delle licenze.

## Da decidere (Mario)

| | proposta | alternativa |
|---|---|---|
| Drawdown atteso del book (95° percentile a 12 mesi) | 7,5%, metà del limite | 10%: più size, meno margine |
| Soglia t in-sample | 2,5 | 3 |
| Inizio della riserva | 01/07/2026 | 01/01/2027: più pulita, ma si aspetta |
| Forward minimo | 30 trade e 3 mesi | 50 trade |
| Strumenti | gli stessi di `motore/` | aprire a barre giornaliere e ad altri mercati |

## Cosa non c'è ancora

- Nessuno script: `check_report.py` non ha una `--fase` live, il vicinato dei parametri e il gate
  marginale live non sono scritti.
- Nessuna misura: nessuna soglia qui è stata provata su una strategia. La prima che passa di qui
  dirà se sono troppo larghe o troppo strette; cambiarle dopo vale solo per le successive.
- Tasse e cambio EUR/USD non sono considerati.
