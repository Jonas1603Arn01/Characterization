"""Tests für das Aufräumen verwaister Bilder: vor jedem Backup und
Transfer-Export werden Dateien im images-Ordner gelöscht, die weder von der
aktuellen Datenbank noch von einem Undo-Schnappschuss referenziert werden."""
import base64
import zipfile
from pathlib import Path

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


def make_mol_with_image(client) -> dict:
    p = client.post("/api/projects", json={"name": "P"}).json()
    mol = client.post("/api/molecules", json={"project_id": p["id"], "name": "M-1"}).json()
    r = client.post(f"/api/molecules/{mol['id']}/image", content=PNG_1x1)
    assert r.status_code == 200, r.text
    return r.json()


def test_backup_removes_orphan_keeps_referenced(client, tmp_path):
    mol = make_mol_with_image(client)
    orphan = tmp_path / "images" / "mol-99-verwaist.png"
    orphan.write_bytes(PNG_1x1)

    assert client.post("/api/backups").status_code == 201
    assert not orphan.exists()
    assert Path(mol["image_path"]).exists()


def test_undo_referenced_image_survives_cleanup(client, tmp_path):
    """Nach dem Löschen eines Moleküls referenziert nur noch der
    Undo-Schnappschuss dessen Bild — das Aufräumen muss es stehen lassen,
    damit Strg+Z das Molekül samt Bild zurückbringt."""
    mol = make_mol_with_image(client)
    img = Path(mol["image_path"])
    assert client.delete(f"/api/molecules/{mol['id']}").status_code == 204

    assert client.post("/api/backups").status_code == 201
    assert img.exists()  # von einem Undo-Schnappschuss referenziert

    assert client.post("/api/undo").status_code == 200
    mols = client.get("/api/projects").json()[0]["molecules"]
    assert mols[0]["image_exists"] is True


def test_transfer_export_excludes_orphans(client, tmp_path):
    make_mol_with_image(client)
    orphan = tmp_path / "images" / "verwaist.png"
    orphan.write_bytes(PNG_1x1)
    out = tmp_path / "out"
    out.mkdir()

    res = client.post("/api/transfer/export", json={"target_dir": str(out)}).json()
    with zipfile.ZipFile(res["file"]) as zf:
        assert "images/verwaist.png" not in zf.namelist()
        assert any(n.startswith("images/mol-") for n in zf.namelist())
    assert not orphan.exists()


def test_cleanup_skips_when_snapshot_unreadable(client, tmp_path):
    """Ist ein Undo-Schnappschuss nicht lesbar, wird im Zweifel gar nichts
    gelöscht — lieber ein paar Waisen behalten als ein gebrauchtes Bild."""
    make_mol_with_image(client)
    orphan = tmp_path / "images" / "verwaist.png"
    orphan.write_bytes(PNG_1x1)
    (tmp_path / "undo" / "undo-99999999.db").write_bytes(b"kaputt")

    assert db.cleanup_orphan_images() == 0
    assert orphan.exists()
