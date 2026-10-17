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
| **MCL** | ~$200 **[stima]** | ~0,40 **[stima]** | $2,00 | 2,5% |

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

**Ma il range di MCL non l'abbiamo misurato**: lo 0,40 di R/ATR e una stima da un ATR di ~$2
sul crude. Va misurato con `ATR_Window_Study` prima di costruirci sopra qualunque cosa.

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
