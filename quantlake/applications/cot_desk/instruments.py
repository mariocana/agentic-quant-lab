"""Ticker -> instrument lookup for the COT desk.

The list itself lives in applications/symbols.py (COT_INSTRUMENTS), the
same one the bronze ingester uses, so there is a single source of truth.
"""
from symbols import COT_INSTRUMENTS, COTInstrument as Instrument

INSTRUMENTS: dict[str, Instrument] = {i.symbol: i for i in COT_INSTRUMENTS}
