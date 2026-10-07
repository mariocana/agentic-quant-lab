"""Delta table maintenance: compact small files, then vacuum the old ones.

Every upsert adds new Parquet files, and the live runners merge every
FLUSH_INTERVAL seconds, so tables fill up with tiny files and reads slow
down. Compaction rewrites them into larger ones; vacuum deletes the files
no longer referenced once they are older than the retention window (time
travel within that window keeps working).

Gold tables listed in reference/instruments (gold_table column) are read
by alpha-quant, which records the Delta version it used and may reopen it
later: those are compacted but never vacuumed, so every old version stays
readable (they keep growing on disk; vacuum them by hand if needed).

Run it while no live runner is writing: a concurrent merge makes the
compaction commit fail. Such a table is reported and skipped, the next
run picks it up.

    poetry run maintain                    # every table under DATA_ROOT
    poetry run maintain --layer gold       # only data/gold
    poetry run maintain --dry-run          # list what would be done
"""
import argparse
from dataclasses import dataclass
from pathlib import Path

import polars as pl
from deltalake import DeltaTable

from quantlake.config import DATA_ROOT

LAYERS = ("bronze", "silver", "gold")
DEFAULT_RETENTION_HOURS = 7 * 24


@dataclass
class TableReport:
    path: Path
    files_before: int
    files_removed: int = 0
    files_added: int = 0
    vacuumed: int = 0
    vacuum_skipped: bool = False
    error: str | None = None


def find_tables(root: Path) -> list[Path]:
    """Every Delta table under root (gold nests them as <table>/<timeframe>)."""
    if not root.exists():
        return []
    return sorted(log.parent for log in root.rglob("_delta_log") if log.is_dir())


def protected_gold_tables(data_root: Path = DATA_ROOT) -> set[str]:
    """Gold tables alpha-quant reads: the gold_table values in reference/instruments."""
    path = str(data_root / "reference" / "instruments")
    if not DeltaTable.is_deltatable(path):
        return set()
    df = pl.from_arrow(DeltaTable(path).to_pyarrow_table(columns=["gold_table"]))
    return set(df["gold_table"].drop_nulls().to_list())


def maintain_table(
    path: Path,
    retention_hours: int = DEFAULT_RETENTION_HOURS,
    dry_run: bool = False,
    vacuum: bool = True,
) -> TableReport:
    dt = DeltaTable(str(path))
    report = TableReport(path=path, files_before=len(dt.files()), vacuum_skipped=not vacuum)
    if dry_run:
        if vacuum:
            report.vacuumed = len(dt.vacuum(retention_hours=retention_hours, dry_run=True,
                                            enforce_retention_duration=False))
        return report

    metrics = dt.optimize.compact()
    report.files_removed = metrics.get("numFilesRemoved", 0)
    report.files_added = metrics.get("numFilesAdded", 0)
    if vacuum:
        report.vacuumed = len(dt.vacuum(retention_hours=retention_hours, dry_run=False,
                                        enforce_retention_duration=False))
    return report


def run(
    layers: tuple[str, ...] = LAYERS,
    retention_hours: int = DEFAULT_RETENTION_HOURS,
    dry_run: bool = False,
    data_root: Path = DATA_ROOT,
) -> list[TableReport]:
    protected = protected_gold_tables(data_root)
    reports = []
    for layer in layers:
        for path in find_tables(data_root / layer):
            keep_versions = layer == "gold" and path.relative_to(data_root / "gold").parts[0] in protected
            try:
                reports.append(maintain_table(path, retention_hours, dry_run, vacuum=not keep_versions))
            except Exception as exc:  # one bad table must not stop the others
                reports.append(TableReport(path=path, files_before=-1, error=f"{type(exc).__name__}: {exc}"))
    return reports


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--layer", choices=LAYERS, action="append",
                        help="limit to a layer (repeatable); default: all")
    parser.add_argument("--retention-hours", type=int, default=DEFAULT_RETENTION_HOURS,
                        help=f"keep unreferenced files younger than this (default {DEFAULT_RETENTION_HOURS})")
    parser.add_argument("--dry-run", action="store_true", help="report only, change nothing")
    args = parser.parse_args()

    reports = run(tuple(args.layer or LAYERS), args.retention_hours, args.dry_run)
    failed = 0
    for r in reports:
        name = r.path.relative_to(DATA_ROOT) if r.path.is_relative_to(DATA_ROOT) else r.path
        if r.error:
            failed += 1
            print(f"FAIL {name}: {r.error}")
        else:
            vac = "vacuum skipped (read by alpha-quant)" if r.vacuum_skipped else f"{r.vacuumed} vacuumed"
            if args.dry_run:
                vac = "no vacuum (read by alpha-quant)" if r.vacuum_skipped else f"{r.vacuumed} to vacuum"
                print(f"     {name}: {r.files_before} files, {vac}")
            else:
                print(f"ok   {name}: {r.files_removed} -> {r.files_added} files compacted, {vac}")
    print(f"{len(reports)} tables, {failed} failed")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
