"""Tests für Datei-Verlinkung, Existenz-Flags, Datenfelder und Strukturbild."""
import pytest
from fastapi.testclient import TestClient

from app import db
from app.main import app


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


def entry(mol, code):
    return next(e for e in mol["entries"] if e["type_code"] == code)


def test_file_linking_and_exists_flags(client, mol, tmp_path):
    e = entry(mol, "procedure")
    real = tmp_path / "vorschrift.docx"
    real.write_text("x")

    r = client.patch(f"/api/entries/{e['id']}", json={"file_path": str(real)}).json()
    assert r["file_path"] == str(real)
    assert r["file_exists"] is True

    r = client.patch(
        f"/api/entries/{e['id']}", json={"file_path": str(tmp_path / "geloescht.docx")}
    ).json()
    assert r["file_exists"] is False  # toter Pfad wird erkannt

    # "" löscht die Verlinkung
    r = client.patch(f"/api/entries/{e['id']}", json={"file_path": ""}).json()
    assert r["file_path"] is None
    assert r["file_exists"] is None


def test_folder_linking(client, mol, tmp_path):
    e = entry(mol, "nmr_1h")
    folder = tmp_path / "nmr" / "10"
    folder.mkdir(parents=True)
    r = client.patch(f"/api/entries/{e['id']}", json={"folder_path": str(folder)}).json()
    assert r["folder_exists"] is True


def test_broken_paths_counted_on_molecule(client, mol, tmp_path):
    e = entry(mol, "ir")
    client.patch(f"/api/entries/{e['id']}", json={"file_path": str(tmp_path / "weg.pdf")})
    m = client.get(f"/api/molecules/{mol['id']}").json()
    assert m["broken_paths"] == 1


def test_notes_add_edit_delete_any_type(client, mol, tmp_path):
    """Beliebig viele Notizen pro Eintrag, einzeln editier- und löschbar;
    alle landen im Export."""
    ms = entry(mol, "ms")
    n1 = client.post(f"/api/entries/{ms['id']}/notes",
                     json={"text": "HRMS: 212.1068"}).json()
    n2 = client.post(f"/api/entries/{ms['id']}/notes", json={}).json()
    assert n2["text"] == ""

    r = client.patch(f"/api/notes/{n2['id']}", json={"text": "zweite Notiz"}).json()
    assert r["text"] == "zweite Notiz"

    m = client.get(f"/api/molecules/{mol['id']}").json()
    ms_now = next(e for e in m["entries"] if e["type_code"] == "ms")
    assert [n["text"] for n in ms_now["notes"]] == ["HRMS: 212.1068", "zweite Notiz"]

    target = tmp_path / "export"
    target.mkdir()
    client.post(f"/api/molecules/{mol['id']}/export", json={"target_dir": str(target)})
    info = (target / "P" / "M-1" / "Info.txt").read_text(encoding="utf-8")
    assert "Mass spectrometry — notes:\nHRMS: 212.1068\nzweite Notiz" in info
    # Notizen zusätzlich als .txt im Methoden-Unterordner
    note_txt = (target / "P" / "M-1" / "Mass spectrometry" / "Notes.txt").read_text(encoding="utf-8")
    assert note_txt == "HRMS: 212.1068\n\nzweite Notiz"

    assert client.delete(f"/api/notes/{n1['id']}").status_code == 204
    assert client.delete(f"/api/notes/{n2['id']}").status_code == 204
    m = client.get(f"/api/molecules/{mol['id']}").json()
    assert next(e for e in m["entries"] if e["type_code"] == "ms")["notes"] == []


