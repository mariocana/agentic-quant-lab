# ORB Breakout su ES — pre-registrazione (24/10/2026)

**Scritta prima di qualunque run su `@ES` nell'IS.** Stesso codice (`ORB_Breakout.txt`), stessa
logica del Fabio Model, strumento diverso.

## Perché ES, e perché ha senso riprovare

Su NQ l'ORB è morto **due volte, per due ragioni diverse**:

1. **Unità di rischio troppo grande** (1° ottobre): lo stop è tutto il range di apertura, e su
   NQ vale ~$180 per micro. Il drawdown al 95° percentile era **$3.121 per micro** contro $2.000.
2. **Edge che non regge fuori campione** (15 ottobre): con i filtri, IS t 2,74 → OOS t 0,80.

**ES risponde alla prima.** Nello Stage 1 di settembre (64 trade, 2026) la perdita media su ES
era **$923 sul contratto pieno = ~$92 per MES**, dentro la finestra di rischio ammissibile
($60-110 per micro, `prompt_ricerca_strategie.md`). Su NQ era il doppio.

**Alla seconda non risponde.** ES e NQ si muovono insieme (~0,9 intraday): se l'ORB ha perso
l'edge sul Nasdaq nel 2025-26, è probabile che l'abbia perso anche sull'S&P.

## Configurazione: la base, senza i filtri di NQ

| input | valore | perché |
|---|---|---|
| `ORB_Dur_Min` | 30 | il Fabio Model |
| `TP_RR` | 1.0 | idem |
| `AllowLong` / `AllowShort` | 1 / 0 | come su NQ |
| `Trade_End_H` | 14 | flat 14:00 CT |
| `MaxRisk_USD` | **0** | la soglia $3.000 era tarata sui range di NQ |
| `UseDeltaFilter` | **0** | la soglia 200 è in unità di volume di NQ, ES ne fa ~3 volte tanto |
| `UseEntryCutoff` | **0** | il cutoff delle 11 su NQ peggiorava fuori campione |

Nessuno dei filtri si trasferisce senza ritararlo, e ritararlo su ES sarebbe ottimizzare.

## Run e soglie

| | |
|---|---|
| chart | `@ES` 5 min, sessione **RTH CME azionari** come su NQ, timezone Exchange (CT) |
| costi | **$11,25/lato** (MES: $0,50 Lucid + 1 tick $1,25, ×10), Bar Magnifier 1 min |
| IS | `TradeStartEL`/range del grafico **2020-01-01 → 2024-12-31** |
| Gate 2 | **t ≥ 2 · WR ≥ 55% · R:R 0,5-1** (±5%): qui c'è il bracket, quindi vale il profilo prop |
| OOS 2025-26 | **contaminato per correlazione**: l'ORB su NQ ci ha già detto t 0,80. Verdetto **asimmetrico**: se fallisce è morta; se passa è provvisoria, da confermare sul live |

## Cosa ci aspettiamo

**Il riferimento è la base su NQ, non la versione filtrata:** IS 2020-2024 **t 1,39** con
costi di $2,50/lato, quindi più bassi dei nostri. Su ES lo stesso movimento contiene ~4 volte
meno tick, quindi i costi pesano di più.

**Aspettativa: non passa** (t fra 0,5 e 1,5). Passerebbe solo se l'ORB funzionasse meglio
sull'S&P che sul Nasdaq, e niente di quello che abbiamo visto lo suggerisce.

**Cosa ci dà comunque:** la distribuzione del rischio per trade su ES **nell'IS**, non sul
2026. Se il range di ES sta davvero a ~$90 per MES su cinque anni, è un dato che vale per
qualunque strategia ancorata al range di apertura su ES.

## Verdetto Stage 2 (24/10/2026): Gate 2 fallito, causa A

| run | n | avg | t | WR | R:R | |
|---|---|---|---|---|---|---|
| **long (pre-registrato)** | 868 | −$6,08 | **−0,19** | 54,4% | 0,83 | `ORB_ES_S2_IS_long.xlsx` |
| long + short | 1.269 | −$20,90 | −0,73 | 51,5% | 0,89 | fuori pre-registrazione |
| short | 782 | −$60,56 | −1,68 | 46,2% | 1,01 | fuori pre-registrazione |

**Sotto l'aspettativa dichiarata** (t 0,5-1,5). I due run long+short e short non erano
pre-registrati: non cambiano niente perché falliscono anch'essi, e nessuno viene scelto.

**Nemmeno a costi zero.** Il long lordo vale $16,42 a trade ($22,50 di costi a giro), cioè
t ~0,5. Su NQ la base faceva t 1,39: su ES il breakout d'apertura non c'è. Lo short perde
anche lordo (−$38): eredita il rialzo dell'S&P.

**Il dato che resta: il rischio per trade su ES, cinque anni.** Perdite del long, per MES:

| media | mediana | p75 | p90 | p95 | max |
|---|---|---|---|---|---|
| $84 | $67 | $112 | $166 | $198 | $444 |

Per anno la media sta fra $56 (2021) e $131 (2022). Il 74% delle perdite è sotto $110. Quindi
lo Stage 1 sul 2026 ($92) non era un'anomalia: **su ES una strategia ancorata al range di
apertura sta dentro la finestra $60-110 per micro**, salvo negli anni come il 2022.

**Template**: il report finisce alle 16:00, quindi Globex 24h invece di RTH. Non cambia
niente: il codice costruisce il range e chiude per orario (08:30-09:00, uscita 14:00).

OOS 2025-26 su ES non toccato.
