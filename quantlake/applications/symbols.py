"""End of video 2.2 — shared instrument list.

Single source of truth for the symbol universe used across the Binance
arc. Both the historical bootstrap (this module) and the live strategy
(Module 4.3) import from here. One change here, both scripts see it.
"""

from dataclasses import dataclass



# ── top_10_momentum_crypto strategy universe ─────────────────────────────
TOP10 = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT",  "SOLUSDT",  "XRPUSDT",
    "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "LINKUSDT", "DOTUSDT",
]


# Macro instruments (M5)
@dataclass(frozen=True)
class MacroInstrument:
    """A macro instrument (FX / commodity / index) mapped across sources.

    Dukascopy gives deep spot-ish historical bars; Capital.com gives the
    live CFD feed. Both are normalised into silver/macro_ohlcv on
    Capital's price scale (see applications/historical/macro_silver.py
    introduced in v0.5.4).
    """
    symbol: str         # canonical name (used in bronze/silver/gold partitions)
    duka: str           # Dukascopy instrument code (empty when unavailable)
    capital: str        # Capital.com epic
    price_scale: float  # Dukascopy per-instrument decimal scaling


MACRO_INSTRUMENTS = [
    MacroInstrument("EURUSD", "EURUSD",     "EURUSD",    100_000.0),
    MacroInstrument("GBPUSD", "GBPUSD",     "GBPUSD",    100_000.0),
    MacroInstrument("XAUUSD", "XAUUSD",     "GOLD",        1_000.0),
    MacroInstrument("SPX500", "USA500IDXUSD", "US500",       1_000.0),
    MacroInstrument("WTI",    "LIGHTCMDUSD",  "OIL_CRUDE",   1_000.0),
    # Wheat CFD - no Dukascopy history available; lives on Capital-only.
    MacroInstrument("WHEAT",  "",           "WHEAT",       1_000.0),
]

FRED_SERIES = ["DGS10", "DGS2", "T10Y2Y", "DFF", "T10YIE"]


# US winter wheat belt centroids - aimed at agricultural zones rather
# than state geographical centers.
WHEAT_STATES = {
    "KS": (38.5, -98.0),
    "OK": (35.5, -97.5),
    "TX": (32.0, -100.0),
    "CO": (39.0, -105.5),
    "MT": (47.0, -109.5),
    "ND": (47.5, -100.5),
    "SD": (44.5, -100.0),
    "NE": (41.5, -99.5),
    "WA": (47.5, -120.5),
    "ID": (44.0, -114.5),
}




# ── Volatility / options context (Stucchi playbook) ──────────────────────
VOL_INDICES = ["VIX", "VIX9D", "VIX1D", "VIX3M", "VXN"]  # VXN = Nasdaq-100, EM for NQ
CASH_INDICES = ["NDX"]  # real level from nasdaq.com (futures are back-adjusted); SPX close comes from squeezemetrics
CHAIN_UNDERLYINGS = ["SPX"]


@dataclass(frozen=True)
class MCFile:
    """A MultiCharts ExportBars CSV in data/multicharts/."""
    symbol: str     # canonical name in bronze
    file: str       # file stem written by the indicator
    chart_tz: str   # time zone of the MultiCharts chart
    recent: bool = False  # short export (last days): always rewrites the range it covers


# ── Binance USDⓈ-M perpetuals (historical/binance_um.py) ─────────────────
# Exchange symbols; reference/instruments names the perpetual "<symbol>-PERP".
UM_PERPS = ["BTCUSDT"]


# Full history (exported once, and again after each quarterly roll: multicharts.py --replace)
# + a short chart of the last days, exported in the morning / before NY.
MC_FILES = [
    MCFile("ES", "ES_1min", "America/Chicago"),
    MCFile("ES", "ES_recent", "America/Chicago", recent=True),
    MCFile("NQ", "NQ_1min", "America/Chicago"),
    MCFile("NQ", "NQ_recent", "America/Chicago", recent=True),
]


