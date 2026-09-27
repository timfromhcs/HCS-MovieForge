"""MovieForge control-plane API: health, models, projects, and a job event stream.

Thin HTTP/WS layer over the headless managers. The UI is built on top of these
endpoints; every endpoint reads real manager state (no hard-coded labels).
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from engine.model_manager.manager import ModelManager  # noqa: E402
from engine.project_manager.manager import ProjectManager  # noqa: E402
from packages.project_format.src.db import ProjectDB  # noqa: E402
from packages.telemetry.src.probe import probe_hardware  # noqa: E402

app = FastAPI(title="MovieForge Control Plane", version="0.1.0")


class ProjectCreate(BaseModel):
    name: str
    project_id: str
    description: str = ""


@app.get("/health")
def health() -> dict:
    """Live readiness: hardware profile summary + model-lock presence."""
    profile = probe_hardware()
    lock = ModelManager().get_lock()
    return {
        "status": "ok",
        "os": profile.os_name,
        "vulkan": profile.vulkan_device.device_name,
        "ram_total_mb": profile.system_memory.total_ram_mb,
        "models_locked": len(lock.get("models", {})),
    }


@app.get("/models")
def models() -> list[dict]:
    """Lists manifests with installation state from the real lock file."""
    mgr = ModelManager()
    installed = mgr.get_lock().get("models", {})
    return [{**m, "installed": m.get("id") in installed} for m in mgr.list_manifests()]


@app.get("/projects")
def projects() -> list[str]:
    """Lists project IDs present on disk."""
    root = ProjectManager().projects_root
    return sorted(p.name for p in root.iterdir() if p.is_dir() and (p / "manifest.json").exists())


@app.post("/projects", status_code=201)
def project_create(body: ProjectCreate) -> dict:
    """Creates a canonical project directory + WAL database."""
    try:
        path = ProjectManager().create_project(name=body.name, project_id=body.project_id)
    except FileExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"project_id": body.project_id, "path": str(path)}


@app.get("/projects/{project_id}/shots")
def project_shots(project_id: str) -> list[dict]:
    """Reads shot rows for storyboards/timelines from the project database."""
    db_path = ProjectManager().projects_root / project_id / "movieforge.db"
    if not db_path.exists():
        raise HTTPException(status_code=404, detail="unknown project")
    db = ProjectDB(db_path)
    with db.get_connection() as conn:
        rows = conn.execute(
            "SELECT shot_id, scene_id, shot_number, camera_prompt, status FROM shots ORDER BY shot_number ASC"
        ).fetchall()
    return [dict(r) for r in rows]


@app.websocket("/ws/jobs")
async def jobs_stream(websocket: WebSocket) -> None:
    """Pushes project job-state snapshots (bounded: closes on client disconnect)."""
    await websocket.accept()
    project_id = websocket.query_params.get("project", "")
    db_path = ProjectManager().projects_root / project_id / "movieforge.db" if project_id else None
    try:
        while True:
            payload: dict = {"project_id": project_id, "jobs": []}
            if db_path is not None and db_path.exists():
                db = ProjectDB(db_path)
                with db.get_connection() as conn:
                    rows = conn.execute(
                        "SELECT job_id, type, status, updated_at FROM jobs ORDER BY updated_at DESC LIMIT 50"
                    ).fetchall()
                payload["jobs"] = [dict(r) for r in rows]
            await websocket.send_json(payload)
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        pass
