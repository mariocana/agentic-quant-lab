# SPEC — Overnight Bias ORB, NQ (Stage 0, 29/10/2026)

**Fonte:** `education/protocollo/9.TheBridge/STRATEGIES/PROP FIRM NATIVE HIGH RR/Overnight Bias ORB.txt`
(OFB_OvernightBiasORB_Signal), unico file della cartella «high RR» del corso.
**Codice:** `OvernightBiasORB.txt`, in MultiCharts `Mario_OvernightBiasORB`. La logica è quella
dell'autore riga per riga. Cambiano solo gli orari di default, in CT invece che in ET, e la
finestra `TradeStartEL` / `TradeEndEL`, che separa il lead-in dal periodo valutato.

## Ipotesi

Dove apre il cash rispetto al range della notte dice chi ha il controllo. Un open nel terzo
alto del range overnight rende probabile la continuazione al rialzo, uno nel terzo basso al
ribasso. Si compra solo il breakout dell'opening range a 15 minuti in quella direzione. Il
movimento deve avere trend (ADX ≥ 20), non deve partire da una barra di esaurimento e la
giornata deve avere un range «normale». Target 3 volte lo stop: pochi trade vinti, ma grandi.

**Perché dovrebbe funzionare:** l'overnight è il posizionamento di chi ha già agito; l'apertura
nella stessa direzione lo conferma. Chi perde: chi fada il breakout d'apertura nei giorni di
trend.

| | |
|---|---|
| Famiglia | breakout del range di apertura · momentum, con filtro di bias |
| Strumento · TF · sessione | @NQ → MNQ · **15 min** · **Globex**, timezone Exchange (CT) |
| Overnight | dalla **mezzanotte CT** (cambio data) alle 08:30. Non dalle 17:00: è la scelta dell'autore |
| Bias | open ≥ 67% del range overnight → solo long; ≤ 33% → solo short; in mezzo niente |
| Opening range | 08:30–08:45 CT. Giorno scartato se il range supera 2 volte la sua media (EMA 20) |
| Entry | prima chiusura oltre l'OR nel verso del bias, 08:45–12:00 CT, ADX(16) ≥ 20, barra ≤ 2,5 volte la media di 20 → next bar at market |
| Stop | 0,30 × ATR giornaliero RTH (15 giorni), dalla close del segnale |
| Target | 3 × stop |
| Altre uscite | flat 14:30 CT |
| Trade/giorno | max 4, una posizione alla volta |

## I numeri dell'autore (header del codice, costi zero, 1 NQ)

| | trade | PF | net | DD |
|---|---|---|---|---|
| IS 2006–2019 | 1.112 | 1,35 | $50.445 | $6.160 |
| OOS 2020 → 08/2026 | 599 | **1,66** | $257.615 | **$20.195** |

- **Avg OOS ~$430 per NQ lordo**, ~$415 dopo $15 di costi: ~$41 per micro.
- **DD OOS $20.195 per NQ = ~$2.020 per micro, l'intero MLL di Lucid.** Fuori dal profilo
  WR 54–72% e R:R 0,5–1 per costruzione: con R:R 3 il WR atteso è intorno al 35%.

## Contaminazione

1. **Il nostro IS 2020–24 e il nostro OOS 2025–26 stanno entrambi nell'OOS dichiarato
   dall'autore.** Se la dichiarazione è vera, i parametri non hanno mai visto i nostri dati e
   tutto il nostro periodo è fuori campione. Ma il file è stato pubblicato **dopo** aver visto
   quell'OOS, con PF 1,66: è un risultato selezionato per la pubblicazione.
2. **Fuori campione pulito: dal 1/9/2026**, il mese dopo la fine del suo OOS.
3. **k = 1**: nessuna nostra variante, si gira solo il default dell'autore.

## Criteri

| fase | criterio | se fallisce |
|---|---|---|
| **1 — meccanica** (100 giorni) | ingressi solo nel verso del bias e fra 08:45 e 12:00 CT; stop = 0,3 × ATR e target = 3 × stop dalla close del segnale (controllo su 5 trade a mano); flat alle 14:30; max 4 ingressi al giorno, mai due posizioni; scaling ×10 esatto | si corregge il codice |
| **2 — IS 2020–2024** | **solo via B** (WR e R:R della via A esclusi per costruzione): **t > 0,5** e trade peggiore ≤ $500 per micro | cimitero |
| **3 — OOS 2025–2026**, una volta | gate marginale contro il book live (`pipeline_semplice.md`) | cimitero, definitivo |

**Verdetto asimmetrico in fase 3**, come per le altre del corso: fallire conta pieno; passare
vale come ingresso in prova dal vivo, con il forward dal 1/9/2026.

**Trade peggiore.** Con l'ATR giornaliero RTH di NQ fra 250 e 450 pt, lo stop sta fra 75 e
135 pt: $150–270 per micro. Sotto $500 salvo gap o giorni estremi; si controlla in fase 2.

**Il rischio vero è il DD, non il trade.** Il gate marginale lo misura direttamente: a 1 micro
un DD come quello dell'autore manda il book contro l'MLL. Un'attesa di Δ contiguo negativo è
ragionevole.

**Costi.** $7,50 per lato nel campo commissione, slippage 0. Lo stop è un ordine stop: in live
va emulato come DPB (`go_live.md`).

**Attesa dichiarata:** se i numeri dell'autore valgono sul nostro IS, t ≥ 3. Visto che sono
selezionati per la pubblicazione, ci aspettiamo **t fra 1 e 2,5**.

## Setup del chart (fase 1)

@NQ **15 min**, sessione **Globex** (CME 17:00–16:00 CT), timezone Exchange, Bar Magnifier
1 min, IOG off, Max bars back 250. Lead-in: il chart parte **2 mesi** prima della finestra
valutata (servono 15 giorni di ATR e 20 di media dell'OR). Finestra con `TradeStartEL` /
`TradeEndEL`: IS `1200101`–`1241231`.
