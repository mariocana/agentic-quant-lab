# Night FIB di Unger — **archivio, non testata**

Trascritta il 24/10/2026 da `13. Codici/Night FIB/EasyLanguage/Night FIB MC-TS.txt`
(identico alla copia in `0. Risorse/MC-TS`, a parte i fine riga). Codice: `NightFIB.txt`, da
salvare in MultiCharts come `Mario_NightFIB`.

## La strategia
FTSE MIB future (FIB) **5 min** + serie giornaliera come data2, ora dell'exchange. Solo long,
**overnight**:

| | |
|---|---|
| Condizione | (ieri ha fatto un minimo più basso di quello del giorno prima **e** il prezzo è sotto il minimo di ieri) **oppure** oggi ha aperto almeno 0,5% sotto la chiusura di ieri |
| Ingresso | a mercato dopo la barra delle **17:30**, se la condizione è vera |
| Uscita | a mercato dopo la barra delle **09:20** del giorno dopo |
| Stop | nessuno |

È un "compra la debolezza e tienila la notte".

## Perché è archiviata
Il FIB è su IDEM (Borsa Italiana), che le prop futures non offrono. Inoltre la posizione è
overnight e senza stop: con la regola "flat prima della chiusura" non si porterebbe nemmeno su
un indice CME senza cambiarne la natura.
