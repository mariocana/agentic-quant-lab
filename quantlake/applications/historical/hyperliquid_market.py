"""Pull the trading desk's hourly market samples into bronze.

Copies every day file the desk has and we don't (or that grew since: today's file
grows every hour), then merges them into bronze/hyperliquid_market. Safe to run
as often as you like.

Needs in quantlake/.env:
    DESK_URL       the deployed desk, e.g. https://agentic-quant-lab-production.up.railway.app
    DESK_PASSWORD  the desk's dashboard password

Run:
    poetry run python applications/historical/hyperliquid_market.py
"""
import os
import sys

from dotenv import load_dotenv

from quantlake.bronze.connectors import hyperliquid_market as hm
from quantlake.config import BRONZE_ROOT

load_dotenv()

url, password = os.getenv("DESK_URL", "").strip(), os.getenv("DESK_PASSWORD", "").strip()
if not url or not password:
    sys.exit("DESK_URL and DESK_PASSWORD must be set in quantlake/.env")

raw_dir = BRONZE_ROOT / hm.RAW_DIR_NAME
changed = hm.pull(hm.DeskMarketSource(url, password), raw_dir)
if not changed:
    print("up to date")
    sys.exit(0)

rows = hm.ingest(changed, str(BRONZE_ROOT / hm.TABLE_NAME))
print(f"{len(changed)} day file(s) pulled: {', '.join(p.name[:10] for p in changed)}")
print(f"{rows:,} rows merged into bronze/{hm.TABLE_NAME}")
