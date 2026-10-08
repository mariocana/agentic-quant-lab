"""Railway cron job: SPX option chain snapshot -> R2.

The CBOE serves only the current chain, so a snapshot missed is lost for good:
this job takes them even when the Mac is off. Railway runs it every 5 minutes
in a few UTC hours (railway.json); the job decides from the New York clock
whether a slot is due, so the US/EU daylight-saving changes need no edits.

    slot (ET)  Rome (usually)  why
    02:20      08:20           before London
    09:20      15:20           before the cash open: EM 0DTE at the open
    10:00      16:00           after the opening range
    15:40      21:40           before the close (MOC)

Each snapshot is one parquet file:
    cboe_option_chain/SPX/<ET date>/<slot>_<HHMMSS>Z.parquet
A slot already saved for the day is skipped. CHAIN_FORCE=1 (or --force) takes
a snapshot now, whatever the time: use it once to test a new deployment.

The Mac imports the files into bronze with applications/cloud_sync.py.
"""
import os
import sys
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from quantlake import remote
from quantlake.bronze.connectors.cboe import CBOEOptionChainConnector

ET = ZoneInfo("America/New_York")
SLOTS = [time(2, 20), time(9, 20), time(10, 0), time(15, 40)]
WINDOW = timedelta(minutes=5)   # = cron step
PREFIX = "cboe_option_chain/SPX"


def due_slot(now_et: datetime) -> time | None:
    if now_et.weekday() >= 5:
        return None
    for s in SLOTS:
        start = now_et.replace(hour=s.hour, minute=s.minute, second=0, microsecond=0)
        if start <= now_et < start + WINDOW:
            return s
    return None


def main() -> None:
    now_et = datetime.now(timezone.utc).astimezone(ET)
    force = os.getenv("CHAIN_FORCE") == "1" or "--force" in sys.argv
    slot = due_slot(now_et)
    if slot is None and not force:
        print(f"{now_et:%Y-%m-%d %H:%M} ET: no slot due")
        return
    tag = f"{slot:%H%M}" if slot else "manual"
    day = f"{PREFIX}/{now_et:%Y-%m-%d}/"
    if slot and any(k.rsplit("/", 1)[-1].startswith(tag + "_") for k in remote.list_keys(day)):
        print(f"{now_et:%Y-%m-%d} slot {tag} ET already saved")
        return
    df = CBOEOptionChainConnector(max_dte=90, strike_band=0.20).fetch(symbol="SPX")
    if df.is_empty():
        sys.exit("empty chain from CBOE")
    ts = df["timestamp"][0]
    path = remote.write_parquet(df, f"{day}{tag}_{ts:%H%M%S}Z.parquet")
    print(f"slot {tag} ET: {len(df):,} options, spot {df['spot'][0]} -> {path}")


if __name__ == "__main__":
    main()
