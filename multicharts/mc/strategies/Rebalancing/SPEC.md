# Rebalancing — anticipare il ribilanciamento dei fondi pensione

**Stage 0, 24/10/2026.** Candidata al ruolo di seconda gamba di DriftPullback.

## Fonte

**Harvey, Mazzoleni, Melone — *The Unintended Consequences of Rebalancing***, NBER w33554
(febbraio 2025), versione Fisher/Dice del **14 gennaio 2026**, 76 pagine. Campione
**10/09/1997 → 17/03/2023**, giornaliero, futures E-mini S&P 500 e T-note a 10 anni.

## Il meccanismo

I fondi istituzionali tengono quote fisse, tipicamente 60% azioni / 40% obbligazioni. Quando le
azioni battono i bond la quota azionaria sale, e il fondo **deve** vendere azioni e comprare bond
per tornare al target. Lo fa in due modi:

- **a soglia**: quando la quota si allontana dal target di più di δ (nella pratica ~2 punti);
- **a calendario**: l'ultimo giorno lavorativo del mese, con il grosso dei flussi nell'ultima
  settimana (i fondi pensione devono anche vendere titoli per pagare le pensioni di inizio mese).

È un flusso **obbligato dal mandato**, da migliaia di miliardi l'anno, e prevedibile perché
dipende solo dai rendimenti passati. Gli autori stimano che costi agli investitori ~16 miliardi
l'anno: è il guadagno di chi si mette davanti.

## Il filtro

| # | | |
|---|---|---|
| 1 | futures | ✅ E-mini S&P 500 e T-note a 10 anni |
| 2 | replicato | ~ coerente con Etula et al. 2020 (vendite di fine mese dei fondi pensione) e Chinco-Fos 2021; replica indipendente non referata (Quant Returns, luglio 2025: «anche nel periodo recente continua a sovraperformare») |
| 3 | flusso forzato | ✅ ribilanciamento per mandato |
| 4 | costi | ✅ Sharpe netto ~1 nel paper. Per noi: ~$2,25 a giro per MES contro ~$30 attesi a trade a edge intatto |
| 5 | intraday | ✅ con l'adattamento sotto: un trade al giorno, dentro la giornata Lucid |
| 6 | età | pubblicato febbraio 2025, molto ripreso dalla stampa (Bloomberg, FT): rischio di decadimento alto |
| 7 | t ≥ 3 | ✅ sulla sola gamba azionaria: soglia **t 3,11**, calendario × ultima settimana **t 3,52** (Tabella 3) |
| **8** | **oltre il 2021** | ✅ **fino a marzo 2023**, appena sopra la soglia |
| 9 | dati accessibili | ✅ solo i prezzi di S&P e T-note |

**Effetto sulla sola gamba azionaria:** −15,9 bp (soglia) e −16,9 bp (calendario) sul giorno dopo
per una deviazione standard del segnale. La strategia del paper (long-short S&P contro T-note)
rende ~10% annuo con Sharpe **1,11**, **0,90** escludendo la crisi 2008-09 e marzo 2020.

## Le regole, prese dal paper così come sono (Appendice B e sezione 4)

**Prezzi:** **S&P 500 cash (`$SPX.X`)** e `@TY` alle **15:00 CT** di ogni giorno (perché il cash e non `@ES`: vedi lo Stage 1 sotto). Il paper usa le chiusure e in una nota
riporta che con i prezzi delle 15:30 ET i risultati non cambiano: l'orario non è critico.

**Pesi simulati**, aggiornati ogni giorno con i rendimenti `rs` (S&P) e `rb` (T-note):

    w' = w(1+rs) / ( w(1+rs) + (1−w)(1+rb) )

- **Soglia**, per ciascun δ = 0%, 0,1%, ..., 2,5% (26 portafogli): se ieri |w − 60%| ≥ δ il
  portafoglio è stato riportato al 60% alla chiusura, e oggi parte da lì; altrimenti continua a
  derivare. `Threshold = media su δ di (w − 60%)`.
- **Calendario**: riportato al 60% alla chiusura dell'ultimo giorno lavorativo del mese.
  `Calendar = w − 60%`.

**Peso della strategia per il giorno dopo:**

    peso = ½ · (−Threshold / 1,5%)  +  ½ · CalMod

    CalMod = sign(−Calendar)          se oggi è negli ultimi 5 giorni lavorativi del mese
           = sign(Calendar del giorno T−4)  se oggi è il primo giorno lavorativo del mese
           = 0                        altrimenti

**Direzione = segno del peso**, sempre 1 contratto: noi non scaliamo per l'intensità del segnale.

## L'adattamento a Lucid

Il paper tiene da chiusura a chiusura. Noi **entriamo alla riapertura delle 17:00 CT e usciamo
alle 15:10 CT del giorno dopo**: è un'unica giornata di trading Lucid (18:00 → 16:45 ET), quindi
flat a fine giornata. Si perdono le ore fra le 15:00 e le 17:00 CT del giorno del segnale (in parte a mercato chiuso).

