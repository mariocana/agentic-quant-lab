# Scaletta

Ordine deliberato: prima il validatore, gli agenti per ultimi. La fabbrica senza un
cancello che sa dire "non funziona" produce falsi positivi più in fretta.

## Adesso

- [x] **1. Test sui confini di import.** `trading-desk/` non importa da `alphaquant`,
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
      `trading-desk/var/` prima di simulare qualunque cosa nuova.
      - [x] 7.1 costi reali dal journal (`alphaquant.calibration.desk_fills`): 126 fill,
            maker 1,5 bps, taker 4,5 bps + slippage 7,3 bps medio. Fatto il 09/11.
      - [x] 7.2 profilo di venue `hyperliquid` in `config/costs.yaml`, fee verificate,
            slippage no (misurato su testnet).
      - [x] 7.3 `alphaquant.engine.desk_replay`: il `run_cycle` del desk sul passato,
            con orologio spostato (time_machine) e file in una cartella temporanea.
            Funding regolato fra i cicli, delisting chiusi all'ultimo prezzo. Fatto il 09/11.
      - [ ] 7.4 decisioni live contro decisioni rigiocate (`scripts/compare_decisions.py`):
            108 set di target, dal journal locale e dal desk su Railway. Strumento pronto
            il 09/11; il verdetto aspetta la fine del backfill (oggi 653 differenze su
            1.120 sono "no_bars"). Il P&L non si confronta: il testnet riempiva a prezzi
            fino al 2,6% lontani da mainnet.
      - [x] 7.5 `engine/desk_trades.to_simresult`: i fill diventano trade da piatto a
            piatto, con fee e funding della posizione; la somma dei P&L netti è uguale
            alla variazione di equity. Il replay registra le versioni Delta lette. Fatto
            il 09/11.
- [ ] **8. Gate di portafoglio, registro delle prove, holdout bloccato dal codice.**
      - [x] 8.1 `alphaquant.registry`: append-only con catena di hash, `k` = spec giudicate
            in validation. File: `alpha-quant/registry/trials.jsonl`. Fatto il 09/11.
      - [x] 8.2 holdout chiuso dal codice: `config/splits.yaml` (train 06/2023-03/2025,
            validation 04-12/2025, holdout 2026), `HistoricalMarket` rifiuta le date di
            holdout finché il registro non lo apre, una volta per spec. Fatto il 09/11.
      - [x] 8.3 gate di portafoglio (`validation/portfolio.py`): giorni, trade, Sharpe
            netto, deflated Sharpe con `k` dal registro, drawdown ≤ 25%, fee ≤ 50%
            dell'edge lordo; holdout contro lo Sharpe di validation della stessa spec.
            `alphaquant.evaluate`: spec → replay → gate → registro in una chiamata. Fatto il 09/11.
      - [ ] 8.4 primo verdetto su `reversal_v1` (aspetta il backfill completo). Nota nel
            registro: il suo holdout 2026 è stato visto in aggregato il 09/11. ~mezza giornata.
- [x] **9. Registro delle strategie e shadow mode nel desk.** `trading-desk/config/strategies.yaml`
      (al massimo una `active`, `shadow` quante si vuole, classi solo da `desk.signals`);
      ogni shadow gira dopo il ciclo attivo nel suo conto paper `var/shadow/<id>/`, senza
      notifiche e senza via verso l'exchange. Endpoint `/api/strategies`. Fatto il 09/11.
      Manca: il funding nei conti paper (attivo e shadow).
- [x] **10. Agenti.** Pacchetto `factory/` (spec con pagina obbligatoria, controllo
      statico + smoke run, comandi `new/check/freeze/evaluate/holdout/promote/status`) e in
      `.claude/` la skill `/quant-factory` con `factory-researcher`, `factory-critic`
      (due passaggi), `factory-spec-builder`, `factory-coder`. Provato end to end sui dati
      veri con un registro di prova. Il desk ha perso `research/`, `backtest/` e gli schemi
      Thesis/Review. Fatto il 10/11.

## Pulizie

- [ ] `acceptance.py` legge la password da `.env`.
- [ ] `.env.example`: manca `DESK_PASSWORD`, `HL_UNIFIED_COLLATERAL` è doppio.
- [ ] Le 9 posizioni orfane su testnet.
- [ ] I due test `DriftPullback` di alpha-quant: in pensione o con dati sintetici.
- [ ] README alla radice del laboratorio.

## Vincoli di convivenza con multicharts

Le regole stanno in `architettura.md`, sezione "Convivenza con il `/lab` di multicharts":
nomi `factory-*` e `/quant-factory`, agenti e skill solo in `agentic-quant-lab/.claude/`, stato e codice
separati, tabelle ES/NQ di quantlake intatte.

## Decisioni aperte

- Quale Sharpe live basta per mettere soldi propri.
- Un subaccount per strategia, prima della seconda strategia live.
