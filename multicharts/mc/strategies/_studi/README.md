# Studi: misure che non appartengono a una strategia sola

Indicatori che misurano una **premessa**, non una strategia. Servono a decidere *dove* e *se*
vale la pena scrivere codice, e si applicano a piu' strumenti nello stesso pomeriggio.

## `DriftPersistence_Study.txt`

**La domanda:** dopo un drift di un'ora, il prezzo tende a **continuare**?

E' la premessa di DriftPullback, l'unica strategia con un edge dimostrato. Il suo porting su
@YM e' fallito (eccesso da **+2,52** a **+0,07 pp**) **pur avendo trasferito perfettamente la
geometria** — WR 61,8% contro 63,5%, R:R 0,62 contro 0,64. Quindi l'edge e' di NQ, ma non
sappiamo *perche'*. Se la ragione e' la persistenza del momentum intraday, allora e' una
**proprieta' misurabile dello strumento** e si puo' cercare dove esiste, invece di provare un
porting alla volta.

**Il metro:** in un random walk la persistenza e' **50%**. Conta solo l'**eccesso sul 50%**
col suo errore standard. Soglia per crederci: **3 errori standard**.

**Perche' questo non ha i bug degli altri misuratori:** non c'e' nessun primo tocco da
risolvere, quindi **nessun tie-break dentro la barra**; e non c'e' niente di "non risolto" da
escludere, perche' **ogni osservazione ha un segno**. E' un test sul segno di un rendimento
forward, e il calcolo e' sfasato di `FwdBars` barre cosi' che non ci sia look-ahead.

**Uso:** chart **15 min**, timezone Exchange (CT), **2020-2024**, `ShowLog 1`. Applicare a
**@NQ** (il controllo: li' sappiamo che l'edge c'e'), **@YM** (il controllo negativo: li'
sappiamo che non c'e'), poi **@RTY**, **@GC**, **@CL**. Cambiare `Tag` ogni volta e mettere
`ResetFile 0` dal secondo in poi, cosi' il log li raccoglie tutti.

**Come si legge:** se NQ esce alto e YM basso, **la misura e' validata** e il numero degli
altri tre si puo' credere. Se NQ e YM escono uguali, la premessa e' sbagliata e la ragione per
cui DriftPullback funziona e' un'altra — che e' comunque un'informazione, e chiude una strada.

---

## Esito del 18/10/2026: **la premessa e' sbagliata**

Log: `mc/docs/measures/drift_persistence_*_2020-2024.txt`. Run pulito: nessun `nan`, tasso
d'armamento fra 65,5% e 69,8% su tutti e cinque, sotto la soglia dell'80%.

| | persistenza | eccesso | errori std | expectancy di seguire il drift |
|---|---|---|---|---|
| **NQ** | 50,15% | +0,15 pp | +0,45 | +0,0252 ATR |
| **YM** | 50,18% | +0,18 pp | +0,55 | +0,0212 ATR |
| RTY | 49,89% | −0,11 pp | −0,35 | +0,0125 ATR |
| CL | 49,31% | −0,69 pp | −2,09 | +0,0075 ATR |
| **GC** | **47,86%** | **−2,14 pp** | **−6,34** | −0,0002 ATR |

### La regola scritta prima del run, applicata

> *«Se NQ e YM escono uguali, la premessa e' sbagliata e la ragione per cui DriftPullback
> funziona e' un'altra.»*

**NQ e YM escono identici: 50,15% e 50,18%.** Anche in expectancy si somigliano (+0,025 e
+0,021 ATR). Il controllo positivo e quello negativo non si distinguono.

**Quindi l'edge di DriftPullback NON e' la persistenza incondizionata del drift orario.** Sta
nella **congiunzione**: drift + pullback + barra di trigger + la geometria d'uscita. La
premessa, presa da sola, non distingue lo strumento dove funziona da quello dove non funziona.
E' coerente col paper *Fast Alpha*: il valore sta nel **timing** che il pullback aggiunge alla
direzione, non nella direzione da sola.

**La strada «misura la premessa per trovare lo strumento» e' chiusa.**

### Il dato secondario, ed e' il segnale statistico piu' forte mai misurato

**GC mostra anti-persistenza: 47,86%, a −6,34 errori standard.** Dopo un'ora di drift, nella
mezz'ora dopo l'oro **inverte piu' spesso di quanto continui**. Non e' rumore.

**Ma non vale niente cosi' com'e'**: la mossa che inverte e' **piu' piccola** di quella che
continua (0,755 contro 0,822 ATR). Fadare vale `0,5214 × 0,755 − 0,4786 × 0,822 =
+0,0002 ATR`. **Il vantaggio di frequenza e' cancellato esattamente da quello di ampiezza.**

> **Lezione di metodo**: un test sul *segno* puo' essere significativissimo con expectancy
> nulla, quando le ampiezze sono asimmetriche. Il primo tocco con bracket fisso non ha questo
> difetto, perche' fissa le ampiezze per costruzione. Il test sul segno ha senso solo se si
> guarda anche la mossa media nei due casi — che per fortuna questo indicatore stampava.

**Va testato con un bracket?** E' l'unico segnale forte che abbiamo, ma tre cose pesano
contro: e' **mean reversion a orizzonte corto**, che *Fast Alpha* dice non profittevole dopo i
costi; MGC e' il micro **piu' caro** del listino fra quelli plausibili ($2,60 RT, 3,2% di R);
e su GC e CL abbiamo gia' misurato **la peggiore stabilita' di regime**. Resta in coda, non in
cima.

### Il bug del run precedente non cambiava il verdetto

RTY prima del fix: **−0,12 pp**, dopo: **−0,11**. Il conteggio non era inquinato; il `nan`
toccava solo le righe diagnostiche.
