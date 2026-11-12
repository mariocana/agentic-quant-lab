"""Overnight Bias ORB (strategies/OvernightBiasORB/OvernightBiasORB.txt), riga per riga.

Una serie: barre da 15 minuti. ADX di Wilder come DirMovement di TradeStation/MC: con un
riscaldamento lungo la condizione iniziale non conta. La finestra TradeStartEL/TradeEndEL e' il
`dal`/`al` del motore.
"""

DEFAULT = dict(SessStart=830, OREnd=845, LastEntry=1200, FlatTime=1430, SessEnd=1500,
               MaxTradesPerDay=4, BiasLongMin=0.67, BiasShortMax=0.33, ADXLen=16, ADXMin=20,
               BreakSkipMult=2.5, BarAvgLen=20, MinORx=0, MaxORx=2, ORMedianDays=20,
               ATR_k=0.30, ATR_Days=15, TakeProfitRR=3, NumContracts=1)


class ADX:
    """ADX(len) di Wilder: DM e true range lisciati con 1/len, poi DX lisciato con 1/len."""

    def __init__(self, n):
        self.n, self.k = n, 0
        self.prev = None
        self.tr = self.pdm = self.mdm = 0.0
        self.adx = 0.0
        self.dx_buf = []

    def aggiorna(self, h, l, c):
        if self.prev is None:
            self.prev = (h, l, c)
            return 0.0
        ph, pl, pc = self.prev
        self.prev = (h, l, c)
        su, giu = h - ph, pl - l
        pdm = su if su > giu and su > 0 else 0.0
        mdm = giu if giu > su and giu > 0 else 0.0
        tr = max(h, pc) - min(l, pc)
        n = self.n
        self.k += 1
        if self.k <= n:                       # primi n: somme semplici, poi media
            self.tr += tr / n; self.pdm += pdm / n; self.mdm += mdm / n
        else:
            self.tr += (tr - self.tr) / n
            self.pdm += (pdm - self.pdm) / n
            self.mdm += (mdm - self.mdm) / n
        if self.k < n or self.tr <= 0:
            return self.adx
        dip, dim = 100 * self.pdm / self.tr, 100 * self.mdm / self.tr
        dx = 100 * abs(dip - dim) / (dip + dim) if dip + dim > 0 else 0.0
        if len(self.dx_buf) < n:
            self.dx_buf.append(dx)
            self.adx = sum(self.dx_buf) / len(self.dx_buf)
        else:
            self.adx += (dx - self.adx) / n
        return self.adx


