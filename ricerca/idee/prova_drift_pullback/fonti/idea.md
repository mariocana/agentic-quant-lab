> Idea di Mario, come l'aveva scritta prima di qualsiasi misura. Fonte: strategia di un praticante (corso).

# SPEC — DriftPullback v2.1 (Stage 0)

**Ipotesi**: quando il Nasdaq ha già driftato in una direzione durante la seduta, quel
drift tende a continuare; il posto più economico per entrarci non è il breakout ma il
**primo pullback contro** il drift.
**Perché**: letteratura sul momentum intraday dei futures su indice (famiglia "fast
alpha", Zarattini & Pagani). I trend intraday sono alimentati da flussi che non si
esauriscono in una stampata sola — ribilanciamenti sistematici, hedging di book di
opzioni, momentum chaser che arrivano tardi. Un pullback poco profondo dentro un drift
già stabilito è quasi sempre una pausa (presa di profitto, caccia agli stop), non
un'inversione.
**Chi perde**: chi fade la prima discesa e chi insegue tardi pagando lo spread al
momentum. Noi forniamo liquidità di continuazione a un prezzo un po' migliore.
**Fonte**: tutorial completo di Francesco Agnello
(`mc/education/protocollo/11. Strategy Feedbacks/1. DriftPullback_Tutorial_.pdf`, 18 pp.,
riporta ogni blocco del sorgente v2.1) + live 002 del corso. **Il sorgente non è nel
repo**: il codice in `DriftPullback.txt` è una riscrittura dal walkthrough del PDF →
lo Stage 1 è una verifica di *fedeltà*, non solo di meccanica.
**Stato dichiarato dall'autore**: validato, in live su conti funded. Per noi resta un
candidato da rivalidare: i suoi numeri non sono i nostri.

**Ruolo nel basket**: è **l'unica candidata del corso che nasce già col profilo prop**
invece di doverci essere adattata — WR alto, R:R 0.5, flat EOD, e soprattutto un **cap
strutturale di perdita giornaliera** scritto nella strategia (`MaxLossesPerDay 2`).
Porta anche il lato **short**, che oltre a NQ First5 manca al basket.

| | |
|---|---|
| Famiglia | momentum intraday / continuazione del drift, long e short |
| Strumento · TF · sessione | @NQ · **due serie: data1 = 5 min (esecuzione), data2 = 15 min (segnale)** · Globex 24h, chart CT |
| Armamento (15m, solo a fine barra) | close oltre l'ancora **e** ancora inclinata nella stessa direzione **e** drift 1h ≥ ±0.10% |
| Ancora | `AnchorType` 2 = VWAP di sessione (default v2.1) · 0 = SMA(20) — **entrambe validate dall'autore** |
| Trigger (5m) | prima barra contro il drift (rossa se long, verde se short) entro **6** barre 5m dall'armamento → *next bar at market* |
| Exit | bracket fisso: stop **80 pt**, target **40 pt** long / **50 pt** short; flat a 14:55 CT; `SetExitOnClose` |
| Guardrail | max **4** ingressi e max **2** perdite al giorno |
| Trade/giorno | 1–4 |
| Profilo dichiarato | avg $77, WR 65%, t-stat OOS 2.2 |

**IS**: 2020-01-01 → 2024-12-31 · **OOS**: 2025-01-01 → oggi.
Configurazione di riferimento = quella validata: `AnchorType 2`, `ExitMode 0`,
`SizeMode 1`, `BaseCts 1`, `StopSlipTicks 2`, tutti i default di sessione su chart CT.

## Perché il bracket è "al contrario" (ed è il punto)

Stop largo 80 pt, target piccolo 40–50: sembra rovesciato finché non lo si lega al
meccanismo. I pullback dentro un drift si risolvono **poco profondi e in fretta**, quindi
la strategia compra un win rate alto su un tragitto corto e lo paga con stop pieni
occasionali. È il motivo per cui i guardrail giornalieri non sono decorazione: servono a
limitare quanti di quegli stop può consegnare una giornata storta.

**Conti (1 contratto, NQ = $20/pt; ÷10 = equivalente micro MNQ)**

| | NQ mini | MNQ micro |
|---|---|---|
| Stop 80 pt + 2 tick di slippage | $1.610 | $161 |
| Target long 40 pt | $800 | $80 |
| Target short 50 pt | $1.000 | $100 |
| **Worst day** (2 stop) | **$3.220** | **$322** |

Su Apex 50k (daily loss $1.000) il worst day struttrale consente **fino a 3 micro**
(3 × $322 = $966). È il primo caso in cui il numero di contratti massimo non lo decide il
simulatore Monte Carlo ma la strategia stessa — e il simulatore dello Stage 7 non potrà
che confermarlo o abbassarlo.

