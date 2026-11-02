# SPEC — VWAP Pullback + gate ADX, v4 del corso, NQ (Stage 0, 29/10/2026)

**Perché esiste.** La nostra `SPEC.md` aveva il gate ADX come variante Stage 4, sopra una base
che è morta in fase 2 (t IS 0,87; filtrata 0,69). La versione che l'autore usa nel trittico
delle Live 4 e 5 è la **v4 «C.S.»**
(`education/protocollo/9.TheBridge/STRATEGIES/PROP FIRM NATIVE LOW RR/VWAP Pullback + ADX gate.txt`):
gate ADX acceso, solo long, un trade al giorno. Non l'abbiamo mai testata. Si riparte dallo
Stage 0 sulla v4 completa, non come filtro sulla nostra base.

## Codice

`VWAP_Pullback.txt`, lo stesso file. Il nucleo della v4 coincide con la nostra v1: l'autore
scrive «CORE LOGIC: unchanged from v1 port». Aggiunti i cinque input del gate ADX, spenti
di default: con i default il codice resta la v1 dei report vecchi.

Profilo v4, da impostare negli input:

| input | v4 | nostra base |
|---|---|---|
| `UseADXElev` / `ADXElev_Thr` | **1 / 20**: ADX(14) ≥ 20 | 0 |
| `UseADXDecay` / `ADXDecay_LB` | **1 / 1**: ADX ≤ ADX della barra prima | 0 |
| `ADX_Len` | 14 | — |
| `TradeShorts` | **0** (solo long) | 1 |
| `VwapEndTime` / `EntryEndTime` | **1700 / 1700** CT | 1500 / 1400 |
| `EODFlatTime` | **1555** CT | 1455 |
| `MaxTradesPerDay`, `RetestMode`, `StopMode`, swing | 1, 1, 1, 20/5 | uguali |
| sizing | 1 contratto fisso (`UseVolSizing false`) | 1 contratto |

Il gate si valuta sulla barra del segnale, con ingresso alla barra dopo: niente lookahead.
**Ritarda, non annulla**: i latch restano armati e l'ingresso parte appena l'ADX torna in
regola, se il reclaim è ancora vero.

**Orari.** Su Globex il VWAP accumula fino alle 16:00 CT, quando il mercato chiude, e il flat
è alle 15:55. Prima dello Stage 7 va verificato l'orario di chiusura obbligatoria su Lucid.

## Ipotesi

Uguale a `SPEC.md` (ritorno sul VWAP nella direzione del bias dell'opening range). In più:
il retest funziona quando c'è trend (ADX ≥ 20) e il trend si sta raffreddando (ADX in calo),
cioè su un pullback e non su un'inversione.

## Contaminazione

1. **Il gate è nato guardando il risultato.** Live 002, 30:40–31:26: l'autore cambia l'ingresso
   con l'ADX dopo una performance recente scarsa e pubblica la v4 **il 3 luglio 2026**. Tutto
   quello che viene prima è in-sample per il gate, OOS 2025–26 compreso.
2. **È la quarta versione di VWAP Pullback** dopo base, filtrata e `StopMode 2`. Regola delle
   varianti a posteriori: **k = 4**.
3. **Fuori campione pulito: dal 3/7/2026.** Circa 4 mesi, con un trade al giorno al massimo e
   solo long: poche decine di trade, non abbastanza per un t.

## Criteri

| fase | criterio | se fallisce |
|---|---|---|
| **1 — meccanica** (100 giorni) | solo long, max 1 ingresso al giorno, nessun ingresso con ADX < 20 o ADX in salita (log `ShowLog 1`), stop e target sui pivot dichiarati, flat alle 15:55, scaling ×10 esatto. Misurare la distribuzione della distanza dello stop **prima** della fase 2 | si corregge il codice |
| **2 — IS 2020–2024** | via A: t ≥ 2 · WR ≥ 55% · R:R 0,5–1. Altrimenti via B: **t > 1,03** (k = 4) e trade peggiore ≤ $500 per micro | cimitero |
| **3 — OOS 2025–2026**, una volta | via A: t ≥ 1,3. Via B: gate marginale | cimitero, definitivo |

**Verdetto asimmetrico in fase 3**, come per VaultBreak v8: il fallimento conta pieno, il
successo vale solo come ingresso in prova dal vivo. Il forward dal 3/7/2026 si legge a parte,
come controllo di direzione (avg > 0), non come test.

**Trade peggiore.** Lo stop è un pivot swing di ampiezza variabile: nella v1 la coda superava
$500 per micro. La v4 non ha un tetto (`MaxStopPoints 0`). Metterlo a 250 pt sarebbe una
nostra modifica e va dichiarata: **non lo mettiamo**. Il criterio $500 si giudica sul report
così com'è.

**Costi.** $7,50 per lato nel campo commissione, slippage 0.

**Attesa dichiarata:** l'autore dichiara WR 82% e avg $300 fuori campione. Noi ci aspettiamo
t IS fra 0,5 e 1,5. Il gate toglie trade a una base che aveva t 0,87, e un filtro migliora un
t solo se toglie più perdite che guadagni.

## Setup del chart (fase 1)

@NQ **1 min**, sessione **Globex 24h** (17:00–16:00 CT), timezone Exchange, volume da trade,
Bar Magnifier off (1 min è già la risoluzione minima), IOG off, Max bars back ≥ 42.

## Pre-registrazione
- registrata: 811259f   # blocco aggiunto il 02/11/2026 per /lab; i valori sono quelli scritti sopra il 29/10
- via: A|B          # via A; se non passa, via B
- k-varianti: 4     # base, filtrata, StopMode 2, v4 con ADX
- attesa: t IS fra 0,5 e 1,5; il gate toglie trade a una base che aveva t 0,87
- kill: fase 2 via A t < 2 o WR < 55% o R:R fuori 0,5-1, e via B t <= 1,03 o trade peggiore > $500 per micro; fase 3 t < 1,3 (via A) o gate marginale (via B); verdetto OOS asimmetrico, forward pulito dal 3/7/2026
- costi: $7,50 per lato nel campo commissione (slippage incluso), slippage 0
