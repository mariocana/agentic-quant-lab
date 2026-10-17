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
