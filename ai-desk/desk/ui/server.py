"""HTTP layer over DeskService. Local only: binds 127.0.0.1, no auth."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from desk.ui.service import DeskService

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


def main(host: str = "127.0.0.1", port: int = 8765):
    import uvicorn
    uvicorn.run("desk.ui.server:app", host=host, port=port, log_level="info")
