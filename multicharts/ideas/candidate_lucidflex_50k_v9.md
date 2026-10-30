<!-- researcher.py, 25/10/2026, claude-code on the claude.ai plan, model claude-opus-5-5, focus: Approfondisci la pista aperta dell'overnight drift: leggi Boyarchenko-Larsen-Whelan (The Overnight Drift, NY Fed) per fuso, finestra esatta, ampiezza in punti e costi; poi verifica se la finestra cade dentro la stessa sessione CME (flat EOD LucidFlex). -->

# Ricerca del 25/10/2026: la pista dell'overnight drift

## Riassunto in tre righe

1. **Nessuna candidata e nessuna quasi-candidata.** L'overnight drift non entra: l'effetto è morto dopo il 2021, e a dirlo sono gli autori stessi. Lo scrivono per l'S&P e anche per NQ e YM, quindi il filtro 8, che è eliminatorio, fallisce.
2. **La finestra entrerebbe nel conto.** L'ora 02:00–03:00 ET (01:00–02:00 CT) cade dentro la stessa giornata CME e dentro la giornata Lucid, che va dalle 18:00 ET alle 16:45 ET. Il vincolo «flat EOD» non è il motivo dello scarto.
3. **Anche con l'effetto vivo non sarebbe bastato.** La versione semplice rendeva circa un costo andata-ritorno per trade, cioè Sharpe 1,10 lordo e −0,54 netto secondo gli autori. Facendo 1 trade al giorno, resta molto sotto i $10 al giorno per micro.

---

## Tabella di sintesi

| # | Nome | Strumento · TF | Famiglia | Stop dichiarato (punti → $/micro) | n/anno attesi | WR atteso | R:R atteso | Fonte | Verdetto |
|---|---|---|---|---|---|---|---|---|---|
| — | Overnight Drift 02:00–03:00 ET, non condizionata | MES · 60 min | event / flusso | nessuno nel paper [manca] | ~250 [stima: 1 al giorno] | [manca] | [manca] | Boyarchenko-Larsen-Whelan, RFS 2023 + Liberty Street 07/2026 | **SCARTATA**: filtri 8 e 4, $/giorno |
| — | Overnight Drift condizionata (long 01:30–03:30 ET dopo flusso netto in vendita in chiusura) | MES · 30 min | event / flusso | nessuno [manca] | < 250 [manca: quota di giorni attivi non riportata] | [manca] | [manca] | come sopra (dati del paper riportati da terzi) | **SCARTATA**: filtro 8, più un dubbio sul filtro 9 |
| — | European open, 4 ore (Bondarenko-Muravyev, JFQA 2023) | MES | event | [manca] | ~250 | [manca] | [manca] | sintesi su IDEAS e nei risultati di ricerca | **SCARTATA**: filtro 8 (campione 2004-2018, nessun follow-up dopo il 2021) |

Le schede «mezza pagina» si fanno solo per le candidate vive, e qui non ce ne sono. Al loro posto metto la scheda completa della pista richiesta: la prossima ricerca non deve riaprirla.

---

## Scheda: Overnight Drift (Boyarchenko, Larsen, Whelan)

### Cosa dice la fonte

**Paper:** *The Overnight Drift*, Review of Financial Studies 36(9), 2023, 3502-3547; working paper [NY Fed Staff Report 917](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf).
- Il PDF è arrivato come binario compresso e il fetch non l'ha estratto. I numeri sotto vengono quindi dal post degli autori del 2026 e da una sintesi di terzi che li riporta. È lettura di seconda mano: va segnalato.

**Strumento e fuso.** Futures E-mini S&P 500, ora di New York (ET) [fonte: [Liberty Street, 07/2026](https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/)].

**Finestra.** Dalle **02:00 alle 03:00 ET**, attorno all'apertura europea, cioè **01:00–02:00 CT** [stima: ET − 1 ora]. Il post precisa che la giornata CME va dalle 18:00 alle 18:00 ET [fonte: Liberty Street 2026].

**Ampiezza della versione non condizionata.**

