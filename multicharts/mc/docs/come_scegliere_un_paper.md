# Come scegliere un paper prima di spenderci un run

**Il problema da cui si parte:** la maggior parte di cio' che e' pubblicato non regge.

- **McLean e Pontiff** (*Journal of Finance*, 2016), 97 predittori: rendimenti **26% piu'
  bassi fuori campione** e **58% piu' bassi dopo la pubblicazione**. Il decadimento e'
  massimo 3-4 anni dopo l'uscita del paper.
- **Hou, Xue e Zhang** (*Review of Financial Studies*, 2020), oltre 450 anomalie: una quota
  grande non si replica — fra circa la meta' e i due terzi a seconda della versione e della
  soglia, e di piu' alzando l'asticella a **t ≥ 3**. Il numero esatto e' contestato (Chen e
  Zimmermann), il fenomeno no.

Quindi **«pubblicato su una buona rivista» non basta.** Serve un filtro che si applica in
un'ora, senza scrivere codice, prima di decidere se vale un run.

## Il filtro, in ordine di peso

| # | domanda | perche' |
|---|---|---|
| 1 | **E' testato su futures**, o almeno sull'indice che tradiamo? | *Fast Alpha* era su SPY, e su YM non si e' trasferito. Azioni singole ed ETF non contano |
| 2 | **E' replicato** da autori indipendenti, o su molti mercati e periodi? | un solo paper su un solo mercato e' il caso tipico del 58% che sparisce |
| 3 | **Ha un meccanismo di flusso forzato?** Hedging, ribilanciamenti, benchmark di esecuzione, fornitura di liquidita' | un flusso obbligato non sparisce perche' qualcuno l'ha pubblicato; un pattern comportamentale si' |
| 4 | **Riporta i costi**, e l'edge per trade e' piu' grande del costo per trade? | lo studio cripto del 2026: edge da 1,3 punti base, costo da 5 |
| 5 | **E' intraday e chiude entro la sessione?** Quanti segnali al giorno? | flat EOD obbligatorio. **≥ 2 al giorno** per una gamba principale, **~1** accettabile per una seconda |
| 6 | **Quanti anni ha?** | oltre 3-4 anni dalla pubblicazione, aspettarsi **meta' dell'edge** |
| 7 | **Il t del paper e' ≥ 3?** | lo standard per il multiple testing (Harvey-Liu-Zhu, Hou-Xue-Zhang), ed e' la stessa soglia che usiamo noi |

**Come si usa:** i punti 1, 3 e 5 sono **eliminatori** (dal 24/10 anche **8 e 9**, vedi in fondo) — se uno manca, il paper non entra.
Gli altri danno il **prior**: decidono quanto aspettarsi, e quindi la soglia da
pre-registrare.

## Dove cercare, in ordine di affidabilita'

1. **Riviste di primo livello**: *Journal of Finance*, *Journal of Financial Economics*,
   *Review of Financial Studies*. Poi *JFQA*, *Review of Finance*.
2. **Riviste specifiche**: ***Journal of Futures Markets*** (il nostro strumento) e
   *Journal of Financial Markets* (microstruttura e intraday).
3. **Aggregatori che fanno gia' parte del filtro**: **Quantpedia** (schede con backtest e
   indicazione della replica), **Alpha Architect** (recensioni critiche), **CXO Advisory**
   (verifiche scettiche).
4. **SSRN**: working paper non referati. Utili, ma guardare gli autori, le citazioni e se poi
   e' stato pubblicato.
5. **Google Scholar, «citato da»**: chi l'ha citato, e soprattutto **chi l'ha replicato o
   smentito**. E' il modo piu' rapido per il punto 2.

## Il limite strutturale, da sapere prima di cercare

**La letteratura solida e' quasi tutta a frequenza giornaliera o mensile**: inutile per una
prop intraday con flat a fine giornata. E gli effetti intraday **ad alta frequenza** ben
documentati richiedono dati di book e vengono mangiati dai costi.

> Lo spazio utile e' stretto: **effetti intraday da 1-3 segnali al giorno con un meccanismo
> di flusso forzato.** E' per questo che e' difficile, non perche' cerchiamo male.

## Un esempio che passa il filtro

**Baltussen, Da, Lammers, Martens — *Hedging demand and market intraday momentum***,
*Journal of Financial Economics* 142 (2021), 377-403.

| filtro | |
|---|---|
| 1. futures | **si'**: oltre 60 futures su azionario, obbligazionario, commodity e valute |
| 2. replicato | **si'**: estende Gao-Han-Li-Zhou (*JFE* 2018), e su 60+ mercati dal **1974 al 2020** |
| 3. meccanismo | **si'**: il **gamma hedging** dei market maker di opzioni e degli ETF a leva — flusso obbligato |
| 4. costi | da verificare nel testo |
| 5. intraday | **si'**: la mezz'ora finale e' prevista dal rendimento del resto della giornata. **~1 segnale al giorno**: da seconda gamba, non da prima |
| 6. eta' | pubblicato nel 2021: siamo **oltre** il picco di decadimento. Aspettarsi meta' |
| 7. t | da verificare nel testo |

**E cade in una finestra quasi libera**: la mezz'ora finale e' 14:30-15:00 CT. Nell'OOS
2025-2026 DriftPullback ha **22 ingressi su 1.439** nell'ora delle 14:00.

