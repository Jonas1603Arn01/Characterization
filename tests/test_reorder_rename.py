"""Tests für die Projekt-Reihenfolge (Drag & Drop) und das Umbenennen von Molekülen."""
import pytest
from fastapi.testclient import TestClient

from app import db
from app.main import app


@pytest.fixture()
def client(tmp_path):
    db.init_db(tmp_path / "test.db")
    with TestClient(app) as c:
        yield c


def project_names(client):
    return [p["name"] for p in client.get("/api/projects").json()]


def make_projects(client, names):
    return {name: client.post("/api/projects", json={"name": name}).json()["id"]
            for name in names}


# ---------- Projekt-Reihenfolge ----------

def test_new_projects_keep_creation_order(client):
    make_projects(client, ["Zeta", "Alpha", "Mitte"])
    assert project_names(client) == ["Zeta", "Alpha", "Mitte"]


def test_reorder_changes_listing(client):
    ids = make_projects(client, ["A", "B", "C"])
    r = client.post("/api/projects/reorder",
                    json={"order": [ids["C"], ids["A"], ids["B"]]})
    assert r.status_code == 200
    assert project_names(client) == ["C", "A", "B"]


def test_reorder_must_contain_all_projects(client):
    ids = make_projects(client, ["A", "B"])
    r = client.post("/api/projects/reorder", json={"order": [ids["A"]]})
    assert r.status_code == 422
    r = client.post("/api/projects/reorder", json={"order": [ids["A"], ids["B"], 999]})
    assert r.status_code == 422
    assert project_names(client) == ["A", "B"]  # nichts verändert


def test_new_project_appears_after_reorder_at_end(client):
    ids = make_projects(client, ["A", "B"])
    client.post("/api/projects/reorder", json={"order": [ids["B"], ids["A"]]})
    client.post("/api/projects", json={"name": "Neu"})
    assert project_names(client) == ["B", "A", "Neu"]


def test_reorder_is_undoable(client):
    ids = make_projects(client, ["A", "B"])
    client.post("/api/projects/reorder", json={"order": [ids["B"], ids["A"]]})
    assert project_names(client) == ["B", "A"]
    assert client.post("/api/undo").status_code == 200
    assert project_names(client) == ["A", "B"]


# ---------- Molekül-Reihenfolge ----------

def make_molecules(client, project_id, names):
    return {name: client.post("/api/molecules",
                              json={"project_id": project_id, "name": name}).json()["id"]
            for name in names}


def molecule_names(client, project_name):
    projects = client.get("/api/projects").json()
    p = next(p for p in projects if p["name"] == project_name)
    return [m["name"] for m in p["molecules"]]


def test_molecules_keep_creation_order(client):
    ids = make_projects(client, ["P"])
    make_molecules(client, ids["P"], ["Zeta", "Alpha", "Mitte"])
    assert molecule_names(client, "P") == ["Zeta", "Alpha", "Mitte"]


def test_reorder_molecules_within_project(client):
    ids = make_projects(client, ["P"])
    mols = make_molecules(client, ids["P"], ["A", "B", "C"])
    r = client.post("/api/molecules/reorder",
                    json={"order": [mols["C"], mols["A"], mols["B"]]})
    assert r.status_code == 200
    assert molecule_names(client, "P") == ["C", "A", "B"]


def test_reorder_molecules_must_cover_whole_project(client):
    ids = make_projects(client, ["P", "Q"])
    mols_p = make_molecules(client, ids["P"], ["A", "B"])
    mols_q = make_molecules(client, ids["Q"], ["X"])
    # unvollständig
    r = client.post("/api/molecules/reorder", json={"order": [mols_p["A"]]})
    assert r.status_code == 422
    # Moleküle aus verschiedenen Projekten gemischt
    r = client.post("/api/molecules/reorder",
                    json={"order": [mols_p["A"], mols_p["B"], mols_q["X"]]})
    assert r.status_code == 422
    # leer
    assert client.post("/api/molecules/reorder", json={"order": []}).status_code == 422
    assert molecule_names(client, "P") == ["A", "B"]  # nichts verändert


def test_moved_molecule_lands_at_end_of_target(client):
    ids = make_projects(client, ["P", "Q"])
    mols_p = make_molecules(client, ids["P"], ["A"])
    mols_q = make_molecules(client, ids["Q"], ["X", "Y"])
    # X in Q an den Anfang gezogen, dann A aus P nach Q verschoben
    client.post("/api/molecules/reorder", json={"order": [mols_q["Y"], mols_q["X"]]})
    r = client.patch(f"/api/molecules/{mols_p['A']}", json={"project_id": ids["Q"]})
    assert r.status_code == 200
    assert molecule_names(client, "Q") == ["Y", "X", "A"]


def test_molecule_reorder_is_undoable(client):
    ids = make_projects(client, ["P"])
    mols = make_molecules(client, ids["P"], ["A", "B"])
    client.post("/api/molecules/reorder", json={"order": [mols["B"], mols["A"]]})
    assert molecule_names(client, "P") == ["B", "A"]
    assert client.post("/api/undo").status_code == 200
    assert molecule_names(client, "P") == ["A", "B"]


# ---------- Molekül umbenennen ----------

@pytest.fixture()
def project(client):
    return client.post("/api/projects", json={"name": "P"}).json()


def test_rename_molecule(client, project):
    mol = client.post("/api/molecules",
                      json={"project_id": project["id"], "name": "JA-001"}).json()
    r = client.patch(f"/api/molecules/{mol['id']}", json={"name": "JA-001b"})
    assert r.status_code == 200
    assert r.json()["name"] == "JA-001b"
    listed = client.get("/api/projects").json()[0]["molecules"]
    assert [m["name"] for m in listed] == ["JA-001b"]


def test_rename_to_existing_name_in_project_conflicts(client, project):
    client.post("/api/molecules", json={"project_id": project["id"], "name": "JA-001"})
    mol = client.post("/api/molecules",
                      json={"project_id": project["id"], "name": "JA-002"}).json()
    r = client.patch(f"/api/molecules/{mol['id']}", json={"name": "JA-001"})
    assert r.status_code == 409


def test_rename_to_own_name_is_ok(client, project):
    mol = client.post("/api/molecules",
                      json={"project_id": project["id"], "name": "JA-001"}).json()
    r = client.patch(f"/api/molecules/{mol['id']}", json={"name": "JA-001"})
    assert r.status_code == 200


def test_rename_empty_rejected(client, project):
    mol = client.post("/api/molecules",
                      json={"project_id": project["id"], "name": "JA-001"}).json()
    r = client.patch(f"/api/molecules/{mol['id']}", json={"name": "   "})
    assert r.status_code == 422
