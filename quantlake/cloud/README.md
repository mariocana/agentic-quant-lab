# Job cloud: foto della catena SPX su Railway + R2

La CBOE mostra solo la catena opzioni del momento: una foto non scattata è persa. Questo
job le scatta anche a Mac spento e le salva su Cloudflare R2; il Mac le importa nel lake
quando crei la scheda di sessione (o con `applications/cloud_sync.py`).

```
Railway (cron ogni 5 min, in poche ore UTC)          Mac
  cloud/chain_job.py                                  applications/cloud_sync.py
    slot dovuto? (02:20 / 09:20 / 10:00 / 15:40 ET)     legge i parquet nuovi da R2
    → catena SPX dalla CBOE                             → bronze/cboe_option_chain
    → R2: cboe_option_chain/SPX/<data>/<slot>_….parquet → gold/em_0dte
```

Il cloud scrive solo file parquet; le tabelle Delta le scrive solo il Mac.

| Slot (ora di New York) | Di solito a Roma | A cosa serve |
|---|---|---|
| 02:20 | 08:20 | prima di Londra |
| 09:20 | 15:20 | prima dell'apertura cash: EM 0DTE all'apertura |
| 10:00 | 16:00 | dopo l'opening range |
| 15:40 | 21:40 | prima della chiusura (MOC) |

Il job ragiona sull'orologio di New York, quindi i cambi di ora legale non richiedono
modifiche. Il cron di Railway gira ogni 5 minuti solo nelle ore UTC che contengono gli slot
(`python/quantlake/railway.json`); fuori slot il job esce subito.

## 1. Cloudflare R2 (una volta)

1. Dashboard Cloudflare → **R2 Object Storage**. Se è la prima volta va attivato: Cloudflare
   chiede un metodo di pagamento anche per il piano gratuito (10 GB inclusi; qui serve
   meno di 1 GB l'anno).
2. **Create bucket** → nome `quantlake`, località automatica.
3. R2 → **Manage API tokens** → **Create API token**:
   - permessi **Object Read & Write**
   - **Apply to specific buckets only** → `quantlake`
4. Annota i quattro valori: **Account ID** (nella pagina R2), **Access Key ID**, **Secret
   Access Key** (si vede una volta sola), nome del bucket.

## 2. Prova dal Mac (2 minuti)

Metti i quattro valori in `python/quantlake/.env` (è in `.gitignore`):

```
R2_ENDPOINT=https://<account id>.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET=quantlake
```

(`R2_ENDPOINT` è l'URL "S3 API" che Cloudflare mostra con le chiavi; in alternativa
`R2_ACCOUNT_ID` con il solo account id.) Il token "Account API token" non serve: non
metterlo nel `.env`.

Poi, da `python/quantlake`:

```bash
PYTHONPATH=src .venv/bin/python cloud/chain_job.py --force
```

```bash
.venv/bin/python applications/cloud_sync.py
```

Il primo scrive una foto `manual_….parquet` su R2, il secondo la importa. Se funzionano, le
chiavi e il bucket sono a posto.

## 3. Railway (una volta)

1. **New Project → Deploy from GitHub repo** → `mariocana/my-codes` (autorizza l'app GitHub
   di Railway sul repository privato).
2. Nel servizio → **Settings**:
   - **Root Directory**: `python/quantlake`
   - il file di configurazione è `python/quantlake/railway.json`: Railway lo legge da solo
     nella Root Directory (se nel campo *Config file* c'è un altro percorso, svuotalo o metti
     `python/quantlake/railway.json`). Senza, Railway usa Railpack e fallisce con "no start
     command"
   - controlla che compaiano **Builder: Dockerfile** con `cloud/Dockerfile` e **Cron
     Schedule** `*/5 6,7,13,14,15,19,20 * * 1-5`
3. **Variables**: le stesse quattro `R2_*` del `.env`.
4. Deploy. Il servizio non resta acceso: parte a ogni tick del cron e si spegne. Il costo
   sta nei pochi centesimi al mese del piano Hobby.

**Verifica**: alla prima ora di slot (in un giorno feriale, alle 08:20 di Roma) i log del
servizio devono mostrare `slot 0220 ET: … options … -> quantlake/cboe_option_chain/…`. Gli
altri tick scrivono `no slot due`, ed è normale.

Se invece compare un errore HTTP 403 dalla CBOE, la CBOE blocca gli IP del data center:
il piano non funziona da Railway e conviene saperlo subito.

Per una foto immediata da Railway (per esempio dopo una modifica): variabile
`CHAIN_FORCE=1`, aspetta un tick dentro le ore del cron, poi toglila.

## 4. Dopo

- `contesto.py` (cioè `nuova_sessione.sh`) importa da solo le foto nuove: non devi fare
  altro.
- Il job launchd `com.mario.quantlake.chain` sul Mac non serve più. Per toglierlo:

```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.mario.quantlake.chain.plist
```
