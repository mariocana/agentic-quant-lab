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
- [ ] **5. Ingest dello snapshot in `quantlake/bronze`.** ~2 ore.

## Dopo (4-8 settimane)

- [ ] **6. Connettore Hyperliquid in quantlake.** Barre, funding, OI, `listed_at`,
      `underlying_market_open` come colonna della barra. ~1-2 giorni.
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
