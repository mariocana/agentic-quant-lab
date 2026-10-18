# PtnBaseSA — la funzione dei pattern base di Unger

Non è una strategia: è la funzione che Trend Following, Counter Trend, Gap e BIAS usano come
filtro d'ingresso (`MyPtnLY`, `MyPtnSY` = pattern che deve essere vero; `MyPtnLN`, `MyPtnSN` =
pattern che deve essere falso; 41 = sempre vero, 42 = sempre falso, cioè "nessun filtro").

**Fonte**: codice nell'editor di Unger, video 4x01 (compilato il 20/01/2016). Le descrizioni
sono le slide del modulo 3 (3x01–3x04) e `12x03 pattern base reference.docx`. Il file
trascritto in `13. Codici` aveva errori di lettura e due copie diverse: non usato.

## File
| file | cosa |
|---|---|
| `PtnBaseSA.txt` | la funzione (Return Type **TrueFalse**) |
| `PtnBaseSA_Check.txt` | indicatore per lo Stage 1: a fine sessione stampa 40 cifre, una per pattern |
| `check_ptn.py` | ricalcola i 40 pattern dal log e li confronta (solo libreria standard) |

## I pattern
Indici: **0 = sessione in corso** (valori fino alla barra corrente), 1 = ieri, … 5 = cinque
sessioni fa. O/H/L/C = open, high, low, close della sessione.

| # | tipo | condizione |
|---|---|---|
| 1 | volatilità (indecisione) | corpo di ieri < 50% del range di ieri |
| 2 | volatilità | \|O1 − C5\| < 50% di (H5 − C1) |
| 3 | volatilità | \|O5 − C1\| < 50% del range delle ultime 5 sessioni |
| 4 / 5 | direzionale su | H0 − O0 > (H1 − O1) × 1 / × 1,5 *(usa oggi)* |
| 6 / 7 | direzionale giù | O0 − L0 > (O1 − L1) × 1 / × 1,5 *(usa oggi)* |
| 8 / 9 | direzionale | 3 chiusure consecutive in salita / in discesa (C1>C2>C3>C4) |
| 10 / 11 | direzionale | ieri massimo e minimo più alti / più bassi di l'altro ieri |
| 12 / 13 | espansione / compressione | range di oggi > / < 0,75% del minimo di oggi *(usa oggi)* |
| 14 / 15 | direzionale | ieri chiusura in salita / in discesa |
| 16 / 17 | direzionale | ieri chiusura sotto / sopra l'apertura |
| 18 / 19 | direzionale | ieri chiusura in calo / in rialzo di oltre lo 0,5% |
| 20 | forza | oggi sopra il massimo di ieri *(usa oggi)* |
| 21 | trend su | massimo di ieri > massimo di 5 giorni fa |
| 22 | debolezza | oggi sotto il minimo di ieri *(usa oggi)* |
| 23 | trend giù | minimo di ieri < minimo di 5 giorni fa |
| 24 / 25 | | massimo di ieri il più alto / il più basso degli ultimi 4 giorni |
| 26 / 27 | | minimo di ieri il più basso / il più alto degli ultimi 4 giorni |
| 28 / 29 | | 2 chiusure in salita e apertura di oggi sopra la chiusura di ieri / il contrario |
| 30 / 31 | | ieri chiusura nel 20% alto / basso del range |
| 32 | gap | apertura di oggi sopra il massimo o sotto il minimo di ieri |
| 33 / 34 | gap | apertura di oggi oltre lo 0,5% sotto / sopra la chiusura di ieri |
| 35 | inside oggi | oggi dentro il range di ieri *(usa oggi)* |
| 36 | contrazione | range di ieri < (range di 2 e 3 giorni fa) / 3 |
| 37 | contrazione | range in calo per 3 giorni |
| 38 | inside bar | ieri inside bar |
| 39 | | ieri **non** outside bar (con disuguaglianze strette, come nel codice) |
| 40 | outside bar | ieri outside bar |
| 41 / 42 | — | sempre vero / sempre falso |

**I pattern "usa oggi"** (4–7, 12, 13, 20, 22, 35) cambiano durante la sessione. In una
strategia intraday sono legittimi; su barre giornaliere sarebbero lookahead.

## Stage 1 (verifica, non è una strategia)
1. PowerLanguage Editor → New → **Function** `PtnBaseSA`, Return Type **TrueFalse**, incolla
   `PtnBaseSA.txt`, compila. Se `OpenS` / `HighS` / `LowS` / `CloseS` non esistono nella tua
   versione di MultiCharts, la compilazione lo dice: mandami l'errore e le scrivo.
2. New → **Indicator** `PtnBaseSA_Check`, incolla, compila.
3. Chart **@ES 30 min**, template **17:00–16:00 CT senza pause**, ultimi ~100 giorni;
   inserisci l'indicatore. Copia l'output del PowerLanguage Editor in un `.txt`.
4. Mandami il `.txt`: lancio `python3 check_ptn.py log.txt`.

**Gate 1**: tutti i 40 pattern coincidono con il ricalcolo su tutte le sessioni con 5 giorni
di storia. In più controllo a mano O/H/L/C di due sessioni contro il chart, e i valori di
sessione contro le barre `1d_cme` di quantlake.
