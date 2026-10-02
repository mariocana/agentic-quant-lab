"""SqueezeMetrics DIX / GEX daily history -> bronze/squeezemetrics.

Run:
    .venv/bin/python applications/historical/squeezemetrics.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import quantlake.bronze.ingest as bronze
from quantlake.bronze.connectors.squeezemetrics import SqueezeMetricsConnector

TABLE = SqueezeMetricsConnector.TABLE_NAME

df = SqueezeMetricsConnector().fetch()
df = bronze.add_partition_columns(df, symbol="SPX")
bronze.save(df, TABLE)
print(f"[SPX] {len(df):,} days, last {df['timestamp'].max()}")
