"""Delta table maintenance: compact small files, then vacuum the old ones.

Every upsert adds new Parquet files, and the live runners merge every
FLUSH_INTERVAL seconds, so tables fill up with tiny files and reads slow
down. Compaction rewrites them into larger ones; vacuum deletes the files
no longer referenced once they are older than the retention window (time
travel within that window keeps working).

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
    error: str | None = None


def find_tables(root: Path) -> list[Path]:
    """Every Delta table under root (gold nests them as <table>/<timeframe>)."""
    if not root.exists():
        return []
    return sorted(log.parent for log in root.rglob("_delta_log") if log.is_dir())


def maintain_table(
    path: Path,
    retention_hours: int = DEFAULT_RETENTION_HOURS,
    dry_run: bool = False,
) -> TableReport:
    dt = DeltaTable(str(path))
    report = TableReport(path=path, files_before=len(dt.files()))
    if dry_run:
        report.vacuumed = len(dt.vacuum(retention_hours=retention_hours, dry_run=True,
                                        enforce_retention_duration=False))
        return report

    metrics = dt.optimize.compact()
    report.files_removed = metrics.get("numFilesRemoved", 0)
    report.files_added = metrics.get("numFilesAdded", 0)
    report.vacuumed = len(dt.vacuum(retention_hours=retention_hours, dry_run=False,
                                    enforce_retention_duration=False))
    return report


def run(
    layers: tuple[str, ...] = LAYERS,
    retention_hours: int = DEFAULT_RETENTION_HOURS,
    dry_run: bool = False,
    data_root: Path = DATA_ROOT,
) -> list[TableReport]:
    reports = []
    for layer in layers:
        for path in find_tables(data_root / layer):
            try:
                reports.append(maintain_table(path, retention_hours, dry_run))
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
        elif args.dry_run:
            print(f"     {name}: {r.files_before} files, {r.vacuumed} to vacuum")
        else:
            print(f"ok   {name}: {r.files_removed} -> {r.files_added} files compacted, {r.vacuumed} vacuumed")
    print(f"{len(reports)} tables, {failed} failed")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