def test_extra_files_any_type(client, mol, tmp_path):
    """Beliebig viele zusätzliche Datei-Referenzen pro Eintrag; tote Pfade
    zählen in broken_paths, Export kopiert alle."""
    ir = entry(mol, "ir")
    f1 = tmp_path / "zusatz1.csv"
    f1.write_text("a")
    f2 = tmp_path / "zusatz2.csv"
    f2.write_text("b")

    r1 = client.post(f"/api/entries/{ir['id']}/files", json={"path": str(f1)}).json()
    client.post(f"/api/entries/{ir['id']}/files", json={"path": str(f2)})
    dead = client.post(f"/api/entries/{ir['id']}/files",
                       json={"path": str(tmp_path / "weg.csv")}).json()
    assert r1["exists"] is True
    assert dead["exists"] is False

    m = client.get(f"/api/molecules/{mol['id']}").json()
    assert m["broken_paths"] == 1
    ir_now = next(e for e in m["entries"] if e["type_code"] == "ir")
    assert len(ir_now["files"]) == 3

    target = tmp_path / "export"
    target.mkdir()
    result = client.post(f"/api/molecules/{mol['id']}/export",
                         json={"target_dir": str(target)}).json()
    sub = target / "P" / "M-1" / "IR spectrum"
    assert (sub / "zusatz1.csv").is_file()
    assert (sub / "zusatz2.csv").is_file()
    assert any("weg.csv" in w for w in result["warnings"])

    assert client.delete(f"/api/files/{dead['id']}").status_code == 204
    m = client.get(f"/api/molecules/{mol['id']}").json()
    assert m["broken_paths"] == 0

    assert client.post(f"/api/entries/{ir['id']}/files", json={"path": "  "}).status_code == 422


def test_extra_file_change_path(client, mol, tmp_path):
    """Zusatzdateien: Verlinkung nachträglich auf eine andere Datei umstellen
    (wie „ändern…" bei den festen Feldern); leerer Pfad wird abgelehnt."""
    ir = entry(mol, "ir")
    a = tmp_path / "a.csv"
    a.write_text("a")
    created = client.post(f"/api/entries/{ir['id']}/files",
                          json={"path": str(a), "label": "Rohdaten"}).json()

    b = tmp_path / "b.csv"
    b.write_text("b")
    r = client.patch(f"/api/files/{created['id']}", json={"path": str(b)})
    assert r.status_code == 200, r.text
    assert r.json()["path"] == str(b)
    assert r.json()["exists"] is True
    assert r.json()["label"] == "Rohdaten"  # Bezeichnung bleibt

    assert client.patch(f"/api/files/{created['id']}", json={"path": "  "}).status_code == 422

    r = client.patch(f"/api/files/{created['id']}", json={"path": str(tmp_path / "weg.csv")}).json()
    assert r["exists"] is False
    m = client.get(f"/api/molecules/{mol['id']}").json()
    assert m["broken_paths"] == 1


def test_text_note_migration(client, mol):
    """Alte Einzel-Notizen (text_note-Spalte) werden in die Notiz-Tabelle überführt."""
    from sqlalchemy import text as sql
    from app import db as dbmod

    ir = entry(mol, "ir")
    with dbmod._engine.begin() as conn:  # Altbestand simulieren
        conn.execute(sql("UPDATE data_entries SET text_note='3300 cm-1 (OH)' WHERE id=:i"),
                     {"i": ir["id"]})
    assert dbmod.migrate_text_notes() == 1
    assert dbmod.migrate_text_notes() == 0  # idempotent

    m = client.get(f"/api/molecules/{mol['id']}").json()
    ir_now = next(e for e in m["entries"] if e["type_code"] == "ir")
    assert [n["text"] for n in ir_now["notes"]] == ["3300 cm-1 (OH)"]


def test_file_labels(client, mol, tmp_path):
    """Zusatzdateien sind frei benennbar (beim Anlegen und nachträglich)."""
    ir = entry(mol, "ir")
    f = tmp_path / "daten.csv"
    f.write_text("x")
    created = client.post(f"/api/entries/{ir['id']}/files",
                          json={"path": str(f), "label": "Rohdaten UV"}).json()
    assert created["label"] == "Rohdaten UV"

    r = client.patch(f"/api/files/{created['id']}", json={"label": "Kalibrierung"}).json()
    assert r["label"] == "Kalibrierung"
    r = client.patch(f"/api/files/{created['id']}", json={"label": ""}).json()
    assert r["label"] is None


