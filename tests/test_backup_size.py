"""Tests für die Beschleunigung des App-Starts.

Beim Start und beim Beenden sichert die App Datenbank und Bilder. Liegt der
Datenordner auf einem Netzlaufwerk, war das der mit Abstand teuerste Teil des
Öffnens: die aus ChemDraw eingefügten Bilder sind unkomprimierte Bitmaps und
wurden auch so ins ZIP gelegt (bei 30 Molekülen rund 37 MB, einmal übers Netz
gelesen und einmal geschrieben — bei jedem Start UND jedem Beenden).

Zwei Dinge sichern das hier ab:
* Die Bilder werden gepackt abgelegt.
* Das automatische Backup entfällt, wenn sich seit dem letzten nichts geändert
  hat — der Rückweg besteht dann ja bereits als Datei.
Das Backup von Hand („Backup jetzt") sichert dagegen immer.

Dazu kommt, was der Nutzer beim Öffnen sieht: der Browser darf die Adresse
erst bekommen, wenn der Server sie auch beantwortet.
"""
import importlib
import os
import threading
import zipfile

import pytest
from fastapi.testclient import TestClient

from app import db
from app.main import app
from app.models import Molecule, Project

# Gut komprimierbar, wie die Strukturbilder aus ChemDraw (viel Weißfläche)
BITMAP = b"BM" + bytes(200_000)


@pytest.fixture()
def client(tmp_path):
    db.init_db(tmp_path / "test.db")
    with TestClient(app) as c:
        yield c


def add_image(name: str = "mol-1.bmp", inhalt: bytes = BITMAP) -> None:
    """Bild ablegen UND von einem Molekül aus verlinken — unverlinkte Bilder
    räumt cleanup_orphan_images vor jedem Backup zu Recht weg."""
    d = db.images_dir()
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_bytes(inhalt)
    with db._SessionLocal() as s:
        vorhanden = s.query(Molecule).filter_by(image_path=name).first()
        if vorhanden:
            return
        projekt = s.query(Project).first()
        if projekt is None:
            projekt = Project(name="Testprojekt")
            s.add(projekt)
            s.flush()
        s.add(Molecule(project_id=projekt.id, name=name, image_path=name))
        s.commit()


def change_db() -> None:
    with db._SessionLocal() as s:
        s.add(Project(name=f"P{s.query(Project).count()}"))
        s.commit()


def test_bilder_werden_gepackt_gesichert(client):
    add_image()
    name = db.create_backup()
    ziel = db._backup_dir / name
    with zipfile.ZipFile(ziel) as zf:
        eintrag = zf.getinfo("images/mol-1.bmp")
    assert eintrag.compress_type == zipfile.ZIP_DEFLATED
    # Die Bitmap darf im ZIP nur einen Bruchteil ihrer Größe einnehmen
    assert eintrag.compress_size < len(BITMAP) // 20
    assert ziel.stat().st_size < len(BITMAP) // 10


def test_gepacktes_backup_stellt_bilder_unveraendert_wieder_her(client):
    add_image()
    name = db.create_backup()
    (db.images_dir() / "mol-1.bmp").unlink()

    db.restore_backup(name)
    assert (db.images_dir() / "mol-1.bmp").read_bytes() == BITMAP


def test_altes_ungepacktes_backup_bleibt_lesbar(client, tmp_path):
    """Backups aus früheren App-Versionen liegen unkomprimiert vor."""
    add_image()
    alt = db._backup_dir / "app-20200101-000000.zip"
    alt.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(alt, "w") as zf:
        zf.write(db._db_path, "app.db", compress_type=zipfile.ZIP_DEFLATED)
        zf.write(db.images_dir() / "mol-1.bmp", "images/mol-1.bmp",
                 compress_type=zipfile.ZIP_STORED)
    (db.images_dir() / "mol-1.bmp").unlink()

    db.restore_backup(alt.name)
    assert (db.images_dir() / "mol-1.bmp").read_bytes() == BITMAP


