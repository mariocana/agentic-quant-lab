"""prova_nq_first5 (ricerca/idee/prova_nq_first5/hypothesis.md, «Regola eseguibile»).

Una serie: barre da 5 minuti di NQ, etichetta all'ora di chiusura (la barra delle 08:35 copre
08:30-08:34:59). EMA(12) sulle chiusure, alpha = 2/13, in continuo su tutte le barre Globex,
inizializzata con la prima chiusura e mai azzerata. Alla chiusura della barra delle 08:35:
close > EMA -> long, close < EMA -> short, close = EMA -> niente. Esce alla chiusura della
prima barra con orario >= 15:00; nelle giornate corte esce il SetExitOnClose del motore
(chiusura dell'ultima barra prima della pausa). Un trade al giorno, nessuno stop, nessun target.

Il motore conosce solo ordini per la barra dopo: ingresso e uscita «a mercato» scattano
all'apertura della barra successiva (08:35:00 e 15:00:00), non al close della barra del segnale.
"""

DEFAULT = dict(EMALen=12, EntryTime=835, ExitTime=1500, AllowLongs=True, AllowShorts=True,
               NumContracts=1)


class PROVA_NQ_FIRST5:
    def __init__(self, **inp):
        self.p = dict(DEFAULT, **inp)
        self.alpha = 2.0 / (self.p['EMALen'] + 1)
        self.ema = None
        self.dataPrec = None
        self.tradesToday = 0

    def su_barra(self, ctx):
        p, b = self.p, ctx.b()

        # EMA continua su tutte le barre, notte compresa
        if self.ema is None:
            self.ema = b.c
        else:
            self.ema += self.alpha * (b.c - self.ema)

        if b.data != self.dataPrec:
            self.tradesToday = 0
        self.dataPrec = b.data

        mp = ctx.market_position
        if mp == 0 and b.ora == p['EntryTime'] and self.tradesToday < 1:
            if b.c > self.ema and p['AllowLongs']:
                ctx.buy('First5.L', p['NumContracts'])
                self.tradesToday += 1
            elif b.c < self.ema and p['AllowShorts']:
                ctx.sell_short('First5.S', p['NumContracts'])
                self.tradesToday += 1

        if mp != 0 and b.ora >= p['ExitTime']:
            ctx.sell('L.Flat')
            ctx.buy_to_cover('S.Flat')