**Nota di onesta'**: e' **momentum**, la stessa famiglia di DriftPullback. Ma con un
meccanismo diverso (flusso di hedging contro timing del drift) e in un orario diverso. La
correlazione va misurata, non assunta.

## E DriftPullback, passerebbe questo filtro?

Solo a meta': *Fast Alpha* e' un singolo paper di una societa' di ricerca, non referato, del
2026, su SPY e non su futures. Eppure e' l'unica sopravvissuta.

**Perche' il filtro migliora il prior, ma a decidere sono i nostri test.** Non serve a
trovare la strategia giusta: serve a non spendere un giorno su una che parte gia' sbagliata.

## Fonti

- [McLean e Pontiff, *Does Academic Research Destroy Stock Return Predictability?*](https://Www.Gwern.net/doc/economics/2016-mclean.pdf)
- [Hou, Xue, Zhang, *Replicating Anomalies* — sintesi Alpha Architect](https://alphaarchitect.com/replicating-anomalies/)
- [Baltussen, Da, Lammers, Martens — working paper](https://www3.nd.edu/~zda/intramom.pdf) · [scheda RePEc](https://ideas.repec.org/a/eee/jfinec/v142y2021i1p377-403.html)
- [Alpha Architect sul gamma hedging](https://alphaarchitect.com/hot-topic-does-gamma-hedging-actually-affect-stock-prices/)

---

## Il primo caso alla prova (23/10/2026)

**Baltussen et al. ha passato il filtro ed e' morto al primo run**: t 0,52 sul 2020-2024
contro 3,64 attesi. Sugli 82 trade dentro il suo campione (gen-apr 2020) t 1,49; sui 1.165
dopo, **t −0,22**. Decadimento totale.

**Cosa ci dice sul filtro:** ha fatto il suo lavoro — fonte solida, meccanismo vero, un solo
run per decidere invece di una settimana — **ma il punto 6 va corretto**. «Aspettarsi meta'
dell'edge» era ottimista: per un effetto intraday su futures liquidissimi, pubblicato e
replicato, **va pre-registrato aspettandosi anche zero**. Il valore del filtro non e'
promettere un edge: e' far morire in fretta le idee che lo hanno perso.

---

## Due domande in piu', dopo i casi di ottobre (23/10/2026)

| # | domanda | perche' |
|---|---|---|
| 8 | **Il campione arriva oltre il 2021, o un lavoro recente conferma che l'effetto e' vivo?** | Due effetti sui futures su indice con dati fino al 2020 sono **morti entrambi dopo il 2021**: il momentum dell'ultima mezz'ora (Baltussen et al., nostro test: t −0,22 dopo maggio 2020) e l'*overnight drift* (Boyarchenko-Larsen-Whelan, *RFS* 2023), **dichiarato scomparso dagli stessi autori** a luglio 2026: la finestra 2-3 ET rendeva il 3,7% annuo ed e' vicina a zero dal 2021, anche su Nasdaq e Dow |
| 9 | **I dati che il segnale richiede sono accessibili a noi?** | un effetto condizionato su dati proprietari non e' testabile, per quanto sia vero |

**La regola che ne viene:** prima di spendere un run su un paper con dati pre-2021, **cercare
un follow-up recente** — spesso degli stessi autori. Per l'overnight drift avrebbe risparmiato
un'intera giornata di lavoro: la risposta era gia' pubblicata.

E il motivo probabile della moria e' uno solo: **dal 2022 le opzioni 0DTE hanno cambiato il
posizionamento gamma dei dealer**, e gli effetti intraday sui futures su indice dipendono da li'.


---

## La domanda 8 diventa eliminatoria (24/10/2026)

**Regola:** un paper il cui campione finisce prima del 2021 **non entra**, a meno che un lavoro
recente — degli stessi autori o di altri — mostri che l'effetto e' vivo dopo il 2021. Senza
deroghe. Eliminatorie ora sono **1, 3, 5, 8 e 9**.

**Il caso che l'ha decisa: FX Fix.** Krohn-Mueller-Whelan (*JF* 2024), campione 1999-2018. Su
EUR nel 2020-2024 la direzione c'e' ancora, ma ne resta **un quarto**: t lordo ~1 su entrambe le
finestre, sotto i costi del contratto intero. Il paper era passato con la domanda 8 segnata come
rischio, non come blocco.

**Perche' non bastava saperlo:** il caso FX Fix esclude la spiegazione "e' colpa delle 0DTE".
Le valute non dipendono dal gamma dei dealer azionari, eppure il decadimento e' lo stesso. Il
fattore comune e' piu' semplice: **effetto pubblicato, campione vecchio**.

| candidata | campione del paper | quanto ne restava nel nostro IS |
|---|---|---|
| LastHalfHour (Baltussen et al.) | fino al 2020 | t −0,22 dopo maggio 2020 |
| overnight drift (Boyarchenko et al.) | fino al 2020 | dichiarato morto dagli autori |
| FX Fix (Krohn-Mueller-Whelan) | fino al 2018 | 23-28% del lordo |

**Come si applica in pratica:** il primo controllo su un paper e' la data di fine del campione.
Se e' prima del 2021, si cerca "citato da" su Google Scholar e un follow-up degli autori; se non
c'e' evidenza post-2021, ci si ferma li', prima di leggere il resto.
