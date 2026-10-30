# NQ First5 — istruzioni Stage 1

Codice: `NQ_First5.txt`. Originali del corso (intatti, come riferimento):
`mc/protocollo/6. Code Templates/1. Strategies/18. NQ_First5_EMA_DayHold_BASE.txt` e
`…_FILTERED.txt`, più le note in `18. NQ_First5_strategy_notes.pdf`.

## Chart
- **@NQ · 5 min · Globex 24h**, timezone **Exchange** (CT). La risoluzione a 5 minuti è
  vincolante: la barra di riferimento è definita lì (su 1 min `0835` sarebbe la quinta
  barra, su 15 min non esiste).
- Max bars back: auto va bene per il base; con i filtri serve storia per l'ADR.
- Costi $2.50/lato + 1 tick. **Bar Magnifier non necessario**: tutti i fill sono a
  chiusura barra.

## Verifica meccanica (Gate 1)
- Un ingresso al giorno, sempre alla barra che chiude alle **08:35**, mai altrove.
- Direzione coerente con EMA(12): con `ShowLog` non previsto, si controlla sul chart
  confrontando close e EMA sulla barra di riferimento.
- Uscita alla prima barra ≥ **15:00**, a chiusura; nelle mezze giornate interviene
  `SetExitOnClose` (annotare quei giorni).
- Con `NumContracts 10` il P&L per trade ×10.
- `UseFilters 1`: i trade iniziano solo dopo **100 sessioni** di warm‑up → per
  confrontare base e filtrata usa **la stessa data di inizio** per entrambe.

## Differenze rispetto ai template del corso
- BASE e FILTERED uniti in un solo signal con `UseFilters` (0/1), così si confrontano
  nello stesso run; logica identica agli originali.
- Flag `AllowLongs`/`AllowShorts`/`UseFilters` numerici 0/1 (ottimizzatore).
- Aggiunto `StopPts` (default **0 = off**, comportamento identico all'originale): è la
  variante prop dello Stage 4, non si accende prima.
