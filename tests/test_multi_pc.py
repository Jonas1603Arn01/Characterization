"""Tests für das Arbeiten von mehreren PCs mit demselben Datensatz:
PC-unabhängige Bildverweise, laufwerksunabhängige Pfade (UNC), Sperrdatei
mit Lesemodus und Wechsel des Datenordners."""
import base64
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import config, db, paths
from app.main import app

PNG_1x1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)

UNC = "\\\\server\\home"


@pytest.fixture()
def client(tmp_path):
    db.init_db(tmp_path / "test.db")
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def fake_h_drive(monkeypatch):
    """H: ist ein Netzlaufwerk auf \\\\server\\home, C: ein lokales Laufwerk."""
    monkeypatch.setattr(paths, "_mapped_drives", lambda: {"H": UNC})
    monkeypatch.setattr(paths, "_drive_type",
                        lambda letter: paths.DRIVE_REMOTE if letter == "H" else paths.DRIVE_FIXED)
    monkeypatch.setattr(paths, "_IS_WIN", True)


def make_mol(client, name="M-1"):
    p = client.post("/api/projects", json={"name": "P"}).json()
    return client.post("/api/molecules", json={"project_id": p["id"], "name": name}).json()


def stored(tmp_path, sql):
    con = sqlite3.connect(tmp_path / "test.db")
    try:
        return con.execute(sql).fetchall()
    finally:
        con.close()


# ---------- Bilder: nur Dateiname in der DB ----------

def test_pasted_image_is_stored_by_name_only(client, tmp_path):
    mol = make_mol(client)
    r = client.post(f"/api/molecules/{mol['id']}/image", content=PNG_1x1)
    assert r.status_code == 200, r.text
    [(value,)] = stored(tmp_path, "SELECT image_path FROM molecules")
    assert "\\" not in value and "/" not in value  # relativ zum images-Ordner
    # Die API liefert trotzdem den absoluten Pfad dieses PCs
    assert Path(r.json()["image_path"]).parent == (tmp_path / "images").resolve()
    assert r.json()["image_exists"] is True
    assert client.get(f"/api/molecules/{mol['id']}/image").status_code == 200


def test_old_absolute_image_paths_are_relativized_on_start(tmp_path):
    """Datensatz einer älteren Version: Bildpfade zeigen absolut auf den
    images-Ordner -> beim Start auf den Dateinamen gekürzt."""
    db.init_db(tmp_path / "test.db")
    with TestClient(app) as c:
        mol = make_mol(c)
        c.post(f"/api/molecules/{mol['id']}/image", content=PNG_1x1)
    [(name,)] = stored(tmp_path, "SELECT image_path FROM molecules")
    absolute = str((tmp_path / "images" / name).resolve())
    con = sqlite3.connect(tmp_path / "test.db")
    con.execute("UPDATE molecules SET image_path = ?", (absolute,))
    con.commit()
    con.close()

    db.init_db(tmp_path / "test.db")  # "nächster Start"
    with TestClient(app) as c:
        mols = c.get("/api/projects").json()[0]["molecules"]
        assert mols[0]["image_exists"] is True
    assert stored(tmp_path, "SELECT image_path FROM molecules") == [(name,)]


# ---------- Verlinkte Dateien: Netzlaufwerk -> UNC ----------

def test_paths_round_trip(fake_h_drive):
    assert paths.to_portable("H:\\Uni\\x.docx") == UNC + "\\Uni\\x.docx"
    assert paths.to_portable("h:/Uni/x.docx") == UNC + "\\Uni\\x.docx"
    assert paths.to_portable("H:\\") == UNC + "\\"
    assert paths.to_portable("C:\\lokal\\x.docx") == "C:\\lokal\\x.docx"
    assert paths.to_display(UNC + "\\Uni\\x.docx") == "H:\\Uni\\x.docx"
    assert paths.to_display(UNC) == "H:\\"
    assert paths.to_display("\\\\other\\share\\x") == "\\\\other\\share\\x"
    assert paths.is_local_only("C:\\lokal\\x.docx") is True
    assert paths.is_local_only("H:\\Uni\\x.docx") is False
    assert paths.is_local_only(UNC + "\\x") is False


