# hyperliquid-bridge

Il connettore verso Hyperliquid: esecuzione, rischio e journal. **Non contiene strategie e
non decide niente.** Il segnale nasce in MultiCharts; questo pacchetto servirà a copiare su un
perp la posizione che MultiCharts vuole, come fa il bridge MT5 sui CFD.

**Stato: fermo, il bridge non c'è ancora.** Qui c'è quello che il bridge userà. Manca il pezzo
che legge lo stato di MultiCharts e lo trasforma in ordini.

Fino al 12/11/2026 era `trading-desk`, un desk autonomo con una strategia sua (`reversal_v1`,
bocciata in validation). Strategie, ciclo giornaliero, shadow mode e time stop sono stati
tolti: restano in git fino al commit `74ae180`.

## Cosa c'è

| modulo | cosa fa |
|---|---|
| `hlbridge/execution/hyperliquid.py` | ordini con un API wallet che non può prelevare; idempotenza per `cloid`; riconciliazione dei fill |
| `hlbridge/execution/ledger.py` | quale posizione è nostra, chi l'ha aperta e quando; una posizione non nostra non si tocca |
| `hlbridge/execution/paper.py` | conto simulato ai prezzi veri, con i costi misurati (maker 1,5 bps, taker 4,5 + 7,3 bps) |
| `hlbridge/risk/` | il motore di rischio (limiti in `config/limits.yaml`), lo stato (perdita del giorno, drawdown, halt) e il kill switch |
| `hlbridge/data/hl_market.py` | prezzi, funding, book e stato del conto, in sola lettura |
| `hlbridge/data/market_record.py` | ogni ora lo stato grezzo del mercato in `var/market/`, per quantlake: open interest e listini non si riscaricano |
| `hlbridge/journal/`, `hlbridge/pm/` | journal append-only e avvisi Telegram |
| `hlbridge/ui/` | pagina di controllo: conto, posizioni, limiti, kill switch, chiusura di tutto |

## Cosa manca per il bridge

Dall'[audit del 12/11](../docs/audit_2026-11-12.md), prima di mandare un ordine vero:

1. **Il lettore dello stato di MultiCharts**: il file `mario_stato_<STRAT>.csv` del bridge a
   stato (`multicharts/bridge/SPEC.md`), letto ogni secondo, con un ordine solo quando la
   posizione voluta cambia.
2. **Lo stop d'emergenza sull'exchange.** Oggi `_place_stop` parte solo se l'ordine viene
   eseguito subito; un ordine post-only non lo è mai, e sul testnet 44 posizioni su 44 sono
   rimaste senza stop.
3. **Il rischio fra un ordine e l'altro.** `RiskState.observe` va chiamato sullo snapshot
   periodico, con l'inizio giornata ancorato alla mezzanotte UTC.
4. **Limiti per strategia.** Il tetto del 5% dell'equity per asset è nato per un book di molti
   nomi: una posizione sola su un perp ci sbatte subito.
5. **Un subaccount per strategia**, e un allarme quando il bridge non riesce a seguire MultiCharts.

## Uso

```bash
uv venv --python 3.12 .venv && uv pip install -p .venv/bin/python -e ".[dev]"
.venv/bin/python -m pytest -q
.venv/bin/hlbridge status          # conto paper, prezzi veri
.venv/bin/hlbridge ui              # pagina di controllo su 127.0.0.1:8765
.venv/bin/hlbridge kill            # kill switch: nessun rischio nuovo, chiudere resta permesso
```

`.env` da `.env.example`. La chiave è quella dell'API wallet, mai quella del conto. `HL_TESTNET=1`
è il default. Le variabili della pagina hanno ancora il prefisso `DESK_` (`DESK_PASSWORD`,
`DESK_MODE`, `DESK_SNAPSHOT_MINUTES`, `DESK_MARKET_MINUTES`): non le ho rinominate per non
rompere la configurazione che c'è su Railway.

`scripts/testnet_smoke.py` manda un ordine solo su testnet e lo chiude: prova che firma,
ordine, fill e riconciliazione funzionano. `scripts/spot_to_perps.py` sposta USDC da spot a
perp su testnet.

## Deploy

Su Railway il servizio era configurato sulla cartella `trading-desk/`. **Con questo nome nuovo
vanno cambiati a mano, nelle impostazioni del servizio, Root Directory e Watch Paths**
(`hyperliquid-bridge` e `hyperliquid-bridge/**`); il comando d'avvio è `hlbridge ui`
(`railway.json`). Finché non si cambia, il deploy dal ramo con la cartella rinominata fallisce.
`var/` va su un volume: tiene journal, stato del rischio e registro del mercato.
