"""Where alphaquant finds quantlake's data and its own cost settings.

alphaquant never writes into QUANTLAKE_DATA_ROOT: it only reads Delta tables.
"""
import os
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Same variable quantlake uses; default = sibling checkout python/quantlake/data
QUANTLAKE_DATA_ROOT = Path(
    os.getenv("QUANTLAKE_DATA_ROOT", str(_PROJECT_ROOT.parent / "quantlake" / "data"))
)
COSTS_FILE = Path(os.getenv("ALPHAQUANT_COSTS_FILE", str(_PROJECT_ROOT / "config" / "costs.yaml")))
