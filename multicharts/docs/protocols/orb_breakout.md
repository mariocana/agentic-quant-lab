# Protocollo di test — ORB Breakout (base model)

EA: `orb/OrbBreakout_EA.mq5`
Fondamento: *Market Intraday Momentum* (JFE 2018). È il base model validato nel
video (Fabio Valentini / analisi Monti): range dei primi 30 min NY, breakout su
chiusura, stop all'estremo opposto del range, target 1R, flat a fine giornata.

> Differenza con l'IVB: l'IVB entra sulla **2ª candela** (conferma) con stop stretto;
> qui si entra sulla **1ª candela che chiude oltre il range**, stop al **lato opposto
> del range** (R = altezza del range). Sono due varianti: testiamole entrambe.

---

## 1. Strumento e timeframe
- **NAS100 / US100 (o NQ)** — **M5** (lo strumento e il TF del video).
- In secondo piano: US500, US30.

## 2. Config della sessione (ORA DEL SERVER)
Allinea gli orari all'apertura di New York:
- `InpRangeStartHour/Minute` = **09:30 NY** convertito al tuo server (guarda dove cade
  l'apertura cash USA sul tuo broker; spesso 15:30 o 16:30 server).
- `InpRangeDurMin = 30`.
- `InpTradeEndHour/Minute` = **14:00 NY** convertito (flat + fine ingressi).
- `InpAllowLong = true`, `InpAllowShort = false` (long only, come il video).
- `InpTP_RR = 1.0` (target 1R).

Verifica nel Diario che il range NON sia vuoto (orari allineati).

## 3. L'esperimento chiave: la SIZING
Testa lo **stesso set** con due modalità e confronta il **return/drawdown**:

| Modalità | Come | Attesa |
|---|---|---|
| `FIXED_LOTS` | `InpFixedLots = 1` | baseline, giudica l'edge puro |
| `FIXED_RISK_USD` | rischio $ fisso per trade | **return/DD migliore** (vol targeting) |

Nota: `FIXED_RISK_USD` = **rischio $ costante, NON composto** → niente distorsione da
compounding (la lezione del Turtle). Tara `InpRiskUSD` per avere ~4-6 contratti medi;
`InpMaxLots` come tetto di sicurezza. Evita `PERCENT_RISK` in valutazione (composta).

## 4. Periodo / costi
- **IS/OOS**: usa lo storico M5 disponibile (spesso dal ~2019); es. 2019→oggi con
  **Forward 1/3**. Se puoi, prova anche un periodo più lungo (l'edge è **recente**).
- Modello **1 minuto OHLC**; **spread + commissioni reali** (indice → incidono).

## 5. Test dello SPLIT-SAMPLE per ogni filtro (metodo del video)
Prima di aggiungere QUALSIASI filtro (conferma, trend, ecc.):
1. dividi il periodo in **due metà**;
2. misura la performance **con** e **senza** il filtro in **entrambe** le metà;
3. il filtro è reale **solo se migliora in TUTTE E DUE**. Se aiuta in una sola →
   è coincidenza (come il delta): **scartalo**.

## 6. Soglie di accettazione (OOS)
- **Return/Drawdown** il più alto possibile (metrica principale).
- Profit Factor ≥ 1.2–1.3 ; Max DD ≤ ~25% ; #trade ≥ 100 (IS) ; forward che tiene.

---

## 7. Passi
1. Compila `OrbBreakout_EA`.
2. **NAS100 M5**, box allineato all'apertura NY, flat 14:00 NY, long only, 1R.
3. Gira `FIXED_LOTS` (baseline) → annota return/DD.
4. Gira `FIXED_RISK_USD` (stesso set) → confronta return/DD (atteso +).
5. Mandami i due report (o gli export) e li confrontiamo, come per il Turtle.

## 8. Cautela (dal video)
- L'edge è **concentrato negli ultimi ~5 anni** (post-2019 NASDAQ molto trend). I regimi
  cambiano: non dare per scontato che i prossimi 5 anni somiglino agli ultimi 5.
- Long only in un mercato mediamente rialzista: parte del rendimento può essere "costo di
  essere long". (Nel video, filtrare per trend up peggiorava → segno di edge intraday reale.)