class OBO:
    def __init__(self, **inp):
        self.p = dict(DEFAULT, **inp)
        self.adx = ADX(self.p['ADXLen'])
        self.rng = []                         # High - Low delle barre, per Average(...)[1]
        self.dataPrec = None
        self.orHigh, self.orLow, self.orDone = 0.0, 999999.0, False
        self.tradesToday = 0
        self.sessOpenPx = 0.0
        self.onHigh, self.onLow, self.onBias = 0.0, 999999.0, 0
        self.orMedApprox, self.orCount, self.regimeOK = 0.0, 0, True
        self.stopPx = self.tgtPx = 0.0
        self.atrRthHi, self.atrRthLo, self.atrRthCl, self.atrRthSeen = 0.0, 999999.0, 0.0, False
        self.atrPrevCl = 0.0
        self.trBuf = [0.0] * 200
        self.atrPos = self.atrFilled = 0
        self.atrRef, self.atrOK = 0.0, False
        self.onPos = 0.0

    def su_barra(self, ctx):
        p, b = self.p, ctx.b()
        t = b.ora
        adx = self.adx.aggiorna(b.h, b.l, b.c)
        n = p['BarAvgLen']
        avgRng = sum(self.rng[-n:]) / n if len(self.rng) >= n else 0.0
        self.rng.append(b.h - b.l)
        if len(self.rng) > 400:
            del self.rng[:200]

        if self.dataPrec is not None and b.data != self.dataPrec:
            if self.atrRthSeen:
                trVal = self.atrRthHi - self.atrRthLo
                if self.atrPrevCl > 0:
                    trVal = max(trVal, abs(self.atrRthHi - self.atrPrevCl), abs(self.atrRthLo - self.atrPrevCl))
                self.trBuf[self.atrPos] = trVal
                self.atrPos += 1
                if self.atrPos >= p['ATR_Days']:
                    self.atrPos = 0
                if self.atrFilled < p['ATR_Days']:
                    self.atrFilled += 1
                self.atrPrevCl = self.atrRthCl
            self.atrRthHi, self.atrRthLo, self.atrRthCl, self.atrRthSeen = 0.0, 999999.0, 0.0, False
            self.atrOK = self.atrFilled >= p['ATR_Days']
            self.atrRef = sum(self.trBuf[:p['ATR_Days']]) / p['ATR_Days'] if self.atrOK else 0.0
            self.orHigh, self.orLow, self.orDone = 0.0, 999999.0, False
            self.tradesToday = 0
            self.sessOpenPx, self.onBias = 0.0, 0
            self.onHigh, self.onLow = b.h, b.l
        elif self.dataPrec is not None:
            if t <= p['SessStart']:
                self.onHigh = max(self.onHigh, b.h)
                self.onLow = min(self.onLow, b.l)
        self.dataPrec = b.data

        if p['SessStart'] < t <= p['SessEnd']:
            if not self.atrRthSeen:
                self.atrRthHi, self.atrRthLo, self.atrRthSeen = b.h, b.l, True
            else:
                self.atrRthHi = max(self.atrRthHi, b.h)
                self.atrRthLo = min(self.atrRthLo, b.l)
            self.atrRthCl = b.c

        if self.sessOpenPx == 0 and p['SessStart'] < t <= p['OREnd']:
            self.sessOpenPx = b.o
            if self.onHigh > self.onLow:
                self.onPos = (self.sessOpenPx - self.onLow) / (self.onHigh - self.onLow)
                if self.onPos >= p['BiasLongMin']:
                    self.onBias = 1
                elif self.onPos <= p['BiasShortMax']:
                    self.onBias = -1
                else:
                    self.onBias = 9

        if p['SessStart'] < t <= p['OREnd']:
            self.orHigh = max(self.orHigh, b.h)
            self.orLow = min(self.orLow, b.l)

        if not self.orDone and t > p['OREnd'] and self.orHigh > 0:
            self.orDone = True
            self.regimeOK = True
            r = self.orHigh - self.orLow
            if self.orMedApprox > 0:
                self.regimeOK = p['MinORx'] * self.orMedApprox <= r <= p['MaxORx'] * self.orMedApprox
            if self.orMedApprox == 0:
                self.orMedApprox = r
            else:
                self.orMedApprox += 2 / (p['ORMedianDays'] + 1) * (r - self.orMedApprox)
            self.orCount += 1
            if self.orCount < p['ORMedianDays']:
                self.regimeOK = True

        stopPts = p['ATR_k'] * self.atrRef
        atrStopOK = self.atrOK and stopPts > 0
        adxOK = adx >= p['ADXMin']
        barRngOK = avgRng == 0 or (b.h - b.l) <= p['BreakSkipMult'] * avgRng
        mp = ctx.market_position
        canWork = self.orDone and self.regimeOK and adxOK and atrStopOK \
            and p['OREnd'] < t <= p['LastEntry'] and mp == 0 and self.tradesToday < p['MaxTradesPerDay']

        if canWork:
            if b.c > self.orHigh:
                if barRngOK and self.onBias == 1:
                    self.stopPx, self.tgtPx = b.c - stopPts, b.c + stopPts * p['TakeProfitRR']
                    ctx.buy('OBO-L', p['NumContracts'])
                    ctx.sell('OBO-L-SL0', self.stopPx, 'stop')
                    ctx.sell('OBO-L-TP0', self.tgtPx, 'limite')
                    self.tradesToday += 1
            elif b.c < self.orLow:
                if barRngOK and self.onBias == -1:
                    self.stopPx, self.tgtPx = b.c + stopPts, b.c - stopPts * p['TakeProfitRR']
                    ctx.sell_short('OBO-S', p['NumContracts'])
                    ctx.buy_to_cover('OBO-S-SL0', self.stopPx, 'stop')
                    ctx.buy_to_cover('OBO-S-TP0', self.tgtPx, 'limite')
                    self.tradesToday += 1

        if mp == 1:
            if t >= p['FlatTime']:
                ctx.sell('OBO-XL')
            else:
                ctx.sell('OBO-L-SL', self.stopPx, 'stop')
                ctx.sell('OBO-L-TP', self.tgtPx, 'limite')
        if mp == -1:
            if t >= p['FlatTime']:
                ctx.buy_to_cover('OBO-XS')
            else:
                ctx.buy_to_cover('OBO-S-SL', self.stopPx, 'stop')
                ctx.buy_to_cover('OBO-S-TP', self.tgtPx, 'limite')