def test_start_backup_entfaellt_wenn_sich_nichts_geaendert_hat(client):
    add_image()
    erstes = db.create_backup(only_if_changed=True)
    assert erstes is not None

    assert db.create_backup(only_if_changed=True) is None
    assert db.create_backup(only_if_changed=True) is None
    assert [b["name"] for b in db.list_backups()] == [erstes]


def test_geaenderte_datenbank_wird_wieder_gesichert(client):
    add_image()
    db.create_backup(only_if_changed=True)
    change_db()
    assert db.create_backup(only_if_changed=True) is not None


def test_geaendertes_bild_wird_wieder_gesichert(client):
    """Auch wenn die Datenbank gleich bleibt: neue, geänderte oder gelöschte
    Bilder müssen ein Backup auslösen."""
    add_image()
    db.create_backup(only_if_changed=True)

    add_image("mol-2.bmp")  # neues Bild
    assert db.create_backup(only_if_changed=True) is not None

    db.create_backup(only_if_changed=True)
    (db.images_dir() / "mol-2.bmp").write_bytes(BITMAP + b"anders")  # geändert
    assert db.create_backup(only_if_changed=True) is not None

    db.create_backup(only_if_changed=True)
    (db.images_dir() / "mol-2.bmp").unlink()  # gelöscht
    assert db.create_backup(only_if_changed=True) is not None


def test_aenderung_wird_auch_bei_gleicher_groesse_und_zeit_erkannt(client, tmp_path):
    """Der gefährlichste Fall, deshalb ohne Zeitspiel nachgestellt: Die
    Datenbank hat sich geändert, sieht von außen aber unverändert aus. Genau
    das passiert im Betrieb — SQLite schreibt in vorhandene Seiten (Größe
    bleibt gleich), und Windows führt die Änderungszeit einer geöffneten
    Datei nur grob nach. Fiele das Backup dann aus, wäre die Arbeit der
    Sitzung nirgends gesichert."""
    add_image()
    db.create_backup(only_if_changed=True)
    assert db.create_backup(only_if_changed=True) is None  # noch nichts passiert

    vorher = db._db_path.stat()
    roh = bytearray(db._db_path.read_bytes())
    roh[-16:] = bytes(16) if roh[-16:] != bytes(16) else b"x" * 16  # Inhalt ändern
    db._db_path.write_bytes(roh)                                    # Größe bleibt gleich
    os.utime(db._db_path, ns=(vorher.st_atime_ns, vorher.st_mtime_ns))  # Zeit zurück

    assert db._db_path.stat().st_size == vorher.st_size
    assert db._db_path.stat().st_mtime_ns == vorher.st_mtime_ns
    assert db.create_backup(only_if_changed=True) is not None


def test_aenderung_im_laufenden_betrieb_wird_gesichert(client):
    """Ergänzend der normale Weg: Änderung über die App, Datenbankdatei die
    ganze Zeit geöffnet."""
    add_image()
    db.create_backup(only_if_changed=True)
    assert db.create_backup(only_if_changed=True) is None

    client.post("/api/projects", json={"name": "Im Betrieb angelegt"})
    assert db.create_backup(only_if_changed=True) is not None


def test_backup_von_hand_sichert_immer(client):
    """Der Knopf „Backup jetzt" darf nie stillschweigend nichts tun."""
    add_image()
    db.create_backup(only_if_changed=True)
    assert db.create_backup(only_if_changed=True) is None  # automatisch: übersprungen

    r = client.post("/api/backups")
    assert r.status_code == 201
    assert len(db.list_backups()) == 2


def test_fehlendes_kennzeichen_sichert_im_zweifel(client):
    """Ohne (oder mit unlesbarem) Kennzeichen wird gesichert, nicht übersprungen."""
    add_image()
    db.create_backup(only_if_changed=True)
    (db._backup_dir / db.BACKUP_STATE_FILE).write_text("kaputt", encoding="utf-8")
    assert db.create_backup(only_if_changed=True) is not None


def test_geloeschtes_backup_wird_neu_angelegt(client):
    """Zeigt das Kennzeichen auf ein Backup, das es nicht mehr gibt, muss
    wieder gesichert werden — sonst stünde man ohne Rückweg da."""
    add_image()
    name = db.create_backup(only_if_changed=True)
    (db._backup_dir / name).unlink()
    assert db.create_backup(only_if_changed=True) is not None


