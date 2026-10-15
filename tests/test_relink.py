"""Tests für das Wiederfinden umbenannter Dateien (app/relink.py).

Wird eine verlinkte Datei im Ordner umbenannt, soll der Verweis heil bleiben:
die App sucht die Datei an ihrer Dateisystem-Kennung wieder und schreibt den
neuen Namen in die Datenbank.
"""
import pytest
from fastapi.testclient import TestClient

from app import db, relink
from app.main import app


@pytest.fixture()
def client(tmp_path):
    db.init_db(tmp_path / "db" / "test.db")
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def mol(client):
    project = client.post("/api/projects", json={"name": "P"}).json()
    return client.post(
        "/api/molecules", json={"project_id": project["id"], "name": "M-1"}
    ).json()


def entry(mol, code="procedure"):
    return next(e for e in mol["entries"] if e["type_code"] == code)


def hole(client, mol_id, code="procedure"):
    return entry(client.get(f"/api/molecules/{mol_id}").json(), code)


def verlinke(client, entry_id, **felder):
    """Pfad setzen und die Kennung nachtragen lassen (läuft im Hintergrund)."""
    r = client.patch(f"/api/entries/{entry_id}", json=felder)
    assert r.status_code == 200
    relink.flush()
    return r.json()


def test_umbenannte_datei_wird_wiedergefunden(client, mol, tmp_path):
    daten = tmp_path / "messung"
    daten.mkdir()
    alt = daten / "vorschrift.docx"
    alt.write_text("x")
    e = entry(mol)
    verlinke(client, e["id"], file_path=str(alt))

    neu = daten / "Vorschrift final.docx"
    alt.rename(neu)

    gezeigt = hole(client, mol["id"])
    assert gezeigt["file_path"] == str(neu)
    assert gezeigt["file_exists"] is True
    # und zwar dauerhaft: der neue Name steht in der Datenbank
    assert hole(client, mol["id"])["file_path"] == str(neu)


def test_umbenannter_ordner_wird_wiedergefunden(client, mol, tmp_path):
    alt = tmp_path / "NMR-Rohdaten"
    alt.mkdir()
    e = entry(mol, "nmr_1h")
    verlinke(client, e["id"], folder_path=str(alt))

    neu = tmp_path / "NMR-Rohdaten (geprüft)"
    alt.rename(neu)

    gezeigt = hole(client, mol["id"], "nmr_1h")
    assert gezeigt["folder_path"] == str(neu)
    assert gezeigt["folder_exists"] is True


def test_geloeschte_datei_bleibt_tot(client, mol, tmp_path):
    f = tmp_path / "weg.docx"
    f.write_text("x")
    e = entry(mol)
    verlinke(client, e["id"], file_path=str(f))
    f.unlink()

    gezeigt = hole(client, mol["id"])
    assert gezeigt["file_path"] == str(f)  # nichts wird erfunden
    assert gezeigt["file_exists"] is False


def test_falsche_datei_wird_nicht_genommen(client, mol, tmp_path):
    """Im Ordner liegt eine andere Datei mit gleicher Endung — die darf die
    Suche nicht übernehmen, sie hat eine andere Kennung."""
    f = tmp_path / "meins.docx"
    f.write_text("x")
    (tmp_path / "fremd.docx").write_text("x")
    e = entry(mol)
    verlinke(client, e["id"], file_path=str(f))
    f.unlink()

    assert hole(client, mol["id"])["file_exists"] is False


def test_ohne_kennung_bleibt_alles_beim_alten(client, mol, tmp_path, monkeypatch):
    """Liefert das Dateisystem keine Kennung (manche Netzfreigaben), wird
    nichts gemerkt und nichts wiedergefunden — aber auch nichts kaputt."""
    monkeypatch.setattr(relink, "file_id", lambda st: None)
    alt = tmp_path / "alt.docx"
    alt.write_text("x")
    e = entry(mol)
    verlinke(client, e["id"], file_path=str(alt))

    neu = tmp_path / "neu.docx"
    alt.rename(neu)
    gezeigt = hole(client, mol["id"])
    assert gezeigt["file_path"] == str(alt)
    assert gezeigt["file_exists"] is False


