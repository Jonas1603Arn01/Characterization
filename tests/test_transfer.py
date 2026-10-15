"""Tests für die Weitergabe: Transferdatei erstellen und auf einem
(simulierten) anderen PC einlesen."""
import base64
import shutil
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


def test_export_creates_zip_with_manifest(client, tmp_path):
    client.post("/api/projects", json={"name": "P"})
    out = tmp_path / "out"
    out.mkdir()
    r = client.post("/api/transfer/export", json={"target_dir": str(out)})
    assert r.status_code == 200, r.text
    res = r.json()
    assert res["projects"] == 1 and res["molecules"] == 0
    with zipfile.ZipFile(res["file"]) as zf:
        names = zf.namelist()
        assert "app.db" in names
        assert "transfer.json" in names


def test_export_rejects_missing_target(client):
    r = client.post("/api/transfer/export", json={"target_dir": "C:\\gibt\\es\\nicht"})
    assert r.status_code == 422


def test_roundtrip_to_other_pc(tmp_path):
    """Export auf PC A, Einlesen auf PC B (eigener Datenordner): Daten kommen an,
    App-eigene Bilder werden dort gefunden (sie stehen nur mit Dateinamen in
    der DB — ein Umschreiben ist nicht mehr nötig)."""
    src_dir = tmp_path / "pc-a"
    dst_dir = tmp_path / "pc-b"
    out = tmp_path / "out"
    out.mkdir()

    db.init_db(src_dir / "test.db")
    with TestClient(app) as c:
        p = c.post("/api/projects", json={"name": "Projekt"}).json()
        mol = c.post("/api/molecules", json={"project_id": p["id"], "name": "M-1"}).json()
        r = c.post(f"/api/molecules/{mol['id']}/image", content=PNG_1x1)
        assert r.status_code == 200, r.text
        transfer = c.post("/api/transfer/export", json={"target_dir": str(out)}).json()
    assert transfer["projects"] == 1 and transfer["molecules"] == 1

    # "Anderer PC": der images-Ordner von PC A existiert dort nicht
    shutil.rmtree(src_dir / "images")
    db.init_db(dst_dir / "test.db")
    with TestClient(app) as c:
        assert c.get("/api/projects").json() == []
        r = c.post("/api/transfer/import", json={"path": transfer["file"]})
        assert r.status_code == 200, r.text
        res = r.json()
        assert res["projects"] == 1 and res["molecules"] == 1
        assert res["rewritten"] == 0  # relative Bildnamen brauchen kein Umschreiben
        assert res["created"] is not None

        mols = c.get("/api/projects").json()[0]["molecules"]
        assert mols[0]["name"] == "M-1"
        assert mols[0]["image_exists"] is True
        assert Path(mols[0]["image_path"]).parent == (dst_dir / "images").resolve()


def test_import_backs_up_current_state(client, tmp_path):
    client.post("/api/projects", json={"name": "Vorher"})
    out = tmp_path / "out"
    out.mkdir()
    file = client.post("/api/transfer/export", json={"target_dir": str(out)}).json()["file"]
    before = len(client.get("/api/backups").json())
    r = client.post("/api/transfer/import", json={"path": file})
    assert r.status_code == 200, r.text
    assert len(client.get("/api/backups").json()) == before + 1


def test_password_protected_roundtrip(client, tmp_path):
    """Mit Passwort exportieren: Einlesen ohne bzw. mit falschem Passwort wird
    mit 401 abgelehnt (und ändert nichts), mit richtigem klappt es."""
    client.post("/api/projects", json={"name": "Geheim"})
    out = tmp_path / "out"
    out.mkdir()
    r = client.post("/api/transfer/export",
                    json={"target_dir": str(out), "password": "sehr geheim"})
    assert r.status_code == 200, r.text
    assert r.json()["encrypted"] is True
    file = r.json()["file"]

    # Inhalt ist wirklich verschlüsselt: Lesen ohne Passwort schlägt fehl
    with zipfile.ZipFile(file) as zf:
        assert all(info.flag_bits & 0x1 for info in zf.infolist())
        with pytest.raises(RuntimeError):
            zf.read("app.db")

    client.post("/api/projects", json={"name": "Neuer Stand"})
    backups_before = len(client.get("/api/backups").json())

    r = client.post("/api/transfer/import", json={"path": file})
    assert r.status_code == 401  # Passwort nötig
    r = client.post("/api/transfer/import", json={"path": file, "password": "falsch"})
    assert r.status_code == 401  # falsches Passwort
    # Abgelehnte Versuche haben nichts angefasst: Stand und Backups unverändert
    names = [p["name"] for p in client.get("/api/projects").json()]
    assert names == ["Geheim", "Neuer Stand"]
    assert len(client.get("/api/backups").json()) == backups_before

    r = client.post("/api/transfer/import", json={"path": file, "password": "sehr geheim"})
    assert r.status_code == 200, r.text
    names = [p["name"] for p in client.get("/api/projects").json()]
    assert names == ["Geheim"]