Il weekend: segnale del venerdì, ingresso alla riapertura della domenica, uscita lunedì alle 15:10.

## Strumento, campione, soglie

| | |
|---|---|
| sviluppo | **`@ES` 5 min** Globex 24h, timezone Exchange (CT), **data2 `@TY` 5 min**, **data3 `$SPX.X` 5 min** |
| operatività | **MES** (1/10). `@TY` resta solo un dato: su Lucid non si trada |
| costi | $0,50/lato Lucid + 1 tick ($1,25) per MES → **$11,25/lato** su `@ES` in MultiCharts |
| lead-in | il grafico parte dal **01/01/2018**: due anni per far derivare i 26 portafogli |
| IS | **2020-2024** |
| OOS | **2025-2026, una volta** |
| Gate 2 | **t ≥ 2** (uscita a tempo senza bracket: WR e R:R si annotano, non si giudicano) |
| Gate 5 | t ≥ 1,3 sull'OOS |

## Cosa ci aspettiamo

**Potenza, stima grezza:** ~10-13 bp a trade a edge intatto contro ~120 bp di volatilità
giornaliera dell'S&P → t ~0,09 per trade.

| | n | edge intatto | edge dimezzato |
|---|---|---|---|
| IS 2020-2024 | ~1.250 | t ~2,9 | t ~1,5 |
| OOS 2025-2026 | ~450 | t ~1,8 | t ~0,9 |

**Tre avvertenze, dichiarate prima:**

1. **L'IS non è indipendente dal paper.** Il loro campione arriva a marzo 2023: dell'IS sono dati
   nuovi solo aprile 2023 – dicembre 2024. Il test vero è l'**OOS**, tutto dopo la
   pubblicazione.
2. **Solo la gamba azionaria.** Senza T-note manca la copertura che abbassa la volatilità della
   strategia del paper. E il segnale è più spesso short che long: va contro il rialzo di fondo
   dell'S&P, che nel 2020-2024 è stato forte.
3. **Il profilo di rischio è l'opposto di quello prop.** Tutta la giornata senza stop: deviazione
   standard ~$300 per MES al giorno, WR attesa 50-53%. Se passa i gate, decide lo **Stage 7**.

**Aspettativa:** passa il Gate 2 (l'IS è in gran parte il campione del paper), e il rischio vero
è l'OOS. Lettura pre-registrata: un Gate 2 fallito con dati in gran parte del paper vorrebbe dire
che la gamba azionaria da sola, con il nostro orario, non porta l'effetto. Cimitero, nessuna
variante.

**Correlazione con DriftPullback:** questa è contrarian, DriftPullback momentum. Ci aspettiamo
correlazione bassa o negativa. Va misurata sui trade, non assunta.

---

## Stage 1, primo giro (24/10/2026): segnale giusto, due errori di dati e orari

**La logica del segnale è giusta.** Il ricalcolo Python indipendente coincide con MultiCharts su
**2.196 giorni su 2.196** (2018 → 23/10/2026): `thr`, `cal`, `calMod`, `dir` identici.

**Errore 1: `@ES` è traslato.** TradeStation aggiusta `@ES` all'indietro **per somma**: il
02/01/2024 vale 5.448 contro ~4.770 del contratto reale, il 02/01/2020 4.066 contro ~3.260. Il
rendimento `Close/Close[1] − 1` di una serie traslata verso l'alto è **sottostimato**: −12% nel
2024, −25% nel 2020. Il segnale pesa i rendimenti azionari contro quelli obbligazionari, quindi
ne esce distorto. **Correzione:** il rendimento azionario si prende dall'**S&P 500 cash**
(`$SPX.X`, data3). Il paper usa i futures, ma riporta che con l'indice i risultati sono gli stessi
(Appendice, Tabella D.4); la differenza fra i due è il carry, ~1-2 bp al giorno contro movimenti
da 100. Su `@TY` la traslazione è ~1% (113,45 contro ~112,3): trascurabile, resta.

**Errore 2: il venerdì la sessione del grafico finisce alle 15:15.** Con l'uscita alle 15:40 i
trade del giovedì restavano aperti **tutto il weekend** (16 casi su 84) e uscivano con la rete di
sicurezza la domenica sera. **Correzione:** uscita alle **15:10**, prima della chiusura del
venerdì. Altri 2 casi erano festività con chiusura alle 12:00 (MLK, Presidents' Day): restano
alla rete di sicurezza, che esce alla riapertura delle 17:00. Sono ~8 giorni l'anno.

**Da annotare, non da giudicare:** il segnale è **short il 76% dei giorni** (1.672 su 2.196),
long il 24%. È l'avvertenza 2 resa concreta: la gamba azionaria da sola va contro il rialzo di
fondo.
