# SPEC — Counter Trend di Unger su 6B (Stage 0)

**Ipotesi**: nella mattina di Londra, un eccesso oltre le bande di Bollinger contro la
direzione del giorno prima rientra. Se ieri GBP ha chiuso in rialzo e stamattina il prezzo
scende sotto la banda inferiore e poi ci rientra, si compra; specularmente short.
**Perché**: all'apertura di Londra gli ordini accumulati in Asia producono spinte che spesso
sono rumore di liquidità, non informazione; quando vanno contro il movimento del giorno
prima vengono riassorbite. Chi perde: chi insegue il primo movimento della sessione europea.
**Fonte**: Andrea Unger, *Trading System Supremacy*, modulo 5. Codice `DevelopRev` nel video
5x01 (compilato il 21/01/2016), parametri finali nel 5x02: **`DevelopRev(14, 15, 40, 40, 300,
8, 2359, 0, 0.01, 0, 20, 2)`**, GBPUSD forex 30 min, dati TradeStation. Risultato mostrato,
2008 → gennaio 2016 su 100.000 GBP: **net $157.956, PF 1,74, max DD $11.708, commissioni e
slippage $0** (riga "Commission Paid $0,00, Slippage Paid $0,00" del report).
**Ruolo**: il secondo counter trend della pipeline, e il primo su una **valuta**.

| | |
|---|---|
| Famiglia | counter trend / ritorno dentro le bande, long e short |
| Strumento · TF | **6B** (@BP, CME British Pound, 62.500 GBP, $6,25 a pip) · **30 min** · Globex 17:00–16:00 CT, chart CT |
| Bande | Bollinger sul close, 20 periodi, 2 deviazioni |
| Finestra | dalla barra delle **02:00 CT** (= 03:00 New York, mattina di Londra) per le prime 8 barre; domenica esclusa |
| Long | close che incrocia al rialzo la banda inferiore, **ieri chiusura in rialzo** (pattern 14), **ieri non outside bar** (no 40) |
| Short | close che incrocia al ribasso la banda superiore, **ieri chiusura in ribasso** (15), no 40 |
| Stop / target | **100 pip = $625 a contratto** / nessuno |
| Uscita a tempo | **nessuna** (variante A): esce a stop o per inversione su un segnale opposto |

**Fuso orario.** Il grafico di Unger è in ora di New York: la sessione della domenica sul suo
grafico parte alle 17:00 e dura poche ore, che è l'apertura del forex alle 17:00 ET. Le sue
03:00 sono quindi 03:00 ET = **02:00 CT** sul chart di 6B.

**IS**: 2020‑01‑01 → 2024‑12‑31 · **OOS**: 2025‑01‑01 → oggi. Parametri **congelati** a quelli
del video; tutto dopo gennaio 2016 è fuori campione per l'autore.

## Il conto: per LucidFlex 50k la risposta è già nota (causa B)

Lucid non ha micro forex: l'unità minima è un 6B intero. Con i numeri di Unger, prima di
qualsiasi run:
- **peggior trade**: lo stop vale $625 a contratto, più costi e slittamento, contro la soglia
  di $500 (25% dell'MLL). **Fallisce per costruzione.**
- **drawdown**: il suo max DD di $11.708 su 100.000 GBP vale **~$7.300 su un 6B** (× 0,625),
  contro $1.000 di soglia e $2.000 di MLL.

Quindi su LucidFlex 50k la strategia **non entra** anche se l'edge esistesse: sarebbe causa
B. Lo Stage 2 serve a misurare **se l'edge esiste**, per archiviarla con il numero giusto per
un conto più grande o per capitale proprio (decisione dell'utente, 18/10/2026).

## Varianti pre‑registrate

| variante | `FlatEOD` | ruolo |
|---|---|---|
| **A** (originale) | 0 | fedele a Unger: la misura dell'edge |
| **B** | 1 | flat a fine sessione (16:00 CT): l'edge resta se si toglie la posizione overnight? |

## Criteri dello Stage 2 (edge, non conto)

Sul run A, costi veri:
- avg trade netto > 0 con **t ≥ 2**;
- almeno 3 anni su 5 positivi, nessun anno oltre il 50% del profitto;
- confronto con Unger: PF dello stesso ordine (1,3+) **dopo i costi**, che lui non aveva.

Se A fallisce: causa A, cimitero. Se A passa: archiviata come "edge presente, causa B su
LucidFlex 50k", con il DD per contratto misurato.

**Costi**: `8.75$ per Contract` per lato ($2,50 + 1 tick $6,25; la commissione Lucid sulle
valute è $2,40), slippage `0 ticks`.

## Note
- **Posizioni overnight e weekend** nella variante A: lo stop a 100 pip non protegge dai gap
  della domenica sera. Il worst day non è limitato; la variante B lo limita a uno stop più
  un'inversione (un solo ingresso per lato nella finestra).
- **`MyEndTime`** è un input del codice di Unger che il codice non usa: tenuto per fedeltà.
- **Spot contro futures**: GBPUSD spot e 6B si muovono insieme, ma 6B ha la sessione CME e
  gli orari di liquidità del futures. Il segnale è sulle stesse ore.
- **Back‑adjustment**: stop in prezzo, quindi in punti: il continuo aggiustato non lo
  distorce. Le bande di Bollinger sono su differenze di prezzo, invarianti a uno spostamento.