def test_linked_paths_are_stored_as_unc_and_shown_with_drive_letter(client, tmp_path, fake_h_drive):
    mol = make_mol(client)
    entry = mol["entries"][0]
    r = client.patch(f"/api/entries/{entry['id']}", json={"file_path": "H:\\Uni\\proc.docx"})
    assert r.status_code == 200, r.text
    assert r.json()["file_path"] == "H:\\Uni\\proc.docx"  # Anzeige: lokaler Buchstabe
    assert r.json()["file_local"] is False
    assert stored(tmp_path, "SELECT file_path FROM data_entries WHERE file_path IS NOT NULL") \
        == [(UNC + "\\Uni\\proc.docx",)]

    r = client.post(f"/api/entries/{entry['id']}/files", json={"path": "H:\\Uni\\spec.pdf"})
    assert r.status_code == 201
    assert stored(tmp_path, "SELECT path FROM entry_files") == [(UNC + "\\Uni\\spec.pdf",)]

    # Lokaler Pfad bleibt lokal und wird als solcher gekennzeichnet
    r = client.patch(f"/api/entries/{entry['id']}", json={"folder_path": "C:\\lokal\\ordner"})
    assert r.json()["folder_path"] == "C:\\lokal\\ordner"
    assert r.json()["folder_local"] is True

    # Literatur-SI am Molekül: gleiche Regeln (UNC gespeichert, Buchstabe angezeigt)
    r = client.patch(f"/api/molecules/{mol['id']}", json={"si_path": "H:\\Uni\\si.pdf"})
    assert r.json()["si_path"] == "H:\\Uni\\si.pdf"
    assert r.json()["si_local"] is False
    assert stored(tmp_path, "SELECT si_path FROM molecules") == [(UNC + "\\Uni\\si.pdf",)]
    r = client.patch(f"/api/molecules/{mol['id']}", json={"si_path": "C:\\lokal\\si.pdf"})
    assert r.json()["si_local"] is True


def test_existing_drive_paths_are_migrated_on_start(tmp_path, fake_h_drive):
    db.init_db(tmp_path / "test.db")
    with TestClient(app) as c:
        make_mol(c)
    con = sqlite3.connect(tmp_path / "test.db")
    con.execute("UPDATE data_entries SET file_path = 'H:\\Uni\\alt.docx'")
    con.execute("UPDATE molecules SET si_path = 'H:\\Uni\\alt_si.pdf'")
    con.commit()
    con.close()
    db.init_db(tmp_path / "test.db")
    assert stored(tmp_path, "SELECT DISTINCT file_path FROM data_entries WHERE file_path IS NOT NULL") \
        == [(UNC + "\\Uni\\alt.docx",)]
    assert stored(tmp_path, "SELECT si_path FROM molecules") == [(UNC + "\\Uni\\alt_si.pdf",)]


def test_exists_remembers_unreachable_server(monkeypatch):
    calls = []

    def fake_stat(p, *args, **kwargs):
        calls.append(p)
        raise OSError("Netzwerkpfad nicht gefunden")

    def fake_exists(p):
        calls.append(p)
        return False

    monkeypatch.setattr(paths.os, "stat", fake_stat)
    monkeypatch.setattr(paths.os.path, "exists", fake_exists)
    paths._down.clear()
    assert paths.exists("\\\\down\\share\\a.txt") is False
    assert paths.exists("\\\\down\\share\\b.txt") is False
    # 1. Pfad: Datei + Freigabe-Wurzel geprüft; 2. Pfad: gar nicht mehr
    assert calls == ["\\\\down\\share\\a.txt", "\\\\down\\share"]
    paths._down.clear()


def test_unreachable_share_is_checked_once_per_request(monkeypatch):
    """Tote Pfade derselben Freigabe kosteten je zwei Zugriffe (Datei und
    Freigabe-Wurzel). Innerhalb einer Anfrage wird die Wurzel nur einmal
    geprüft — an der Erkennung selbst ändert das nichts."""
    wurzeln = []
    monkeypatch.setattr(paths.os, "stat",
                        lambda p, *a, **k: (_ for _ in ()).throw(OSError("weg")))
    monkeypatch.setattr(paths.os.path, "exists",
                        lambda p: (wurzeln.append(p), True)[1])  # Freigabe da, Datei nicht
    paths._down.clear()
    with paths.scan_scope():
        assert paths.exists("\\\\srv\\share\\a.txt") is False
        assert paths.exists("\\\\srv\\share\\b.txt") is False
        assert paths.exists("\\\\srv\\share\\c.txt") is False
    assert wurzeln == ["\\\\srv\\share"]
    assert paths._down == {}  # Freigabe war erreichbar -> nicht als tot gemerkt
    paths._down.clear()


