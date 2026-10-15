"""Tests für die Versionskennung der Bilder (<slot>_version): Die Oberfläche
hängt sie an die Bild-URL. Sie darf sich nur ändern, wenn sich die Bilddatei
ändert — nicht bei jeder Änderung am Molekül, sonst lädt der Browser die
mehrere MB großen ChemDraw-BMPs ständig neu vom Datenordner. Passt die
Kennung einer Anfrage zum aktuellen Stand, darf der Browser das Bild
dauerhaft behalten."""
import base64
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import clipboard_win, db
from app.main import app

PNG_1x1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


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


def paste(client, mol, monkeypatch, kind="image"):
    monkeypatch.setattr(clipboard_win, "read_clipboard_image", lambda: PNG_1x1)
    r = client.post(f"/api/molecules/{mol['id']}/{kind}/clipboard")
    assert r.status_code == 200, r.text
    return r.json()


def test_ohne_bild_keine_version(client, mol):
    data = client.get(f"/api/molecules/{mol['id']}").json()
    for kind in ("image", "scheme", "equation"):
        assert data[f"{kind}_version"] is None


@pytest.mark.parametrize("kind", ["image", "scheme", "equation"])
def test_version_bleibt_bei_aenderungen_am_molekuel(client, mol, monkeypatch, kind):
    data = paste(client, mol, monkeypatch, kind)
    version = data[f"{kind}_version"]
    assert version
    for patch in ({"color": "farblos"}, {"literature_known": True}, {"name": "M-2"}):
        r = client.patch(f"/api/molecules/{mol['id']}", json=patch)
        assert r.status_code == 200, r.text
        assert r.json()[f"{kind}_version"] == version
    # Dieselbe Kennung steht auch in der Projektliste
    listed = client.get("/api/projects").json()[0]["molecules"][0]
    assert listed[f"{kind}_version"] == version


def test_neues_bild_bekommt_neue_version(client, mol, monkeypatch):
    first = paste(client, mol, monkeypatch)
    second = paste(client, mol, monkeypatch)  # gleicher Inhalt, neue Datei
    assert second["image_version"] != first["image_version"]


def test_von_hand_geaenderte_datei_bekommt_neue_version(client, mol, monkeypatch):
    data = paste(client, mol, monkeypatch)
    img = Path(data["image_path"])
    later = img.stat().st_mtime + 10
    os.utime(img, (later, later))
    fresh = client.get(f"/api/molecules/{mol['id']}").json()
    assert fresh["image_version"] != data["image_version"]


def test_passende_version_darf_im_browser_bleiben(client, mol, monkeypatch):
    data = paste(client, mol, monkeypatch)
    r = client.get(f"/api/molecules/{mol['id']}/image", params={"v": data["image_version"]})
    assert r.status_code == 200
    assert r.content == PNG_1x1
    assert "immutable" in r.headers["cache-control"]


@pytest.mark.parametrize("params", [{}, {"v": "veraltet"}])
def test_ohne_passende_version_kein_dauerhaftes_behalten(client, mol, monkeypatch, params):
    paste(client, mol, monkeypatch)
    r = client.get(f"/api/molecules/{mol['id']}/image", params=params)
    assert r.status_code == 200
    assert r.content == PNG_1x1
    assert "immutable" not in r.headers.get("cache-control", "")
