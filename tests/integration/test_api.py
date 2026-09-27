"""API automation (control-plane critical paths): health, models, projects, shots, job stream."""

from fastapi.testclient import TestClient

from apps.api.src.main import app

client = TestClient(app)


def test_health_reports_live_state():
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["ram_total_mb"] > 0
    assert body["models_locked"] >= 7


def test_models_list_matches_lock():
    res = client.get("/models")
    assert res.status_code == 200
    ids = {m["id"] for m in res.json()}
    assert "image.bonsai.flux2-klein.q2k" in ids or any("bonsai" in i for i in ids)


def test_projects_and_shots():
    res = client.get("/projects")
    assert res.status_code == 200
    assert "minifilm_spark7" in res.json()
    res = client.get("/projects/minifilm_spark7/shots")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    res = client.get("/projects/does_not_exist/shots")
    assert res.status_code == 404


def test_project_create_conflict_or_created(tmp_path=None):
    res = client.post("/projects", json={"name": "X", "project_id": "minifilm_spark7"})
    assert res.status_code == 409


def test_jobs_stream_snapshot():
    with client.websocket_connect("/ws/jobs?project=minifilm_spark7") as ws:
        payload = ws.receive_json()
        assert payload["project_id"] == "minifilm_spark7"
        assert isinstance(payload["jobs"], list)