# ---------- Sperre: nur ein PC schreibt ----------

def test_lock_file_is_written_and_removed(tmp_path):
    db.init_db(tmp_path / "test.db")
    lock = tmp_path / db.LOCK_FILE
    assert lock.is_file()
    entry = json.loads(lock.read_text())
    assert entry["computer"] == db.computer_name()
    assert db.is_read_only() is False
    db.close_db()
    assert not lock.exists()


def test_other_pc_opens_read_only_and_can_take_over(tmp_path):
    lock = tmp_path / db.LOCK_FILE
    now = datetime.now().isoformat(timespec="seconds")
    lock.write_text(json.dumps({"computer": "OTHER-PC", "user": "x", "pid": 1,
                                "since": now, "heartbeat": now}))
    db.init_db(tmp_path / "test.db")
    with TestClient(app) as c:
        status = c.get("/api/status").json()
        assert status["read_only"] is True
        assert status["lock"]["computer"] == "OTHER-PC"
        r = c.post("/api/projects", json={"name": "P"})
        assert r.status_code == 423
        assert "OTHER-PC" in r.json()["detail"]
        assert c.get("/api/projects").json() == []  # Lesen geht
        # Kein Backup im Lesemodus (würde in den fremden Datenordner schreiben)
        assert c.post("/api/backups").status_code == 423

        r = c.post("/api/lock/takeover")
        assert r.status_code == 200 and r.json()["read_only"] is False
        assert json.loads(lock.read_text())["computer"] == db.computer_name()
        assert c.post("/api/projects", json={"name": "P"}).status_code == 201


def test_stale_lock_is_taken_over_silently(tmp_path):
    lock = tmp_path / db.LOCK_FILE
    old = (datetime.now() - timedelta(seconds=db.LOCK_STALE_SECONDS + 60)).isoformat(timespec="seconds")
    lock.write_text(json.dumps({"computer": "OTHER-PC", "pid": 1, "since": old, "heartbeat": old}))
    db.init_db(tmp_path / "test.db")
    assert db.is_read_only() is False
    assert json.loads(lock.read_text())["computer"] == db.computer_name()


def test_writable_pc_becomes_read_only_after_foreign_takeover(tmp_path):
    db.init_db(tmp_path / "test.db")
    with TestClient(app) as c:
        assert c.post("/api/projects", json={"name": "P"}).status_code == 201
        now = datetime.now().isoformat(timespec="seconds")
        (tmp_path / db.LOCK_FILE).write_text(json.dumps(
            {"computer": "OTHER-PC", "pid": 1, "since": now, "heartbeat": now}))
        # Nächste Änderung prüft die Sperrdatei -> abgewiesen, Status zeigt es
        assert c.post("/api/projects", json={"name": "Q"}).status_code == 423
        assert c.get("/api/status").json()["read_only"] is True
        assert [p["name"] for p in c.get("/api/projects").json()] == ["P"]
    # Beim Beenden bleibt die fremde Sperre stehen
    assert json.loads((tmp_path / db.LOCK_FILE).read_text())["computer"] == "OTHER-PC"


def test_read_only_switches_to_writable_when_lock_disappears(tmp_path):
    lock = tmp_path / db.LOCK_FILE
    now = datetime.now().isoformat(timespec="seconds")
    lock.write_text(json.dumps({"computer": "OTHER-PC", "pid": 1, "since": now, "heartbeat": now}))
    db.init_db(tmp_path / "test.db")
    with TestClient(app) as c:
        assert c.get("/api/status").json()["read_only"] is True
        lock.unlink()  # anderer PC hat die App beendet
        assert c.get("/api/status").json()["read_only"] is False
        assert c.post("/api/projects", json={"name": "P"}).status_code == 201


# ---------- Datenordner wechseln ----------