# ── CFTC Commitments of Traders (migrated from cot-analyzer) ─────────────
@dataclass(frozen=True)
class COTInstrument:
    """A futures contract tracked in bronze/cftc_cot.

    If a contract returns no rows, its CFTC code is probably wrong —
    check on publicreporting.cftc.gov/resource/6dca-aqww.json?contract_market_name=...
    """
    symbol: str      # canonical name (bronze partition)
    cftc_code: str   # cftc_contract_market_code
    name: str        # human-readable CFTC contract name
    category: str    # FX | Crypto | Index | Rates | Commodity


COT_INSTRUMENTS = [
    # Forex
    COTInstrument("AUD",      "232741", "AUSTRALIAN DOLLAR",     "FX"),
    COTInstrument("GBP",      "096742", "BRITISH POUND",         "FX"),
    COTInstrument("CAD",      "090741", "CANADIAN DOLLAR",       "FX"),
    COTInstrument("EUR",      "099741", "EURO FX",               "FX"),
    COTInstrument("JPY",      "097741", "JAPANESE YEN",          "FX"),
    COTInstrument("CHF",      "092741", "SWISS FRANC",           "FX"),
    COTInstrument("NZD",      "112741", "NEW ZEALAND DOLLAR",    "FX"),
    COTInstrument("USD",      "098662", "U.S. DOLLAR INDEX",     "FX"),
    # Crypto
    COTInstrument("BTC",      "133741", "BITCOIN",               "Crypto"),
    COTInstrument("ETH",      "146021", "ETHER CASH SETTLED",    "Crypto"),
    # Index
    COTInstrument("SPX",      "13874+", "S&P 500 CONSOLIDATED",  "Index"),
    COTInstrument("ES",       "13874A", "E-MINI S&P 500",        "Index"),
    COTInstrument("NQ",       "209742", "NASDAQ-100 MINI",       "Index"),
    COTInstrument("YM",       "124603", "DOW JONES MINI ($5)",   "Index"),
    COTInstrument("RTY",      "239742", "RUSSELL 2000 MINI",     "Index"),
    COTInstrument("EMD",      "33874A", "E-MINI S&P 400",        "Index"),
    COTInstrument("VX",       "1170E1", "VIX FUTURES",           "Index"),
    # Rates
    COTInstrument("ZQ",       "045601", "30-DAY FED FUNDS",      "Rates"),
    COTInstrument("ZT",       "042601", "2-YEAR T-NOTES",        "Rates"),
    COTInstrument("ZF",       "044601", "5-YEAR T-NOTES",        "Rates"),
    COTInstrument("ZN",       "043602", "10-YEAR T-NOTES",       "Rates"),
    COTInstrument("ZB",       "020601", "30-YEAR T-BOND",        "Rates"),
    COTInstrument("UB",       "020604", "ULTRA T-BOND",          "Rates"),
    # Commodities
    COTInstrument("CL_NYMEX", "067651", "CRUDE OIL WTI (NYMEX)", "Commodity"),
    COTInstrument("CL_ICE",   "067411", "CRUDE OIL WTI (ICE)",   "Commodity"),
    COTInstrument("NG",       "023651", "NATURAL GAS",           "Commodity"),
    COTInstrument("GC",       "088691", "GOLD",                  "Commodity"),
    COTInstrument("SI",       "084691", "SILVER",                "Commodity"),
    COTInstrument("HG",       "085692", "COPPER #1",             "Commodity"),
    COTInstrument("PA",       "075651", "PALLADIUM",             "Commodity"),
    COTInstrument("PL",       "076651", "PLATINUM",              "Commodity"),
    COTInstrument("AL",       "191693", "ALUMINUM MWP",          "Commodity"),
]