def test_mehrfach_verlinkte_datei_wird_ueberall_umgeschrieben(client, mol, tmp_path):
    alt = tmp_path / "spektrum.svg"
    alt.write_text("<svg/>")
    e1, e2 = entry(mol, "nmr_1h"), entry(mol, "nmr_13c")
    verlinke(client, e1["id"], svg_path=str(alt))
    verlinke(client, e2["id"], svg_path=str(alt))
    # zusätzlich als freie Zusatzdatei am selben Eintrag
    r = client.post(f"/api/entries/{e1['id']}/files", json={"path": str(alt)})
    assert r.status_code == 201

    neu = tmp_path / "spektrum-1H.svg"
    alt.rename(neu)

    voll = client.get(f"/api/molecules/{mol['id']}").json()
    assert entry(voll, "nmr_1h")["svg_path"] == str(neu)
    assert entry(voll, "nmr_13c")["svg_path"] == str(neu)
    assert entry(voll, "nmr_1h")["files"][0]["path"] == str(neu)
    assert voll["broken_paths"] == 0


def test_si_datei_der_literaturstelle(client, mol, tmp_path):
    alt = tmp_path / "si.pdf"
    alt.write_text("x")
    client.patch(f"/api/molecules/{mol['id']}", json={"si_path": str(alt)})
    relink.flush()

    neu = tmp_path / "SI Angew 2024.pdf"
    alt.rename(neu)

    gezeigt = client.get(f"/api/molecules/{mol['id']}").json()
    assert gezeigt["si_path"] == str(neu)
    assert gezeigt["si_exists"] is True


def test_lesemodus_repariert_nicht(client, mol, tmp_path, monkeypatch):
    """Der zweite PC arbeitet nur lesend — er darf auch nicht reparieren."""
    alt = tmp_path / "alt.docx"
    alt.write_text("x")
    e = entry(mol)
    verlinke(client, e["id"], file_path=str(alt))
    neu = tmp_path / "neu.docx"
    alt.rename(neu)

    monkeypatch.setattr(db, "_read_only", True)
    assert hole(client, mol["id"])["file_path"] == str(alt)
    monkeypatch.undo()
    assert hole(client, mol["id"])["file_path"] == str(neu)


def test_erfolglose_suche_wiederholt_sich_nicht(client, mol, tmp_path, monkeypatch):
    """Ein endgültig gelöschter Verweis darf nicht bei jedem Neuladen den
    ganzen Ordner durchsuchen — erst wenn sich am Ordner etwas ändert."""
    f = tmp_path / "weg.docx"
    f.write_text("x")
    e = entry(mol)
    verlinke(client, e["id"], file_path=str(f))
    f.unlink()

    suchen = []
    echt = relink._search
    monkeypatch.setattr(relink, "_search", lambda *a: suchen.append(a) or echt(*a))

    hole(client, mol["id"])
    assert len(suchen) == 1
    hole(client, mol["id"])
    assert len(suchen) == 1  # Ordner unverändert -> keine zweite Suche

    (tmp_path / "neu-dazu.txt").write_text("x")  # Ordner ändert sich
    hole(client, mol["id"])
    assert len(suchen) == 2


def test_kennung_wird_nur_einmal_ermittelt(client, mol, tmp_path):
    """Nach dem ersten Merken wird eine unveränderte Datei nicht wieder
    angefasst — sonst kostete jedes Neuladen einen Zugriff je Datei."""
    f = tmp_path / "vorschrift.docx"
    f.write_text("x")
    e = entry(mol)
    verlinke(client, e["id"], file_path=str(f))

    assert relink.record([str(f)]) == 1  # einmal schreiben geht immer
    vorher = len(relink._known)
    hole(client, mol["id"])
    relink.flush()
    assert len(relink._known) == vorher


def test_neuladen_kostet_keinen_zusaetzlichen_zugriff(client, mol, tmp_path, monkeypatch):
    """Sind die Kennungen einmal gemerkt, fasst das Wiederfinden beim
    Neuladen keine Datei mehr an — es sieht nur in der Merkliste nach."""
    f = tmp_path / "vorschrift.docx"
    f.write_text("x")
    ordner = tmp_path / "rohdaten"
    ordner.mkdir()
    e = entry(mol)
    verlinke(client, e["id"], file_path=str(f))
    verlinke(client, entry(mol, "nmr_1h")["id"], folder_path=str(ordner))

    zugriffe = []
    echt = relink._stat
    monkeypatch.setattr(relink, "_stat", lambda p: zugriffe.append(p) or echt(p))
    assert client.get("/api/projects").status_code == 200
    relink.flush()
    assert zugriffe == []
