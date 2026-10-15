import base64
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import db
from app.main import app

# Minimales gültiges 1×1-PNG
PNG_1x1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


@pytest.fixture()
def client(tmp_path):
    # vor dem Lifespan initialisieren, damit ensure_db nicht die echte DB anlegt
    db.init_db(tmp_path / "test.db")
    with TestClient(app) as c:
        yield c


def make_molecule(client, name="Verbindung 1", smiles=None):
    project = client.post("/api/projects", json={"name": "Testprojekt"}).json()
    resp = client.post(
        "/api/molecules",
        json={"project_id": project["id"], "name": name, "smiles": smiles},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_create_project_and_molecule_with_default_entries(client):
    mol = make_molecule(client)
    # 7 Standardtypen, alle benötigt, alle fehlend
    assert len(mol["entries"]) == 7
    assert all(e["required"] for e in mol["entries"])
    assert all(e["status"] == "missing" for e in mol["entries"])
    assert mol["completeness"] == "incomplete"


def test_smiles_computes_formula_and_mass(client):
    mol = make_molecule(client, smiles="c1ccccc1")  # Benzol
    assert mol["formula"] == "C6H6"
    assert abs(mol["exact_mass"] - 78.0470) < 0.001


def test_invalid_smiles_rejected(client):
    project = client.post("/api/projects", json={"name": "P"}).json()
    resp = client.post(
        "/api/molecules",
        json={"project_id": project["id"], "name": "X", "smiles": "not-a-smiles"},
    )
    assert resp.status_code == 422


def test_three_states_and_completeness(client):
    mol = make_molecule(client)
    entries = {e["type_code"]: e for e in mol["entries"]}

    # Alle auf vorhanden außer Schmelzpunkt
    for code, e in entries.items():
        if code != "mp":
            client.patch(f"/api/entries/{e['id']}", json={"status": "present"})
    mol = client.get(f"/api/molecules/{mol['id']}").json()
    assert mol["completeness"] == "incomplete"

    # Schmelzpunkt auf "n. z." -> zählt NICHT als fehlend -> vollständig
    resp = client.patch(f"/api/entries/{entries['mp']['id']}", json={"required": False})
    assert resp.json()["status"] == "na"
    mol = client.get(f"/api/molecules/{mol['id']}").json()
    assert mol["completeness"] == "complete"


def test_other_entries_add_rename_delete(client):
    mol = make_molecule(client)
    resp = client.post(
        f"/api/molecules/{mol['id']}/entries", json={"custom_label": "Elementaranalyse"}
    )
    assert resp.status_code == 201
    entry = resp.json()
    assert entry["custom_label"] == "Elementaranalyse"

    resp = client.patch(f"/api/entries/{entry['id']}", json={"custom_label": "EA"})
    assert resp.json()["custom_label"] == "EA"

    assert client.delete(f"/api/entries/{entry['id']}").status_code == 204
    # Standardeinträge sind nicht löschbar
    std = mol["entries"][0]
    assert client.delete(f"/api/entries/{std['id']}").status_code == 422


def test_rename_fixed_field_labels(client):
    """Feste Ordner-/Datei-Felder sind frei umbenennbar; "" stellt den Standard wieder her."""
    mol = make_molecule(client)
    entry = next(e for e in mol["entries"] if e["type_code"] == "nmr_1h")
    assert entry["folder_label"] is None and entry["file_label"] is None
    assert entry["svg_label"] is None

    resp = client.patch(f"/api/entries/{entry['id']}",
                        json={"folder_label": "Rohdaten", "file_label": "Auswertung",
                              "svg_label": "Abbildung"})
    data = resp.json()
    assert data["folder_label"] == "Rohdaten"
    assert data["file_label"] == "Auswertung"
    assert data["svg_label"] == "Abbildung"

    resp = client.patch(f"/api/entries/{entry['id']}", json={"folder_label": ""})
    assert resp.json()["folder_label"] is None


def test_nmr_hat_ein_drittes_feld_fuer_das_svg_spektrum(client, tmp_path):
    """Neben Mess-Ordner und MNova-Datei hängt an jedem NMR-Eintrag das SVG."""
    types = {t["code"]: t for t in client.get("/api/datatypes").json()}
    for code in ("nmr_1h", "nmr_13c"):
        keys = [f["key"] for f in types[code]["fields"]]
        assert keys == ["folder", "file", "svg"]

    mol = make_molecule(client)
    entry = next(e for e in mol["entries"] if e["type_code"] == "nmr_1h")
    assert entry["svg_path"] is None

    svg = tmp_path / "1H.svg"
    svg.write_text("<svg/>")
    data = client.patch(f"/api/entries/{entry['id']}",
                        json={"svg_path": str(svg)}).json()
    assert data["svg_path"] == str(svg)
    assert data["svg_exists"] is True
    # Der Status bleibt Handarbeit: das SVG ist kein Beleg für „vorhanden"
    assert data["status"] == "missing"

    fehlt = client.patch(f"/api/entries/{entry['id']}",
                         json={"svg_path": str(tmp_path / "weg.svg")}).json()
    assert fehlt["svg_exists"] is False

    assert client.patch(f"/api/entries/{entry['id']}",
                        json={"svg_path": ""}).json()["svg_path"] is None


def test_2d_nmr_hat_je_ein_svg_fuer_hsqc_und_hmbc(client, tmp_path):
    """2D-NMR bekommt statt eines SVG-Spektrums zwei: HSQC und HMBC."""
    types = {t["code"]: t for t in client.get("/api/datatypes").json()}
    fields = types["nmr_2d"]["fields"]
    assert [f["key"] for f in fields] == ["folder", "file", "svg", "svg2"]
    assert [f["label"]["en"] for f in fields[2:]] == ["HSQC spectrum", "HMBC spectrum"]

    mol = make_molecule(client)
    entry = next(e for e in mol["entries"] if e["type_code"] == "nmr_2d")
    hsqc, hmbc = tmp_path / "HSQC.svg", tmp_path / "HMBC.svg"
    hsqc.write_text("<svg/>")
    hmbc.write_text("<svg/>")
    data = client.patch(f"/api/entries/{entry['id']}",
                        json={"svg_path": str(hsqc), "svg2_path": str(hmbc),
                              "svg2_label": "HMBC (CDCl3)"}).json()
    assert data["svg_path"] == str(hsqc)
    assert data["svg2_path"] == str(hmbc)
    assert data["svg2_exists"] is True
    assert data["svg2_label"] == "HMBC (CDCl3)"

    assert client.patch(f"/api/entries/{entry['id']}",
                        json={"svg2_path": ""}).json()["svg2_path"] is None


# Alle drei Bild-Slots (Struktur, Reaktionsschema, Reaktionsgleichung) nutzen dieselbe Upload-Logik
IMAGE_SLOTS = [("image", "image_path"), ("scheme", "scheme_path"), ("equation", "equation_path")]


@pytest.mark.parametrize("kind,field", IMAGE_SLOTS)
def test_paste_image_sets_slot(client, kind, field):
    mol = make_molecule(client)
    r = client.post(
        f"/api/molecules/{mol['id']}/{kind}",
        content=PNG_1x1,
        headers={"Content-Type": "image/png"},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data[f"{kind}_exists"] is True
    saved = Path(data[field])
    assert saved.is_file()
    assert saved.parent == db.images_dir()
    # Bild wird ausgeliefert
    img = client.get(f"/api/molecules/{mol['id']}/{kind}")
    assert img.status_code == 200
    assert img.content == PNG_1x1


@pytest.mark.parametrize("kind", [k for k, _ in IMAGE_SLOTS])
def test_paste_image_rejects_non_image(client, kind):
    mol = make_molecule(client)
    r = client.post(
        f"/api/molecules/{mol['id']}/{kind}",
        content=b"das ist kein bild",
        headers={"Content-Type": "image/png"},
    )
    assert r.status_code == 422


@pytest.mark.parametrize("kind,field", IMAGE_SLOTS)
def test_paste_image_replaces_previous_managed_file(client, kind, field):
    mol = make_molecule(client)
    first = client.post(
        f"/api/molecules/{mol['id']}/{kind}", content=PNG_1x1,
        headers={"Content-Type": "image/png"},
    ).json()
    first_path = Path(first[field])
    second = client.post(
        f"/api/molecules/{mol['id']}/{kind}", content=PNG_1x1,
        headers={"Content-Type": "image/png"},
    ).json()
    second_path = Path(second[field])
    assert first_path != second_path
    assert not first_path.exists()  # altes, von der App verwaltetes Bild wurde entfernt
    assert second_path.is_file()


def test_paste_scheme_keeps_structure_image_separate(client):
    """Die Slots sind unabhängig — Schema-Upload darf das Strukturbild nicht anfassen."""
    mol = make_molecule(client)
    struct = client.post(
        f"/api/molecules/{mol['id']}/image", content=PNG_1x1,
        headers={"Content-Type": "image/png"},
    ).json()
    data = client.post(
        f"/api/molecules/{mol['id']}/scheme", content=PNG_1x1,
        headers={"Content-Type": "image/png"},
    ).json()
    assert data["image_path"] == struct["image_path"]
    assert Path(data["image_path"]).is_file()
    assert data["scheme_path"] != data["image_path"]


def test_move_molecule_between_projects(client):
    mol = make_molecule(client)
    p2 = client.post("/api/projects", json={"name": "Zielprojekt"}).json()

    r = client.patch(f"/api/molecules/{mol['id']}", json={"project_id": p2["id"]})
    assert r.status_code == 200
    assert r.json()["project_id"] == p2["id"]

    # Duplikat im Zielprojekt wird abgelehnt, Molekül bleibt wo es ist
    dup = client.post(
        "/api/molecules", json={"project_id": mol["project_id"], "name": mol["name"]}
    ).json()
    r = client.patch(f"/api/molecules/{dup['id']}", json={"project_id": p2["id"]})
    assert r.status_code == 409
    assert client.get(f"/api/molecules/{dup['id']}").json()["project_id"] == mol["project_id"]

    # unbekanntes Zielprojekt -> 404
    assert client.patch(f"/api/molecules/{mol['id']}", json={"project_id": 999}).status_code == 404


def test_duplicate_names_rejected(client):
    mol = make_molecule(client)
    resp = client.post(
        "/api/molecules", json={"project_id": mol["project_id"], "name": mol["name"]}
    )
    assert resp.status_code == 409
    resp = client.post("/api/projects", json={"name": "Testprojekt"})
    assert resp.status_code == 409


def test_dashboard(client):
    mol = make_molecule(client)
    entries = {e["type_code"]: e for e in mol["entries"]}
    client.patch(f"/api/entries/{entries['nmr_1h']['id']}", json={"status": "present"})
    client.patch(f"/api/entries/{entries['nmr_2d']['id']}", json={"required": False})

    dash = client.get("/api/dashboard").json()
    assert dash["total_molecules"] == 1
    assert dash["complete_molecules"] == 0
    assert dash["by_type"]["nmr_1h"] == {"required": 1, "present": 1}
    assert "nmr_2d" not in dash["by_type"]  # n. z. taucht nicht als Anforderung auf
