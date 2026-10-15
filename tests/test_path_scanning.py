"""Absicherung der Beschleunigungen rund um die Pfadprüfung:

- Das Dashboard darf keine Datei mehr anfassen (die Kennzahlen hängen nur an
  den Einträgen) — auf einem Datenordner im Netz war das der halbe Aufwand
  jedes Neuladens.
- Innerhalb einer Antwort wird jeder Pfad höchstens einmal geprüft, ohne dass
  sich das Ergebnis ändert.
- Beides darf die angezeigten Werte nicht verschieben: Dashboard und
  Projektliste müssen dieselbe Vollständigkeit melden.
"""
import os.path

import pytest
from fastapi.testclient import TestClient

from app import api, db, paths, relink
from app.main import app


@pytest.fixture()
def client(tmp_path):
    db.init_db(tmp_path / "test.db")
    with TestClient(app) as c:
        yield c


def make_molecule(client, name="Verbindung 1"):
    project = client.post("/api/projects", json={"name": "Testprojekt"}).json()
    return client.post(
        "/api/molecules", json={"project_id": project["id"], "name": name}
    ).json()


def link_paths(client, mol, existing: str, missing: str):
    """Einen vorhandenen und einen toten Pfad verlinken. Danach warten, bis
    die Dateikennungen im Hintergrund nachgetragen sind (app/relink.py) —
    sonst zählte deren einmaliger Zugriff in die Messung der nächsten
    Anfrage hinein."""
    client.patch(f"/api/entries/{mol['entries'][0]['id']}", json={"file_path": existing})
    client.patch(f"/api/entries/{mol['entries'][1]['id']}", json={"folder_path": missing})
    relink.flush()


@pytest.fixture()
def counted(monkeypatch):
    """Zählt jeden Zugriff des Servers aufs Dateisystem — einzeln geprüfte
    Pfade wie gelesene Ordner. Auf einem Datenordner im Netz ist jeder davon
    eine Anfrage übers Netz, ihre Zahl ist also das eigentliche Maß."""
    calls: list[str] = []
    echt_stat, echt_exists, echt_scandir = os.stat, os.path.exists, os.scandir
    monkeypatch.setattr(os, "stat",
                        lambda p, *a, _f=echt_stat, **k: (calls.append(str(p)), _f(p, *a, **k))[1])
    monkeypatch.setattr(os.path, "exists",
                        lambda p, _f=echt_exists: (calls.append(str(p)), _f(p))[1])
    monkeypatch.setattr(os, "scandir",
                        lambda p=".", _f=echt_scandir: (calls.append(str(p)), _f(p))[1])
    return calls


def test_dashboard_fasst_keine_datei_an(client, tmp_path, counted):
    mol = make_molecule(client)
    link_paths(client, mol, str(tmp_path), str(tmp_path / "weg"))
    counted.clear()

    assert client.get("/api/dashboard").status_code == 200
    assert counted == []


def test_projektliste_prueft_jeden_pfad_nur_einmal(client, tmp_path, counted):
    """Der tote Verweis wird für <feld>_exists und für broken_paths gebraucht —
    aber nur einmal beim Dateisystem erfragt."""
    mol = make_molecule(client)
    tot = str(tmp_path / "weg")
    link_paths(client, mol, str(tmp_path), tot)
    counted.clear()

    liste = client.get("/api/projects").json()
    assert counted.count(tot) == 1

    eintraege = liste[0]["molecules"][0]["entries"]
    assert eintraege[0]["file_exists"] is True
    assert eintraege[1]["folder_exists"] is False
    assert liste[0]["molecules"][0]["broken_paths"] == 1


def test_dashboard_und_liste_melden_dieselbe_vollstaendigkeit(client):
    """Beide Wege berechnen die Vollständigkeit getrennt — sie müssen
    übereinstimmen, auch wenn Einträge auf „nicht zutreffend“ stehen."""
    projekt = client.post("/api/projects", json={"name": "Testprojekt"}).json()
    neu = lambda name: client.post(
        "/api/molecules", json={"project_id": projekt["id"], "name": name}
    ).json()
    offen, fertig = neu("Offen"), neu("Fertig")
    for e in fertig["entries"]:
        client.patch(f"/api/entries/{e['id']}", json={"status": "present"})
    client.patch(f"/api/entries/{offen['entries'][0]['id']}", json={"required": False})

    dash = client.get("/api/dashboard").json()
    molekuele = [m for p in client.get("/api/projects").json() for m in p["molecules"]]
    assert dash["total_molecules"] == len(molekuele)
    assert dash["complete_molecules"] == sum(
        1 for m in molekuele if m["completeness"] == "complete"
    )
    assert dash["complete_molecules"] == 1


def test_merkliste_liefert_dasselbe_wie_die_einzelpruefung(tmp_path):
    """scan_scope darf das Ergebnis von exists() nicht verändern."""
    da = tmp_path / "da.txt"
    da.write_text("x", encoding="utf-8")
    weg = tmp_path / "weg.txt"

    ohne = [paths.exists(str(da)), paths.exists(str(weg))]
    with paths.scan_scope():
        mit = [paths.exists(str(da)), paths.exists(str(weg))]
        wiederholt = [paths.exists(str(da)), paths.exists(str(weg))]
    assert ohne == mit == wiederholt == [True, False]
    # nach dem Geltungsbereich wird wieder frisch geprüft
    weg.write_text("x", encoding="utf-8")
    assert paths.exists(str(weg)) is True


