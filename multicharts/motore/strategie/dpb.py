"""DriftPullback v2.1 (strategies/DriftPullback/DriftPullback_v21.txt), riga per riga.

Solo i rami usati dai report: AnchorType 2 (VWAP di sessione su data2), DriftMode 0 (drift in %),
ExitMode 0 (punti fissi), SizeMode 1. Gli altri rami alzano un errore invece di fare altro.
data1 = barre da 5 minuti (esecuzione), data2 = barre da 15 minuti (segnale).
"""

DEFAULT = dict(AnchorType=2, DriftLen=4, DriftThreshPct=0.10, DriftMode=0, PullbackWindow=6,
               ExitMode=0, LongSLpts=80, LongTPpts=40, ShortSLpts=80, ShortTPpts=50,
               StopSlipTicks=2, TradeLongs=True, TradeShorts=True, MaxTradesPerDay=4,
               MaxLossesPerDay=2, SessStart=930, SessEnd=1430, FlatTime=1455,
               VwapStart=830, VwapEnd=1500, SizeMode=1, BaseCts=1, TickSize=0.25)


class DPB:
    def __init__(self, barre2, **inp):
        self.p = dict(DEFAULT, **inp)
        if self.p['AnchorType'] != 2 or self.p['DriftMode'] != 0 or self.p['ExitMode'] != 0 \
                or self.p['SizeMode'] != 1:
            raise SystemExit('dpb.py: solo AnchorType 2, DriftMode 0, ExitMode 0, SizeMode 1')
        self.d2 = barre2
        self.j = -1                       # indice dell'ultima barra data2 chiusa
        self.t2 = None
        self.sPV = self.sVol = self.sVwap = self.sVwapLast = self.sVwapPrev = 0.0
        self.ma2 = self.ma2prev = self.driftPct = 0.0
        self.longArmed = self.shortArmed = False
        self.armedBars = self.tradesToday = self.lossesToday = 0
        self.prevMP = self.tradeCount = 0
        self.dataPrec = None

    def su_barra(self, ctx):
        p, b = self.p, ctx.b()
        slip = p['StopSlipTicks'] * p['TickSize']
        cts = max(p['BaseCts'], 1)

        # data2: ultima barra da 15 minuti chiusa entro la chiusura di questa
        while self.j + 1 < len(self.d2) and self.d2[self.j + 1].t <= b.t:
            self.j += 1
        if self.j < p['DriftLen']:
            return
        d2 = self.d2[self.j]

        # reset giornaliero
        if self.dataPrec is not None and b.data != self.dataPrec:
            self.tradesToday = self.lossesToday = 0
            self.longArmed = self.shortArmed = False
            self.armedBars = 0
            self.sPV = self.sVol = self.sVwap = self.sVwapLast = self.sVwapPrev = 0.0
        self.dataPrec = b.data

        # nuova barra da 15 minuti (il codice confronta solo l'ora, come qui)
        newBar2 = False
        if d2.ora != self.t2:
            newBar2, self.t2 = True, d2.ora

        if newBar2:
            self.sVwapPrev = self.sVwapLast
            if p['VwapStart'] < d2.ora <= p['VwapEnd']:
                self.sPV += (d2.h + d2.l + d2.c) / 3 * d2.v
                self.sVol += d2.v
            if self.sVol > 0:
                self.sVwap = self.sPV / self.sVol
            self.sVwapLast = self.sVwap

        self.ma2 = self.sVwapLast
        self.ma2prev = self.sVwapPrev if self.sVwapPrev > 0 else self.ma2
        anchorOK = self.ma2 > 0

        c_n = self.d2[self.j - p['DriftLen']].c
        if c_n != 0:
            self.driftPct = (d2.c - c_n) / c_n * 100
        longOK = self.driftPct >= p['DriftThreshPct']
        shortOK = self.driftPct <= -p['DriftThreshPct']

        if newBar2:
            if anchorOK and d2.c > self.ma2 and self.ma2 > self.ma2prev and longOK:
                self.longArmed, self.shortArmed, self.armedBars = True, False, 0
            elif anchorOK and d2.c < self.ma2 and self.ma2 < self.ma2prev and shortOK:
                self.shortArmed, self.longArmed, self.armedBars = True, False, 0
            else:
                self.longArmed = self.shortArmed = False

        if self.longArmed or self.shortArmed:
            self.armedBars += 1
            if self.armedBars > p['PullbackWindow']:
                self.longArmed = self.shortArmed = False

        if ctx.total_trades > self.tradeCount:
            if ctx.position_profit(1) < 0:
                self.lossesToday += 1
            self.tradeCount = ctx.total_trades

        mp = ctx.market_position
        if mp != 0 and self.prevMP == 0:
            self.tradesToday += 1
        self.prevMP = mp

        if mp == 0 and p['SessStart'] <= b.ora < p['SessEnd'] \
                and self.tradesToday < p['MaxTradesPerDay'] and self.lossesToday < p['MaxLossesPerDay']:
            if p['TradeLongs'] and self.longArmed and b.c < b.o:
                ctx.buy('DriftPB.L', cts)
                self.longArmed = False
            if p['TradeShorts'] and self.shortArmed and b.c > b.o:
                ctx.sell_short('DriftPB.S', cts)
                self.shortArmed = False

        if mp == 1:
            ctx.sell('L.SL', ctx.entry_price - p['LongSLpts'] - slip, 'stop')
            ctx.sell('L.TP', ctx.entry_price + p['LongTPpts'], 'limite')
        if mp == -1:
            ctx.buy_to_cover('S.SL', ctx.entry_price + p['ShortSLpts'] + slip, 'stop')
            ctx.buy_to_cover('S.TP', ctx.entry_price - p['ShortTPpts'], 'limite')

        if mp != 0 and b.ora >= p['FlatTime']:
            ctx.sell('L.Flat')
            ctx.buy_to_cover('S.Flat')
