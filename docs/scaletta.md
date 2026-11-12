# Scaletta

> **12/11/2026: cambio di rotta.** La fabbrica Hyperliquid è chiusa: `alpha-quant/`,
> `/quant-factory` e gli agenti `factory-*` sono stati tolti (restano in git fino a `7cc21f9`).
> Il laboratorio ora è il desk di ricerca a monte di `/lab` ([desk_ricerca.md](desk_ricerca.md)),
> con multicharts dentro. `trading-desk/` è diventato `hyperliquid-bridge/`: solo il connettore,
> senza strategie, fermo finché il bridge MultiCharts → Hyperliquid non c'è.
> Quello che segue è la storia fino al 10/11: i punti 7, 8 e 10 descrivono codice che non c'è più.
>
> **Adesso:** il giro di prova di `/ricerca` (tre idee morte e DriftPullback), e il backup del lake.

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

- [x] **6. Connettore Hyperliquid in quantlake.**
      - [x] barre 1d (tutta la storia) e 1h (solo le ultime ~5000 per perp: aggiornare
            almeno ogni qualche mese), funding orario dal 12/05/2023. Fatto il 09/11.
      - [x] `reference/hyperliquid_listings` e `universe_on(giorno)`: l'universo
            punto-nel-tempo, delistati compresi.
      - [x] backfill completo dei 561 perp: finito il 10/11, zero errori.
      - [x] `underlying_market_open` in silver (`silver/hyperliquid_ohlcv_1h` e `_1d`):
            ogni perp associato al calendario del sottostante in
            `reference/hyperliquid_underlying.py`. Fatto il 09/11. Da rivedere: le voci in
            `NEEDS_REVIEW` (21) e i 4 perp non identificati (`UNIDENTIFIED`).
      - L'open interest storico non esiste nell'API: c'è solo dal registro del desk (punto 4).
- [x] **7. Simulatore livello 2 in alpha-quant**, calibrato contro i fill veri di
      `trading-desk/var/` prima di simulare qualunque cosa nuova.
      - [x] 7.1 costi reali dal journal (`alphaquant.calibration.desk_fills`): 126 fill,
            maker 1,5 bps, taker 4,5 bps + slippage 7,3 bps medio. Fatto il 09/11.
      - [x] 7.2 profilo di venue `hyperliquid` in `config/costs.yaml`, fee verificate,
            slippage no (misurato su testnet).
      - [x] 7.3 `alphaquant.engine.desk_replay`: il `run_cycle` del desk sul passato,
            con orologio spostato (time_machine) e file in una cartella temporanea.
            Funding regolato fra i cicli, delisting chiusi all'ultimo prezzo. Fatto il 09/11.
      - [x] 7.4 decisioni live contro decisioni rigiocate (`scripts/compare_decisions.py`),
            a backfill completo, 10/11: sui cicli del desk paper alle 00:05 con dati
            completi (31/10-08/11) **9 su 9 identiche**, stessi asset, stessi lati, stessa
            size al centesimo. Le differenze hanno due cause verificate: i cicli di ottobre
            erano su testnet, dove il desk tiene solo i perp quotati lì (21 in meno); il
            09-10/11 la barra del giorno prima non era ancora in quantlake (backfill partito
            il 09 sera). Il P&L non si confronta: il testnet riempiva a prezzi fino al 2,6%
            lontani da mainnet.
      - [x] 7.5 `engine/desk_trades.to_simresult`: i fill diventano trade da piatto a
            piatto, con fee e funding della posizione; la somma dei P&L netti è uguale
            alla variazione di equity. Il replay registra le versioni Delta lette. Fatto
            il 09/11.
- [x] **8. Gate di portafoglio, registro delle prove, holdout bloccato dal codice.**
      - [x] 8.1 `alphaquant.registry`: append-only con catena di hash, `k` = spec giudicate
            in validation. File: `alpha-quant/registry/trials.jsonl`. Fatto il 09/11.
      - [x] 8.2 holdout chiuso dal codice: `config/splits.yaml` (train 06/2023-03/2025,
            validation 04-12/2025, holdout 2026), `HistoricalMarket` rifiuta le date di
            holdout finché il registro non lo apre, una volta per spec. Fatto il 09/11.
      - [x] 8.3 gate di portafoglio (`validation/portfolio.py`): giorni, trade, Sharpe
            netto, deflated Sharpe con `k` dal registro, drawdown ≤ 25%, fee ≤ 50%
            dell'edge lordo; holdout contro lo Sharpe di validation della stessa spec.
            `alphaquant.evaluate`: spec → replay → gate → registro in una chiamata. Fatto il 09/11.
      - [x] 8.4 primo verdetto su `reversal_v1`, 10/11: **FAIL in validation**
            (04-12/2025). Sharpe -2,02, rendimento -17,4%, drawdown 18,1%, deflated
            Sharpe 0,038 con k=1. Perde prima dei costi (P&L lordo -1.739, fee 109,
            funding +105 incassato): non è un problema di costi, il segnale ha il segno
            sbagliato su quel periodo. L'holdout non si spende. k = 1.
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
- [x] I due test `DriftPullback` di alpha-quant: tolti con la metodologia prop, 10/11.
- [ ] README alla radice del laboratorio.

## multicharts

Dal 12/11/2026 sta in `multicharts/`: vedi `architettura.md`, sezione "multicharts dentro il
laboratorio".

## Decisioni aperte

- Quale Sharpe live basta per mettere soldi propri.
- Un subaccount per strategia, prima della seconda strategia live.

## Prossimo sul percorso verso il live

- [ ] Il cancello dallo shadow al live, in codice: giorni minimi di shadow, Sharpe in
      avanti contro quello di validation, decisioni dello shadow uguali a quelle del
      replay sugli stessi giorni. Serve un endpoint del desk che esponga il journal
      dello shadow.
