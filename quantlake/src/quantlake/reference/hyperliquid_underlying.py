"""Which market each Hyperliquid perp follows, and when that market is open.

A HIP-3 perp on TSLA trades 24/7, but Tesla trades 6.5 hours a day. Outside
those hours the oracle has nothing live to read, the book thins out and funding
absorbs whatever imbalance builds up until the Monday open. A strategy that does
not know whether the underlying was open is learning from two different markets
as if they were one.

Calendars:
  always   24/7: main-dex crypto, and HIP-3 perps on crypto indices (TOTAL2, BTCD)
  XNYS     US cash equities, ETFs and cash indices (S&P 500, Nasdaq 100)
  CME      CME Globex futures: Sunday 17:00 to Friday 16:00 Chicago, halted
           16:00-17:00 every day. Metals, energy, rates.
  FX       24/5: Sunday 17:00 to Friday 17:00 New York
  XKRX XTKS XHKG XSHG XBOM   Korea, Tokyo, Hong Kong, Shanghai, Mumbai (for NSE,
           same hours and holidays)
  none     no public market: pre-IPO companies. The underlying is never open;
           the price is whatever the oracle deployer says it is.

A perp not in the map gets no calendar, and its column stays null: unknown is
not the same as closed. NEEDS_REVIEW lists the mappings made with doubt, as of
09/11/2026 — they are best guesses and should be checked against each deployer's
oracle documentation before any strategy relies on them.
"""
from __future__ import annotations

XNYS = ("AAOI AAPL AMAT AMD AMZN ARM ASML AVGO BABA BB BE BIRD BMNR BOT BX CBRS CIEN CIFR "
        "COHR COIN COST CRCL CRDO CRWD CRWV CVX DELL DKNG DRAM DRV EBAY EWJ EWT EWY EWZ GDX "
        "GEV GLW GME GOOGL GPRO HIMS HOOD IBM ICE IGV INTC IONQ IREN KORU KSTR LITE LLY LRCX "
        "LYTE MAGS MELI META MRNA MRVL MSFT MSTR MU MUU NBIS NCLD NET NFLX NOK NOW NVDA ORCL "
        "PLTR QCOM QNT RDDT RIVN RKLB SHAZ SMCI SMH SNDK SNXX SOFI SOXL STRC STX TER TLT TSLA "
        "TSM TTWO TWST UMC URNM USAR VST WDC XBI XLE ZM SP500 XYZ100").split()
CME = "GOLD SILVER PLATINUM PALLADIUM COPPER CL BRENTOIL NATGAS HO 2Y 10Y 30Y".split()
FX = "EUR GBP JPY".split()
XKRX = "SMSN SKHX SKHY HYUNDAI KR200".split()
XTKS = "SOFTBANK KIOXIA JP225".split()
XHKG = "XIAOMI TCNT MINIMAX ZHIPU".split()
XSHG = "CAMBRICON GIGADEV".split()
XBOM = "RELIANCE NIFTY".split()
ALWAYS = "BTCD TOTAL2 OTHERS BVIV".split()
NONE = "OAI ANTH ANT SPCX SHEIN OURA JIO CXMT UNITREE".split()

NEEDS_REVIEW = set(
    "DRAM BOT CBRS KSTR LYTE NCLD QNT SHAZ SNXX TWST USAR "      # tickers not checked one by one
    "BRENTOIL "                                                 # ICE, approximated with CME hours
    "2Y 10Y 30Y "                                               # yields: futures hours assumed
    "SP500 XYZ100 "                                             # cash index hours, not futures
    "MINIMAX ZHIPU UNITREE JIO CXMT".split()                    # listing status of recent IPOs
)

# Looked at and not identified: the column stays null for these on purpose. Kept
# apart from perps nobody has looked at yet, which the data test reports.
UNIDENTIFIED = set("PRL ANSEM TREAD PURRDAT".split())

_BY_TICKER: dict[str, str] = {}
for _cal, _names in (("XNYS", XNYS), ("CME", CME), ("FX", FX), ("XKRX", XKRX), ("XTKS", XTKS),
                     ("XHKG", XHKG), ("XSHG", XSHG), ("XBOM", XBOM), ("always", ALWAYS), ("none", NONE)):
    for _n in _names:
        assert _n not in _BY_TICKER, f"{_n} mapped twice"
        _BY_TICKER[_n] = _cal


def calendar_for(symbol: str, dex: str) -> str | None:
    """'always' for the main dex; for HIP-3 the ticker after the colon, the same
    on every dex (xyz:NVDA and io:NVDA follow the same stock). None if unknown."""
    if dex == "main":
        return "always"
    return _BY_TICKER.get(symbol.split(":", 1)[-1])
