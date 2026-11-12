# prova_vwap_fade: critica

## Filtri (`come_scegliere_un_paper.md`)

| # | filtro | esito | perché |
|---|---|---|---|
| 1 | testato su futures | **no** | nessuna fonte misura il fade sul VWAP, né su NQ né altrove; l'unica misura citata (Zarattini-Aziz) è su QQQ/TQQQ e va nel verso opposto |
| 2 | replicato | no | non c'è nemmeno un primo risultato da replicare |
| 3 | flusso forzato | non stabilito | il benchmark VWAP è un flusso di esecuzione, ma l'ipotesi stessa ammette che su NQ passa solo indirettamente e che i VWAP passivi non guardano il prezzo |
| 4 | costi riportati | no | nessuna fonte; costo di 1,5-2 $ assunto dall'autore |
| 5 | intraday, flat EOD, frequenza | sì | sessione 08:30-15:00 CT, chiusura forzata alle 15:00, 2-4 al giorno stimati (non misurati) |
| 6 | età | non stabilito | nessun paper a cui dare una data |
| 7 | t ≥ 3 | no | nessun t: il 66% è una soglia da raggiungere, non un risultato |
| 8 | campione dopo il 2021 o conferma recente | **no** | nessuna evidenza che l'effetto esista, tanto meno dopo il 2021; l'unica evidenza post-2021 citata (QQQ 2018-2023) dice trend, non ritorno |
| 9 | dati accessibili | sì | basta OHLCV a 1 minuto su NQ, che c'è |

## Fonti

L'unica fonte nella cartella è `fonti/idea.md`. I due numeri dell'ipotesi ci sono e i conti
sono giusti: (2,5 − 1,0)/2,5 = 60%; 1,3/1,97 = 66%. Sono però aritmetica su un random walk e su
un PF desiderato, non un effetto osservato. Le tre fonti esterne sono citate senza numeri e
senza pagina verificata: non reggono nessun numero e non provano che l'effetto esista.

## Conto dei costi

Edge per trade = WR·1σ − (1−WR)·1,5σ; σ = 20 punti (ipotesi non verificata); MNQ 2 $/punto;
costo 1,75 $ a trade (metà della forchetta assunta).

- alla soglia (WR 66%): 0,15σ = 3 pt = 6,00 $ lordi, 4,25 $ netti × 2-4 trade = **8,50-17,00 $/giorno**
- all'aspettativa dichiarata da Mario (+3, WR 63%): 0,075σ = 1,5 pt = 3,00 $ lordi, 1,25 $ netti × 2-4 = **2,50-5,00 $/giorno**
- minimo del perimetro: **10 $/giorno per micro**

Alla soglia il conto passa solo con 3 o più trade al giorno; al valore atteso dall'autore stesso
non passa a nessuna frequenza. Da solo non basta per il KILL, perché la regola chiede di prendere
per buono il numero della fonte, ma conferma che serve proprio il risultato che nessuno ha mai
osservato.

## Verdetto

Mancano due filtri eliminatori: il **1** (nessuna misura su futures, anzi nessuna misura) e
l'**8** (nessuna prova che l'effetto sia vivo dopo il 2021; l'unica evidenza recente sullo
stesso indice va nel verso opposto). Anche il perdente è debole: l'ipotesi ammette di non saper
nominare chi perde sempre, e il flusso legato al benchmark VWAP spiegherebbe altrettanto bene
la continuazione che trovano Zarattini-Aziz.

VERDETTO: KILL
