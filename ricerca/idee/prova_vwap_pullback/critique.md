# Critica: prova_vwap_pullback

## Filtri (come_scegliere_un_paper.md)

| # | filtro | esito | perché |
|---|---|---|---|
| 1 | futures | sì | backtest del corso su NQ 1 minuto |
| 2 | replicato | no | un corso anonimo, nessun autore indipendente |
| 3 | flusso forzato | non stabilito | il benchmark VWAP è un flusso obbligato, ma gli algo VWAP comprano in proporzione al volume, non a un livello di prezzo: che il prezzo "reagisca" al VWAP è un'idea comportamentale |
| 4 | costi | no | il corso non li riporta; $80 lordi su posizioni tenute overnight |
| 5 | intraday, segnali/giorno | no | flat 14:55 sì, ma al massimo 1 trade al giorno e la stima dell'ipotesi è 0,5–0,7, sotto il minimo di 1 |
| 6 | età | non stabilito | non si sa quando il corso è uscito; il backtest parte dal 2021 |
| 7 | t ≥ 3 | non stabilito | nessuna statistica; PF 1,2 e WR 58% senza numerosità |
| 8 | campione post-2021 | sì, debole | dichiarato "dal 2021", ma non verificabile |
| 9 | dati accessibili | sì | basta OHLCV a 1 minuto, ce l'abbiamo |

## Fonti

Fonte 1 (`fonti/idea.md`): i numeri ci sono (avg ~$80, PF 1,2, WR 58%, NQ 1 min dal 2021),
ma sono affermazioni di un corso, senza pagina e senza codice, e si riferiscono alla versione
che tiene overnight, non a questa regola. La variante ADX è dichiarata non verificata. Fonte 2
(il "90%+" di Madhavan 2002): ritirata dall'ipotesi stessa, nessuna pagina letta. Nessuna fonte
con pagina verificata sostiene l'edge della regola che si vuole misurare.

## Conto

Prendendo per buono il numero del corso, anche se è overnight e lordo:

- edge lordo per trade, micro: $80 / 10 = **$8**
- costi per trade, micro: **$2–3** (ingresso e stop a mercato con 1 tick ciascuno, più commissione)
- netto per trade: **$5–6**
- segnali al giorno: **0,5–0,7** (stima dell'ipotesi; tetto di costruzione 1)
- dollari al giorno per micro: 0,6 × $5,5 ≈ **$3,3** (intervallo $2,5–4,2)
- anche al tetto di 1 trade al giorno: 1 × $6 = **$6**

Soglia del perimetro: **$10 al giorno per micro**. Sotto anche nel caso migliore, e servirebbero
~$17 netti per trade sul micro (~$170 sul contratto intero), più del doppio di quanto dichiara la
fonte con la tenuta overnight.

## Verdetto

KILL, per quattro ragioni indipendenti, ognuna sufficiente:

1. **Fuori perimetro**: l'orizzonte intraday chiede almeno 1 segnale al giorno; la regola ha un
   tetto di 1 trade al giorno e una frequenza attesa di 0,5–0,7. Per questo cade il filtro 5,
   che è eliminatorio.
2. **I costi se lo mangiano**: $3,3 al giorno per micro contro $10, usando il numero più
   favorevole della fonte.
3. **Le fonti non lo dicono**: l'unico numero viene da un corso senza pagina, ed è per una
   regola diversa (con tenuta overnight).
4. **Nessuno che perde, in modo solido**: chi insegue il breakout e chi sfuma il pullback sono
   figure comportamentali. La storia del rinforzo intermittente spiegherebbe allo stesso modo il
   risultato opposto ("nella metà dei giorni sfumare il pullback paga"). Il filtro 3 resta non
   stabilito.

La regola in sé è eseguibile e non lascia parametri liberi: non è questo il problema.

VERDETTO: KILL