def test_merkliste_endet_mit_der_anfrage(tmp_path):
    """Eine Datei, die zwischen zwei Anfragen entsteht, wird sofort gesehen —
    gemerkt wird nur innerhalb eines Geltungsbereichs."""
    neu = tmp_path / "neu.txt"
    with paths.scan_scope():
        assert paths.exists(str(neu)) is False
    neu.write_text("x", encoding="utf-8")
    with paths.scan_scope():
        assert paths.exists(str(neu)) is True


def test_geltungsbereiche_verschachteln_sich(tmp_path):
    """molecule_summary öffnet einen eigenen Geltungsbereich; innerhalb der
    Projektliste darf das den äußeren nicht vorzeitig beenden."""
    datei = tmp_path / "x.txt"
    datei.write_text("x", encoding="utf-8")
    with paths.scan_scope():
        assert paths.exists(str(datei)) is True
        with paths.scan_scope():
            assert paths.exists(str(datei)) is True
        datei.unlink()
        assert paths.exists(str(datei)) is True  # noch aus der Merkliste
    assert paths.exists(str(datei)) is False     # danach frisch geprüft


# ---------- Gebündelte Vorabprüfung (paths.prefetch) ----------

def test_ordner_wird_einmal_gelesen_statt_jede_datei_einzeln(tmp_path, counted):
    """Die verwalteten Bilder liegen alle im selben images-Ordner. Statt jede
    Datei zu erfragen, wird der Ordner einmal gelesen — bei zehn Dateien also
    ein Netzzugriff statt zehn."""
    dateien = []
    for i in range(10):
        f = tmp_path / f"bild-{i}.png"
        f.write_text("x", encoding="utf-8")
        dateien.append(str(f))
    fehlt = str(tmp_path / "gibt-es-nicht.png")
    counted.clear()

    with paths.scan_scope():
        paths.prefetch(dateien + [fehlt])
        assert all(paths.exists(d) for d in dateien)
        assert paths.exists(fehlt) is False
    assert counted == [str(tmp_path)]


def test_vorabpruefung_liefert_dasselbe_wie_einzelpruefung(tmp_path):
    """Gebündelt geprüft muss exakt dasselbe herauskommen wie einzeln —
    auch für Ordner, Wurzeln und Pfade mit abweichender Schreibweise."""
    (tmp_path / "unterordner").mkdir()
    datei = tmp_path / "Datei.TXT"
    datei.write_text("x", encoding="utf-8")
    kandidaten = [
        str(datei),
        str(datei).lower(),            # Windows unterscheidet keine Schreibweise
        str(tmp_path / "unterordner"),
        str(tmp_path / "fehlt.txt"),
        str(tmp_path),
        str(tmp_path) + os.sep,        # abschließender Trenner
        r"\\kein-server-xyz\share\a.txt",
        r"\\kein-server-xyz\share",    # die Freigabe selbst
    ]
    einzeln = [os.path.exists(k) for k in kandidaten]
    paths._down.clear()
    with paths.scan_scope():
        paths.prefetch(kandidaten)
        gebuendelt = [paths.exists(k) for k in kandidaten]
    paths._down.clear()
    assert gebuendelt == einzeln


def test_stat_liefert_zeiten_ohne_zweiten_zugriff(tmp_path, counted):
    """cdx_stale vergleicht Änderungszeiten. Die kommen aus derselben
    Abfrage, die schon die Existenz beantwortet hat."""
    bild = tmp_path / "mol.png"
    bild.write_text("x", encoding="utf-8")
    cdx = tmp_path / "mol.cdx"
    cdx.write_text("x", encoding="utf-8")
    os.utime(cdx, (0, os.stat(bild).st_mtime + 60))  # .cdx später bearbeitet
    counted.clear()

    with paths.scan_scope():
        paths.prefetch([str(bild), str(cdx)])
        assert api.cdx_stale(str(bild), str(cdx)) is True
        assert api.cdx_stale(str(cdx), str(bild)) is False
        assert paths.exists(str(bild)) is True
    assert counted == [str(tmp_path)]


def test_unlesbarer_ordner_faellt_auf_einzelpruefung_zurueck(tmp_path):
    """Lässt sich ein Ordner nicht lesen, muss jeder Pfad darin einzeln
    geprüft werden — nur so greift auch die Erkennung toter Freigaben."""
    fehlt = tmp_path / "gibt-es-nicht"
    kandidaten = [str(fehlt / "a.txt"), str(fehlt / "b.txt")]
    with paths.scan_scope():
        paths.prefetch(kandidaten)
        assert [paths.exists(k) for k in kandidaten] == [False, False]


def test_projektliste_prueft_bilder_gebuendelt(client, tmp_path, counted):
    """Ende zu Ende: die Bilder aller Moleküle kosten zusammen einen Zugriff
    auf den images-Ordner, nicht einen pro Bild."""
    projekt = client.post("/api/projects", json={"name": "Testprojekt"}).json()
    bilder = db.images_dir()
    bilder.mkdir(parents=True, exist_ok=True)
    for i in range(5):
        name = f"mol-{i}.png"
        (bilder / name).write_text("x", encoding="utf-8")
        mol = client.post("/api/molecules",
                          json={"project_id": projekt["id"], "name": f"M{i}"}).json()
        client.patch(f"/api/molecules/{mol['id']}", json={"image_path": str(bilder / name)})
    counted.clear()

    liste = client.get("/api/projects").json()
    molekuele = liste[0]["molecules"]
    assert len(molekuele) == 5
    assert all(m["image_exists"] for m in molekuele)
    assert counted.count(str(bilder)) == 1
    assert not any(c.endswith(".png") for c in counted)
