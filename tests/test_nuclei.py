"""Weitere NMR-Kerne (¹⁹F, ³¹P …) als eigener Eintrag: Katalog, Felder,
gesetzte Bezeichnung und der Vorschlag für die Kopfzeile."""
import pytest
from fastapi.testclient import TestClient

from app import chem_text, db, nuclei
from app.main import app


@pytest.fixture()
def client(tmp_path):
    db.init_db(tmp_path / "test.db")
    with TestClient(app) as c:
        yield c


def make_molecule(client):
    project = client.post("/api/projects", json={"name": "Testprojekt"}).json()
    return client.post("/api/molecules",
                       json={"project_id": project["id"], "name": "Verbindung 1"}).json()


def add(client, mol, label):
    resp = client.post(f"/api/molecules/{mol['id']}/entries",
                       json={"custom_label": label})
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------- Katalog ----------

def test_katalog_bietet_die_gaengigen_kerne_an(client):
    """Der Kern wird ausgewählt, nicht getippt — mit Bezeichnung, üblichen
    Nachkommastellen und der Vorbelegung für „{¹H}"."""
    data = client.get("/api/nuclei").json()
    codes = {n["code"] for n in data["nuclei"]}
    assert {"19F NMR", "31P NMR", "11B NMR", "29Si NMR", "15N NMR"} <= codes
    # ¹H und ¹³C sind feste Datentypen und stehen nicht zur Auswahl
    assert "1H NMR" not in codes and "13C NMR" not in codes

    fluor = next(n for n in data["nuclei"] if n["code"] == "19F NMR")
    assert fluor["name"]["de"] == "Fluor" and fluor["name"]["en"] == "Fluorine"
    assert fluor["decoupled"] is False and fluor["digits"] == 2
    # ³¹P wird üblicherweise ¹H-entkoppelt gemessen
    assert next(n for n in data["nuclei"] if n["code"] == "31P NMR")["decoupled"] is True


def test_zusaetzliche_kerne_bekommen_die_nmr_felder(client):
    """Ein ¹⁹F-Eintrag hat Mess-Ordner, MNova-Datei und SVG-Spektrum —
    dieselben Felder wie ¹H und ¹³C, nicht nur das allgemeine Datei-Feld."""
    fields = client.get("/api/nuclei").json()["fields"]
    assert [f["key"] for f in fields] == ["folder", "file", "svg"]
    types = {t["code"]: t for t in client.get("/api/datatypes").json()}
    assert fields == types["nmr_1h"]["fields"]

    mol = make_molecule(client)
    entry = add(client, mol, "19F NMR")
    assert entry["is_nmr"] is True
    assert entry["in_document"] is True   # NMR gehört ins Dokument
    # die Spalten der drei Felder stehen an jedem Eintrag bereit
    for field in ("folder_path", "file_path", "svg_path"):
        assert field in entry


def test_bezeichnung_wird_fuer_die_anzeige_gesetzt(client):
    """Gespeichert „19F NMR", angezeigt „¹⁹F NMR" — die einfache Schreibweise
    bleibt in der Datenbank, daran hängen Export und Suche."""
    mol = make_molecule(client)
    entry = add(client, mol, "31P{1H} NMR")
    assert entry["custom_label"] == "31P{1H} NMR"
    assert entry["display_label"] == "³¹P{¹H} NMR"

    andere = add(client, mol, "Elementaranalyse")
    assert andere["is_nmr"] is False
    assert andere["display_label"] == "Elementaranalyse"


@pytest.mark.parametrize("label,gesetzt", [
    ("19F NMR", "¹⁹F NMR"),
    ("13C{1H} NMR", "¹³C{¹H} NMR"),
    ("1H,15N HMBC", "¹H,¹⁵N HMBC"),
    ("Elementaranalyse", "Elementaranalyse"),
    ("JA294", "JA294"),          # Probennummer bleibt unangetastet
    (None, ""),
])
def test_typeset(label, gesetzt):
    assert chem_text.typeset(label) == gesetzt


