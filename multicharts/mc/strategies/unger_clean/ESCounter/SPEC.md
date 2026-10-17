# SPEC — ESCounter (Unger, Stage 0)

**Ipotesi**: su ES un falso breakout del minimo della sessione precedente si riassorbe: se
la chiusura a 30 minuti torna sopra quel minimo, il prezzo risale; si compra.
**Perché**: il minimo di ieri è un livello che tutti guardano, sotto cui stanno gli stop dei
long. Quando viene rotto e subito ripreso, chi ha venduto la rottura è intrappolato e deve
ricomprare (stop dei short più copertura), mentre i long fermati rientrano. Chi perde: chi
vende il breakout del minimo. È il lato **counter trend** del modulo ES di Unger: il lato
short speculare (vendere il ritorno sotto il massimo di ieri) **perde** 2008–2016 nel video
9x05, quindi l'effetto è asimmetrico e vale solo al rialzo, coerente con la deriva
rialzista di lungo periodo dell'indice.
**Fonte**: Andrea Unger, *Trading System Supremacy*, modulo 9 ("approfondimento trading su
ES"), video 9x04 (codice al secondo 20, compilato il 23/03/2016; ottimizzazione del target
al 6:18) e 9x05 (lato short al 2:30). Risultato mostrato da Unger, 2008–2016, target $1.250:
**369 trade, avg $179,81, PF 1,34, WR 56,4%, DD intraday −$15.437** (costi non visibili).
**Ruolo nel basket**: un **counter trend / mean reversion**, la famiglia che la pipeline non
ha mai provato (tutte e sei le morte erano momentum o breakout). Strumento ES, già nella
lista Lucid.

| | |
|---|---|
| Famiglia | counter trend / falso breakout, solo long |
| Strumento · TF · dati | **@ES** (sviluppo) → **MES** (÷10) · data1 **30 min**, data2 **1440 min** (stesso simbolo) · Globex 17:00–16:00 CT, chart CT |
| Livello | `MyLow` = minimo della sessione precedente, fissato sulla barra delle **17:30** |
| Entry | dentro la finestra 17:30 → 15:30, close a 30 min che **incrocia al rialzo** `MyLow` → buy next bar at market |
| Stop / target | **$700 / $1.500 per contratto** = 14 / 30 punti ES → R:R 2,14 (alternativa di Unger: target $1.250) |
| Uscita a tempo | **nessuna** nell'originale (variante A): la posizione può durare più giorni |
| Filtro `mybars` | 1 = sempre vero (valore finale di Unger) |

**IS**: 2020‑01‑01 → 2024‑12‑31 · **OOS**: 2025‑01‑01 → oggi.
**Tutto il periodo dopo marzo 2016 non è mai stato visto da Unger.** I parametri sono
congelati a quelli del video e **non si riottimizzano**: l'IS 2020–2024 funziona, per lui, da
test fuori campione. Se servisse un secondo campione indipendente, il 2016‑04 → 2019‑12 è
pulito anche quello.

## Varianti pre‑registrate

| variante | `FlatEOD` | `MaxEntries` | `myProfit` | ruolo |
|---|---|---|---|---|
| **A** (originale) | 0 | 0 | 1500 | fedele a Unger: misura se l'edge esiste ancora |
| **B** (prop) | 1 | 2 | 1500 | **caso base per la prop**: flat a fine sessione, al massimo 2 ingressi per sessione |
| A' / B' | come A / B | | 1250 | il target alternativo di Unger, solo se A o B passano il Gate 2 |

**Perché B esiste.** Due regole della pipeline sono violate dall'originale:
1. **"Flat prima della chiusura"** (criterio di progetto preso da Apex): l'originale tiene la
   posizione anche nel weekend, e uno stop a $700 non protegge da un gap di riapertura.
2. **Worst day noto per costruzione**: l'originale può rientrare dopo ogni stop, quindi più
   stop nella stessa sessione. Il tetto a 2 ingressi lo rende finito.

