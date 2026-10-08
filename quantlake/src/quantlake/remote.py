"""Remote object store for jobs that run in the cloud (Cloudflare R2, S3 API).

The cloud jobs (python/quantlake/cloud/) write plain parquet files here; the
Mac imports them into the local Delta tables (applications/cloud_sync.py).
Only one writer per Delta table, the Mac: the cloud never touches the lake.

Configuration from the environment (.env locally, variables on Railway):
    R2_ENDPOINT (S3 API URL, https://<account>.r2.cloudflarestorage.com)
        or R2_ACCOUNT_ID,
    R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET
or, for tests, QUANTLAKE_REMOTE_DIR=/some/folder (local folder, same layout).
"""
import io
import os

import polars as pl
import pyarrow.fs as pafs

from quantlake import config  # noqa: F401  (loads .env)


def store() -> tuple[pafs.FileSystem, str] | None:
    """(filesystem, base path) or None when nothing is configured."""
    if local := os.getenv("QUANTLAKE_REMOTE_DIR"):
        return pafs.LocalFileSystem(), local.rstrip("/")
    endpoint = os.getenv("R2_ENDPOINT") or (
        f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com" if os.getenv("R2_ACCOUNT_ID") else None
    )
    keys = ("R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET")
    if not endpoint or not all(os.getenv(k) for k in keys):
        return None
    fs = pafs.S3FileSystem(
        access_key=os.environ["R2_ACCESS_KEY_ID"],
        secret_key=os.environ["R2_SECRET_ACCESS_KEY"],
        endpoint_override=endpoint.rstrip("/"),
        region="auto",
    )
    return fs, os.environ["R2_BUCKET"]


def _require() -> tuple[pafs.FileSystem, str]:
    s = store()
    if s is None:
        raise RuntimeError("remote store not configured: set R2_* (or QUANTLAKE_REMOTE_DIR)")
    return s


def write_parquet(df: pl.DataFrame, key: str) -> str:
    fs, base = _require()
    path = f"{base}/{key}"
    if isinstance(fs, pafs.LocalFileSystem):
        fs.create_dir(path.rsplit("/", 1)[0], recursive=True)
    buf = io.BytesIO()
    df.write_parquet(buf)
    with fs.open_output_stream(path) as f:
        f.write(buf.getvalue())
    return path


def list_keys(prefix: str) -> list[str]:
    fs, base = _require()
    sel = pafs.FileSelector(f"{base}/{prefix}", recursive=True, allow_not_found=True)
    return sorted(i.path[len(base) + 1:] for i in fs.get_file_info(sel) if i.type == pafs.FileType.File)


def read_parquet(key: str) -> pl.DataFrame:
    fs, base = _require()
    with fs.open_input_file(f"{base}/{key}") as f:
        return pl.read_parquet(io.BytesIO(f.read()))