# ---------- Frequenzen ----------

def test_frequenz_folgt_aus_dem_kernverhaeltnis():
    """An einem 500-MHz-Gerät misst ¹⁹F bei 471 MHz, ³¹P bei 202 MHz."""
    assert nuclei.frequency("19F NMR", 500.13) == "471"
    assert nuclei.frequency("31P{1H} NMR", 500.13) == "202"
    assert nuclei.frequency("13C NMR", 500.13) == "126"
    assert nuclei.frequency("Elementaranalyse", 500.13) is None


def test_geraetebezeichnung_wird_mitgedacht():
    """In der Kopfzeile steht die Gerätebezeichnung („500 MHz"), gemessen wird
    ¹H bei 500.13 MHz — sonst käme für ¹⁹F 470 statt der üblichen 471 heraus.
    Egal, welcher Kern die Frequenz liefert, es kommt dasselbe Gerät heraus."""
    for label, angabe in [("1H NMR", "500"), ("13C NMR", "126"), ("19F NMR", "471")]:
        assert nuclei.proton_frequency(label, angabe) == pytest.approx(500.13)
    assert nuclei.proton_frequency("13C NMR", "101") == pytest.approx(400.13)
    # Frequenz, die zu keiner Gerätebezeichnung passt, bleibt, wie sie ist
    assert nuclei.proton_frequency("13C NMR", "90") == pytest.approx(357.92, abs=0.01)
    assert nuclei.proton_frequency("13C NMR", "keine Zahl") is None


# ---------- Kopfzeilen-Vorschlag ----------

def test_kopfzeile_uebernimmt_die_bedingungen_der_schon_erfassten_kerne(client):
    """Lösungsmittel und Temperatur stehen wörtlich wie beim ¹H, die Frequenz
    wird aus dessen Gerätefrequenz umgerechnet."""
    mol = make_molecule(client)
    proton = next(e for e in mol["entries"] if e["type_code"] == "nmr_1h")
    client.post(f"/api/entries/{proton['id']}/notes",
                json={"text": "1H NMR (500 MHz, CDCl3, 298 K) δ [ppm] = 7.26 (s, 1H, CH)"})

    fluor = add(client, mol, "19F NMR")
    text = client.get(f"/api/entries/{fluor['id']}/head").json()["text"]
    assert text == "19F NMR (471 MHz, CDCl3, 298 K) δ [ppm] = "
    # auch für die festen Typen
    kohlenstoff = next(e for e in mol["entries"] if e["type_code"] == "nmr_13c")
    assert (client.get(f"/api/entries/{kohlenstoff['id']}/head").json()["text"]
            == "13C NMR (126 MHz, CDCl3, 298 K) δ [ppm] = ")


def test_kopfzeile_erfindet_nichts(client):
    """Ohne erfasste Bedingungen bleibt es bei der Bezeichnung; die Notiz wird
    ohnehin nur auf Knopfdruck gefüllt."""
    mol = make_molecule(client)
    fluor = add(client, mol, "19F NMR")
    assert client.get(f"/api/entries/{fluor['id']}/head").json()["text"] == "19F NMR δ [ppm] = "

    andere = add(client, mol, "Elementaranalyse")
    assert client.get(f"/api/entries/{andere['id']}/head").status_code == 422


def test_kopfzeile_auch_aus_dem_13c_wenn_kein_1h_erfasst_ist(client):
    """Steht nur das ¹³C, folgt die Gerätefrequenz daraus."""
    mol = make_molecule(client)
    kohlenstoff = next(e for e in mol["entries"] if e["type_code"] == "nmr_13c")
    client.post(f"/api/entries/{kohlenstoff['id']}/notes",
                json={"text": "13C NMR (126 MHz, DMSO-d6) δ [ppm] = 128.5"})
    phosphor = add(client, mol, "31P{1H} NMR")
    text = client.get(f"/api/entries/{phosphor['id']}/head").json()["text"]
    assert text == "31P{1H} NMR (202 MHz, DMSO-d6) δ [ppm] = "
