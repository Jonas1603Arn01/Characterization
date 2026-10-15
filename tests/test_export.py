"""Tests für den Molekül-Export."""
import pytest
from fastapi.testclient import TestClient

from app import db
from app.main import app


@pytest.fixture()
def client(tmp_path):
    db.init_db(tmp_path / "test.db")
    with TestClient(app) as c:
        yield c


def test_export_copies_linked_data_and_warns_on_dead_paths(client, tmp_path):
    project = client.post("/api/projects", json={"name": "Projekt: A/B"}).json()
    mol = client.post(
        "/api/molecules",
        json={"project_id": project["id"], "name": "M-1", "smiles": "c1ccccc1"},
    ).json()
    entries = {e["type_code"]: e for e in mol["entries"]}

    # Quelldaten anlegen
    src = tmp_path / "quellen"
    src.mkdir()
    (src / "vorschrift.docx").write_text("v")
    nmr = src / "nmr" / "10"
    nmr.mkdir(parents=True)
    (nmr / "fid").write_text("fid")
    (src / "spektrum.mnova").write_text("m")
    (src / "spektrum.svg").write_text("<svg/>")
    img = src / "struktur.png"
    img.write_bytes(b"\x89PNG")
    scheme = src / "reaktion.png"
    scheme.write_bytes(b"\x89PNG")
    equation = src / "gleichung.png"
    equation.write_bytes(b"\x89PNG")

    client.patch(f"/api/entries/{entries['procedure']['id']}",
                 json={"file_path": str(src / "vorschrift.docx")})
    client.patch(f"/api/entries/{entries['nmr_1h']['id']}",
                 json={"folder_path": str(nmr), "file_path": str(src / "spektrum.mnova"),
                       "svg_path": str(src / "spektrum.svg")})
    client.post(f"/api/entries/{entries['nmr_1h']['id']}/notes", json={"text": "7.26 ppm"})
    client.patch(f"/api/entries/{entries['ir']['id']}",
                 json={"file_path": str(src / "geloescht.pdf")})  # toter Pfad
    client.patch(f"/api/entries/{entries['mp']['id']}", json={"mp_value": 80.1})
    client.patch(f"/api/molecules/{mol['id']}",
                 json={"image_path": str(img), "scheme_path": str(scheme),
                       "equation_path": str(equation)})

    target = tmp_path / "export"
    target.mkdir()
    r = client.post(f"/api/molecules/{mol['id']}/export",
                    json={"target_dir": str(target)})
    assert r.status_code == 200, r.text
    result = r.json()

    # <Projekt>/<Molekül>/, Methoden als Unterordner darin (Standardsprache: Englisch)
    base = target / "Projekt_ A_B" / "M-1"
    assert (base / "Procedure" / "vorschrift.docx").is_file()
    assert (base / "¹H NMR" / "spektrum.mnova").is_file()
    assert (base / "¹H NMR" / "spektrum.svg").is_file()
    assert (base / "¹H NMR" / "10" / "fid").is_file()  # ganzer Mess-Ordner kopiert
    assert (base / "¹H NMR" / "Notes.txt").read_text(encoding="utf-8") == "7.26 ppm"
    assert (base / "Structure.png").is_file()
    assert (base / "Reaction scheme.png").is_file()
    assert (base / "Reaction equation.png").is_file()

    info = (base / "Info.txt").read_text(encoding="utf-8")
    assert "C6H6" in info
    assert "7.26 ppm" in info
    assert "80.1 °C" in info

    assert len(result["warnings"]) == 1
    assert "geloescht.pdf" in result["warnings"][0]
    # IR-Ordner wurde nicht angelegt (nur toter Pfad)
    assert not (base / "IR spectrum").exists()


