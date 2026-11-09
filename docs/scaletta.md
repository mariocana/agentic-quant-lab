# Scaletta

Ordine deliberato: prima il validatore, gli agenti per ultimi. La fabbrica senza un
cancello che sa dire "non funziona" produce falsi positivi più in fretta.

## Adesso

- [x] **1. Test sui confini di import.** `ai-desk/` non importa da `alphaquant`,
      `quantlake`, `factory` né da SDK LLM. Fatto (`f66fdc8`).
- [x] **2. Alert Telegram.** Bot da @BotFather, `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID`
      su Railway. Fatto il 09/11.
- [ ] **3. Backup della lake.** `quantlake/data/` (2,6 GB) esiste in una copia sola. ~30 min.
      Rimandato il 09/11: serve un disco esterno, e il Mac ha 12 GB liberi (98% pieno).
- [x] **4. Registro del mercato nel desk.** Ogni ora `metaAndAssetCtxs` grezzo del dex
      principale e di tutti i dex HIP-3, in `var/market/AAAA-MM-GG.jsonl.gz` (~32 KB a
      campione, ~280 MB l'anno). Endpoint `/api/market` e `/api/market/{giorno}`. Fatto il
      09/11; parte al primo deploy.
- [x] **5. Ingest in `quantlake/bronze`.** `applications/historical/hyperliquid_market.py`
      copia i file giornalieri del desk in `bronze/_raw/hyperliquid_market/` (archivio
      byte per byte) e li fonde in `bronze/hyperliquid_market`, una riga per
      (campione, dex, asset), partizionata per dex. Fatto il 09/11. Si lancia a mano:
      il desk tiene i file sul volume, quindi lanciarlo una volta a settimana non perde
      niente.

## Dopo (4-8 settimane)

- [ ] **6. Connettore Hyperliquid in quantlake.**
      - [x] barre 1d (tutta la storia) e 1h (solo le ultime ~5000 per perp: aggiornare
            almeno ogni qualche mese), funding orario dal 12/05/2023. Fatto il 09/11.
      - [x] `reference/hyperliquid_listings` e `universe_on(giorno)`: l'universo
            punto-nel-tempo, delistati compresi.
      - [ ] backfill completo dei 561 perp (~10 ore, in corso dal 09/11, riprende da solo).
      - [x] `underlying_market_open` in silver (`silver/hyperliquid_ohlcv_1h` e `_1d`):
            ogni perp associato al calendario del sottostante in
            `reference/hyperliquid_underlying.py`. Fatto il 09/11. Da rivedere: le voci in
            `NEEDS_REVIEW` (21) e i 4 perp non identificati (`UNIDENTIFIED`).
      - L'open interest storico non esiste nell'API: c'è solo dal registro del desk (punto 4).
- [ ] **7. Simulatore livello 2 in alpha-quant**, calibrato contro i fill veri di
      `ai-desk/var/` prima di simulare qualunque cosa nuova. ~3-5 giorni.
- [ ] **8. Gate di portafoglio, registro delle prove, holdout bloccato dal codice.**
      Il loader rifiuta le date di holdout finché la spec non è registrata con il suo
      hash. ~3 giorni. Qui arriva il primo verdetto su `reversal_v1`.
- [ ] **9. Registro delle strategie e shadow mode per strategia nel desk.** ~1-2 giorni.
- [ ] **10. Agenti, in quest'ordine:**
      1. `SourceRef.page` obbligatorio: ogni numero preso da un paper porta la pagina. ~10 min.
      2. coder (il più verificabile)
      3. spec builder
      4. ricercatore + critico al **primo passaggio**, sull'ipotesi, prima del codice
      5. critico al secondo passaggio, sul risultato: dossier append-only, nessun veto

## Pulizie

- [ ] `acceptance.py` legge la password da `.env`.
- [ ] `.env.example`: manca `DESK_PASSWORD`, `HL_UNIFIED_COLLATERAL` è doppio.
- [ ] Le 9 posizioni orfane su testnet.
- [ ] I due test `DriftPullback` di alpha-quant: in pensione o con dati sintetici.
- [ ] README alla radice del laboratorio.

## Vincoli di convivenza con multicharts

Le regole stanno in `architettura.md`, sezione "Convivenza con il `/lab` di multicharts":
nomi `factory-*`, agenti e skill solo in `agentic-quant-lab/.claude/`, stato e codice
separati, tabelle ES/NQ di quantlake intatte.

## Decisioni aperte

- Quale Sharpe live basta per mettere soldi propri.
- Un subaccount per strategia, prima della seconda strategia live.
- Rinominare `ai-desk/` (proposta: `trading-desk/`) e cambiare Root Directory e
  Watch Paths su Railway.
