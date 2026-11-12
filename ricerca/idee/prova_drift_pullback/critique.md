# critique — prova_drift_pullback

## Filtri (`come_scegliere_un_paper.md`)

| # | filtro | esito | perché |
|---|---|---|---|
| 1 | futures | non stabilito | il praticante dice NQ, ma il PDF non è nel repo; l'unico paper (Zarattini et al.) è su SPY |
| 2 | replicato | no | una strategia di un corso, nessuna replica indipendente; il paper citato fa un'altra regola (breakout) |
| 3 | flusso forzato | **no** | l'unico flusso obbligato (gamma dei dealer) non entra nella regola; gli altri due sono racconto comportamentale |
| 4 | costi | non stabilito | non si sa se i $77 sono netti né se sono a mini o micro |
| 5 | intraday, flat EOD | sì | flat 14:55 CT, 1-4 trade al giorno dichiarati |
| 6 | età | sì | materiale recente, ma non pubblicato: niente decadimento da pubblicazione da stimare, né prova che non ci sia |
| 7 | t ≥ 3 | **no** | l'autore stesso dichiara t fuori campione 2,2 |
| 8 | campione oltre il 2021 | non stabilito | si dichiara un OOS e la strategia è in live, ma periodo e numeri non sono verificabili |
| 9 | dati accessibili | sì | barre OHLCV di NQ a 5 e 15 minuti, le abbiamo |

## Verdetto

KILL, per tre ragioni indipendenti.

1. **Le fonti non lo dicono.** La fonte 1 (tutorial Agnello, 18 pp.) non è nel repo: nessuna
   pagina si può aprire. $77 a trade, WR 65%, t 2,2 vengono solo dalla trascrizione in
   `fonti/idea.md`, che non indica le pagine. La fonte 2 (Zarattini, Aziz, Barbon, SSRN 4824172)
   è letta solo dall'abstract, è su SPY e descrive un breakout con trailing stop, non un
   ingresso sul pullback con bracket 80/40: non sostiene nessun numero della regola. La stessa
   ipotesi lo ammette: «Nessun numero della regola viene da una fonte con pagina verificata».
2. **Manca un filtro eliminatorio (3).** La regola prende tutti i drift dello 0,10% in un'ora
   e non guarda il gamma, il calendario dei ribilanciamenti né altro flusso obbligato.
3. **Nessuno che perde.** Il contrarian e l'inseguitore tardivo non sono costretti a niente.
   L'unica controparte obbligata, il dealer corto gamma, sta dalla nostra parte. E la storia
   regge anche al contrario: «la prima barra contraria dopo un drift è l'esaurimento» si
   racconta altrettanto bene.

**Il conto**, prendendo per buono il numero della fonte:
- $77 a trade letti come mini: **$7,70 a trade per micro**. Se fossero a micro, 38,5 punti
  su un target da 40 non sono plausibili.
- Costi per micro: 1-3 tick × $0,50 = $0,50-1,50, più circa $0,50-1,00 di commissione
  andata e ritorno: **$1,00-2,50 a trade**, se i $77 sono lordi.
- Netto per micro: $5,20-6,70 a trade, $7,70 se i $77 sono già netti.
- Segnali al giorno: 1,5-2 secondo l'ipotesi, 1 al minimo del perimetro.
  - a 1 segnale al giorno: **$5,20-7,70 < $10**: KILL;
  - a 1,5: $7,80-11,55, a cavallo;
  - a 2: $10,40-15,40, sopra di poco.
- Il conto passa solo con la frequenza ottimistica e i $77 presi come netti. Il t di 2,2
  dichiarato dall'autore resta comunque sotto i 3 errori standard del perimetro.

Il conto da solo non uccide l'idea, perché a 2 segnali al giorno passa. La uccidono i punti 1-3.

VERDETTO: KILL
