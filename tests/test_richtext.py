"""Tests für formatierte Notizen (fett/kursiv/hoch-/tiefgestellt): das
Frontend schickt HTML, der Server bereinigt es auf b/i/sup/sub/br, leitet
den Klartext ab (Export, ältere App-Versionen) und rüstet die Spalte
entry_notes.html bei Bestandsdaten nach. Dazu die Migration der neuen
Spalten für den dritten Bild-Slot (Reaktionsgleichung).
"""
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app import db, richtext
from app.main import app


# ---------- Bereinigung & Klartext ----------

def test_sanitize_keeps_only_formatting_tags():
    raw = '<div style="x">CDCl<sub>3</sub> <script>alert(1)</script>' \
          '<span onclick="y"><strong>fett</strong> <em>kursiv</em></span><br></div>'
    assert richtext.sanitize(raw) == "CDCl<sub>3</sub> <b>fett</b> <i>kursiv</i>"


def test_sanitize_repairs_nesting_and_drops_empty_tags():
    assert richtext.sanitize("<b>fett<i>beides</b>nur kursiv</i>") == "<b>fett<i>beides</i></b>nur kursiv"
    assert richtext.sanitize("<b></b>text<sup></sup><br><br>") == "text"
    assert richtext.sanitize("a<div>b</div><p>c</p>") == "a<br>b<br>c"


def test_to_text_uses_unicode_super_and_subscript():
    assert richtext.to_text("<sup>13</sup>C-NMR (CDCl<sub>3</sub>)<br>δ = 7.26") == "¹³C-NMR (CDCl₃)\nδ = 7.26"
    assert richtext.to_text("H<sub>2</sub>O<sup>+</sup>") == "H₂O⁺"
    assert richtext.to_text("d &lt; 7 &amp; e") == "d < 7 & e"


def test_plain_text_round_trip():
    html = richtext.text_to_html("a < b & c\nzweite Zeile")
    assert html == "a &lt; b &amp; c<br>zweite Zeile"
    assert richtext.is_plain(html)
    assert richtext.to_text(html) == "a < b & c\nzweite Zeile"


# ---------- API ----------

@pytest.fixture()
def client(tmp_path):
    db.init_db(tmp_path / "test.db")
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def entry(client):
    project = client.post("/api/projects", json={"name": "P"}).json()
    mol = client.post("/api/molecules", json={"project_id": project["id"], "name": "M-1"}).json()
    return next(e for e in mol["entries"] if e["type_code"] == "nmr_13c")


def test_note_with_formatting_stores_html_and_derived_text(client, entry):
    r = client.post(f"/api/entries/{entry['id']}/notes",
                    json={"html": "<sup>13</sup>C-NMR: CDCl<sub>3</sub>, <b>77.2</b><script>x</script>"})
    assert r.status_code == 201, r.text
    note = r.json()
    assert note["html"] == "<sup>13</sup>C-NMR: CDCl<sub>3</sub>, <b>77.2</b>"
    assert note["text"] == "¹³C-NMR: CDCl₃, 77.2"

    r = client.patch(f"/api/notes/{note['id']}", json={"html": "nur <i>kursiv</i>"}).json()
    assert r == {"id": note["id"], "html": "nur <i>kursiv</i>", "text": "nur kursiv"}


def test_note_without_formatting_stays_plain(client, entry):
    """Ohne Formatierung bleibt html leer — die Notiz ist eine reine Textnotiz
    (ältere App-Versionen sehen exakt dasselbe)."""
    note = client.post(f"/api/entries/{entry['id']}/notes",
                       json={"html": "a &lt; b<br>zweite Zeile<br>"}).json()
    assert note["html"] is None
    assert note["text"] == "a < b\nzweite Zeile"

    # Klassischer Text-Aufruf funktioniert weiterhin und löscht eine Formatierung
    client.patch(f"/api/notes/{note['id']}", json={"html": "<b>x</b>"})
    r = client.patch(f"/api/notes/{note['id']}", json={"text": "wieder Text"}).json()
    assert r["html"] is None
    assert r["text"] == "wieder Text"