@pytest.fixture()
def own_config(tmp_path, monkeypatch):
    """config.json in einen Temp-Ordner umleiten, damit Tests die echte
    Konfiguration nie anfassen."""
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "config.json")
    monkeypatch.setattr(config, "DEFAULT_DATA_DIR", tmp_path / "app" / "data")
    monkeypatch.setattr(config, "DEFAULT_BACKUP_DIR", tmp_path / "app" / "backups")
    monkeypatch.setattr(db, "DATA_DIR", tmp_path / "app" / "data")


def test_switch_data_dir_copies_into_empty_folder(tmp_path, own_config):
    db.init_db()  # Standard-Datenordner (umgeleitet)
    with TestClient(app) as c:
        mol = make_mol(c)
        c.post(f"/api/molecules/{mol['id']}/image", content=PNG_1x1)
        shared = tmp_path / "share" / "Characterization-Data"
        shared.parent.mkdir()  # das "Netzlaufwerk" existiert, der Datenordner noch nicht
        r = c.post("/api/settings/data-dir", json={"path": str(shared)})
        assert r.status_code == 200, r.text
        assert r.json()["copied"] is True
        assert r.json()["data_dir"] == str(shared)
        assert (shared / "app.db").is_file()
        assert len(list((shared / "images").iterdir())) == 1
        assert (shared / db.LOCK_FILE).is_file()
        assert config.load()["data_dir"] == str(shared)
        # Weiterarbeiten im neuen Ordner: Bild wird dort gefunden
        mols = c.get("/api/projects").json()[0]["molecules"]
        assert mols[0]["image_exists"] is True
        assert Path(mols[0]["image_path"]).parent == (shared / "images").resolve()
        # Backups liegen jetzt beim Datensatz
        c.post("/api/backups")
        assert list((shared / "backups").glob("app-*.zip"))
    # Alter Ordner unangetastet, Sperre dort freigegeben
    assert (tmp_path / "app" / "data" / "app.db").is_file()
    assert not (tmp_path / "app" / "data" / db.LOCK_FILE).exists()


def test_switch_data_dir_opens_existing_dataset(tmp_path, own_config):
    shared = tmp_path / "share"
    db.init_db(shared / "app.db")  # "PC A" hat dort schon gearbeitet
    with TestClient(app) as c:
        c.post("/api/projects", json={"name": "Von PC A"})
    db.init_db()  # "PC B" mit leerem lokalem Datensatz
    with TestClient(app) as c:
        assert c.get("/api/projects").json() == []
        r = c.post("/api/settings/data-dir", json={"path": str(shared)})
        assert r.status_code == 200, r.text
        assert r.json()["copied"] is False
        assert [p["name"] for p in c.get("/api/projects").json()] == ["Von PC A"]


def test_switch_with_explicit_db_never_touches_config(client, tmp_path, monkeypatch):
    """Test-Server/Tests arbeiten mit eigener DB (init_db(pfad)): ein
    Ordnerwechsel darf die echte config.json nicht schreiben — sonst öffnet
    die echte App beim nächsten Start den Test-Datensatz (ist passiert)."""
    sentinel = tmp_path / "must-not-exist.json"
    monkeypatch.setattr(config, "CONFIG_PATH", sentinel)
    target = tmp_path / "elsewhere"
    r = client.post("/api/settings/data-dir", json={"path": str(target)})
    assert r.status_code == 200, r.text
    assert r.json()["data_dir"] == str(target)
    assert not sentinel.exists()


def test_switch_data_dir_rejects_unreachable_parent(client):
    r = client.post("/api/settings/data-dir", json={"path": "Q:\\gibt\\es\\nicht\\data"})
    assert r.status_code == 422


# ---------- Automatische Backups und die Sperre ----------
# Das Start-/Beenden-Backup entfällt, wenn sich seit dem letzten nichts
# geändert hat (siehe test_backup_size.py). Bei einem gemeinsamen Datenordner
# liegt das Kennzeichen dafür im Backup-Ordner und gilt für ALLE PCs — es
# beschreibt den Datensatz, nicht den Rechner. Diese Tests halten fest, dass
# das mit der Sperre zusammenspielt.

