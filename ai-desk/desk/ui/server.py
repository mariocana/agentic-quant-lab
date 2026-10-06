"""HTTP layer over DeskService. Local only: binds 127.0.0.1, no auth."""
from __future__ import annotations

from pathlib import Path

import logging

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from desk.ui.service import DeskService

log = logging.getLogger(__name__)
STATIC = Path(__file__).parent / "static"
app = FastAPI(title="ai-desk")
svc: DeskService | None = None


def service() -> DeskService:
    global svc
    if svc is None:
        svc = DeskService()
    return svc


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/state")
def state():
    return service().state()


@app.get("/api/equity")
def equity():
    return service().equity_series()


@app.get("/api/cycle")
def cycle():
    return service().last_cycle_detail()


@app.get("/api/journal")
def journal(kind: str | None = None, last: int = 50):
    return service().journal(kind, last)


@app.get("/api/universe")
def universe():
    return service().universe()


@app.get("/api/logs")
def logs(last: int = 200):
    return list(service().logs)[-last:]


@app.get("/api/limits")
def limits():
    return service().limits_form()


class LimitsBody(BaseModel):
    values: dict[str, float]


@app.put("/api/limits")
def put_limits(body: LimitsBody):
    try:
        service().save_limits(body.values)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"ok": True}


class RunBody(BaseModel):
    dry_run: bool = False


@app.post("/api/run")
def run(body: RunBody):
    s = service()
    if s.running:
        raise HTTPException(409, "a cycle is already running")
    s.run_async(dry_run=body.dry_run)
    return {"started": True}


class KillBody(BaseModel):
    on: bool


@app.post("/api/kill")
def kill(body: KillBody):
    service().kill(body.on)
    return {"ok": True}


@app.post("/api/unlock")
def unlock():
    service().unlock()
    return {"ok": True}


@app.post("/api/flatten")
def flatten():
    return {"fills": service().flatten()}


class ResetBody(BaseModel):
    starting_equity: float = 10_000.0


@app.post("/api/paper/reset")
def reset(body: ResetBody):
    try:
        service().reset_paper(body.starting_equity)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"ok": True}


class SettingsBody(BaseModel):
    mode: str | None = None
    confirm: str | None = None
    schedule_enabled: bool | None = None
    schedule_time_utc: str | None = None
    snapshot_minutes: int | None = None


@app.put("/api/settings")
def put_settings(body: SettingsBody):
    try:
        return service().update_ui_settings({k: v for k, v in body.model_dump().items() if v is not None})
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.exception_handler(Exception)
async def on_error(_, exc):
    return JSONResponse(status_code=500, content={"error": f"{type(exc).__name__}: {exc}"})


def preflight(root: Path | None = None) -> None:
    """Build step for a project without a bundler: compile every module and parse the
    dashboard's script before the port opens.

    A syntax error in Python would otherwise surface as a 500 on the first request,
    and one in the dashboard as a blank page with a working-looking server. Both have
    happened; neither should cost a debugging session.
    """
    import compileall
    import re
    import shutil
    import subprocess
    import tempfile

    root = root or Path(__file__).resolve().parent.parent
    if not compileall.compile_dir(str(root), quiet=2, force=True):
        raise SystemExit("preflight failed: a Python module does not compile (see above)")

    page = root / "ui" / "static" / "index.html"
    html = page.read_text()
    scripts = re.findall(r"<script>(.*?)</script>", html, re.S)
    node = shutil.which("node")
    if not scripts:
        raise SystemExit(f"preflight failed: no script found in {page}")
    if node:
        for i, js in enumerate(scripts):
            with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
                f.write(js)
                tmp = f.name
            r = subprocess.run([node, "--check", tmp], capture_output=True, text=True)
            Path(tmp).unlink(missing_ok=True)
            if r.returncode:
                raise SystemExit(f"preflight failed: {page} script #{i + 1}\n{r.stderr.strip()}")
        checked = f"dashboard script parsed ({Path(node).name})"
    else:
        checked = "dashboard script NOT parsed (node not installed)"
    n = len(list(root.rglob("*.py")))
    log.info("preflight ok: %d python files compiled, %s", n, checked)


def main(host: str = "127.0.0.1", port: int = 8765, reload: bool = False, skip_preflight: bool = False):
    import uvicorn
    if not skip_preflight:
        preflight()
    if reload:
        log.warning("--reload is for development: the desk restarts on every edit, "
                    "which can interrupt a running cycle. Never use it on a live account.")
    uvicorn.run("desk.ui.server:app", host=host, port=port, log_level="info",
                reload=reload, reload_dirs=[str(Path(__file__).resolve().parent.parent)] if reload else None)