def test_notes_export_uses_plain_text(client, entry, tmp_path):
    client.post(f"/api/entries/{entry['id']}/notes",
                json={"html": "<b>HRMS</b> C<sub>6</sub>H<sub>6</sub><sup>+</sup>"})
    mol_id = client.get("/api/projects").json()[0]["molecules"][0]["id"]
    target = tmp_path / "export"
    target.mkdir()
    r = client.post(f"/api/molecules/{mol_id}/export", json={"target_dir": str(target)})
    assert r.status_code == 200, r.text
    notes = (target / "P" / "M-1" / "¹³C NMR" / "Notes.txt").read_text(encoding="utf-8")
    assert notes == "HRMS C₆H₆⁺"
    assert "<b>" not in (target / "P" / "M-1" / "Info.txt").read_text(encoding="utf-8")


# ---------- Migration von Bestandsdaten ----------

def test_old_database_gets_new_columns(tmp_path):
    """Datensatz einer älteren App-Version (ohne entry_notes.html und ohne
    Reaktionsgleichung-Spalten) wird beim Öffnen nachgerüstet; vorhandene
    Notizen bleiben als reine Textnotizen erhalten."""
    old = tmp_path / "old.db"
    con = sqlite3.connect(old)
    con.executescript("""
        CREATE TABLE projects (id INTEGER PRIMARY KEY, name VARCHAR UNIQUE, sort_order INTEGER NOT NULL DEFAULT 0, created_at DATETIME);
        CREATE TABLE molecules (id INTEGER PRIMARY KEY, project_id INTEGER, name VARCHAR, smiles VARCHAR,
            formula VARCHAR, exact_mass FLOAT, image_path VARCHAR, scheme_path VARCHAR,
            image_cdx_path VARCHAR, scheme_cdx_path VARCHAR, literature_known BOOLEAN NOT NULL DEFAULT 0,
            doi VARCHAR, citation VARCHAR, si_path VARCHAR, physical_state VARCHAR, color VARCHAR,
            consistency VARCHAR, sample_available BOOLEAN NOT NULL DEFAULT 0, sample_number VARCHAR,
            sample_comment VARCHAR, sort_order INTEGER NOT NULL DEFAULT 0, created_at DATETIME, updated_at DATETIME);
        CREATE TABLE data_entries (id INTEGER PRIMARY KEY, molecule_id INTEGER, type_code VARCHAR,
            custom_label VARCHAR, required BOOLEAN NOT NULL DEFAULT 1, status VARCHAR NOT NULL DEFAULT 'missing',
            folder_path VARCHAR, file_path VARCHAR, folder_label VARCHAR, file_label VARCHAR,
            text_note VARCHAR, mp_value FLOAT, updated_at DATETIME);
        CREATE TABLE entry_files (id INTEGER PRIMARY KEY, entry_id INTEGER, path VARCHAR, label VARCHAR, updated_at DATETIME);
        CREATE TABLE entry_notes (id INTEGER PRIMARY KEY, entry_id INTEGER, text VARCHAR NOT NULL DEFAULT '', updated_at DATETIME);
        INSERT INTO projects (id, name, created_at) VALUES (1, 'Alt', '2026-01-01 00:00:00');
        INSERT INTO molecules (id, project_id, name, created_at, updated_at) VALUES (1, 1, 'M-alt', '2026-01-01 00:00:00', '2026-01-01 00:00:00');
        INSERT INTO data_entries (id, molecule_id, type_code, updated_at) VALUES (1, 1, 'ms', '2026-01-01 00:00:00');
        INSERT INTO entry_notes (id, entry_id, text, updated_at) VALUES (1, 1, 'HRMS: 212.1068 <alt>', '2026-01-01 00:00:00');
    """)
    con.commit()
    con.close()

    db.init_db(old)
    con = sqlite3.connect(old)
    mol_cols = {r[1] for r in con.execute("PRAGMA table_info(molecules)")}
    note_cols = {r[1] for r in con.execute("PRAGMA table_info(entry_notes)")}
    con.close()
    assert {"equation_path", "equation_cdx_path",
            "name_html", "citation_html", "sample_comment_html"} <= mol_cols
    assert "html" in note_cols

    with TestClient(app) as c:
        m = c.get("/api/molecules/1").json()
        assert m["equation_path"] is None and m["equation_exists"] is None
        assert m["name"] == "M-alt" and m["name_html"] is None
        note = next(e for e in m["entries"] if e["type_code"] == "ms")["notes"][0]
        assert note == {"id": 1, "text": "HRMS: 212.1068 <alt>", "html": None}