def bild_und_molekuel(name="mol-1.bmp"):
    from app.models import Molecule, Project
    d = db.images_dir()
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_bytes(b"BM" + bytes(50_000))
    with db._SessionLocal() as s:
        p = s.query(Project).first()
        if p is None:
            p = Project(name="P")
            s.add(p)
            s.flush()
        s.add(Molecule(project_id=p.id, name=name, image_path=name))
        s.commit()


def fremde_sperre(ordner, frisch=True):
    t = datetime.now() - (timedelta() if frisch
                          else timedelta(seconds=db.LOCK_STALE_SECONDS + 60))
    s = t.isoformat(timespec="seconds")
    (ordner / db.LOCK_FILE).write_text(json.dumps(
        {"computer": "ANDERER-PC", "user": "y", "pid": 1, "since": s, "heartbeat": s}))


def fremde_aenderung(db_datei):
    """Ein anderer PC schreibt in den Datensatz."""
    con = sqlite3.connect(db_datei)
    con.execute("INSERT INTO projects (name, sort_order, created_at) "
                "VALUES ('Vom anderen PC', 0, '2026-01-01')")
    con.commit()
    con.close()


def test_lesender_pc_sichert_nicht_und_hinterlaesst_kein_kennzeichen(tmp_path):
    """Im Lesemodus darf nichts in den fremden Datenordner geschrieben werden
    — auch kein Backup und kein Kennzeichen."""
    db.init_db(tmp_path / "test.db")
    bild_und_molekuel()
    db.create_backup()
    vorher = [b["name"] for b in db.list_backups()]
    kennzeichen = (db._backup_dir / db.BACKUP_STATE_FILE).read_bytes()
    db.close_db()

    fremde_sperre(tmp_path)
    db.init_db(tmp_path / "test.db")
    assert db.is_read_only() is True
    assert db.create_backup(only_if_changed=True) is None
    assert db.create_backup() is None  # auch von Hand nicht
    assert [b["name"] for b in db.list_backups()] == vorher
    assert (db._backup_dir / db.BACKUP_STATE_FILE).read_bytes() == kennzeichen


def test_start_sichert_wenn_ein_anderer_pc_geaendert_hat(tmp_path):
    """Der andere PC ist abgestürzt, ohne zu sichern. Unser Start darf sich
    nicht auf das Kennzeichen von vorher verlassen."""
    db.init_db(tmp_path / "test.db")
    bild_und_molekuel()
    db.create_backup(only_if_changed=True)
    vorher = len(db.list_backups())
    db.close_db()

    fremde_aenderung(tmp_path / "test.db")

    db.init_db(tmp_path / "test.db")  # macht das Start-Backup selbst
    assert len(db.list_backups()) > vorher


def test_uebernahme_der_sperre_holt_das_backup_nach(tmp_path):
    """Beim Start im Lesemodus entfällt das Backup. Übernimmt dieser PC
    später die Sperre, muss es nachgeholt werden — der andere PC kann
    inzwischen etwas geändert haben."""
    db.init_db(tmp_path / "test.db")
    bild_und_molekuel()
    db.create_backup(only_if_changed=True)
    db.close_db()

    fremde_sperre(tmp_path)
    db.init_db(tmp_path / "test.db")
    assert db.is_read_only() is True
    vorher = len(db.list_backups())

    fremde_aenderung(tmp_path / "test.db")
    (tmp_path / db.LOCK_FILE).unlink()  # anderer PC hat beendet
    assert db.refresh_lock_state() is True  # still übernommen
    assert len(db.list_backups()) > vorher


def test_kennzeichen_meint_immer_den_stand_im_zip(tmp_path):
    """Ändert ein anderer PC den Datensatz, während wir gerade packen, darf
    kein Kennzeichen zurückbleiben, das einen Stand behauptet, den kein
    Backup enthält — sonst überspringt der nächste Start zu Unrecht."""
    db.init_db(tmp_path / "test.db")
    bild_und_molekuel()
    echt = db._write_backup_state

    def dazwischen(name, state):
        fremde_aenderung(tmp_path / "test.db")  # anderer PC schreibt jetzt
        echt(name, state)

    db._write_backup_state = dazwischen
    try:
        db.create_backup(only_if_changed=True)
    finally:
        db._write_backup_state = echt

    assert db.create_backup(only_if_changed=True) is not None