def test_export_without_password_stays_plain(client, tmp_path):
    """Ohne (bzw. mit leerem) Passwort bleibt die Transferdatei unverschlüsselt
    und ohne Passwort einlesbar."""
    client.post("/api/projects", json={"name": "Offen"})
    out = tmp_path / "out"
    out.mkdir()
    r = client.post("/api/transfer/export", json={"target_dir": str(out), "password": ""})
    assert r.json()["encrypted"] is False
    with zipfile.ZipFile(r.json()["file"]) as zf:
        assert not any(info.flag_bits & 0x1 for info in zf.infolist())
    r = client.post("/api/transfer/import", json={"path": r.json()["file"]})
    assert r.status_code == 200, r.text


def test_named_export_and_import(client, tmp_path):
    """Eine Bezeichnung wird Teil des Dateinamens (bereinigt) und beim
    Einlesen wieder mitgeliefert — so bleibt zuordenbar, was geladen wird."""
    client.post("/api/projects", json={"name": "P"})
    out = tmp_path / "out"
    out.mkdir()
    r = client.post("/api/transfer/export",
                    json={"target_dir": str(out), "name": "Stand Juli: für Chef"})
    assert r.status_code == 200, r.text
    res = r.json()
    assert res["name"] == "Stand Juli: für Chef"
    # Ungültige Dateinamens-Zeichen (":") werden ersetzt, der Rest bleibt
    assert Path(res["file"]).name.endswith("-Stand Juli_ für Chef.zip")

    r = client.post("/api/transfer/import", json={"path": res["file"]})
    assert r.status_code == 200, r.text
    assert r.json()["name"] == "Stand Juli: für Chef"


def test_import_backup_is_tagged_and_survives_rotation(client, tmp_path):
    """Das automatische Backup vor einem Import ist als „vor Import“
    gekennzeichnet, wiederherstellbar und wird nicht von der normalen
    10er-Rotation verdrängt."""
    client.post("/api/projects", json={"name": "Alt"})
    out = tmp_path / "out"
    out.mkdir()
    file = client.post("/api/transfer/export", json={"target_dir": str(out)}).json()["file"]
    client.post("/api/projects", json={"name": "Zusatz"})

    assert client.post("/api/transfer/import", json={"path": file}).status_code == 200
    tagged = [b for b in client.get("/api/backups").json() if b["pre_import"]]
    assert len(tagged) == 1
    assert "-import" in tagged[0]["name"]

    # Normale Backups über das Rotationslimit hinaus erzeugen —
    # das Import-Backup bleibt stehen
    for _ in range(db.MAX_BACKUPS + 2):
        assert client.post("/api/backups").status_code == 201
    backups = client.get("/api/backups").json()
    assert sum(1 for b in backups if not b["pre_import"]) == db.MAX_BACKUPS
    assert any(b["name"] == tagged[0]["name"] for b in backups)

    # Rückweg: Wiederherstellen bringt den Stand von vor dem Import zurück
    r = client.post(f"/api/backups/{tagged[0]['name']}/restore")
    assert r.status_code == 200, r.text
    names = [p["name"] for p in client.get("/api/projects").json()]
    assert names == ["Alt", "Zusatz"]


def test_import_rejects_invalid_files(client, tmp_path):
    r = client.post("/api/transfer/import", json={"path": str(tmp_path / "fehlt.zip")})
    assert r.status_code == 404

    bogus = tmp_path / "kein-zip.zip"
    bogus.write_bytes(b"das ist kein zip")
    r = client.post("/api/transfer/import", json={"path": str(bogus)})
    assert r.status_code == 422

    ohne_db = tmp_path / "ohne-db.zip"
    with zipfile.ZipFile(ohne_db, "w") as zf:
        zf.writestr("readme.txt", "hi")
    r = client.post("/api/transfer/import", json={"path": str(ohne_db)})
    assert r.status_code == 422
