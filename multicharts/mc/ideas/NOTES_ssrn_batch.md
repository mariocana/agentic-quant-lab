# I tre paper SSRN in `mc/ideas/` — letti il 30/09/2026

Erano gli unici documenti della cartella davvero **non processati**. Li ho letti tutti e
tre per intero. Verdetto uguale per tutti: **scartato**.

Li tengo in un file solo perché condividono lo stesso difetto di fondo — sono tutti su
Bitcoin, tutti in percentuale, e nessuno produce una regola che possa entrare nella
nostra pipeline. Sotto il perché, uno per uno, così non li si riapre.

---

## 1. `ssrn-5598690.pdf` — *Evaluating the Parabolic SAR Strategy on Bitcoin*
**Mesíček, 13/11/2025, 16 pp.**

Test del Parabolic SAR (step 0,02 / max 0,2) su BTC/USDT 2015–2025, 1H e 1D, in tre
modalità: long-only, short-only, reversal.

**Il risultato è negativo e l'autore lo dice.** Nessuna modalità batte il buy & hold:
long-only 1H rende 35,95% annuo contro 84,99% del B&H, con DD −81,83%; short-only −44,55%
con DD −99,74%; reversal −24,62%. Conclusione testuale: *«performs poorly as a standalone
system»*.

Due motivi per cui non serve, oltre al risultato:

- **Costi a zero.** Backtesting assumptions: *«no fees, no slippage, full capital
  allocation»*. Con 6.370 trade su 1H, i costi sono l'intero esperimento — è esattamente
  l'errore che abbiamo passato due settimane a correggere sulle nostre run.
- **La parte "buona" è fittata.** Il modello «seasonality-calibrated» arriva a Sharpe 1,35
  restringendo l'operatività alle ore e ai giorni **storicamente più profittevoli** — cioè
  scelti dopo aver visto i risultati, senza alcun out-of-sample. È il fitting che la nostra
  pipeline vieta allo Stage 2. Non è un risultato, è una descrizione del passato.

Nulla da prendere. Il PSAR come trailing stop rimane un'idea nota che, semmai, si testa
da sé sulle nostre strategie — questo paper non aggiunge evidenza.

## 2. `ssrn-5580590.pdf` — *An Adaptive Multi-Agent Bitcoin Trading System*
**Singhi, UCL Computer Science, 19 pp. (versione condensata di una tesi da 80).**

Sistema di agenti LLM (DeepSeek-r1) specializzati — analisi tecnica, sentiment, decisione,
riflessione — che si «auto-migliorano» tramite critiche in linguaggio naturale iniettate
nei prompt successivi, senza fine-tuning. Alloca un portafoglio Bitcoin-only.

Interessante come architettura agentica. Inutile per noi, per quattro motivi, in ordine di
gravità:

1. **Contaminazione del test.** L'LLM valuta notizie e sentiment su un periodo,
   luglio 2024 – aprile 2025, che ricade nel suo training. Un modello che "prevede" eventi
   che ha già letto non sta prevedendo niente. Il paper non affronta il problema.
2. **Nove mesi di test.** Un solo ciclo di regime, definito peraltro con medie mobili a
   posteriori.
3. **Nessun costo di transazione.** I rendimenti sono `r_BTC × peso/100`: pura allocazione,
   zero frizione. Ironicamente l'introduzione avverte che *«execution costs, slippage, or
   regime shifts»* possono annullare i rendimenti attesi — e poi non ne modella nessuno.
4. **Non è una regola.** L'output è una decisione di un LLM, non riproducibile né
   codificabile in PowerLanguage. Non è backtestabile nel nostro senso.

Un'osservazione dell'introduzione vale la pena di essere citata perché coincide con quello
che abbiamo derivato da soli: *«being frequently correct does not necessarily translate
into making money… profit depends more on capital allocation, position sizing, and risk
management than on raw directional correctness»*. È il nostro criterio P/D detto a parole.
Conferma, non contributo.

## 3. `ssrn-6467818.pdf` — *Applied Econometrics and Algorithmic Trading*
**59 pp., autore non indicato, elaborato didattico.**

Era il candidato più promettente dei tre nel journal: ADF, volatility clustering, ARIMA,
GARCH, poi MA crossover e RSI mean-reversion con IS/OOS e walk-forward. Struttura giusta,
esecuzione no.

**Il documento si contraddice sui propri dati**, e questo da solo lo chiude:

- Parte I: *«The data is from January 2025 to January 2026»*, `count 364` rendimenti
  giornalieri.
- Parte IV: *«the full dataset (January 2024 to January 2026)»*, con IS gennaio 2024 –
  giugno 2025 e OOS luglio 2025 – gennaio 2026.
- E una walk-forward con **21 finestre** da 90 giorni di training + 30 di test, che
  richiede oltre 700 giorni. Con 364 righe non è calcolabile.

Altri segnali nello stesso senso: la strategia RSI ha **16 trade in-sample** (18 mesi) e
**42 out-of-sample** (7 mesi) — più trade nel periodo più corto; e su 16 trade il paper
riporta un Calmar di 3,87 come se significasse qualcosa.

Almeno i costi ci sono (0,1% per lato) e l'impianto IS/OOS + walk-forward è quello giusto
concettualmente. Ma come riferimento metodologico non serve: la nostra pipeline è più
severa di quella descritta qui, e su dati che esistono.

---

## Cosa ne esce, in una riga

Niente. Nessuna variante pre-registrata, nessun filtro, nessuna nota metodologica.

Il motivo per cui li avevamo tenuti — «magari il terzo serve per il metodo statistico» —
non regge alla lettura. Se serviranno ADF, GARCH o stylised facts, servirà un testo serio,
non un elaborato con i propri dati in disaccordo con se stessi.

**Regola che ne ricavo per i prossimi ingest**, da aggiungere alle cinque domande del
journal: *prima ancora di leggere, guardare quale asset e quali costi.* Tutti e tre erano
identificabili come fuori perimetro dall'abstract — Bitcoin, percentuali, nessuna
frizione. Trenta secondi invece di un'ora.
