# SPEC — GoldGapper di Unger (Stage 0)

**Ipotesi**: quando l'oro apre la sessione asiatica (20:05 New York) **fuori** dal range del
giorno precedente, il gap tende a richiudersi: se il prezzo torna sul bordo del range, la
corsa continua nella direzione della chiusura del gap.
**Perché**: il gap all'apertura asiatica nasce in un momento di liquidità scarsa (dopo la
chiusura di New York e la pausa), spesso da ordini isolati o notizie del pomeriggio USA; il
ritorno nel range del giorno prima segnala che l'apertura era rumore, e chi l'ha inseguita
deve uscire. Chi perde: chi compra il gap su (o vende il gap giù) all'apertura dell'Asia.
**Fonte**: Andrea Unger, *Trading System Supremacy*, modulo 7 ("lavorare sui gap"). Codice
`MyGapFinder` nel 7x01, `GoldGapper` nel 7x02 (editor del 06/02/2016). Parametri finali sul
grafico: **`GoldGapper(2005, 1900, 2000, 0, 41, 41, 42, 42, 1)`**, @GC 5 min, dati
TradeStation, grafico in ora di New York. Risultato mostrato 2008 → inizio 2016: equity da
$100.000 a ~$147.000 a gradini, cioè **pochi trade** (costi non visibili).
**Ruolo**: un **mean reversion su un gap**, su oro, con micro disponibile su Lucid (MGC).

| | |
|---|---|
| Famiglia | mean reversion / chiusura del gap, long e short |
| Strumento · TF | **@GC** (sviluppo) → **MGC** (÷10) · **5 min** · chart in **ora di New York** (Exchange di @GC), sessione 18:00–17:00 ET senza pause |
| Giornata | personalizzata, da **20:05** a **19:00** (ora di New York) del giorno dopo |
| Gap | apertura della barra delle 20:05 sopra il massimo / sotto il minimo della giornata precedente |
| Short | sell stop al **massimo** di ieri, se il gap è su |
| Long | buy stop al **minimo** di ieri, se il gap è giù |
| Ingressi | al massimo uno per data di calendario (`TradesToday`), dentro la finestra 20:05 → 19:00 |
| Stop / target | **$2.000 a contratto GC** (20 punti) / nessuno |
| Uscita | alla barra `sEnd` (`MyExit 1`) |
| Filtri di pattern | **commentati** nel codice di Unger: non usati |

**Fuso orario.** `MyGapFinder(1805, 1700)` del 7x01 è esattamente la giornata Globex 18:00–17:00
**di New York**. Per TradeStation l'exchange di @GC è il COMEX di New York, quindi con
`Time Zone: Exchange` anche il nostro chart è in ora di New York (verificato il 24/10/2026: la
prima barra dopo la pausa è quella delle 18:05). Si usano gli orari di Unger così come sono.

**Le funzioni.** `_DayDefinition`, `Time00` e `TradesToday` si importano dal `GapsFunctions.pla`
del corso (febbraio 2016, quello dei video). Il `_DayDefinition.txt` di maggio 2016 ha una
condizione di reset modificata con cui la strategia non farebbe mai trade (vedi
`Mario_GoldGapper.txt`).

**IS**: 2020‑01‑01 → 2024‑12‑31 · **OOS**: 2025‑01‑01 → oggi. Parametri congelati a quelli del
video; tutto dopo febbraio 2016 è fuori campione per l'autore.

## Varianti pre‑registrate

| variante | `sBeg` | `sEnd` | `MyExit` | ruolo |
|---|---|---|---|---|
| **A** | 2005 | **1900** | 1 | l'ultimo valore sul grafico di Unger: la posizione attraversa la chiusura delle 17:00 e la pausa |
| **B** | 2005 | **1600** | 1 | l'altro valore di Unger e il default del suo codice: **flat prima della chiusura** (17:00), caso base per la prop |

Unger alterna i due valori dopo aver ottimizzato `sEnd`; nel video la scelta finale non è
esplicita. Si testano tutti e due, e **il caso base per la prop è B**.

## Rischi dichiarati prima dei run
- **Pochi trade.** Un'apertura asiatica fuori dal range del giorno prima non è frequente, e
  serve anche il ritorno sul bordo. L'equity di Unger va a gradini. Il Gate 2 chiede ≥ 200
  trade nell'IS: **è probabile che fallisca su questo per costruzione**. Anche se l'edge
  esistesse, pochi trade vogliono dire un'eval lenta.
- **Stop fisso in dollari.** $2.000 = 20 punti: con l'oro a ~1.200 (il test di Unger) era
  l'1,7% del prezzo, nel 2020–2024 (1.500–2.700) è lo 0,7–1,3%, oggi (~4.100) lo 0,5%. Lo
  stop è proporzionalmente **più stretto** che nel test di Unger. Si tiene fedele; se l'edge
  c'è e lo stop esce spesso, una variante con lo stop in percentuale (1,7%) è la prossima
  Stage 0.

## Worst day strutturale
Un ingresso per data, ma la finestra attraversa la mezzanotte: **fino a 2 ingressi per
giornata** (uno prima e uno dopo le 00:00). Worst day = 2 stop = $4.000 su GC, **$400 su MGC**,
più costi e slittamento.

## Soglie del Gate 2 (LucidFlex 50k, ÷10 per MGC)
n ≥ 200 · avg netto ≥ **$140** su GC · PF ≥ 1,2 · WR ≥ 55% · R:R 0,5–1 · max DD ≤ $10.000 su
GC · peggior trade ≤ $5.000 su GC · nessun anno > 50% del profitto.

**Costi**: `12.5$ per Contract` per lato, slippage 0.

**Kill**: gate della pipeline su B. In più, kill se A e B hanno avg netto ≤ 0.
