# SPEC — VaultBreak v8 del corso, NQ (Stage 0, 29/10/2026)

**Perché esiste.** Il 29/10 abbiamo confrontato i codici del corso
(`education/protocollo/9.TheBridge/STRATEGIES/PROP FIRM NATIVE LOW RR/VaultBreak.txt`) con i
nostri. Lo scheletro è lo stesso di `SPEC.md`: noise boundary, VWAP, solo long. Il chart e
tutti i parametri sono diversi. Il nostro cimitero (base OOS t −0,03, `MaxTrades1` OOS t 0,23)
vale per la nostra versione, non per la v8. Quella che l'autore usa nel trittico delle Live 4
e 5 non l'abbiamo mai testata.

Per la regola scritta in `SPEC.md` («se mai si riaprisse, è una nuova spec Stage 0, non una
variante») si riparte da qui.

## Codice

`VaultBreak.txt`, lo stesso file, con gli input della v8. La logica coincide riga per riga.
Unica aggiunta: `CarryGuard`, la chiusura di una posizione rimasta aperta a cambio data, che
nella v8 c'è sempre. Nei nostri default è spenta, così i report vecchi restano riproducibili.

| | v8 (questa spec) | nostra base (`SPEC.md`) |
|---|---|---|
| Chart | @NQ **30 min, sessione Globex**, timezone Exchange | 5 min, RTH |
| `NoiseMult` | **0.3** | 0.60 |
| `DailyATRLen` | **15** sessioni | 252 |
| `EarliestEntry` / `LatestEntry` | **1000 / 1400** CT | 845 / 1400 |
| `FlattenTime` | **1430** CT | 1450 |
| `VWAPExitBars` | **7** (3,5 ore) | 2 |
| `StopLossPts` / `TakeProfitPts` | **75 / 40** ($1.500 / $800) | 100 / 50 |
| `CarryGuard` | **1** | 0 |
| `MaxTradesPerDay` | 3 | 3 |

**Sessione Globex:** il reset `Date <> Date[1]` cade a mezzanotte CT. L'«open» è quello della
mezzanotte e il range medio è quello del giorno di calendario, overnight compreso. È la scelta
dell'autore e la teniamo.

`LatestEntry 1400`: nella v8 l'input vale 1500 ma è inerte. Il vincolo vero è
`Time < FlattenTime` (1430), quindi su barre da 30 min l'ultimo ingresso è la barra delle 14:00.

## Ipotesi

Uguale a `SPEC.md`: chiudere sopra open + una frazione del range medio, con il VWAP a favore,
è un movimento direzionale. Cambia la scala: soglia bassa (0,3) su un range a 15 giorni,
quindi più ingressi e più presto rispetto alla nostra base.

## Contaminazione: il punto delicato

1. **I parametri li ha scelti l'autore, non sappiamo su che periodo.** Una finestra di 15
   sessioni e una soglia di 0,3 hanno l'aria di una taratura recente. L'OOS 2025–26 **va
   considerato visto**.
2. **È la terza versione di VaultBreak su NQ nello stesso OOS** (base, `MaxTrades1`, v8). La
   v8 era nel repo dal 13/10, prima del nostro OOS del 15/10, quindi non l'abbiamo scelta
   dopo il fallimento. Ma la riapriamo dopo. Vale la regola delle varianti a posteriori con
   **k = 3**.
3. **Fuori campione pulito: dal 13/10/2026**, data in cui il materiale è entrato nel repo.

## Criteri

| fase | criterio | se fallisce |
|---|---|---|
| **1 — meccanica** (100 giorni) | stop a −75 pt e target a +40 pt esatti, ingressi fra 10:00 e 14:00 CT, flat alle 14:30 (o `VB-Carry` solo nei giorni corti), max 3 ingressi al giorno, scaling ×10 esatto | si corregge il codice |
| **2 — IS 2020–2024** | via A: t ≥ 2 · WR ≥ 55% · R:R 0,5–1. Altrimenti via B: **t > 0,85** (k = 3) e trade peggiore ≤ $500 per micro | cimitero |
| **3 — OOS 2025–2026**, una volta | via A: t ≥ 1,3. Via B: gate marginale (`pipeline_semplice.md`) | cimitero, definitivo |

**Verdetto asimmetrico in fase 3.** Un OOS fallito è un fallimento pieno. Un OOS passato non
è una conferma, perché il periodo è contaminato. La strategia entra nel book solo come prova
dal vivo, e conta il forward dal 13/10/2026.

**Trade peggiore.** Lo stop vale $150 per micro (75 pt × $2). Il rischio di superare $500
viene solo da gap fra una barra e l'altra; si controlla in fase 2.

**Costi.** $7,50 per lato nel campo commissione (slippage incluso), slippage a 0, come gli
altri report dal 01/10.

**Attesa dichiarata:** t IS fra 1 e 2,5. Il nostro VaultBreak base faceva 2,40 sull'IS ed è
morto fuori campione: un buon IS qui dice poco, la fase che decide è la 3.

## Setup del chart (fase 1)

@NQ 30 min, **sessione Globex** (template CME 17:00–16:00 CT), timezone Exchange, Bar Magnifier
1 min, IOG off, Max bars back ≥ 100. Lead-in: il chart parte almeno 1 mese prima della
finestra valutata; la finestra si fissa con `TradeStartEL` / `TradeEndEL`.
