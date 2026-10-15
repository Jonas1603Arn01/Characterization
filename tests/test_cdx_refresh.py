"""Tests für das Neu-Rendern des Bilds aus der bearbeiteten ChemDraw-Datei:
wird die mitgespeicherte .cdx in ChemDraw geändert und gespeichert, meldet
die API das Bild als veraltet (<slot>_stale) und erzeugt es über
POST …/{image|scheme|equation}/refresh neu (Renderer in Tests gemockt)."""
import base64
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import chemdraw_render, clipboard_win, db
from app.main import app

PNG_1x1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)
CDX_BYTES = clipboard_win.CDX_MAGIC + b"\x00" * 16
# Für die App zählt nur die BM-Signatur — Inhalt egal
BMP_RENDERED = b"BM" + b"\x00" * 60


@pytest.fixture()
def client(tmp_path):
    db.init_db(tmp_path / "test.db")
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def mol(client):
    project = client.post("/api/projects", json={"name": "P"}).json()
    return client.post(
        "/api/molecules", json={"project_id": project["id"], "name": "M-1"}
    ).json()


def paste_with_cdx(client, mol, kind, monkeypatch):
    monkeypatch.setattr(clipboard_win, "read_clipboard_image", lambda: PNG_1x1)
    monkeypatch.setattr(clipboard_win, "read_clipboard_cdx", lambda: CDX_BYTES)
    r = client.post(f"/api/molecules/{mol['id']}/{kind}/clipboard")
    assert r.status_code == 200, r.text
    return r.json()


def touch_cdx_newer(data, kind):
    """Simuliert „in ChemDraw bearbeitet und gespeichert“: .cdx-Zeitstempel
    deutlich hinter den des Bilds setzen."""
    img = Path(data[f"{kind}_path"])
    later = img.stat().st_mtime + 5
    os.utime(data[f"{kind}_cdx_path"], (later, later))


@pytest.mark.parametrize("kind", ["image", "scheme", "equation"])
def test_stale_flag_after_cdx_edit(client, mol, monkeypatch, kind):
    data = paste_with_cdx(client, mol, kind, monkeypatch)
    assert data[f"{kind}_stale"] is False  # frisch eingefügt -> aktuell
    touch_cdx_newer(data, kind)
    r = client.get(f"/api/molecules/{mol['id']}")
    assert r.json()[f"{kind}_stale"] is True


@pytest.mark.parametrize("kind", ["image", "scheme", "equation"])
def test_refresh_rerenders_image_and_keeps_cdx(client, mol, monkeypatch, kind):
    data = paste_with_cdx(client, mol, kind, monkeypatch)
    touch_cdx_newer(data, kind)
    rendered_from = []

    def fake_render(path):
        rendered_from.append(Path(path))
        return BMP_RENDERED

    monkeypatch.setattr(chemdraw_render, "render_cdx", fake_render)
    r = client.post(f"/api/molecules/{mol['id']}/{kind}/refresh")
    assert r.status_code == 200, r.text
    fresh = r.json()
    # Neu gerendert aus genau der mitgespeicherten .cdx
    assert rendered_from == [Path(data[f"{kind}_cdx_path"])]
    # Neues Bild ersetzt das alte, .cdx bleibt erhalten, nichts mehr veraltet
    assert fresh[f"{kind}_path"] != data[f"{kind}_path"]
    assert fresh[f"{kind}_path"].endswith(".bmp")
    assert Path(fresh[f"{kind}_path"]).read_bytes() == BMP_RENDERED
    assert not Path(data[f"{kind}_path"]).exists()
    assert fresh[f"{kind}_cdx_path"] == data[f"{kind}_cdx_path"]
    assert Path(fresh[f"{kind}_cdx_path"]).exists()
    assert fresh[f"{kind}_stale"] is False


def test_refresh_without_cdx_conflict(client, mol, monkeypatch):
    monkeypatch.setattr(clipboard_win, "read_clipboard_image", lambda: PNG_1x1)
    client.post(f"/api/molecules/{mol['id']}/image/clipboard")  # ohne CDX
    r = client.post(f"/api/molecules/{mol['id']}/image/refresh")
    assert r.status_code == 409


def test_refresh_render_error_returns_502(client, mol, monkeypatch):
    data = paste_with_cdx(client, mol, "image", monkeypatch)
    # conftest lässt render_cdx standardmäßig fehlschlagen
    r = client.post(f"/api/molecules/{mol['id']}/image/refresh")
    assert r.status_code == 502
    assert "ChemDraw" in r.json()["detail"]
    # Bild und CDX bleiben unangetastet
    assert Path(data["image_path"]).exists()
    assert Path(data["image_cdx_path"]).exists()


def test_missing_files_do_not_flag_stale(client, mol, monkeypatch):
    data = paste_with_cdx(client, mol, "image", monkeypatch)
    Path(data["image_cdx_path"]).unlink()  # .cdx von Hand gelöscht
    r = client.get(f"/api/molecules/{mol['id']}")
    assert r.json()["image_stale"] is False