def test_transferdatei_wird_gepackt(client, tmp_path):
    add_image()
    ziel = tmp_path / "raus"
    ziel.mkdir()
    db.export_transfer(ziel)
    datei = next(ziel.glob("*.zip"))
    with zipfile.ZipFile(datei) as zf:
        assert zf.getinfo("images/mol-1.bmp").compress_type == zipfile.ZIP_DEFLATED
    assert datei.stat().st_size < len(BITMAP) // 10


def test_verschluesselte_transferdatei_bleibt_lesbar(client, tmp_path):
    """Packen und Verschlüsseln müssen zusammen funktionieren."""
    add_image()
    change_db()
    ziel = tmp_path / "raus"
    ziel.mkdir()
    db.export_transfer(ziel, password="geheim")
    datei = next(ziel.glob("*.zip"))
    assert datei.stat().st_size < len(BITMAP) // 10

    ergebnis = db.import_transfer(datei, password="geheim")
    assert ergebnis["molecules"] >= 0
    assert (db.images_dir() / "mol-1.bmp").read_bytes() == BITMAP


def test_abgebrochenes_backup_hinterlaesst_kein_halbes_zip(client, monkeypatch):
    """Das Beenden-Backup läuft, während der Nutzer das schwarze Fenster
    schließt — Windows räumt den Vorgang nach wenigen Sekunden ab. Ein halb
    geschriebenes ZIP wäre unbrauchbar, würde aber als Backup angeboten.
    Deshalb entsteht es unter einem Arbeitsnamen und heißt erst fertig so."""
    add_image()
    echte_zipfile = zipfile.ZipFile

    class Abbruch(echte_zipfile):
        def write(self, *args, **kwargs):
            super().write(*args, **kwargs)
            raise OSError("Verbindung zum Datenordner verloren")

    monkeypatch.setattr(zipfile, "ZipFile", Abbruch)
    with pytest.raises(OSError):
        db.create_backup()
    monkeypatch.undo()

    assert db.list_backups() == []  # kein halbes ZIP im Angebot
    assert db.create_backup() is not None  # der nächste Versuch geht wieder
    assert not list(db._backup_dir.glob(f"app-*{db.PART_SUFFIX}"))  # Rest weggeräumt


def test_aufraeumen_wartet_auf_ein_laufendes_bild_einfuegen(client):
    """Ein eingefügtes Bild liegt einen Moment im images-Ordner, ohne schon in
    der Datenbank zu stehen. Räumt ein gleichzeitiges Backup genau dann auf,
    hielte es die neue Datei für einen Überrest — also teilen sich beide
    dieselbe Sperre."""
    ordner = db.images_dir()
    ordner.mkdir(parents=True, exist_ok=True)
    neues_bild = ordner / "gerade-eingefuegt.bmp"
    fertig = threading.Event()

    def aufraeumen():
        db.cleanup_orphan_images()
        fertig.set()

    thread = threading.Thread(target=aufraeumen)
    with db.image_lock:  # wie api._save_image_data um Schreiben und Commit
        neues_bild.write_bytes(BITMAP)  # Datei da, Eintrag in der DB fehlt noch
        thread.start()
        assert not fertig.wait(0.3)  # wartet auf die Sperre
        assert neues_bild.is_file()
    thread.join(5)
    assert fertig.is_set()


def test_browser_wird_erst_beim_antwortenden_server_geoeffnet(monkeypatch):
    """Vorher geöffnet zeigt der Browser „Website nicht erreichbar“ und lädt
    von sich aus nicht nach — der Nutzer müsste selbst neu laden, bis der
    Start durch ist."""
    run = importlib.import_module("run")
    antworten = iter([False, False, True])
    geoeffnet: list[str] = []
    monkeypatch.setattr(run, "server_running", lambda: next(antworten))
    monkeypatch.setattr(run.webbrowser, "open", geoeffnet.append)
    monkeypatch.setattr(run.time, "sleep", lambda _: None)

    run.open_browser_when_ready()

    assert geoeffnet == [run.URL]
    assert next(antworten, None) is None  # hat bis zur Antwort gewartet