def test_export_copies_literature_si(client, tmp_path):
    project = client.post("/api/projects", json={"name": "P"}).json()
    mol = client.post("/api/molecules", json={"project_id": project["id"], "name": "M"}).json()
    si = tmp_path / "jacs_si_001.pdf"
    si.write_bytes(b"%PDF-1.4")
    client.patch(f"/api/molecules/{mol['id']}",
                 json={"literature_known": True, "doi": "10.1021/x", "si_path": str(si)})

    target = tmp_path / "export"
    target.mkdir()
    r = client.post(f"/api/molecules/{mol['id']}/export", json={"target_dir": str(target)})
    assert r.status_code == 200, r.text
    base = target / "P" / "M"
    # SI liegt direkt im Molekülordner, erkennbar am Präfix
    assert (base / "SI - jacs_si_001.pdf").read_bytes() == b"%PDF-1.4"
    assert "SI - jacs_si_001.pdf" in r.json()["exported"]
    assert r.json()["warnings"] == []
    info = (base / "Info.txt").read_text(encoding="utf-8")
    assert "known compound — DOI: 10.1021/x" in info
    assert "jacs_si_001.pdf" in info

    # Verschwundene SI -> Warnung statt Abbruch
    si.unlink()
    target2 = tmp_path / "export2"
    target2.mkdir()
    r = client.post(f"/api/molecules/{mol['id']}/export", json={"target_dir": str(target2)})
    assert r.status_code == 200
    assert len(r.json()["warnings"]) == 1
    assert "jacs_si_001.pdf" in r.json()["warnings"][0]
    assert not (target2 / "P" / "M" / "SI - jacs_si_001.pdf").exists()


def test_export_rejects_missing_target(client, tmp_path):
    project = client.post("/api/projects", json={"name": "P"}).json()
    mol = client.post(
        "/api/molecules", json={"project_id": project["id"], "name": "M"}
    ).json()
    r = client.post(f"/api/molecules/{mol['id']}/export",
                    json={"target_dir": str(tmp_path / "gibtsnicht")})
    assert r.status_code == 422


def test_export_twice_does_not_overwrite(client, tmp_path):
    project = client.post("/api/projects", json={"name": "P"}).json()
    mol = client.post(
        "/api/molecules", json={"project_id": project["id"], "name": "M"}
    ).json()
    e = next(x for x in mol["entries"] if x["type_code"] == "procedure")
    f = tmp_path / "v.docx"
    f.write_text("original")
    client.patch(f"/api/entries/{e['id']}", json={"file_path": str(f)})

    target = tmp_path / "export"
    target.mkdir()
    for _ in range(2):
        r = client.post(f"/api/molecules/{mol['id']}/export",
                        json={"target_dir": str(target)})
        assert r.status_code == 200

    sub = target / "P" / "M" / "Procedure"
    assert (sub / "v.docx").is_file()
    assert (sub / "v (2).docx").is_file()  # zweiter Export legt Kopie an


def test_export_whole_project(client, tmp_path):
    project = client.post("/api/projects", json={"name": "Sammelprojekt"}).json()
    for name in ("A", "B"):
        mol = client.post(
            "/api/molecules", json={"project_id": project["id"], "name": name}
        ).json()
        e = next(x for x in mol["entries"] if x["type_code"] == "procedure")
        f = tmp_path / f"vorschrift_{name}.docx"
        f.write_text("x")
        client.patch(f"/api/entries/{e['id']}", json={"file_path": str(f)})

    target = tmp_path / "export"
    target.mkdir()
    r = client.post(f"/api/projects/{project['id']}/export",
                    json={"target_dir": str(target)})
    assert r.status_code == 200, r.text
    result = r.json()
    assert result["molecule_count"] == 2

    base = target / "Sammelprojekt"
    assert (base / "A" / "Procedure" / "vorschrift_A.docx").is_file()
    assert (base / "B" / "Procedure" / "vorschrift_B.docx").is_file()
    assert (base / "A" / "Info.txt").is_file()
    assert (base / "B" / "Info.txt").is_file()


def test_export_empty_project(client, tmp_path):
    project = client.post("/api/projects", json={"name": "Leer"}).json()
    target = tmp_path / "export"
    target.mkdir()
    r = client.post(f"/api/projects/{project['id']}/export",
                    json={"target_dir": str(target)})
    assert r.status_code == 200
    assert r.json()["molecule_count"] == 0
    assert (target / "Leer").is_dir()