| | valore |
|---|---|
| rendimento annualizzato, 1998-2020 (5.691 giorni) | circa **3,7%**, oltre il 60% del 5,9% annuo close-to-close [fonte: Liberty Street 2026] |
| rendimento per giorno, giorni senza annunci | **1,52 bp**, t = **5,98** [fonte: [Avaneendra](https://avaneendra.substack.com/p/the-stock-market-paid-37-a-year-in), che riporta il paper; non verificato sul testo originale] |
| anni positivi | 20 su 23 [stessa fonte] |

**Ampiezza in punti.** Lo stesso rendimento vale in punti in base al livello dell'indice:

| livello S&P | punti per giorno | $ per MES |
|---|---|---|
| ~4.200 (media indicativa dell'IS 2020-2024) [stima] | 4.200 × 0,000152 = **0,64** | 0,64 × $5 = **$3,19** lordi |
| ~7.800 (livello di ottobre 2026) | **1,19** | **$5,93** lordi |

Il livello di ottobre 2026 viene da [CNBC](https://www.cnbc.com/2026/10/05/stock-market-today-live-updates.html), già nel database. Tutti questi sono numeri **lordi, pre-2021**.

**Costi.** Due strategie degli autori sul periodo gen 2004 – dic 2020 [fonte: Avaneendra che riporta il paper]:

| strategia | lordo | netto | Sharpe |
|---|---|---|---|
| non condizionata (long 2–3 ET), comprando all'ask e vendendo al bid | 3,75% annuo | **−0,59%** | 1,10 lordo, **−0,54** netto |
| condizionata (long 01:30–03:30 ET dopo flusso netto negativo in chiusura) | 6,07% | **4,04%** | **1,10** netto |

- **Verifica incrociata con i nostri costi.** ES costa $30 andata-ritorno, cioè 0,6 punti a $50 per punto. L'edge lordo di 0,64 punti è quindi pari a **1,07 volte il costo** [stima]. Serve almeno 3 volte. Il nostro conto è coerente con il netto negativo degli autori.

**Il meccanismo, cioè chi perde.**
- Chi in chiusura USA deve vendere (o comprare) in blocco paga uno sconto ai fornitori di liquidità.
- Il prezzo rientra quando arrivano i compratori europei alle aperture di Francoforte e Londra.
- Il modello è E[R_ON] = squilibrio × varianza / capacità di rischio [fonte: Liberty Street 2026].
- È un flusso di liquidità, quindi il **filtro 3 passa**.

### La morte, dichiarata dagli autori

Fonte: post del 1 luglio 2026, [The Disappearing Overnight Drift](https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/); paper su [SSRN 7035838](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7035838).

- Sul periodo **2021-2025 (1.245 giorni)** la finestra 2–3 ET ha reso **«close to zero»**, e questo vale anche su **NQ e YM**. RTY non è citato.
- **La versione condizionata è indebolita anche lei.** Il divario fra i giorni dopo una chiusura in vendita e quelli dopo una chiusura in acquisto è **«much narrower»**. I numeri sono solo nei grafici [manca un valore numerico].
- **Causa indicata dagli autori: la dispersione dello squilibrio di chiusura è crollata.** La deviazione standard del relative signed volume fra 15:15 e 16:15 ET è passata da 6,5% a 2,9%. VIX (da 20,4 a 19,4) e quota di volume notturno (da 15% a 16%) sono quasi invariati.
  - Questo è un dato utile per il resto della ricerca: **il flusso di chiusura non si è spostato, si è frammentato**. Gli algoritmi tagliano gli ordini in pezzi più piccoli.
- **Prova di mercato.** Gli ETF NightShares (NSPY e NIWM), che andavano long sui futures alla chiusura e vendevano all'apertura, hanno chiuso dopo circa 14 mesi dal lancio di giugno 2022 [fonte: Liberty Street 2026].

### Scheda del filtro

| # | domanda | risposta | fonte |
|---|---|---|---|
| 1 | testato su futures | **sì**, E-mini S&P | Liberty Street 2026 |
| 2 | replicato | **sì**, in parte: Bondarenko-Muravyev (JFQA 2023) trovano lo stesso effetto attorno all'apertura europea, 2004-2018 | [IDEAS](https://ideas.repec.org/a/cup/jfinqa/v58y2023i3p939-967_1.html) |
| 3 | flusso forzato | **sì**: fornitura di liquidità contro lo squilibrio di chiusura | Liberty Street 2026 |
| 4 | costi | **no** nella versione semplice (netto −0,59%); **sì** nella condizionata (netto 4,04%), ma fino al 2020 | Avaneendra / paper |
| 5 | intraday e flat in sessione | **sì per l'orario** (vedi sotto); **no per la frequenza**: 1 trade al giorno al massimo, meno nella condizionata | — |
| 6 | anni dalla pubblicazione | WP 2020, RFS 2023 | — |
| 7 | t ≥ 3 | **sì** (5,98, non condizionata, fino al 2020) | Avaneendra / paper |
| **8** | **vivo dopo il 2021** | **NO: «close to zero» 2021-2025, anche su NQ e YM. ELIMINATORIO** | Liberty Street 2026 |
| 9 | dati accessibili | sì per la non condizionata. La condizionata richiede il **signed volume** di chiusura. In MultiCharts esiste solo il proxy UpTicks/DownTicks, che non è la stessa misura [stima] | — |

### La finestra cade dentro la sessione? Sì

| | orario | fonte |
|---|---|---|
| giornata CME (ES/MES) | domenica–venerdì, 18:00 → 17:00 ET, pausa 17:00–18:00 ET; equivalente 17:00 → 16:00 CT | [CME, specifiche MES](https://cmegroup.com/markets/equities/sp/micro-e-mini-sandp-500.contractSpecs.html) e broker nei risultati di ricerca |
| Lucid (Pro/Flex/Direct) | posizioni chiuse entro le **16:45 ET** (lun–ven), chiusura automatica a quell'ora; si riprende alle **18:00 ET** | [Lucid, Allowed Trading Times](https://support.lucidtrading.com/en/articles/11404729-allowed-trading-times) |
| la finestra 02:00–03:00 ET | è **9 ore dopo** l'apertura della giornata Lucid e **circa 14 ore prima** del cut | [stima] |

- **Conclusione:** un trade aperto alle 02:00 ET e chiuso alle 03:00 ET è dentro la giornata, quindi compatibile col flat EOD.
- **Cosa non è compatibile:** la versione «close → open», cioè quella degli ETF NightShares, perché attraversa il cut delle 16:45 e la pausa.
- **Cosa la pagina Lucid non dice [manca]:**
  - come si definisce la giornata per la regola di consistenza e per l'MLL EOD;
  - l'orario durante l'ora legale: la pagina scrive «EST» anche quando gli Stati Uniti sono in ora legale.

### Perché sarebbe morta anche con l'effetto vivo

- **$ al giorno per micro, versione semplice, prima del 2021:** circa $3,19 lordi a fronte di un costo dello stesso ordine [stima, sopra], quindi netto ≈ 0. Contro una soglia di $10 al giorno.
- **Versione condizionata:** opera solo in una parte dei giorni, e quale parte [manca].
  - Se fosse attiva tutti i giorni: 6,07% / 252 = 2,4 bp ≈ 1,0 punto ES ≈ **$5 lordi per MES** [stima, livello 4.200]. Ancora sotto i $10, e prima dei costi.
- **Frequenza:** 1 segnale al giorno al massimo. È fuori dalla soglia «≥ 2 al giorno» per una gamba principale. Al più andrebbe bene come seconda gamba, a patto di avere edge, ma l'edge non c'è più.

---

## Osservazioni separate (non modificano i vincoli)

1. **Il prompt formula l'esclusione degli «anomalie overnight» in modo troppo largo.** Su Lucid il vincolo vero è «flat entro le 16:45 ET, ripartenza alle 18:00 ET». Effetti che si aprono e si chiudono dentro la sessione Globex notturna (Asia, apertura europea) sono **ammessi dal conto**. Lo sapevamo già nei fatti, perché Gold Asian Range operava 20:00 CT → 10:00 CT. Va escluso solo ciò che attraversa il cut. Lo scrivo come chiarimento della regola, non come allentamento.
2. **Il database ha una voce sbagliata da correggere.** `sr917` è descritto come «Long ES fra le 14:00 e le 15:00 (inventory)». La finestra del paper è **02:00–03:00 ET**, cioè 01:00–02:00 CT. Il motivo dello scarto («Sharpe 1,1 prima dei costi, −0,5 dopo») resta corretto ed è confermato.
3. **La causa della morte è un indizio per il futuro.** Secondo gli autori lo squilibrio di chiusura si è «frammentato» (dispersione da 6,5% a 2,9%). Qualunque idea basata su «grande squilibrio in chiusura → rimbalzo» va pre-registrata aspettandosi zero dopo il 2021. Questo indebolisce anche le piste MOC imbalance che restano aperte nel database ([nexusfi](https://nexusfi.com/showthread.php?t=60003)).
4. **Siamo al quarto caso della stessa regola.** Dopo LastHalfHour, FX Fix e Rebalancing, un effetto pubblicato con campione fino al 2020 non si trova vivo nei dati recenti. Il filtro 8 sta facendo il suo lavoro.

---

## 1. Scartate da me

| Idea | Fonte (link) | Motivo dello scarto in una riga |
|---|---|---|
| Overnight Drift 02:00–03:00 ET su ES/MES, non condizionata | [Liberty Street 07/2026](https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/) · [sr917](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf) | Gli autori la danno «close to zero» nel 2021-2025, anche su NQ e YM (filtro 8). Già prima netto negativo (Sharpe −0,54) |
| Overnight Drift condizionata (long 01:30–03:30 ET dopo vendite in chiusura) | idem + [Avaneendra](https://avaneendra.substack.com/p/the-stock-market-paid-37-a-year-in) | Divario «much narrower» dopo il 2021 (filtro 8). Serve il signed volume, di cui abbiamo solo il proxy UpTicks/DownTicks |
| Overnight drift close → open (stile NightShares) | Liberty Street 2026 | Attraversa il cut Lucid delle 16:45 ET; gli ETF che la facevano hanno chiuso in circa 14 mesi |
| Rendimento delle 4 ore attorno all'apertura europea (Bondarenko-Muravyev, JFQA 2023) | [IDEAS](https://ideas.repec.org/a/cup/jfinqa/v58y2023i3p939-967_1.html) · [Alpha Architect](https://alphaarchitect.com/market-return-around-the-clock/) (403) | Campione 2004-2018, nessun follow-up dopo il 2021. La finestra si sovrappone all'ora 2–3 ET, già morta |
| «La London open muove ES di 10-20 punti» (guide orarie) | [clearedge](https://www.clearedge.trading/post/es-futures-trading-hours-automation-strategies) · [nexusfi academy](https://nexusfi.com/a/exchanges/market-hours) | Affermazioni senza dati e in contraddizione fra loro; nessuna regola |

## 2. Dove ho cercato

| Fonte / query | Cosa ci ho trovato | Vale la pena ritornarci? |
|---|---|---|
| Fetch [sr917.pdf](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf) | PDF binario, testo non estratto | No: i numeri chiave sono nel post 2026 |
| query «Boyarchenko Larsen Whelan overnight drift disappeared 2026 update» | Il follow-up degli autori (Liberty Street, SSRN 7035838) | No: la pista è chiusa |
| Fetch [Liberty Street 07/2026](https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/) | Fuso, finestra, campioni, morte dopo il 2021 anche su NQ e YM, causa | No |
| query «Lucid Trading LucidFlex rules close positions end of day…» + fetch [Lucid support](https://support.lucidtrading.com/en/articles/11404729-allowed-trading-times) | Cut alle 16:45 ET, ripartenza alle 18:00 ET | Sì, ma solo per chiedere al supporto come si definisce la giornata per consistenza e MLL [manca] |
| Fetch [Avaneendra substack](https://avaneendra.substack.com/p/the-stock-market-paid-37-a-year-in) | Sharpe lordo e netto e la strategia condizionata riportati dal paper; nessun backtest proprio dell'autore | No |
| query «overnight drift … Sharpe … bid-ask … RFS 2023» | Liberty Street 2021, CEPR DP14462 | No |
| query «"Disappearing Overnight Drift" conditional … Nasdaq Dow» | Nessun numero oltre il post | No |
| query «E-mini European open 3 a.m. ET return 2023 2024 2025…» | Bondarenko-Muravyev (campione 2004-2018), NightShares | No |
| query «CME Micro E-mini S&P 500 MES contract specifications…» | MES a $5 per punto, tick 0,25 = $1,25; orari 18:00–17:00 ET | Solo come riferimento |
| query «Bondarenko Muravyev Market Return Around the Clock…» + fetch Alpha Architect (403) | Nessuna replica dopo il 2020 | No, salvo che esca un follow-up |
| query «ES futures hourly returns by hour of day 2022-2025…» | Solo guide divulgative senza dati | No. **La misura va fatta da noi** sui dati @ES/@YM in MultiCharts, se mai servisse |

**Budget usato:** 8 ricerche su 15, 6 fetch su 6 (due falliti: sr917 come binario, Alpha Architect con 403). Nessuna pagina conteneva istruzioni rivolte a un agente.

**Il filone overnight-drift è esaurito.** Fra le piste ancora aperte nel database, le più vicine sono quelle sullo squilibrio MOC, e il punto 3 delle osservazioni le indebolisce.

```json
{
  "candidates": [],
  "sources_reviewed": [
    {"url": "https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf", "title": "The Overnight Drift (Boyarchenko, Larsen, Whelan), NY Fed SR 917 / RFS 2023", "kind": "paper", "verdict": "scartato", "reason": "Finestra 02-03 ET (non 14-15 come nel db): netto negativo dopo spread (Sharpe -0,54) e morta dopo il 2021 per gli autori stessi; PDF non estraibile via fetch", "candidate": null},
    {"url": "https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/", "title": "The Disappearing Overnight Drift - Liberty Street Economics (07/2026)", "kind": "paper", "verdict": "scartato", "reason": "Gli autori: finestra 2-3 ET close to zero 2021-2025 anche su NQ e YM; condizionata much narrower. Filtro 8 eliminatorio", "candidate": null},
    {"url": "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7035838", "title": "The Disappearing Overnight Drift (SSRN)", "kind": "paper", "verdict": "scartato", "reason": "Stesso contenuto del post Liberty Street 2026; giudicato dall'estratto, non aperto", "candidate": null},
    {"url": "https://avaneendra.substack.com/p/the-stock-market-paid-37-a-year-in", "title": "The Stock Market Paid 3.7% a Year in One Sleeping Hour (Avaneendra)", "kind": "site", "verdict": "scartato", "reason": "Riassunto del paper con Sharpe lordo/netto e strategia condizionata; nessun backtest proprio", "candidate": null},
    {"url": "https://support.lucidtrading.com/en/articles/11404729-allowed-trading-times", "title": "Lucid Trading - Allowed Trading Times", "kind": "site", "verdict": "aperto", "reason": "Flat entro 16:45 ET, ripartenza 18:00 ET: la sessione notturna Globex e' ammessa; manca la definizione di giornata per consistenza e MLL", "candidate": null},
    {"url": "https://ideas.repec.org/a/cup/jfinqa/v58y2023i3p939-967_1.html", "title": "Bondarenko-Muravyev, Market Return Around the Clock: A Puzzle (JFQA 2023)", "kind": "paper", "verdict": "scartato", "reason": "Campione 2004-2018 senza follow-up post-2021; stessa finestra dell'apertura europea gia' morta (filtro 8)", "candidate": null},
    {"url": "https://alphaarchitect.com/market-return-around-the-clock/", "title": "Alpha Architect - Market Return Around the Clock: A Puzzle", "kind": "site", "verdict": "scartato", "reason": "Fetch 403; il paper recensito e' scartato per il filtro 8, nessun motivo per riaprirla", "candidate": null},
    {"url": "https://cmegroup.com/markets/equities/sp/micro-e-mini-sandp-500.contractSpecs.html", "title": "CME Micro E-mini S&P 500 - contract specs", "kind": "site", "verdict": "scartato", "reason": "Specifica, non strategia: MES $5/pt, tick 0,25 = $1,25, orari 18:00-17:00 ET (da risultati di ricerca)", "candidate": null},
    {"url": "https://www.clearedge.trading/post/es-futures-trading-hours-automation-strategies", "title": "ES Futures Trading Hours: Best Sessions For Automation Strategies (ClearEdge)", "kind": "vendor", "verdict": "scartato", "reason": "Affermazioni sulla London open senza dati; nessuna regola", "candidate": null},
    {"url": "https://nexusfi.com/a/exchanges/market-hours", "title": "Market Hours - NexusFi Academy", "kind": "site", "verdict": "scartato", "reason": "Divulgativa sugli orari, numeri sul movimento notturno senza fonte", "candidate": null}
  ]
}
```

---

## Gate 0 — verifica automatica (gate0.py, nessun modello)

Ricalcolato da codice, non dal ricercatore. `?` = numero non fornito.

| Candidata | Esito | Controlli |
|---|---|---|
