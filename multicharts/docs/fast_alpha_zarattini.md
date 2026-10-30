# «Fast Alpha»: il paper da cui nasce DriftPullback, e cosa dice davvero

Live 002, 08:51: *«Drift pullback comes from an academic paper, **Fast Alpha from Zarattini
and Pagani**. Intraday drift on index futures is a documented effect.»*

Trovato: **Carlo Zarattini e Alberto Pagani, *Improving Performance with Fast Alphas: A
Tactical Overlay for Intraday Trend Trading*, Concretum Group, febbraio 2026.**

## Tre cose che il paper dice e che non sapevamo

### 1. Non e' sui futures su indice. E' su **SPY**, 5 minuti, 2007-2026

La frase *«intraday drift on index futures is a documented effect»* e' **l'estensione del
corso, non la tesi del paper**. Nessuno ha mai stabilito che l'effetto sia generale sui
futures su indice.

> **E' coerente con quello che abbiamo misurato noi**: l'edge di DriftPullback c'e' su NQ
> (+2,52 pp di eccesso) e **non** su YM (+0,07). Non era un porting fallito: era un effetto
> mai dimostrato generale.

### 2. Il segnale di mean reversion a breve e' **NON profittevole da solo**

Il paper misura un segnale di reversione a orizzonte corto: **CAGR lordo ~32% e Sharpe
sopra 2 senza frizioni**, ma **non profittevole dopo i costi di transazione**.

> **Spiega le nostre due morti.** VWAP Fade: eccesso −0,62 pp su 7.516 setup. Gap/overnight
> fade: +0,68 pp su 1.175. Non e' sfortuna nostra ne' scelta sbagliata dello strumento: e'
> **un risultato documentato** che stavamo ri-scoprendo a spese nostre.

### 3. Lo stesso segnale **funziona come overlay di esecuzione** su una strategia di trend

Applicato non come strategia ma come **sovrastruttura di timing** su un intraday trend
following: **+200 punti base all'anno**, Sharpe da **0,87 a 0,99**.

> **E questo spiega perche' DriftPullback funziona.** Non e' momentum, e non e' mean
> reversion: e' **momentum per la direzione, reversione a breve per il timing d'ingresso**.
> Il drift decide da che parte stare, il pullback decide quando entrare. E' esattamente
> l'overlay del paper, implementato come strategia unica.

## Cosa cambia per la seconda gamba

**La direzione che stavamo seguendo era sbagliata in partenza.** Cercavamo una strategia
**mean reverting autonoma** per complementare il momentum. Il paper dice che quella cosa
**non e' profittevole dopo i costi**, e noi l'abbiamo verificato due volte.

**La seconda gamba non deve essere mean reverting. Deve avere la stessa struttura di
DriftPullback — direzione da un segnale di trend, timing da una reversione a breve — ma con
un SEGNALE DI DIREZIONE DIVERSO.**

Candidati di direzione, da misurare non da indovinare:

- il drift su un **orizzonte diverso** (non un'ora: dieci minuti, o mezza giornata);
- il drift su **data2 piu' lento** (giornaliero invece che 15 minuti);
- un segnale di trend **non basato sul prezzo**: volume, delta, apertura relativa.

E la premessa — la persistenza del drift — e' quella che `DriftPersistence_Study` misura.
**Il paper rende quel run piu' importante, non meno**: se la persistenza su NQ e' alta e
altrove no, abbiamo sia il perche' sia il dove.

## Fonti

- [QuanTip: Improving Performance with Fast Alphas — Concretum Group](https://concretumgroup.com/quantip-improving-performance-with-fast-alphas-a-tactical-overlay-for-intraday-trend-trading/)
- [PDF del paper](https://concretumgroup.com/wp-content/uploads/2026/02/Improving-Performance-with-Fast-Alphas-A-Tactical-Overlay-for-Intraday-Trend-Trading.pdf)
- [Concretum Research — elenco paper](https://concretumgroup.com/papers/)
