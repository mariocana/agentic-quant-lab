# Quant VWAP (Andrea Burzichelli) — note dalla live

Video: `Lunedì 18⁄05 - Quant VWAP (Andrea Burzichelli).mp4` · trascrizione: `transcript.txt`
(timestamp a inizio riga). Live in cui usa MultiCharts per **quantificare** i concetti
discrezionali sul VWAP che insegna altrove. **Codice non condiviso.**

## Cosa c'è di usabile

**1. La lunghezza del range di apertura.** Ottimizza la durata del range da 5 a 45 minuti
su un breakout semplice: il profit factor sale fino a **30–32 min** (picco 1,48) e poi
cala; chiama lui stesso overfitting il risultato e lo rivalida out‑of‑sample aggiungendo
due anni col Covid, dove regge.
→ Per noi: i 30 minuti dell'ORB non sono nostri, vengono dal Fabio Model. Un'ottimizzazione
indipendente che cade nello stesso punto dice che siamo in un **cluster**, non su un picco
fittato. Nota di robustezza, non un parametro da cambiare.

**2. VWAP ancorato al breakout come ingresso.** Ancora un VWAP al punto di rottura della
prima mezz'ora e aspetta il **ritracciamento** su una banda di deviazione standard,
entrando nella direzione della rottura. Suoi valori: ingresso **1,5 SD** (si corregge in
diretta: prima diceva 1–2), stop **2× ATR**. Drift positivo anche senza filtri.
→ Per noi: variante d'ingresso pre‑registrata per l'ORB (vedi `ORB_Breakout/SPEC.md`).
Parente del nostro VWAP Pullback, ma con VWAP **ancorato al breakout** invece che di
sessione.

**3. L'edge è recente.** Dice che prima degli ultimi ~2 anni non c'era, e lo attribuisce
all'aumento dell'attività algoritmica che reagisce al VWAP. Stessa avvertenza del corso
sull'ORB post‑2019 → l'OOS 2025→oggi e la tabella annuale sono la parte che conta.

## Da NON trasferire
Il suo ottimo è **TP a 3× lo stop**, e dice che prendere profitto sulla banda opposta
«strozza la strategia». È l'opposto del profilo prop (R:R 0,5–1, WR alto): lui ottimizza
per capitale proprio, dove paga la coda dei winner. Trasferire quel parametro nella
pipeline prop sarebbe un errore di contesto.

## Limiti
Codice non condiviso; backtest su ~1–2 anni; costi non dichiarati → i suoi PF (1,17–1,48)
non sono confrontabili con i nostri gate. Il tentativo finale di combinare breakout 32 min
+ ritracciamento al VWAP centrale + filtro delta **sottoperforma negli ultimi ~300 trade**
e resta irrisolto nella live.

## Altro
Cita **GARCH** come metodo quantitativo per stimare il regime di volatilità (alternativa
al VIX). Da valutare semmai molto più avanti.
