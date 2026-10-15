"""Start-Backup im Hintergrund.

Beim App-Start wurden Datenbank und kompletter Bildbestand gepackt, bevor der
Server Anfragen annahm. Auf dem Netzlaufwerk (120 MB Bilder, langsame
Freigabe) dauerte das über eine Minute — das schwarze Fenster wirkte wie
„App startet nicht“ und wurde geschlossen. Jetzt startet der Server sofort,
das Backup läuft nebenher und enthält trotzdem genau den Stand beim Start.
"""
import sqlite3
import threading
import zipfile
from pathlib import Path

import pytest

from app import db


def _projektnamen(db_datei: Path) -> list[str]:
    con = sqlite3.connect(db_datei)
    try:
        return [n for (n,) in con.execute("SELECT name FROM projects ORDER BY id")]
    finally:
        con.close()


def _projekt_anlegen(db_datei: Path, name: str) -> None:
    con = sqlite3.connect(db_datei)
    con.execute("INSERT INTO projects (name, sort_order, created_at) VALUES (?, 0, '2026-01-01')",
                (name,))
    con.commit()
    con.close()


@pytest.fixture()
def datensatz(tmp_path):
    """Bestehender Datensatz ohne Backup-Kennzeichen — der nächste Start sichert."""
    pfad = tmp_path / "test.db"
    db.init_db(pfad)
    db.close_db()
    _projekt_anlegen(pfad, "Beim Start")
    yield pfad
    if db._start_backup is not None:
        db._start_backup.join(10)
    db.close_db()


@pytest.fixture()
def angehalten(monkeypatch):
    """Hält das Backup an, sobald es ans Packen geht."""
    gestartet, weiter = threading.Event(), threading.Event()
    echtes_aufraeumen = db.cleanup_orphan_images

    def warten():
        gestartet.set()
        weiter.wait(10)
        return echtes_aufraeumen()

    monkeypatch.setattr(db, "cleanup_orphan_images", warten)
    yield gestartet, weiter
    weiter.set()


def test_start_wartet_nicht_auf_das_backup(datensatz, angehalten):
    gestartet, weiter = angehalten
    db.init_db(datensatz, background_backup=True)
    assert gestartet.wait(5)          # das Backup läuft noch …
    assert db._engine is not None     # … und die App ist trotzdem schon bereit
    assert db.list_backups() == []

    weiter.set()
    db._start_backup.join(10)
    assert len(db.list_backups()) == 1


def test_start_backup_enthaelt_den_stand_beim_start(datensatz, angehalten, tmp_path):
    gestartet, weiter = angehalten
    db.init_db(datensatz, background_backup=True)
    assert gestartet.wait(5)
    _projekt_anlegen(datensatz, "Nach dem Start")  # erste Arbeit, während gepackt wird

    weiter.set()
    db._start_backup.join(10)
    [backup] = db.list_backups()
    aus_backup = tmp_path / "aus-backup.db"
    with zipfile.ZipFile(db._backup_dir / backup["name"]) as zf:
        aus_backup.write_bytes(zf.read("app.db"))
    assert _projektnamen(aus_backup) == ["Beim Start"]
    # Der Datensatz hat sich währenddessen geändert: kein Kennzeichen, damit
    # der nächste Start nicht fälschlich überspringt
    assert not (db._backup_dir / db.BACKUP_STATE_FILE).exists()


def test_unveraenderter_start_setzt_das_kennzeichen(datensatz):
    db.init_db(datensatz, background_backup=True)
    db._start_backup.join(10)
    assert len(db.list_backups()) == 1
    assert db.create_backup(only_if_changed=True) is None  # nichts Neues zu sichern


def test_datenordner_wechsel_wartet_auf_laufendes_start_backup(datensatz, angehalten):
    gestartet, weiter = angehalten
    db.init_db(datensatz, background_backup=True)
    assert gestartet.wait(5)

    geschlossen = threading.Event()
    faden = threading.Thread(target=lambda: (db.close_db(), geschlossen.set()))
    faden.start()
    assert not geschlossen.wait(0.3)  # wartet, statt dem Backup den Ordner wegzuziehen

    weiter.set()
    assert geschlossen.wait(10)
    faden.join(10)
    assert len(db.list_backups()) == 1


def test_sqlite_uri_fuer_netzlaufwerk_und_sonderzeichen():
    assert db._sqlite_ro_uri(Path(r"\\server\home\Daten\app.db")) == (
        "file:////server/home/Daten/app.db?mode=ro")
    assert db._sqlite_ro_uri(Path(r"C:\Daten #1 & 100%\app.db")) == (
        "file:///C:/Daten%20%231%20%26%20100%25/app.db?mode=ro")


def test_aufraeumen_in_ordner_mit_sonderzeichen(tmp_path):
    """Mit dem alten URI öffnete SQLite hier eine andere, leere Datei."""
    from app.models import Molecule, Project

    db.init_db(tmp_path / "Daten #1 & 100% Co" / "app.db")
    try:
        bilder = db.images_dir()
        bilder.mkdir(parents=True, exist_ok=True)
        (bilder / "mol-1.bmp").write_bytes(b"BM" + bytes(100))
        (bilder / "verwaist.bmp").write_bytes(b"BM" + bytes(100))
        with db._SessionLocal() as s:
            p = Project(name="P")
            s.add(p)
            s.flush()
            s.add(Molecule(project_id=p.id, name="M", image_path="mol-1.bmp"))
            s.commit()

        assert db.cleanup_orphan_images() == 1
        assert (bilder / "mol-1.bmp").exists()
        assert not (bilder / "verwaist.bmp").exists()
    finally:
        db.close_db()
