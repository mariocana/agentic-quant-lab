# Il difetto nel metodo «eccesso sul caso», e come si corregge

**Trovato il 17/10/2026**, quando ON Reversal ha dato **t = −2,24** allo Stage 2 dopo che la
misura l'aveva autorizzata con **+4,40 pp a 3,06 errori standard**. Non e' un caso di edge
svanito: **era la misura a essere sbagliata**, e in due modi che si sommano.

## Difetto 1 — il tie-break dentro la barra

I miei indicatori risolvono il primo tocco cosi':

```
if Low <= tgtPx then        -> TARGET
else if High >= stopPx then -> STOP
```

**Quando una barra tocca ENTRAMBI, conto sempre il target.** Su barre da 5 minuti, con target
e stop a meno di 1 G di distanza fra loro e all'apertura (il momento piu' volatile), succede
spesso.

**Quanto pesa, misurato:**

| | WR sui risolti |
|---|---|
| misura su barre 5 min (2016-19 / 2020-24) | 64,8% e 64,1% |
| **backtest col percorso a 1 minuto** | **60,7%** |
| il caso | 60,0% |

> **L'eccesso vero e' +0,7 pp, non +4,40.** Lo scarto fra misura e realta' e' quasi
> esattamente l'eccesso che avevo riportato: era **tutto** artefatto.

**Lo stesso difetto e' nel `VWAP_Fade_Study`**, con lo stesso ordine di controlli. Il suo
+0,41 pp era quindi probabilmente **negativo**. Non cambia quel verdetto — era gia' bocciata —
ma va saputo.

## Difetto 2 — i non risolti sono selezionati, non neutri

La misura escludeva dal win rate i setup che non raggiungono ne' target ne' stop entro la
finestra. Erano il **29%**. Li trattavo implicitamente come neutri. **Non lo sono.**

| uscita | n | P&L medio |
|---|---|---|
| `L-flat` | 197 | **−$130,84** |
| `S-flat` | 289 | **−$100,61** |
| **totale** | **486** | **−$54.852** |

**E' selezione, non sfortuna.** Il target sta a 0,50 G e lo stop a 0,75: chi va bene **tocca
il target e si risolve**, chi va male **resta in rosso senza arrivare allo stop** e viene
chiuso a tempo. **Il secchio dei non risolti e' fatto di perdenti per costruzione**, ogni
volta che il target e' piu' vicino dello stop.

## La ricostruzione torna

`713 × $307 + 462 × (−$445) + 486 × (−$112,9) = −$41.568`, contro un net vero di
**−$40.784**. I due difetti spiegano **tutto** il divario.

## Le correzioni al metodo

1. **Le barre ambigue si contano a parte.** Quando una barra tocca target e stop, non si
   decide: si incrementa un contatore `ambigui` e si stampa. Se sono una frazione non
   trascurabile, **il win rate sui risolti non si legge** — esattamente come gia' facciamo col
   `R:R realizzato` e col `sigma all'ingresso`.
2. **Si stampa anche la versione conservativa**, con le ambigue assegnate allo **stop**. Il
   vero sta fra le due, e se il verdetto cambia fra le due versioni la misura non basta e
   serve il backtest.
3. **I non risolti non si escludono mai in silenzio.** Vanno contati, e se sono sopra il 10%
   la misura va dichiarata **parziale**: dice qualcosa sul sottoinsieme che si risolve, non
   sulla strategia.
4. **Con target piu' vicino dello stop, il punto 3 e' obbligatorio**, perche' li' la selezione
   dei non risolti e' strutturale e va sempre nella stessa direzione.

## La lezione piu' generale

I tre difetti trovati oggi negli indicatori di misura (riarmo mancante, caso calcolato sulla
geometria sbagliata, e questi due) hanno una cosa in comune: **erano tutti visibili confrontando
la misura col backtest**, e nessuno era visibile guardando la sola misura.

> **Un indicatore di misura non autorizza una strategia. Al massimo la propone.**
> Il numero che conta resta quello del backtest, con i costi e il Bar Magnifier.