def test_literature_known_and_doi(client, mol, tmp_path):
    m = client.patch(f"/api/molecules/{mol['id']}",
                     json={"literature_known": True, "doi": "10.1021/jacs.0c01234"}).json()
    assert m["literature_known"] is True
    assert m["doi"] == "10.1021/jacs.0c01234"

    # Zitat als Freitext daneben
    m = client.patch(f"/api/molecules/{mol['id']}",
                     json={"citation": "  A. Müller, JACS 2020, 142, 1234.  "}).json()
    assert m["citation"] == "A. Müller, JACS 2020, 142, 1234."

    # DOI und Zitat landen in der Export-Info
    target = tmp_path / "export"
    target.mkdir()
    client.post(f"/api/molecules/{mol['id']}/export", json={"target_dir": str(target)})
    info = (target / "P" / "M-1" / "Info.txt").read_text(encoding="utf-8")
    assert "known compound — DOI: 10.1021/jacs.0c01234" in info
    assert "Citation      A. Müller, JACS 2020, 142, 1234." in info

    # "" entfernt das Zitat
    m = client.patch(f"/api/molecules/{mol['id']}", json={"citation": ""}).json()
    assert m["citation"] is None

    # "" entfernt die DOI, Haken bleibt unabhängig davon
    m = client.patch(f"/api/molecules/{mol['id']}", json={"doi": ""}).json()
    assert m["doi"] is None
    assert m["literature_known"] is True
    m = client.patch(f"/api/molecules/{mol['id']}", json={"literature_known": False}).json()
    assert m["literature_known"] is False


def test_literature_si_file(client, mol, tmp_path):
    """Supporting Information (PDF/Word) der Literaturstelle: eine Datei je
    Molekül, mit Existenz-Flag, zählt zu den toten Pfaden, "" entfernt sie."""
    si = tmp_path / "ja0c01234_si_001.pdf"
    si.write_bytes(b"%PDF-1.4")
    m = client.patch(f"/api/molecules/{mol['id']}",
                     json={"literature_known": True, "si_path": str(si)}).json()
    assert m["si_path"] == str(si)
    assert m["si_exists"] is True
    assert m["broken_paths"] == 0

    # Word-Datei ist ebenso erlaubt; toter Pfad wird erkannt und mitgezählt
    m = client.patch(f"/api/molecules/{mol['id']}",
                     json={"si_path": str(tmp_path / "weg.docx")}).json()
    assert m["si_path"] == str(tmp_path / "weg.docx")
    assert m["si_exists"] is False
    assert m["broken_paths"] == 1

    # "" entfernt die Verlinkung; der Haken bleibt
    m = client.patch(f"/api/molecules/{mol['id']}", json={"si_path": ""}).json()
    assert m["si_path"] is None
    assert m["si_exists"] is None
    assert m["literature_known"] is True
    assert m["broken_paths"] == 0

    # Nicht angegeben -> unverändert
    client.patch(f"/api/molecules/{mol['id']}", json={"si_path": str(si)})
    m = client.patch(f"/api/molecules/{mol['id']}", json={"doi": "10.1/x"}).json()
    assert m["si_path"] == str(si)