Se A guadagna e B no, l'edge sta nel tenere la posizione oltre la sessione: è un risultato
da scrivere, e B muore per incompatibilità con il conto, non per assenza di edge.

## Worst day strutturale

- **Variante B**: 2 stop × $700 = **$1.400 su ES, $140 su MES**, più costi e lo slittamento di
  uno stop in un mercato veloce (circuit breaker, news). Sotto la soglia del peggior trade
  del Gate 2 ($500 per MES) anche raddoppiato.
- **Variante A**: non limitato. Un gap di riapertura (domenica sera, dopo una notizia) può
  saltare lo stop: nel marzo 2020 ES ha aperto la domenica sera al limit down, −5%, cioè
  ~150 punti = **$7.500 su ES, $750 su MES** su un solo trade. È il motivo per cui A serve
  solo da misura.

## Soglie del Gate 2 per ES (LucidFlex 50k, ÷10 per MES)

| Metrica | Soglia | nel report @ES |
|---|---|---|
| n. trade IS | ≥ 200 | ≥ 200 |
| avg trade netto | ≥ $14 per MES | **≥ $140** (≈ 5 × il costo di andata e ritorno, come NQ $70 e GC $140) |
| profit factor | ≥ 1,2 | |
| win rate | ≥ 55% | |
| R:R nominale | 0,5–1 | **l'originale è 2,14: fuori profilo per costruzione** (vedi sotto) |
| max DD ÷ 10 | ≤ $1.000 | ≤ **$10.000** |
| peggior trade ÷ 10 | ≤ $500 | ≤ **$5.000** |
| tabella annuale | nessun anno > 50% del profitto; segno stabile 2021‑23 vs 2024 | |

**R:R fuori profilo, e un numero di Unger che non torna.** Stop 14 punti e target 30 danno un
R:R nominale di 2,14 (1,79 con il target $1.250), mentre la pipeline vuole 0,5–1. Però
nell'ottimizzazione del video, con target $1.250, Unger mostra WR 56,4% e **rapporto vincita
media / perdita media 1,04**. Se le sole uscite fossero stop ($700) e target ($1.250), quel
rapporto starebbe vicino a 1,8. Quindi nel suo backtest molte uscite non erano né a stop né
a target. Le spiegazioni possibili sono slittamenti grandi sugli stop, trade aperti a fine
periodo, o un'uscita che nel codice del video non si vede. **Lo Stage 1 lo verifica** dal
tipo di uscita nella List of Trades. Per il Gate 2 conta il R:R *realizzato*: se è dentro
0,5–1 e il WR ≥ 55%, il profilo regge anche se il nominale no.

**Costi**: `15$ per Contract` per lato ($1,75 Lucid + 1 tick $12,50), slippage `0 ticks`.

## Note

- **Il minimo di "ieri" dipende dal session template di data2.** Con template Globex 17:00–16:00
  la barra giornaliera è la sessione Globex, e `MyLow` è il minimo da 17:00 a 16:00. Unger
  usava IQFeed nel 2016: se il suo daily era la sessione cash, il livello era diverso.
  Si controlla allo Stage 1 (log `ESC LOW`).
- **Orari del 2016.** `endtime 1530` veniva dalla pausa 15:15–15:30 CT, tolta dal CME nel
  2021. Si tiene 1530 per fedeltà; la differenza è al massimo una barra.
- **Back‑adjustment**: stop e target sono in dollari, quindi in punti: il continuo aggiustato
  non li distorce.
- **Session template**: l'export di @ES aveva un template vecchio che tagliava 15:15–16:00
  (vedi quantlake). Il grafico del backtest deve avere 17:00–16:00 senza pause.

**Kill**: gate della pipeline. In più, kill specifico se la variante A ha avg trade netto ≤ 0
nell'IS: con parametri congelati vuol dire che l'effetto del 2008–2016 non c'è più, e la B
non ha niente da proteggere.
