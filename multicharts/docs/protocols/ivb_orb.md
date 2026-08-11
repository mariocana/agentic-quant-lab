# Protocollo di test — IVB Model 1 (Opening Range Breakout)

EA: `ivb/IvbModel1_EA.mq5`
Tipo: **ORB** — box del range in una finestra oraria, poi breakout con conferma.

> Lezione dal Turtle: **ottimizzare con LOTTI FISSI** (`lotMode = FIXEDLOT`) per
> giudicare l'edge senza la distorsione del compounding. Il rischio % lo si
> applica solo alla fine, sul set scelto.

---

## 1. Simboli e timeframe

L'ORB rende dove c'è una **sessione con apertura netta**. Consigliati (indici):
- **US30 / NAS100 / US500** — TF **M5**
- **GER40 (DAX)** — M5

TF: **M5** (l'EA è progettato per M5).

## 2. La cosa più importante: la finestra del BOX

L'edge dell'ORB è **time-of-day specifico**: il box deve coincidere con una vera
apertura di sessione. Imposta `startBoxHour/Minute` e `endBoxHour/Minute` in
**ora del server** all'equivalente dell'apertura che vuoi tradare:
- indici USA → apertura cash **09:30 New York** (converti al tuo server);
- DAX → apertura **09:00 Francoforte**.

Il box di default (16:30–17:04) è solo un segnaposto: **va allineato**.

## 3. Periodo dati (IS / OOS)

- Usa lo storico M5 disponibile per l'indice (spesso dal ~2018/2019 in poi).
- Es.: **2019 → oggi** con **Forward = 1/3** (split automatico IS/OOS).
- Modello: **1 minuto OHLC** (l'EA usa i tick per il breakout, ma OHLC va bene per
  l'ottimizzazione; real-tick solo per la validazione finale).

## 4. Costi (obbligatori)

- **Spread reale + commissione** dell'indice del tuo broker. Su M5 con molti trade
  incidono parecchio: includerli sempre.

## 5. Ottimizzazione

Fissi: `lotMode = FIXEDLOT`, `lotSize` costante (es. 1.0), `exitModeSel` a scelta
(inizia con `CLOSE_ALL_AT` a fine sessione).

| Input | Valori da provare | Note |
|---|---|---|
| entryMode | MARKET / STOP / LIMIT / MARKET_AND_LIMIT | categorico: prova i 4 |
| tpTypeSel | FIBO100 / FIBO200 / R1R1 / R1R2 / R1R3 | categorico |
| endBoxMinute (durata box) | es. 09:45 / 10:00 / 10:15 (fine box) | lunghezza del range |
| closeHour | 16 / 18 / 20 / 22 | ora di chiusura intraday |

Criterio: **Custom max** (l'`OnTester` ora c'è nell'EA).
Algoritmo: **genetico** se lo spazio è grande.

## 6. Soglie di accettazione (in Out-of-Sample)

- **Profit Factor** ≥ 1.2–1.3
- **Max Drawdown** ≤ ~25%
- **# trade** ≥ 100 (IS)
- **Forward che tiene** (non deve crollare rispetto all'IS) — è il vero test
- Curva equity (a lotti fissi) ~**lineare**, non tutta concentrata nell'IS

## 7. Note specifiche IVB

- L'ingresso ha una **candela di conferma** dopo il breakout del box → filtra i falsi
  breakout ma ritarda l'entrata.
- `entryMode = STOP` entra sul massimo/minimo della candela di conferma;
  `LIMIT` sul ritorno; `MARKET` subito. Sono comportamenti molto diversi: testali.
- TP `FIBO100/200` sono estensioni del box; `R1R2/R1R3` sono multipli del rischio.
- Verifica che il box **non sia vuoto** (se la finestra non contiene barre M5, nessun
  trade): controlla l'allineamento orario col Diario.

---

## 8. Prossimo passo

1. **Ricompila** l'IVB (ora ha `OnTester`).
2. Scegli l'indice (es. **US30 M5**), allinea il **box all'apertura USA**, lotti fissi,
   costi reali, forward 1/3.
3. Ottimizza `entryMode` + `tpTypeSel` (giro veloce), poi affina durata box / closeHour.
4. Mandami i **top set** (con Profit/PF/DD%/#trade IS e forward) e l'export, come per
   il Turtle, e li analizziamo.

> In parallelo puoi far girare anche **MacdReversion_EA** (mean-reversion) sullo stesso
> indice: se uno è breakout e l'altro reversione e sono entrambi decenti, insieme
> diversificano bene.
