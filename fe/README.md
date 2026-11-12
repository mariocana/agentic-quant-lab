# fe — la pagina unica del laboratorio

Un server, una pagina, le schede in alto:

| scheda | da dove viene |
|---|---|
| Dati | quantlake: tabelle, grafici, workflow (l'app React in `web/`) |
| Hyperliquid bridge | il connettore su Railway, attraverso `/desk/` |
| COT, Equity | i desk di quantlake (`quantlake/applications/`), montati sotto `/cot` e `/equity` |
| Laboratorio | le idee del desk di ricerca e il loro registro (`lab/`) |

```bash
./start_frontends.sh
```

dalla radice del laboratorio: compila la shell se serve, avvia il server, apre
http://127.0.0.1:8000.

## Come è fatto

- `server.py` prende l'app FastAPI di quantlake (le sue `/api/...` e i desk COT ed
  Equity), aggiunge il proxy del bridge Hyperliquid e la scheda del laboratorio, e serve
  la shell compilata. Gira nell'ambiente poetry di quantlake
  (`poetry install --with dashboard,desk`).
- `web/` è la shell React. Chiede a `/api/apps` quali schede esistono e tiene
  montata ogni scheda una volta aperta, così non perde lo stato.
- `lab/index.html` è la scheda del laboratorio: legge
  `ricerca/registro/trials.jsonl` e `ricerca/idee/`, in sola lettura.

## Il bridge Hyperliquid passa dal server, e perché

Il desk sta dietro una password, e un browser non mostra la richiesta di password
dentro un riquadro che viene da un altro sito. Quindi la password la aggiunge il
server, presa da `quantlake/.env` (`DESK_URL`, `DESK_PASSWORD`). Conseguenza: chi
raggiunge questo server comanda il desk come dalla sua pagina (kill switch,
flatten, cambio di modalità). Per questo ascolta solo su 127.0.0.1 e non va mai
esposto.

La pagina del desk calcola il prefisso dal proprio indirizzo, quindi funziona sia
da sola sulla sua porta sia sotto `/desk/`.
