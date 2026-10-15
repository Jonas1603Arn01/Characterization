"""Tests für den /open-Endpoint und die Sprachumschaltung (X-Lang-Header)."""
import pytest
from fastapi.testclient import TestClient

from app import db
from app.main import app


@pytest.fixture()
def client(tmp_path):
    db.init_db(tmp_path / "test.db")
    with TestClient(app) as c:
        yield c


def test_open_linked_path(client, tmp_path, monkeypatch):
    opened = []
    monkeypatch.setattr("os.startfile", lambda p: opened.append(p), raising=False)
    f = tmp_path / "doc.docx"
    f.write_text("x")
    # Pfad erst in der App verlinken — nur dann darf /open ihn öffnen
    project = client.post("/api/projects", json={"name": "P"}).json()
    mol = client.post(
        "/api/molecules", json={"project_id": project["id"], "name": "M"}
    ).json()
    e = next(x for x in mol["entries"] if x["type_code"] == "procedure")
    client.patch(f"/api/entries/{e['id']}", json={"file_path": str(f)})

    r = client.post("/api/open", json={"path": str(f)})
    assert r.status_code == 200
    assert opened == [str(f)]


def test_open_reveal_opens_containing_folder(client, tmp_path, monkeypatch):
    """Klick auf einen verlinkten Pfad soll den Ordner zeigen, nicht die Datei
    starten — verlinkte Ordner bleiben dabei sie selbst."""
    opened = []
    monkeypatch.setattr("os.startfile", lambda p: opened.append(p), raising=False)
    folder = tmp_path / "daten"
    folder.mkdir()
    f = folder / "doc.docx"
    f.write_text("x")
    project = client.post("/api/projects", json={"name": "P"}).json()
    mol = client.post(
        "/api/molecules", json={"project_id": project["id"], "name": "M"}
    ).json()
    e = next(x for x in mol["entries"] if x["type_code"] == "procedure")
    client.patch(f"/api/entries/{e['id']}", json={"file_path": str(f)})
    nmr = next(x for x in mol["entries"] if x["type_code"] == "nmr_1h")
    client.patch(f"/api/entries/{nmr['id']}", json={"folder_path": str(folder)})

    assert client.post("/api/open", json={"path": str(f), "reveal": True}).status_code == 200
    assert opened == [str(folder)]

    assert client.post(
        "/api/open", json={"path": str(folder), "reveal": True}
    ).status_code == 200
    assert opened == [str(folder), str(folder)]


def test_open_unlinked_path_forbidden(client, tmp_path, monkeypatch):
    """Ein existierender, aber nicht in der App verlinkter Pfad darf nicht
    geöffnet werden (sonst wäre /open ein Startbefehl für beliebige Dateien)."""
    opened = []
    monkeypatch.setattr("os.startfile", lambda p: opened.append(p), raising=False)
    f = tmp_path / "fremd.exe"
    f.write_text("x")
    r = client.post("/api/open", json={"path": str(f)})
    assert r.status_code == 403
    assert opened == []


def test_open_dead_path_404(client, tmp_path):
    # Ohne Header gilt Englisch als Standardsprache
    r = client.post("/api/open", json={"path": str(tmp_path / "weg.docx")})
    assert r.status_code == 404
    assert "no longer exists" in r.json()["detail"]

    r = client.post(
        "/api/open", json={"path": str(tmp_path / "weg.docx")}, headers={"X-Lang": "de"}
    )
    assert "existiert nicht mehr" in r.json()["detail"]


def test_error_messages_localized(client):
    r = client.post("/api/projects", json={"name": "  "})
    assert r.json()["detail"] == "Project name must not be empty"

    r = client.post("/api/projects", json={"name": "  "}, headers={"X-Lang": "de"})
    assert r.json()["detail"] == "Projektname darf nicht leer sein"


def test_datatypes_are_bilingual(client):
    types = {t["code"]: t for t in client.get("/api/datatypes").json()}
    assert types["nmr_1h"]["label"] == {"de": "¹H-NMR", "en": "¹H NMR"}
    assert types["nmr_1h"]["fields"][0]["label"]["en"] == "Data folder"


def test_export_localized(client, tmp_path):
    project = client.post("/api/projects", json={"name": "P"}).json()
    mol = client.post(
        "/api/molecules",
        json={"project_id": project["id"], "name": "M", "smiles": "c1ccccc1"},
    ).json()
    e = next(x for x in mol["entries"] if x["type_code"] == "procedure")
    f = tmp_path / "v.docx"
    f.write_text("x")
    client.patch(f"/api/entries/{e['id']}", json={"file_path": str(f)})

    target = tmp_path / "export"
    target.mkdir()
    r = client.post(f"/api/molecules/{mol['id']}/export",
                    json={"target_dir": str(target)}, headers={"X-Lang": "de"})
    assert r.status_code == 200
    base = target / "P" / "M"
    assert (base / "Versuchsvorschrift" / "v.docx").is_file()  # deutscher Ordnername
    info = (base / "Info.txt").read_text(encoding="utf-8")
    assert "Exakte Masse" in info