# ── Satellite NDVI (Sentinel-2 + USDA CDL + NASS) ────────────────────────
@dataclass(frozen=True)
class NDVIAoi:
    """An area of interest for bronze/sentinel2_ndvi.

    bbox_id is the partition symbol. state/county link the AOI to the
    NASS county yield and state Crop Progress used as ground truth.
    """
    bbox_id: str
    bbox: tuple[float, float, float, float]   # min_lon, min_lat, max_lon, max_lat
    state: str
    county: str
    crop_class: int = 24                       # CDL winter wheat


NDVI_AOIS = [
    NDVIAoi("KS_SUMNER_5KM", (-97.50, 37.20, -97.45, 37.25), "KS", "SUMNER"),
]

# Harvest years. Each new season costs one ~3 GB CDL download (one-time).
NDVI_SEASONS = [2021, 2023, 2025]


# ── Superinvestors (13F-HR, applications/historical/superinvestors.py) ───
# (name shown in the desk, SEC CIK). Every CIK checked on data.sec.gov
# (2026-10-20): name matches and the fund files 13F-HR. Funds that stopped
# filing (Scion, Greenlight) stay listed: the desk marks them as stale.
SUPERINVESTORS = [
    ("Warren Buffett - Berkshire Hathaway", 1067983),
    ("Bill Ackman - Pershing Square", 1336528),
    ("David Einhorn - Greenlight Capital", 1079114),
    ("Daniel Loeb - Third Point", 1040273),
    ("Howard Marks - Oaktree Capital", 949509),
    ("Seth Klarman - Baupost Group", 1061768),
    ("David Tepper - Appaloosa", 1656456),
    ("Michael Burry - Scion Asset Management", 1649339),
    ("Stan Druckenmiller - Duquesne Family Office", 1536411),
    ("Mohnish Pabrai - Dalal Street", 1549575),
    ("Terry Smith - Fundsmith", 1569205),
    ("Li Lu - Himalaya Capital", 1709323),
    ("Chase Coleman - Tiger Global", 1167483),
    ("Stephen Mandel - Lone Pine Capital", 1061165),
    ("Andreas Halvorsen - Viking Global", 1103804),
    ("John Armitage - Egerton Capital", 1581811),
    ("Chuck Akre - Akre Capital", 1112520),
    ("Bruce Berkowitz - Fairholme", 1056831),
    ("Yacktman Asset Management", 905567),
    ("David Rolfe - Wedgewood Partners", 859804),
    ("Polen Capital", 1034524),
    ("Dodge & Cox", 200217),
    ("First Eagle Investment Management", 1325447),
    ("Nelson Peltz - Trian Fund", 1345471),
    ("Chris Hohn - TCI Fund", 1647251),
    ("William Von Mueffling - Cantillon Capital", 1279936),
    ("Duan Yongping - H&H International", 1759760),
    ("Wallace Weitz - Weitz Investment", 883965),
    ("Glenn Greenberg - Brave Warrior Advisors", 1553733),
    ("Richard Pzena - Pzena Investment", 1027796),
    ("C.T. Fitzpatrick - Vulcan Value Partners", 1556785),
    ("Triple Frond Partners", 1454502),
    ("Francois Rochon - Giverny Capital", 1641864),
    ("AKO Capital", 1376879),
    ("Lindsell Train", 1484150),
    ("Leon Cooperman - Omega Family Office", 898382),
    ("David Abrams - Abrams Capital", 1358706),
    ("Abrams Bison Investments", 1317588),
    ("Tom Russo - Gardner Russo & Quinn", 860643),
    ("Tom Gayner - Markel Group", 1096343),
    ("Chris Bloomstran - Semper Augustus", 1115373),
    ("Charlie Munger - Daily Journal", 783412),
    ("Mairs & Power", 1070134),
    ("Greenhaven Associates", 846222),
    ("AltaRock Partners", 1631014),
    ("Pat Dorsey - Dorsey Asset Management", 1671657),
    ("Robert Vinall - RV Capital", 1766596),
    ("Dennis Hong - ShawSpring Partners", 1766908),
    ("Clifford Sosin - CAS Investment Partners", 1697591),
]
