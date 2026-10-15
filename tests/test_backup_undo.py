"""Tests für Backups (erstellen, auflisten, wiederherstellen) und den Undo-Stapel."""
import base64

import pytest
from fastapi.testclient import TestClient

from app import db
from app.main import app

# Minimales gültiges 1×1-PNG (wie in test_api.py)
PNG_1x1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


@pytest.fixture()
def client(tmp_path):
    db.init_db(tmp_path / "test.db")
    with TestClient(app) as c:
        yield c


def project_names(client):
    return [p["name"] for p in client.get("/api/projects").json()]


def test_backup_create_and_list(client):
    r = client.post("/api/backups")
    assert r.status_code == 201
    name = r.json()["name"]
    listed = client.get("/api/backups").json()
    assert any(b["name"] == name for b in listed)
    assert listed[0]["created"] is not None  # Zeitstempel aus dem Dateinamen


def test_backup_restore_returns_old_state(client):
    client.post("/api/projects", json={"name": "Alt"})
    backup = client.post("/api/backups").json()["name"]
    client.post("/api/projects", json={"name": "Neu"})
    assert project_names(client) == ["Alt", "Neu"]

    r = client.post(f"/api/backups/{backup}/restore")
    assert r.status_code == 200
    assert project_names(client) == ["Alt"]


def test_backup_includes_and_restores_images(client, tmp_path):
    project = client.post("/api/projects", json={"name": "P"}).json()
    mol = client.post(
        "/api/molecules", json={"project_id": project["id"], "name": "M-1"}
    ).json()
    r = client.post(f"/api/molecules/{mol['id']}/image", content=PNG_1x1)
    assert r.status_code == 200, r.text
    images = list((tmp_path / "images").iterdir())
    assert len(images) == 1

    backup = client.post("/api/backups").json()["name"]
    assert backup.endswith(".zip")

    images[0].unlink()  # Bilddatei "verloren"
    r = client.post(f"/api/backups/{backup}/restore")
    assert r.status_code == 200
    assert images[0].read_bytes() == PNG_1x1


def test_restore_invalid_names_rejected(client):
    assert client.post("/api/backups/..%5C..%5Cboese.db/restore").status_code in (404, 422)
    assert client.post("/api/backups/app-99999999-999999.db/restore").status_code == 404


def test_undo_stack(client):
    assert client.get("/api/undo").json()["available"] == 0

    client.post("/api/projects", json={"name": "P1"})
    client.post("/api/projects", json={"name": "P2"})
    assert client.get("/api/undo").json()["available"] == 2

    client.post("/api/undo")
    assert project_names(client) == ["P1"]
    client.post("/api/undo")
    assert project_names(client) == []
    # Stapel leer -> 409
    assert client.post("/api/undo").status_code == 409


def test_failed_action_consumes_no_undo_step(client):
    client.post("/api/projects", json={"name": "P1"})
    client.post("/api/projects", json={"name": "  "})   # 422, ändert nichts
    client.post("/api/projects", json={"name": "P1"})   # 409 Duplikat, ändert nichts
    assert client.get("/api/undo").json()["available"] == 1

    client.post("/api/undo")
    assert project_names(client) == []


def test_undo_reverts_delete_and_restore(client):
    p = client.post("/api/projects", json={"name": "Wichtig"}).json()
    client.post("/api/molecules", json={"project_id": p["id"], "name": "M-1"})
    client.delete(f"/api/projects/{p['id']}")
    assert project_names(client) == []

    client.post("/api/undo")  # Löschung rückgängig
    projects = client.get("/api/projects").json()
    assert [x["name"] for x in projects] == ["Wichtig"]
    assert [m["name"] for m in projects[0]["molecules"]] == ["M-1"]

    # Auch das Wiederherstellen eines Backups ist rückgängig machbar
    backup = client.post("/api/backups").json()["name"]
    client.post("/api/projects", json={"name": "Danach"})
    client.post(f"/api/backups/{backup}/restore")
    assert project_names(client) == ["Wichtig"]
    client.post("/api/undo")
    # Projekte erscheinen in Erstellreihenfolge (per Drag & Drop änderbar)
    assert project_names(client) == ["Wichtig", "Danach"]