def test_physical_state_oil_hides_melting_point(client, mol, tmp_path):
    # Feststoff (Default: unbestimmt) zeigt den Schmelzpunkt
    assert any(e["type_code"] == "mp" for e in mol["entries"])

    m = client.patch(f"/api/molecules/{mol['id']}",
                     json={"physical_state": "oil", "color": "gelb",
                           "consistency": "viskos"}).json()
    assert m["physical_state"] == "oil"
    assert m["color"] == "gelb"
    assert m["consistency"] == "viskos"
    # Schmelzpunkt taucht bei einem Öl nicht mehr auf und zählt nicht mehr
    assert not any(e["type_code"] == "mp" for e in m["entries"])
    assert m["required_count"] == 6  # 7 Standardtypen minus Schmelzpunkt

    # Öl mit sonst allen vorhandenen Daten wird vollständig (ohne Schmelzpunkt)
    for e in m["entries"]:
        client.patch(f"/api/entries/{e['id']}", json={"status": "present"})
    assert client.get(f"/api/molecules/{mol['id']}").json()["completeness"] == "complete"

    # Umschalten auf Feststoff bringt den Schmelzpunkt zurück (Wert erhalten)
    m = client.patch(f"/api/molecules/{mol['id']}",
                     json={"physical_state": "solid"}).json()
    assert any(e["type_code"] == "mp" for e in m["entries"])

    # Aggregatzustand/Farbe/Beschaffenheit landen im Export
    client.patch(f"/api/molecules/{mol['id']}", json={"physical_state": "oil"})
    target = tmp_path / "export"
    target.mkdir()
    client.post(f"/api/molecules/{mol['id']}/export", json={"target_dir": str(target)})
    info = (target / "P" / "M-1" / "Info.txt").read_text(encoding="utf-8")
    assert "Physical state" in info and "oil" in info
    assert "Color" in info and "gelb" in info
    assert "Consistency" in info and "viskos" in info
    assert not (target / "P" / "M-1" / "Melting point").exists()


def test_invalid_physical_state_rejected(client, mol):
    assert client.patch(f"/api/molecules/{mol['id']}",
                        json={"physical_state": "gas"}).status_code == 422


def test_na_entry_keeps_files_and_notes(client, mol, tmp_path):
    """Auch ein auf n.z. gesetzter Datentyp kann Dateien und Notizen tragen."""
    ms = entry(mol, "ms")
    client.patch(f"/api/entries/{ms['id']}", json={"required": False})  # n.z.

    f = tmp_path / "extra.pdf"
    f.write_text("x")
    client.post(f"/api/entries/{ms['id']}/files", json={"path": str(f)})
    client.post(f"/api/entries/{ms['id']}/notes", json={"text": "trotzdem notiert"})

    m = client.get(f"/api/molecules/{mol['id']}").json()
    ms_now = next(e for e in m["entries"] if e["type_code"] == "ms")
    assert ms_now["status"] == "na"
    assert len(ms_now["files"]) == 1
    assert [n["text"] for n in ms_now["notes"]] == ["trotzdem notiert"]


def test_mp_value(client, mol):
    mp = entry(mol, "mp")
    r = client.patch(f"/api/entries/{mp['id']}", json={"mp_value": 135.5}).json()
    assert r["mp_value"] == 135.5
    # null löscht den Wert
    r = client.patch(f"/api/entries/{mp['id']}", json={"mp_value": None}).json()
    assert r["mp_value"] is None
    # Status bleibt von Datenfeldern unberührt (manuelle Status-Logik)
    assert r["status"] == "missing"


# Strukturbild, Reaktionsschema und Reaktionsgleichung teilen sich die Logik — alle Slots testen
@pytest.mark.parametrize("kind,field", [("image", "image_path"), ("scheme", "scheme_path"),
                                        ("equation", "equation_path")])
def test_molecule_image_slots(client, mol, tmp_path, kind, field):
    assert client.get(f"/api/molecules/{mol['id']}/{kind}").status_code == 404

    img = tmp_path / f"{kind}.png"
    img.write_bytes(bytes.fromhex("89504e470d0a1a0a"))  # PNG-Magic reicht zum Ausliefern
    m = client.patch(f"/api/molecules/{mol['id']}", json={field: str(img)}).json()
    assert m[f"{kind}_exists"] is True

    resp = client.get(f"/api/molecules/{mol['id']}/{kind}")
    assert resp.status_code == 200
    assert resp.content.startswith(b"\x89PNG")

    m = client.patch(f"/api/molecules/{mol['id']}", json={field: ""}).json()
    assert m[field] is None
