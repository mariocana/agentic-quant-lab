"""One page for the whole lab: a server, a set of tabs.

    Dati            quantlake's tables and charts (its own React app, fe/web)
    COT, Equity     quantlake's desks, Flask apps mounted under /cot and /equity
    Hyperliquid bridge  the deployed connector (Railway), proxied under /desk/
    Laboratorio     the ideas of the research desk and their registry, under /lab/

Everything that was a portal of its own is a tab here: the React shell asks
/api/apps which tabs exist and keeps each one mounted once opened.

The bridge is reached through this server, not by the browser directly:
the desk sits behind a password, and a browser does not show a password prompt
inside a frame from another site. The password is added here, server side, from
quantlake/.env (DESK_URL, DESK_PASSWORD). This server binds 127.0.0.1 only:
whatever reaches it can drive the desk — kill switch, flatten, mode switch —
exactly as the desk's own page can, so it must never be exposed.

Run from quantlake's environment (it has the dashboard's dependencies):
    cd quantlake && poetry run python ../fe/server.py
"""
from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import dotenv_values
from fastapi import Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

FE = Path(__file__).resolve().parent
LAB = FE.parent
WEB_DIST = FE / "web" / "dist"
REGISTRY = LAB / "ricerca" / "registro" / "trials.jsonl"
STAGING = LAB / "ricerca" / "idee"

# quantlake's API (/api/...) with COT and Equity already mounted as tabs
from quantlake.dashboard.server import _mounted, app  # noqa: E402

# ── Hyperliquid bridge, proxied ────────────────────────────────────────────────────
_env = dotenv_values(LAB / "quantlake" / ".env")
DESK_URL = (os.getenv("DESK_URL") or _env.get("DESK_URL") or "").rstrip("/")
_pw = os.getenv("DESK_PASSWORD") or _env.get("DESK_PASSWORD") or ""
_auth = {"Authorization": "Basic " + base64.b64encode(f"desk:{_pw}".encode()).decode()} if _pw else {}
_HOP = {"connection", "keep-alive", "transfer-encoding", "content-encoding", "content-length", "host",
        "authorization", "www-authenticate"}
_client = httpx.AsyncClient(timeout=60.0)


@app.get("/desk")
def desk_root():
    return RedirectResponse("/desk/")


@app.api_route("/desk/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def desk_proxy(path: str, request: Request):
    if not DESK_URL:
        return JSONResponse({"error": "DESK_URL is not set in quantlake/.env"}, status_code=503)
    headers = {k: v for k, v in request.headers.items() if k.lower() not in _HOP} | _auth
    r = await _client.request(request.method, f"{DESK_URL}/{path}", params=request.query_params,
                              content=await request.body(), headers=headers)
    out = {k: v for k, v in r.headers.items() if k.lower() not in _HOP}
    return Response(r.content, status_code=r.status_code, headers=out)


if DESK_URL:
    _mounted.insert(0, {"key": "desk", "label": "Hyperliquid bridge", "path": "/desk/"})


# ── Laboratorio: the research desk's ideas and registry ─────────────────────────
def _registry_rows() -> list[dict]:
    if not REGISTRY.exists():
        return []
    rows = []
    for line in REGISTRY.read_text().splitlines():
        if not line.strip():
            continue
        e = json.loads(line)
        m = e.get("metrics") or {}
        rows.append({"seq": e["seq"], "ts": e["ts"][:16].replace("T", " "), "kind": e["kind"],
                     "idea": e.get("idea") or (e.get("spec") or {}).get("id") or "",
                     "door": e.get("door"), "horizon": e.get("horizon"), "market": e.get("market"),
                     "step": e.get("step"), "eccesso_pp": m.get("eccesso_pp"),
                     "errori_standard": m.get("errori_standard"),
                     "text": e.get("reason") or e.get("title") or e.get("text")})
    return rows


@app.get("/lab/api/registry")
def lab_registry():
    rows = _registry_rows()
    return {"ideas": sum(r["kind"] == "idea" for r in rows),
            "measured": len({r["idea"] for r in rows if r["kind"] == "measure"}),
            "killed": sum(r["kind"] == "killed" for r in rows), "rows": rows}


@app.get("/lab/api/staging")
def lab_staging():
    out = []
    for d in sorted(p for p in STAGING.iterdir() if p.is_dir()) if STAGING.exists() else []:
        stage = "nata"
        for f, s in (("hypothesis.md", "ipotesi"), ("critique.md", "critica"), ("misura.json", "misurata"),
                     ("dossier.md", "dossier"), ("KILLED", "uccisa")):
            if (d / f).exists():
                stage = s
        critique = (d / "critique.md").read_text() if (d / "critique.md").exists() else ""
        misura = json.loads((d / "misura.json").read_text()) if (d / "misura.json").exists() else {}
        out.append({"id": d.name, "stage": stage,
                    "critic": "KILL" if "VERDETTO: KILL" in critique else "GO" if "VERDETTO: GO" in critique else None,
                    "eccesso_pp": misura.get("eccesso_pp"), "errori_standard": misura.get("errori_standard")})
    return {"ideas": out}


@app.get("/lab/")
def lab_page():
    return FileResponse(FE / "lab" / "index.html")


_mounted.append({"key": "lab", "label": "Laboratorio", "path": "/lab/"})

# ── The shell, last: it catches every path nobody else claimed ─────────────────
if WEB_DIST.exists():
    app.mount("/", StaticFiles(directory=str(WEB_DIST), html=True), name="shell")


def main(port: int = 8000) -> None:
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 8000)
