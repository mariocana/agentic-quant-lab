# Dax FirstHour di Unger — **archivio, non testata**

Trascritta il 24/10/2026 da `13. Codici/DAXFirstHour/EasyLanguage/Dax FirstHour MC-TS.txt`
(identico alla copia in `0. Risorse/MC-TS`, a parte i fine riga). Codice: `DaxFirstHour.txt`,
da salvare in MultiCharts come `Mario_DaxFirstHour`.

## La strategia
DAX future **5 min**, ora di Francoforte, breakout della prima ora:

| | |
|---|---|
| Filtro | **daily factor** di ieri: `abs(open − close) < 0,75 × (high − low)`, cioè ieri non è stato un giorno di trend pieno (corpo sotto il 75% del range). Escluso il venerdì |
| Setup | fra le 09:00 e le 09:55, una volta: livello long = massimo del giorno + 0,95 × range del giorno; short = minimo − 0,95 × range |
| Ingresso | stop d'ingresso sui due livelli, al massimo un ingresso al giorno |
| Stop | il massimo del giorno (long) / il minimo (short) fissati al setup, più uno stop di emergenza di 1.000 € a contratto |
| Uscita | alle 21:55 o a fine sessione |

## Perché è archiviata
Il DAX si tratta solo su Eurex (FDAX, FDXM, FDXS), che le prop futures come Lucid non
offrono. Non c'è un equivalente CME. Si tiene come riferimento per l'idea: breakout della prima
ora filtrato dal daily factor del giorno prima.
