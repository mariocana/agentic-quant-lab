# Cosa possiamo tradare su LucidFlex, e quanto costa

**Fonte:** <https://support.lucidtrading.com/en/articles/11508978-approved-products-and-commissions>
· letta il 17/10/2026 (articolo aggiornato il 26/08/2026).

**34 prodotti approvati.** Noi finora abbiamo guardato **solo indici**, che sono 9 su 34.

## Le commissioni vere, per lato

| classe | simboli | $/lato |
|---|---|---|
| **micro indici** | MES · MNQ · M2K · MYM | **0,50** |
| **micro energia** | **MCL** (crude) | **0,50** |
| micro metalli | MGC (oro) | 0,80 |
| micro argento | SIL | 1,60 |
| e-mini indici | ES · NQ · RTY · YM · NKD | 1,75 |
| energia | CL · NG · QM 2,00 · QG 1,30 | 1,30-2,00 |
| metalli | GC · SI · HG · PL | 2,30 |
| valute | 6A · 6B · 6C · 6E · 6J · 6S · 6N | 2,40 |
| agricoli e carni | ZS · ZC · ZL · ZM · ZW · HE · LE | 2,80 |

## La prima cosa che questo verifica: la nostra assunzione sui costi era giusta

Nel simulatore usiamo **$1,50 per round-turn sul micro**. Scomposto con i numeri veri:
**$0,50 × 2 lati = $1,00 di commissione Lucid**, piu **$0,50 di slippage** (un tick di MNQ).
**Torna, ed e leggermente conservativa** — era una stima, ora e un dato.

Stessa verifica sul full-size: usiamo **$7,50/lato** su NQ, che e $1,75 di commissione piu
~$5,75 di slippage, cioe poco piu di un tick ($5). Conservativa ma non assurda.

## Il conto per strumento, al budget di rischio che l'MLL consente

Range RTH mediani **misurati da noi** sul 2020-2024 (`measures/atr_window_rth_2020-2026.txt`),
con R = **$80 per micro**:

| micro | range giornaliero | **R/ATR** | costo round-turn | costo come % di R |
|---|---|---|---|---|
| **MNQ** | $420 | **0,19** | $1,50 | 1,9% |
| MES | $224 | 0,36 | $2,25 | 2,8% |
| **MYM** | $170 | **0,47** | $1,50 | **1,9%** |
| **M2K** | $162 | **0,49** | $1,50 | **1,9%** |
| MGC | $178 | 0,45 | $2,60 | 3,2% |
| **MCL** | **$170** | **0,47** | $2,00 | 2,5% |

**MNQ e il peggiore su R/ATR e di parecchio**: uno stop da $80 vale 0,19 del range
giornaliero, cioe sta dentro il rumore. MYM e M2K sono 2,5 volte meglio **allo stesso costo**.
E il motivo strutturale per cui tre strategie su NQ sono morte sullo stesso numero.

## Quello che si apre, e che non avevamo considerato

**MCL (Micro Crude Oil) costa quanto i micro indici: $0,50 per lato.** E l'unico strumento
non-indice con la commissione piu bassa del listino, e il crude ha driver completamente
diversi dal NASDAQ — inventari, OPEC, geopolitica. **Per il basket e la diversificazione piu
vera disponibile a questo prezzo**, molto piu di un secondo indice: NQ/ES/YM/RTY sono fra loro
0,8-0,95 correlati intraday.

Lesson 3, 18:22: *"A mix of strategies families, **a mix of instruments and asset classes**,
avoid stacking the same logic on the same market."* Finora abbiamo fatto solo la prima meta,
e nemmeno quella (sei strategie su sei erano momentum).

### Misurato il 17/10/2026, e il risultato e una coincidenza utile

`measures/atr_window_rth_CL_2020-2024.txt` e `..._YM_...` (1.250 e 1.248 giorni).

> **MCL e MYM hanno lo stesso identico range giornaliero in dollari: $170 contro $169.**
> E quindi lo stesso R/ATR a ogni budget: **0,35** a $60, **0,47** a $80, **0,65** a $110.

Come unita di rischio sono **intercambiabili**. La scelta fra i due non si fa quindi sul
rischio, si fa su altre tre cose:

| | **MCL** | **MYM** |
|---|---|---|
| range giornaliero per micro | $170 | $169 |
| R/ATR a R=$80 | 0,47 | 0,47 |
| tick in dollari | $1,00 | **$0,50** |
| costo round-turn | $2,00 (2,5% di R) | **$1,50 (1,9%)** |
| stabilita di regime (anno max / anno min) | 2,42 | **1,68** |
| classe di attivo | **crude: driver suoi** | indice azionario, 0,8-0,95 con NQ |

**MYM vince su costo, granularita e stabilita. MCL vince sull'unica cosa che MYM non puo
dare: non e un indice azionario.**

Il 2022 spiega la differenza di stabilita: il crude passa da ~$150 a **$298** di range
mediano (crisi energetica), mentre YM arriva a $239. Una strategia tarata sul crude del 2021
si trova in un mercato diverso nel 2022.

**La mia stima precedente era sbagliata del 18%**: avevo scritto ~$200 di range e R/ATR 0,40,
misurati $170 e 0,47. Nella direzione che favorisce MCL, ma era comunque una stima.

**Controprova riuscita**: YM misura 338,50 punti di range mediano contro i **339,0** della
misura precedente sui cinque indici. Le due campagne di misura combaciano.

## Cosa resta escluso, e perche

- **Valute** ($2,40/lato, nessun micro nel listino): il costo per R e 3 volte quello dei micro
  indici. Esclusi dal budget, non dall'idea.
- **Agricoli e carni** ($2,80/lato, nessun micro): stesso problema, peggiore.
- **SIL** (micro argento, $1,60/lato): il micro piu caro del listino.
- **NKD** (Nikkei): e-mini only, $1,75/lato, e un altro indice azionario — non aggiunge
  diversificazione.

## Prossima misura

`ATR_Window_Study` su **@CL** e **@YM** sul 2020-2024, per avere i range veri invece delle
stime. E lo stesso run serve a decidere lo strumento di VWAP Fade.
