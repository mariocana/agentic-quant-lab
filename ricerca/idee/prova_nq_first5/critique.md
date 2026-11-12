# prova_nq_first5 — critica

`GIA_FATTO`: prova alla cieca, il criterio «già provata» non si applica.

## Filtri (`come_scegliere_un_paper.md`)

| # | filtro | esito | perché |
|---|---|---|---|
| 1 | testato su futures | **no** (eliminatorio) | il template non è testato su niente: l'autore lo dichiara non validato. Zarattini-Aziz è su QQQ, un ETF, con un altro segnale e con lo stop |
| 2 | replicato | no | nessuna replica, nemmeno un primo test |
| 3 | flusso forzato | **non stabilito** (eliminatorio) | il flusso MOO è reale, ma la regola misura il close contro un'EMA fatta di barre notturne, non quel flusso. Che continui fino alle 15:00 nessuna fonte lo documenta |
| 4 | costi riportati, edge > costo | no | nessuna fonte dichiara un edge |
| 5 | intraday, flat EOD, segnali/giorno | sì | 08:35-15:00 CT, 1 segnale al giorno: sta sul minimo del perimetro (`segnali_al_giorno_min: 1`) |
| 6 | età | non stabilito | il template non ha data. Zarattini-Aziz è del 2023 |
| 7 | t ≥ 3 | no | nessun t, nessun numero |
| 8 | campione oltre il 2021 | **no** (eliminatorio) | il template non ha campione. Zarattini-Aziz arriva al 2023, ma su un ETF e con un'altra regola, quindi non conferma questo effetto |
| 9 | dati accessibili | sì | NQ a 1 minuto è nel lake |

## Conto dei costi

- Minimo del perimetro: $10 al giorno per micro. Con 1 segnale al giorno servono $10 netti a trade su MNQ.
- Costo su MNQ: 2 tick × $0,50 = $1, più la commissione (assumiamo circa $1 andata e ritorno), quindi circa $2.
- L'edge lordo deve essere di almeno $12 a trade su MNQ, cioè circa **6 punti NQ di media a trade**, a favore della direzione e su 1.250 trade.
- L'edge dichiarato dalla fonte è **nessuno**: nessuna fonte dà un numero da mettere nel conto. Il conto quindi non si può chiudere né a favore né contro. Su questo criterio da solo non è un KILL.

## Ragioni di KILL

1. **Manca un filtro eliminatorio, l'1**: l'effetto non è testato su futures, e nemmeno su altro. L'unico lavoro testato riguarda un ETF e un segnale diverso.
2. **Manca un filtro eliminatorio, l'8**: nessuna evidenza che l'effetto sia vivo dopo il 2021 su questo strumento con questa regola.
3. **Le fonti non lo dicono**: la fonte 1 non riporta numeri. Della fonte 2 la pagina non è verificata e l'ipotesi stessa dice che non ne riporta nulla. Nessuna fonte sostiene l'affermazione centrale, cioè che il close contro l'EMA(12) alle 08:35 prevede il rendimento 08:35-15:00.
4. **Nessuno che perde**: «chi fa fade e chi entra tardi» non spiega perché continuino a perdere, e lo stesso racconto (il flusso d'apertura si esaurisce nella prima barra) andrebbe bene anche per un'inversione. Il filtro 3 resta quindi non stabilito.

VERDETTO: KILL
