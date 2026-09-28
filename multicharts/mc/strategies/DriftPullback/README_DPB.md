# DriftPullback — istruzioni Stage 1

Codice: `DriftPullback.txt`. Riferimento:
`mc/education/protocollo/11. Strategy Feedbacks/1. DriftPullback_Tutorial_.pdf`
(walkthrough completo del sorgente v2.1) e `…/1. DriftPullback - Full Tutorial
(Francesco Agnello).pdf` (nota di accompagnamento).
**Il sorgente originale non è nel corso**: questo è un porting dal walkthrough. Lo Stage 1
serve anche a verificare che il porting sia fedele.

## Chart — due serie dati, l'ordine conta

1. Crea un chart **@NQ · 5 min** → questa è **Data1** (esecuzione, tutti gli ordini).
2. **Insert → Instrument**, **stesso simbolo**, risoluzione **15 min** → **Data2**
   (segnale). Se l'ordine è invertito la strategia gira al contrario e non se ne accorge
   nessuno.
3. Sessione **Globex 24h** (17:00–16:00 CT), timezone **Exchange**.
   Serve il premarket: il drift della prima ora del cash lo guarda. La VWAP di sessione
   lo esclude da sola tramite `VwapStart`/`VwapEnd`.
4. **Max bars back ≥ 100** (MALen 20 barre da 15 min = 60 barre da 5 min, più il drift).
5. IOG **off**. Costi $2.50/lato + 1 tick.
6. **Backtest con "Extended intra-bar precision"** (Bar Magnifier): i bracket sono stop e
   limit *dentro* la barra a 5 minuti; senza, i fill sono ottimistici.

## Fuso orario — leggere prima del primo run

I cinque input di sessione sono in **ora del chart**. Se sono sbagliati non succede
niente: la strategia trada semplicemente un'ora diversa da quella validata, e ogni
confronto con i numeri dell'autore diventa privo di senso. **Non mescolare le colonne.**

| Input | Significato | Chart Eastern | **Chart Central (default)** |
|---|---|---|---|
| `SessStart` | primo ingresso ammesso | 1030 | **930** |
| `SessEnd` | ultimo ingresso ammesso | 1530 | **1430** |
| `FlatTime` | flat incondizionato | 1555 | **1455** |
| `VwapStart` | inizio accumulo VWAP | 0930 | **830** |
| `VwapEnd` | fine accumulo VWAP | 1600 | **1500** |

`SessStart` salta di proposito **la prima ora di RTH**: è dove si risolvono i gap e dove
il drift è ancora dominato dal posizionamento overnight. Attenzione all'asimmetria:
ancora, VWAP e **armamento** girano dall'apertura, solo il *trigger* è bloccato. Un setup
armato alle 09:15 può legittimamente scattare alle 09:35 se la finestra di pullback è
ancora viva.

## Verifica meccanica (Gate 1)

Con `ShowLog 1`, su ~100 giorni, 1 contratto:

- **Armamento solo a fine barra 15 min.** Nel log gli orari degli `ARM` devono cadere
  sempre su multipli di 15 minuti (…:00, :15, :30, :45). Se compaiono orari intermedi, il
  rilevamento di `newBar2` non funziona e il segnale sta oscillando dentro la barra lenta.
- **Un solo trade per armamento.** Fra un `ARM` e l'ingresso successivo non ci devono
  essere due ingressi.
- **Scadenza.** Un setup armato che non trova la barra contraria deve morire entro **6
  barre da 5 minuti** (≈ 30 min) senza trade.
- **Direzione del trigger.** Ogni ingresso long deve stare su una barra a 5 min **rossa**
  (Close < Open), ogni short su una **verde**. Controllo diretto sul chart.
- **Guardrail.** Mai più di **4** ingressi in una giornata; dopo la **2ª** perdita chiusa,
  nessun nuovo ingresso fino al giorno dopo. Da verificare esplicitamente pescando una
  giornata con 2 stop.
- **Finestra ingressi.** Nessun fill prima di 09:30 CT né dopo 14:30 CT; nessuna
  posizione oltre le **14:55**; nessuna posizione overnight, mai.
- **Stop pessimistici.** I fill in stop devono risultare **2 tick peggiori** del livello
  (0,50 pt = $10/contratto NQ). Se coincidono col livello, `slipPts` non sta arrivando
  all'ordine.
- **Scaling.** Con `BaseCts 10` il P&L per trade ×10 esatto.
- **Warm-up VWAP.** Con `AnchorType 2` non ci deve essere armamento sulla primissima
  barra segnale della giornata (non esiste ancora uno snapshot precedente): è voluto.

### Se si prova anche `EntryMode 1` (variante Stage 4)

Non serve allo Stage 1 — la configurazione da validare è `EntryMode 0` — ma se lo si
accende per curiosità, i controlli sono:

- ogni fill deve avvenire **sopra il massimo** (long) o **sotto il minimo** (short) della
  barra di pullback, mai a un prezzo migliore;
- con `EntryStopBars 1` un setup che non riempie sulla barra successiva deve sparire: nel
  log compare `stop scaduto` e nessun trade;
- il livello **non insegue**: se il prezzo continua a scendere, l'ordine resta dove era;
- i cancelli valgono anche sull'ordine pendente: se scattano le 14:30, o il 4° trade, o la
  2ª perdita mentre l'ordine è appeso, l'ordine va cancellato senza eseguire;
- il numero di trade deve **scendere** rispetto a `EntryMode 0`: se sale, c'è un errore.

## Cosa NON toccare in questa fase

`DriftThreshPct`, `MALen`, `DriftLen`, `PullbackWindow` e i bracket 80/40/50 sono
congelati: sono i numeri fissati in-sample dall'autore **prima** del suo OOS. Toccarli non
migliora la strategia, cancella la validazione. Le uniche cose da muovere allo Stage 1
sono gli orari (per il fuso del tuo chart) e `ShowLog`.

`SizeMode` resta **1** (size fissa, 1 contratto) per tutta la pipeline fino allo Stage 7:
la cushion ladder è logica di deployment, non edge.

## Differenze rispetto al PDF

- Flag numerici **0/1** (`TradeLongs`, `TradeShorts`, `ShowLog`) invece di true/false, per
  poterli mettere nell'ottimizzatore.
- Lo slope check dell'ancora usa il valore memorizzato al confine 15 min precedente
  (`ma2prev`) invece di ricalcolare `Average(Close[1] of data2, …)`: stesso risultato,
  ma coerente con l'architettura "valori congelati" per tutte e tre le ancore.
- Sulla prima barra segnale del giorno con `AnchorType 2` l'armamento è bloccato da
  `anchorOK` (manca `ma2prev`) invece che neutralizzando la condizione di slope. Effetto
  identico a quello descritto nel PDF: nessun armamento su quella barra.
- `MVWAP` (`AnchorType 1`) ricalcolato esplicitamente con un loop su `MALen` barre di
  data2, con fallback `Ticks` se il feed non dà volume.
