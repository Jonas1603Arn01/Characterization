import hashlib
import json
import logging
import os
import re
import shutil
import socket
import sqlite3
import threading
import zipfile
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import pyzipper

from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session, sessionmaker

from . import config, paths
from .models import Base

BASE_DIR = config.BASE_DIR
DATA_DIR = config.DEFAULT_DATA_DIR
BACKUP_DIR = config.DEFAULT_BACKUP_DIR
DB_PATH = DATA_DIR / "app.db"
MAX_BACKUPS = 10
# Backups von unmittelbar vor einem Transfer-Import ("-import" im Namen) sind
# der garantierte Rückweg zum alten Datensatz — sie rotieren separat und
# großzügiger, damit sie nicht von Start/Beenden-Backups verdrängt werden.
MAX_IMPORT_BACKUPS = 20
MAX_UNDO = 20

# Sperrdatei im Datenordner: SQLite auf einem Netzlaufwerk verträgt keine zwei
# gleichzeitig schreibenden PCs. Der erste PC trägt sich ein und erneuert den
# Eintrag regelmäßig; ein zweiter PC öffnet den Datensatz dann nur lesend
# (mit der Möglichkeit, die Sperre bewusst zu übernehmen). Bleibt der
# Eintrag länger als LOCK_STALE_SECONDS unerneuert (Absturz, Stromausfall),
# gilt er als verwaist und wird stillschweigend übernommen.
LOCK_FILE = "in-use.lock"
LOCK_HEARTBEAT_SECONDS = 60
LOCK_STALE_SECONDS = 5 * 60

_engine = None
_SessionLocal = None
_db_path: Path | None = None
_backup_dir: Path | None = None
_undo_seq: int | None = None  # fortlaufende Snapshot-Nummer, sortiert eindeutig
# Anzahl vorhandener Snapshots. Wird zusammen mit _undo_seq einmal aus dem
# Undo-Ordner gelesen und danach mitgeführt: die Oberfläche fragt bei jedem
# Neuladen nach (/api/undo), und auf einem Datenordner im Netz ist schon das
# Auflisten des Ordners eine Anfrage übers Netz.
_undo_count: int | None = None
_undo_cache: list[Path] = []  # Snapshot-Pfade, älteste zuerst
_read_only = False
_lock_holder: dict | None = None  # Eintrag des anderen PCs, wenn nur lesend geöffnet
# True, wenn die DB aus config.json bestimmt wurde (echte App). Tests und der
# Test-Server übergeben eine eigene DB — ein Ordnerwechsel darf dann NIE die
# echte config.json anfassen (sonst öffnet die echte App beim nächsten Start
# den Test-Datensatz).
_config_backed = False
_heartbeat_stop: threading.Event | None = None
_heartbeat_thread: threading.Thread | None = None
# Sperrzustand und Undo-Snapshots werden aus Arbeitsthreads angefasst (die
# Middlewares in main.py halten damit die Event-Loop frei). Früher hat die
# Event-Loop diese Aufrufe von selbst nacheinander ausgeführt — jetzt tut es
# diese Sperre: sonst könnten zwei gleichzeitige Änderungen dieselbe
# Snapshot-Nummer vergeben. Reentrant, weil push/pop die Merkliste über
# _undo_snapshots() mitbenutzen.
_state_lock = threading.RLock()


def ensure_db(background_backup: bool = False) -> None:
    """Nur initialisieren, wenn noch keine Engine existiert (Tests setzen vorher eine eigene)."""
    if _engine is None:
        init_db(background_backup=background_backup)


def init_db(db_path: Path | None = None, *, background_backup: bool = False) -> None:
    """Engine anlegen, Sperre setzen, Backup der bestehenden DB ziehen,
    Tabellen erstellen. Ohne db_path gilt der konfigurierte Datenordner
    (config.json; Standard data\\ im App-Ordner); Tests übergeben eine
    eigene DB und sichern dann neben sich selbst."""
    global _engine, _SessionLocal, _db_path, _backup_dir, _config_backed
    close_db()
    _config_backed = db_path is None
    if db_path is None:
        _db_path = config.data_dir() / "app.db"
        _backup_dir = config.backup_dir()
    else:
        _db_path = db_path
        _backup_dir = db_path.parent / "backups"
    _forget_undo_state()  # wird beim ersten Snapshot aus dem Undo-Ordner gelesen
    _db_path.parent.mkdir(parents=True, exist_ok=True)
    _acquire_lock()
    if _db_path.exists() and not _read_only:
        if background_backup:
            # App-Start: das Backup packt DB und Bildbestand — auf einem
            # Netzlaufwerk leicht über eine Minute. So lange darf der Server
            # nicht warten, sonst wirkt das schwarze Fenster wie „startet nicht“.
            _start_backup_in_background()
        else:
            create_backup(only_if_changed=True)  # Start: nur sichern, wenn nötig
    _engine = create_engine(f"sqlite:///{_db_path}", connect_args={"check_same_thread": False})
    _SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False)
    _migrate_schema()


def _migrate_schema() -> int:
    """Schema und Pfadformen auf den Stand dieser App-Version bringen. Auf
    einem aktuellen Datensatz sind alle Schritte wirkungslos — deshalb auch
    im Lesemodus vertretbar (sonst könnten Abfragen an fehlenden Spalten
    scheitern). Liefert die Anzahl umgeschriebener Bildverweise."""
    Base.metadata.create_all(_engine)
    _ensure_columns()
    migrate_text_notes()
    if _read_only:
        return 0
    rewritten = _relativize_managed_images()
    _portabilize_link_paths()
    return rewritten


def close_db() -> None:
    """Engine schließen und Sperre freigeben (Beenden, Wechsel des Datenordners)."""
    global _engine, _SessionLocal
    # Ein laufendes Start-Backup erst fertig packen lassen — ein Wechsel des
    # Datenordners zöge ihm sonst die Pfade unter den Füßen weg
    with _backup_lock:
        if _engine is not None:
            _engine.dispose()
        _engine = _SessionLocal = None
        _release_lock()


# ---------- Sperre gegen gleichzeitiges Arbeiten von zwei PCs ----------

def _lock_path() -> Path:
    return _db_path.parent / LOCK_FILE


def _own_lock_entry() -> dict:
    now = datetime.now().isoformat(timespec="seconds")
    return {"computer": computer_name(), "user": os.environ.get("USERNAME", ""),
            "pid": os.getpid(), "since": now, "heartbeat": now}


def computer_name() -> str:
    return os.environ.get("COMPUTERNAME") or socket.gethostname()


def _read_lock() -> dict | None:
    try:
        data = json.loads(_lock_path().read_text(encoding="utf-8-sig"))  # BOM tolerieren
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _lock_is_stale(entry: dict) -> bool:
    try:
        beat = datetime.fromisoformat(entry.get("heartbeat") or entry.get("since"))
    except (TypeError, ValueError):
        return True
    return (datetime.now() - beat).total_seconds() > LOCK_STALE_SECONDS


def _write_lock(entry: dict) -> None:
    _lock_path().write_text(json.dumps(entry, indent=2), encoding="utf-8")


def _acquire_lock() -> None:
    """Sperre setzen. Hält ein anderer PC sie noch aktiv, wird der Datensatz
    nur lesend geöffnet (_read_only) — die Oberfläche zeigt das an und bietet
    die Übernahme an."""
    global _read_only, _lock_holder
    _read_only, _lock_holder = False, None
    other = _read_lock()
    own = _own_lock_entry()
    if other and other.get("computer") != own["computer"] and not _lock_is_stale(other):
        _read_only, _lock_holder = True, other
        return
    try:
        _write_lock(own)
    except OSError:
        # Ordner nicht beschreibbar (z. B. Freigabe nur lesend) -> lesend arbeiten
        _read_only = True
        return
    _start_heartbeat()


def _start_heartbeat() -> None:
    global _heartbeat_stop, _heartbeat_thread
    _stop_heartbeat()
    stop = threading.Event()
    lock_file = _lock_path()

    def beat() -> None:
        while not stop.wait(LOCK_HEARTBEAT_SECONDS):
            try:
                entry = json.loads(lock_file.read_text(encoding="utf-8"))
                if not isinstance(entry, dict) or entry.get("pid") != os.getpid():
                    continue  # Sperre wurde inzwischen übernommen/entfernt
                entry["heartbeat"] = datetime.now().isoformat(timespec="seconds")
                lock_file.write_text(json.dumps(entry, indent=2), encoding="utf-8")
            except (OSError, ValueError):
                pass  # Netz kurz weg -> beim nächsten Schlag erneut

    _heartbeat_stop = stop
    _heartbeat_thread = threading.Thread(target=beat, name="lock-heartbeat", daemon=True)
    _heartbeat_thread.start()


def _stop_heartbeat() -> None:
    global _heartbeat_stop, _heartbeat_thread
    if _heartbeat_stop is not None:
        _heartbeat_stop.set()
    _heartbeat_stop = _heartbeat_thread = None


def _release_lock() -> None:
    """Eigene Sperre entfernen (nur die eigene — eine inzwischen von einem
    anderen PC übernommene bleibt stehen)."""
    global _read_only, _lock_holder
    _stop_heartbeat()
    if _db_path is not None and not _read_only:
        entry = _read_lock()
        if entry and entry.get("pid") == os.getpid():
            try:
                _lock_path().unlink()
            except OSError:
                pass
    _read_only, _lock_holder = False, None


def is_read_only() -> bool:
    return _read_only


def lock_holder() -> dict | None:
    """Wer den Datensatz gerade hält, wenn wir nur lesend geöffnet haben
    (Rechnername, Nutzer, seit wann) — sonst None."""
    return dict(_lock_holder) if _lock_holder else None


def refresh_lock_state() -> bool:
    """Sperrzustand mit der Datei abgleichen. Im Lesemodus: ist die fremde
    Sperre inzwischen weg oder verwaist, still übernehmen. Im Schreibmodus:
    hat ein anderer PC die Sperre bewusst übernommen, hier auf Lesen
    umschalten. True, wenn danach schreibbar."""
    global _read_only, _lock_holder
    if _db_path is None:
        return True
    with _state_lock:
        return _refresh_lock_state()


def _refresh_lock_state() -> bool:
    global _read_only, _lock_holder
    other = _read_lock()
    own = computer_name()
    if _read_only:
        if other is None or _lock_is_stale(other) or other.get("computer") == own:
            _take_over_lock()
        return not _read_only
    if other is None:
        try:
            _write_lock(_own_lock_entry())  # Datei verschwunden -> erneuern
        except OSError:
            pass
    elif other.get("computer") != own and not _lock_is_stale(other):
        _stop_heartbeat()
        _read_only, _lock_holder = True, other
    return not _read_only


def take_over_lock() -> None:
    """Sperre bewusst übernehmen (der andere PC arbeitet ab jetzt nur noch
    lesend, sobald er es bemerkt). Holt die beim Start ausgelassenen
    Schreibschritte nach: Backup und Pfad-Migrationen."""
    global _read_only, _lock_holder
    with _state_lock:
        _take_over_lock()


def _take_over_lock() -> None:
    global _read_only, _lock_holder
    _write_lock(_own_lock_entry())
    _read_only, _lock_holder = False, None
    # Der andere PC kann inzwischen eigene Snapshots angelegt haben
    _forget_undo_state()
    _start_heartbeat()
    if _db_path.exists():
        create_backup(only_if_changed=True)
    _migrate_schema()


# ---------- Datenordner (mehrere PCs, Netzlaufwerk) ----------

def status() -> dict:
    return {
        "data_dir": str(_db_path.parent) if _db_path else None,
        "backup_dir": str(_backup_dir) if _backup_dir else None,
        "default_data_dir": str(DATA_DIR),
        "read_only": _read_only,
        "lock": lock_holder(),
        "computer": _own_lock_entry()["computer"],
    }


def switch_data_dir(target: Path) -> dict:
    """Datenordner wechseln (config.json) und die App darauf umstellen.
    Enthält der Zielordner noch keinen Datensatz, wird der aktuelle
    (Datenbank + Bilder) hineinkopiert; enthält er bereits einen — etwa den
    gemeinsamen Ordner auf dem Netzlaufwerk, den ein anderer PC angelegt
    hat — wird einfach dieser geöffnet. Der bisherige Ordner bleibt
    unverändert liegen. Liefert {"copied": bool}."""
    target = Path(target)
    if _db_path is not None and target.resolve() == _db_path.parent.resolve():
        return {"copied": False}
    target.mkdir(parents=True, exist_ok=True)
    copied = False
    if not (target / "app.db").exists() and _db_path is not None and _db_path.exists():
        cleanup_orphan_images()
        shutil.copy2(_db_path, target / "app.db")
        src_images = images_dir()
        if src_images.is_dir():
            shutil.copytree(src_images, target / "images", dirs_exist_ok=True)
        copied = True
    if _config_backed:
        config.set_data_dir(target)
        init_db()
    else:
        init_db(target / "app.db")  # Test-Betrieb: nur umschalten, Konfiguration unberührt
    return {"copied": copied}


def _ensure_columns() -> None:
    """Spalten nachrüsten, die create_all bei bestehenden Tabellen nicht anlegt."""
    needed = {
        "projects": [("sort_order", "INTEGER NOT NULL DEFAULT 0")],
        "molecules": [
            ("sort_order", "INTEGER NOT NULL DEFAULT 0"),
            ("scheme_path", "VARCHAR"),
            ("image_cdx_path", "VARCHAR"),
            ("scheme_cdx_path", "VARCHAR"),
            ("equation_path", "VARCHAR"),
            ("equation_cdx_path", "VARCHAR"),
            ("literature_known", "BOOLEAN NOT NULL DEFAULT 0"),
            ("doi", "VARCHAR"),
            ("citation", "VARCHAR"),
            ("si_path", "VARCHAR"),
            ("physical_state", "VARCHAR"),
            ("color", "VARCHAR"),
            ("consistency", "VARCHAR"),
            ("sample_available", "BOOLEAN NOT NULL DEFAULT 0"),
            ("sample_number", "VARCHAR"),
            ("sample_comment", "VARCHAR"),
            ("name_html", "VARCHAR"),
            ("citation_html", "VARCHAR"),
            ("sample_comment_html", "VARCHAR"),
        ],
        "data_entries": [("folder_label", "VARCHAR"), ("file_label", "VARCHAR"),
                         ("svg_path", "VARCHAR"), ("svg_label", "VARCHAR"),
                         ("svg2_path", "VARCHAR"), ("svg2_label", "VARCHAR"),
                         ("in_document", "BOOLEAN NOT NULL DEFAULT 0")],
        "entry_files": [("label", "VARCHAR")],
        "entry_notes": [("html", "VARCHAR")],
    }
    with _engine.begin() as conn:
        for table, columns in needed.items():
            existing = {row[1] for row in conn.execute(text(f"PRAGMA table_info({table})"))}
            for name, ddl in columns:
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))
                    if table == "data_entries" and name == "in_document":
                        _backfill_in_document(conn)


def _backfill_in_document(conn) -> None:
    """Beim Nachrüsten der Spalte die bisherige Regel festschreiben: eigene
    Einträge, deren Bezeichnung eine NMR-Messung meint, waren schon im
    Word-Dokument und sollen es bleiben."""
    from .chem_text import is_nmr_label

    rows = conn.execute(text(
        "SELECT id, custom_label FROM data_entries WHERE type_code = 'other'"
    )).all()
    ids = [row[0] for row in rows if is_nmr_label(row[1])]
    for entry_id in ids:
        conn.execute(text("UPDATE data_entries SET in_document = 1 WHERE id = :id"),
                     {"id": entry_id})


def migrate_text_notes() -> int:
    """Überführt alte Einzel-Notizen (data_entries.text_note) in die
    Notiz-Tabelle. Idempotent — die Spalte wird danach geleert."""
    from .models import DataEntry, EntryNote

    moved = 0
    with _SessionLocal() as session:
        entries = session.scalars(
            select(DataEntry).where(DataEntry.text_note.is_not(None))
        ).all()
        for e in entries:
            if e.text_note.strip():
                session.add(EntryNote(entry_id=e.id, text=e.text_note))
                moved += 1
            e.text_note = None
        session.commit()
    return moved


def get_session():
    session: Session = _SessionLocal()
    try:
        yield session
    finally:
        session.close()


def new_session() -> Session | None:
    """Eigene Sitzung für Hintergrundarbeiten (die Endpunkte bekommen ihre
    über get_session). None, solange keine Datenbank offen ist."""
    return _SessionLocal() if _SessionLocal is not None else None


def db_file() -> Path | None:
    """Datei der offenen Datenbank — Kennzeichen des Datensatzes für
    prozessweite Merklisten, die beim Wechsel des Datenordners verfallen."""
    return _db_path


def images_dir() -> Path:
    """Ordner für von der App gespeicherte Bilder — neben der aktiven DB, damit
    Tests (eigene DB) nicht in den echten Datenordner schreiben."""
    base = _db_path.parent if _db_path else DATA_DIR
    return base / "images"


def image_file(value: str | None) -> Path | None:
    """Absoluter Pfad zu einem Bild-/CDX-Verweis der Datenbank. Von der App
    gespeicherte Dateien stehen nur mit ihrem Dateinamen in der DB (relativ
    zum images-Ordner des aktuellen Datenordners) — so bleibt der Datensatz
    gültig, egal von welchem PC oder Laufwerksbuchstaben aus er geöffnet
    wird. Absolute Pfade (extern gewählte Bilddateien) bleiben wie sie sind."""
    if not value:
        return None
    p = Path(value)
    if p.is_absolute() or value.startswith("\\\\"):
        return p
    return images_dir() / p.name


def managed_name(target: Path) -> str:
    """Speicherform für eine Datei im images-Ordner: nur der Dateiname."""
    return target.name


def _relativize_managed_images() -> int:
    """Bildverweise, die noch absolut auf einen images-Ordner zeigen, auf den
    Dateinamen kürzen: entweder zeigen sie auf den hiesigen images-Ordner
    (Datensatz aus einer älteren App-Version), oder der Pfad existiert nicht,
    die Datei liegt aber im hiesigen images-Ordner (Transferdatei von einem
    anderen PC — die Bilder kamen mit). Liefert die Anzahl der Umschreibungen."""
    from .models import Molecule

    img_dir = images_dir()
    try:
        img_dir_resolved = img_dir.resolve()
    except OSError:
        img_dir_resolved = img_dir
    changed = 0
    with _SessionLocal() as session:
        for mol in session.scalars(select(Molecule)).all():
            for attr in _IMAGE_COLUMNS:
                old = getattr(mol, attr)
                if not old:
                    continue
                p = Path(old)
                if not (p.is_absolute() or old.startswith("\\\\")):
                    continue  # schon relativ
                try:
                    in_local_dir = p.parent.resolve() == img_dir_resolved
                except OSError:
                    in_local_dir = False
                if in_local_dir or (not paths.exists(old) and (img_dir / p.name).is_file()):
                    setattr(mol, attr, p.name)
                    changed += 1
        session.commit()
    return changed


def _portabilize_link_paths() -> int:
    """Verlinkte Dateien/Ordner auf Netzlaufwerken in UNC-Form bringen (siehe
    paths.py) — einmalig für Bestandsdaten; neue Verweise speichert die API
    direkt so. Liefert die Anzahl der Umschreibungen."""
    from .models import DataEntry, EntryFile, Molecule

    changed = 0
    with _SessionLocal() as session:
        for mol in session.scalars(select(Molecule)).all():
            for attr in ("image_path", "scheme_path", "equation_path"):
                old = getattr(mol, attr)
                if old and Path(old).is_absolute():
                    new = paths.to_portable(old)
                    if new != old:
                        setattr(mol, attr, new)
                        changed += 1
            new = paths.to_portable(mol.si_path)  # Literatur-SI: extern verlinkt
            if mol.si_path and new != mol.si_path:
                mol.si_path = new
                changed += 1
        for e in session.scalars(select(DataEntry)).all():
            for attr in ("folder_path", "file_path", "svg_path", "svg2_path"):
                old = getattr(e, attr)
                new = paths.to_portable(old)
                if old and new != old:
                    setattr(e, attr, new)
                    changed += 1
        for f in session.scalars(select(EntryFile)).all():
            new = paths.to_portable(f.path)
            if new != f.path:
                f.path = new
                changed += 1
        session.commit()
    return changed


# ---------- Aufräumen: verwaiste Bilder im images-Ordner ----------

# Molekül-Spalten, die auf Dateien im images-Ordner zeigen können
_IMAGE_COLUMNS = ("image_path", "scheme_path", "equation_path",
                  "image_cdx_path", "scheme_cdx_path", "equation_cdx_path")


def _sqlite_ro_uri(db_file: Path) -> str:
    """URI zum schreibgeschützten Öffnen einer SQLite-Datei. Der Pfad wird
    prozentkodiert — sonst beendet ein „#“ oder „?“ im Ordnernamen den Pfad,
    und SQLite öffnet stillschweigend eine andere, leere Datei. Eine
    Netzwerkfreigabe braucht vier Schrägstriche: bei „file://129.x/…“ hielte
    SQLite die Adresse für einen Hostnamen und lehnte ab, und das Aufräumen
    fand auf einem Datenordner im Netz nie ein verwaistes Bild."""
    path = db_file.as_posix()  # C:/… bzw. //server/freigabe/…
    if not path.startswith("/"):
        path = "/" + path
    return f"file://{quote(path, safe='/:')}?mode=ro"


def _referenced_images(db_file: Path) -> set[str]:
    """Dateinamen (normcase) aller Bild-/CDX-Verweise in einer DB-Datei.
    Liest per sqlite3 direkt — funktioniert so auch für Undo-Schnappschüsse
    älterer App-Versionen, denen einzelne Spalten fehlen. Wirft sqlite3.Error
    bei unlesbarer Datei."""
    names: set[str] = set()
    con = sqlite3.connect(_sqlite_ro_uri(db_file), uri=True)
    try:
        cols = {row[1] for row in con.execute("PRAGMA table_info(molecules)")}
        for col in _IMAGE_COLUMNS:
            if col not in cols:
                continue
            for (val,) in con.execute(
                f"SELECT {col} FROM molecules WHERE {col} IS NOT NULL"
            ):
                names.add(os.path.normcase(Path(val).name))
    finally:
        con.close()
    return names


# Ein eingefügtes Bild wird erst in den images-Ordner geschrieben und danach
# in der Datenbank vermerkt. Genau dazwischen darf das Aufräumen nicht laufen —
# es hielte die neue Datei für einen Überrest und löschte sie. Die API hält
# diese Sperre um Schreiben und Commit (siehe api._save_image_data).
image_lock = threading.RLock()


def cleanup_orphan_images() -> int:
    """Löscht Dateien im images-Ordner, die weder von der aktuellen Datenbank
    noch von einem Undo-Schnappschuss referenziert werden (z. B. übrig nach
    Undo eines Einfügens oder nach Backup-Wiederherstellungen). Läuft vor
    jedem Backup und Transfer-Export, damit die ZIPs nicht mit ungenutzten
    Bildern wachsen. Gibt die Anzahl gelöschter Dateien zurück."""
    img_dir = images_dir()
    if _db_path is None or _read_only or not img_dir.is_dir():
        return 0
    with image_lock:
        return _cleanup_orphan_images(img_dir)


def _cleanup_orphan_images(img_dir: Path) -> int:
    db_files = [_db_path] if _db_path.exists() else []
    if _undo_dir().is_dir():
        db_files += sorted(_undo_dir().glob("undo-*.db"))
    referenced: set[str] = set()
    try:
        for f in db_files:
            referenced |= _referenced_images(f)
    except sqlite3.Error:
        return 0  # eine DB nicht lesbar -> im Zweifel nichts löschen
    removed = 0
    for p in list(img_dir.iterdir()):
        if p.is_file() and os.path.normcase(p.name) not in referenced:
            try:
                p.unlink()
                removed += 1
            except OSError:
                pass  # Datei gerade in Benutzung -> beim nächsten Lauf
    return removed


# ---------- Backups (manuell, bei Start und Beenden) ----------

def _existing_backups() -> list[Path]:
    """Alle Backups, alphabetisch = chronologisch (Zeitstempel im Namen).
    `.db` sind ältere DB-only-Backups, `.zip` enthält DB + Bilder."""
    return sorted([*_backup_dir.glob("app-*.db"), *_backup_dir.glob("app-*.zip")],
                  key=lambda p: p.name)


def _is_import_backup(p: Path) -> bool:
    """Backup von unmittelbar vor einem Transfer-Import?"""
    return p.stem.endswith("-import")


# Kennzeichen des gesicherten Standes, neben den Backups abgelegt. Damit
# lässt sich vor dem Start-/Beenden-Backup mit ein paar Dateiabfragen klären,
# ob sich seit dem letzten Backup überhaupt etwas geändert hat — statt
# Datenbank und Bilder erst zu lesen und dann neu zu schreiben.
BACKUP_STATE_FILE = ".last-backup.json"
# Arbeitsname eines noch nicht fertig gepackten Backups (siehe create_backup)
PART_SUFFIX = ".part"
# Das Start-Backup läuft nebenher (main.lifespan), das Beenden-Backup und
# „Backup jetzt“ können dazwischenkommen. Immer nur eines auf einmal: sonst
# räumen zwei Läufe gegenseitig ihre Arbeitsdatei weg und rotieren doppelt.
_backup_lock = threading.RLock()


def _current_state(db_bytes: bytes | None = None) -> dict:
    """Fingerabdruck von Datenbank und images-Ordner.

    Die Datenbank wird über ihren Inhalt erkannt. Größe und Änderungszeit
    taugen hier nicht: SQLite schreibt in vorhandene Seiten, die Größe bleibt
    beim Anlegen eines Moleküls also gleich — und Windows führt die
    Änderungszeit einer geöffneten Datei nur grob nach (gemessen: bei zehn
    schnell aufeinanderfolgenden Änderungen blieb sie siebenmal stehen).
    Fällt die letzte Änderung kurz vor das Beenden, wäre das Backup sonst
    ausgefallen und die Arbeit der Sitzung nicht gesichert.

    Die Datenbank ist klein (Größenordnung 100 kB) und wird für das Backup
    ohnehin gelesen; die Bilder, um die es beim Tempo geht, werden nur
    aufgelistet."""
    h = hashlib.sha256()
    if db_bytes is not None:  # Stand beim App-Start (_start_backup_in_background)
        h.update(db_bytes)
    else:
        with open(_db_path, "rb") as f:
            for block in iter(lambda: f.read(1 << 20), b""):
                h.update(block)
    zahl = groesse = 0
    neuste = 0
    img_dir = images_dir()
    try:
        with os.scandir(img_dir) as it:
            for e in it:
                if e.is_file():
                    s = e.stat()
                    zahl += 1
                    groesse += s.st_size
                    neuste = max(neuste, s.st_mtime_ns)
    except OSError:
        pass  # kein images-Ordner -> zählt als leer
    return {"db_hash": h.hexdigest(),
            "db_size": len(db_bytes) if db_bytes is not None else _db_path.stat().st_size,
            "img_count": zahl, "img_size": groesse, "img_mtime": neuste}


def _read_backup_state() -> dict | None:
    try:
        data = json.loads((_backup_dir / BACKUP_STATE_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _write_backup_state(name: str, state: dict) -> None:
    """Kennzeichen schreiben. Der Stand wird übergeben, nicht hier neu
    ermittelt: er muss genau der sein, der nachweislich im ZIP steckt."""
    try:
        (_backup_dir / BACKUP_STATE_FILE).write_text(
            json.dumps({"backup": name, "state": state}, indent=2),
            encoding="utf-8")
    except OSError:
        pass  # ohne Kennzeichen wird beim nächsten Mal einfach wieder gesichert


def _backup_would_be_identical(db_bytes: bytes | None = None) -> bool:
    """True, wenn das jüngste Backup denselben Stand enthält wie jetzt — dann
    bringt ein weiteres keinen zusätzlichen Rückweg. Im Zweifel (kein oder
    unlesbares Kennzeichen, Backup verschwunden) False."""
    merk = _read_backup_state()
    if not merk or not isinstance(merk.get("state"), dict):
        return False
    name = merk.get("backup")
    if not isinstance(name, str) or not (_backup_dir / name).is_file():
        return False
    return merk["state"] == _current_state(db_bytes)


def create_backup(tag: str | None = None, only_if_changed: bool = False) -> str | None:
    """Sichert DB + images-Ordner als ZIP in den Backup-Ordner; behält die
    letzten MAX_BACKUPS. tag (z. B. "import") wird Teil des Dateinamens;
    solche Backups rotieren separat (MAX_IMPORT_BACKUPS).

    only_if_changed: für die automatischen Backups bei Start und Beenden —
    hat sich seit dem letzten Backup nichts geändert, wäre das neue Byte für
    Byte dasselbe, und der Rückweg besteht ja bereits. Auf einem Datenordner
    im Netz spart das beim Öffnen das Lesen und Schreiben des gesamten
    Bildbestands. Das Backup von Hand ("Backup jetzt") sichert immer."""
    if _db_path is None or _read_only or not _db_path.exists():
        return None
    with _backup_lock:
        return _create_backup(tag, only_if_changed)


# Laufendes Start-Backup (Hintergrund-Thread); Tests warten darauf
_start_backup: threading.Thread | None = None


def _start_backup_in_background() -> None:
    """Start-Backup, ohne den Start aufzuhalten. Die Datenbank wird vorher
    eingelesen (klein, Größenordnung 100 kB): im ZIP steckt so genau der
    Stand beim Start — auch wenn Migrationen und die ersten Änderungen schon
    laufen, während der Bildbestand noch gepackt wird. Hat sich der Datensatz
    bis zum Ende geändert, entfällt wie immer das Kennzeichen, und der nächste
    Start sichert erneut."""
    global _start_backup
    db_path = _db_path
    snapshot = db_path.read_bytes()

    def run() -> None:
        try:
            with _backup_lock:
                # Datenordner inzwischen gewechselt oder Sperre abgegeben
                if _db_path != db_path or _read_only:
                    return
                _create_backup(None, True, db_snapshot=snapshot)
        except Exception:  # darf die laufende App nicht beenden
            logging.getLogger("uvicorn.error").exception("Start-Backup fehlgeschlagen")

    _start_backup = threading.Thread(target=run, name="start-backup", daemon=True)
    _start_backup.start()


def _create_backup(tag: str | None, only_if_changed: bool,
                   db_snapshot: bytes | None = None) -> str | None:
    _backup_dir.mkdir(parents=True, exist_ok=True)
    if only_if_changed and _backup_would_be_identical(db_snapshot):
        return None
    cleanup_orphan_images()  # verwaiste Bilder nicht in jedes Backup schleppen
    stand_vorher = _current_state(db_snapshot)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    suffix = f"-{tag}" if tag else ""
    target = _backup_dir / f"app-{stamp}{suffix}.zip"
    i = 2
    while target.exists():  # mehrere Backups in derselben Sekunde
        target = _backup_dir / f"app-{stamp}-{i}{suffix}.zip"
        i += 1
    # Erst unter einem Arbeitsnamen packen, dann umbenennen: bricht das Packen
    # ab (App gewaltsam beendet, Netz weg), bleibt kein halbes ZIP zurück, das
    # später als Backup angeboten und wiederhergestellt werden könnte.
    for rest in _backup_dir.glob(f"app-*{PART_SUFFIX}"):
        rest.unlink(missing_ok=True)
    part = target.with_name(target.name + PART_SUFFIX)
    with zipfile.ZipFile(part, "w") as zf:
        if db_snapshot is None:
            zf.write(_db_path, "app.db", compress_type=zipfile.ZIP_DEFLATED)
        else:
            zf.writestr("app.db", db_snapshot, compress_type=zipfile.ZIP_DEFLATED)
        img_dir = images_dir()
        if img_dir.is_dir():
            for p in sorted(img_dir.iterdir()):
                if p.is_file():
                    # Die aus ChemDraw eingefügten Bilder sind unkomprimierte
                    # Bitmaps — gepackt bleibt vom Bildbestand ein Bruchteil
                    # übrig (bei 30 Molekülen 37 MB -> 0,4 MB). Bereits
                    # komprimierte Formate (PNG) kostet das praktisch nichts.
                    try:
                        zf.write(p, f"images/{p.name}", compress_type=zipfile.ZIP_DEFLATED)
                    except FileNotFoundError:
                        pass  # eben ersetzt — das Start-Backup läuft neben der Arbeit
    os.replace(part, target)
    # Das Kennzeichen darf nur einen Stand behaupten, der auch wirklich im ZIP
    # steckt. Hat sich der Datensatz während des Packens geändert — bei einem
    # Datenordner im Netz kann das ein anderer PC gewesen sein, der die Sperre
    # gerade übernommen hat —, bleibt kein Kennzeichen zurück; dann sichert
    # der nächste Start wieder, statt fälschlich zu überspringen.
    if _current_state() == stand_vorher:
        _write_backup_state(target.name, stand_vorher)
    else:
        (_backup_dir / BACKUP_STATE_FILE).unlink(missing_ok=True)
    regular = [p for p in _existing_backups() if not _is_import_backup(p)]
    imports = [p for p in _existing_backups() if _is_import_backup(p)]
    for old in regular[:-MAX_BACKUPS]:
        old.unlink()
    for old in imports[:-MAX_IMPORT_BACKUPS]:
        old.unlink()
    return target.name


def list_backups() -> list[dict]:
    """Neueste zuerst. `created` wird aus dem Dateinamen gelesen (mtime ist
    durch copy2 der Stand der Quelle, nicht der Sicherungszeitpunkt)."""
    if _backup_dir is None or not _backup_dir.exists():
        return []
    out = []
    for p in reversed(_existing_backups()):
        m = re.match(r"app-(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})", p.name)
        created = f"{m[1]}-{m[2]}-{m[3]}T{m[4]}:{m[5]}:{m[6]}" if m else None
        out.append({"name": p.name, "size": p.stat().st_size, "created": created,
                    "pre_import": _is_import_backup(p)})
    return out


def restore_backup(name: str) -> None:
    """Ersetzt die aktive DB (und bei ZIP-Backups die gesicherten Bilder)
    durch das Backup. Wirft FileNotFoundError."""
    src = (_backup_dir / name) if _backup_dir else None
    if src is None or not src.is_file() or src.parent != _backup_dir:
        raise FileNotFoundError(name)
    _engine.dispose()  # alle Verbindungen schließen, damit die Datei ersetzbar ist
    if src.suffix == ".zip":
        _restore_zip_backup(src)
    else:  # älteres Backup-Format: reine DB-Kopie
        shutil.copy2(src, _db_path)


def _restore_zip_backup(src: Path, password: bytes | None = None) -> None:
    """DB ersetzen und gesicherte Bilder zurücklegen. Bilder, die nur im
    aktuellen Stand existieren, bleiben liegen — ein Undo der
    Wiederherstellung (stellt nur die DB zurück) findet sie dann wieder.
    password: nur für verschlüsselte Transferdateien (Backups sind offen)."""
    img_dir = images_dir()
    with pyzipper.AESZipFile(src) as zf:
        if password:
            zf.setpassword(password)
        for info in zf.infolist():
            if info.is_dir():
                continue
            if info.filename == "app.db":
                _db_path.write_bytes(zf.read(info))
            elif info.filename.startswith("images/"):
                # nur der Dateiname — Pfade aus dem Archiv nie übernehmen
                fname = Path(info.filename).name
                if fname:
                    img_dir.mkdir(parents=True, exist_ok=True)
                    (img_dir / fname).write_bytes(zf.read(info))


# ---------- Weitergabe: Transferdatei für einen anderen PC ----------

TRANSFER_MANIFEST = "transfer.json"


class TransferPasswordError(Exception):
    """Transferdatei ist passwortgeschützt: Passwort fehlt oder ist falsch."""

    def __init__(self, reason: str):  # "required" | "wrong"
        super().__init__(reason)
        self.reason = reason


def _counts() -> tuple[int, int]:
    from .models import Molecule, Project

    with _SessionLocal() as session:
        projects = session.scalar(select(func.count()).select_from(Project)) or 0
        molecules = session.scalar(select(func.count()).select_from(Molecule)) or 0
    return projects, molecules


def export_transfer(target_dir: Path, password: str | None = None,
                    name: str | None = None) -> dict:
    """Packt Datenbank + Bilder + Manifest als ZIP, das auf einem anderen PC
    mit derselben App eingelesen werden kann. Verlinkte externe Dateien
    wandern nicht mit — ihre Pfade bleiben in der Datenbank und zeigen dem
    Empfänger den Speicherort (Netzlaufwerk-Pfade funktionieren direkt).
    Mit Passwort wird der gesamte Inhalt AES-verschlüsselt (die Datei lässt
    sich dann nur über die App mit Passwort einlesen). name (optional) wird
    Teil des Dateinamens und beim Einlesen wieder angezeigt — so bleibt
    zuordenbar, welcher Export gerade geladen wird."""
    from .export import sanitize

    if _db_path is None or not _db_path.exists():
        raise FileNotFoundError("no database")
    cleanup_orphan_images()  # nur tatsächlich genutzte Bilder mitgeben
    projects, molecules = _counts()
    name = (name or "").strip() or None
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base = f"characterization-transfer-{stamp}" + (f"-{sanitize(name)}" if name else "")
    target = target_dir / f"{base}.zip"
    i = 2
    while target.exists():
        target = target_dir / f"{base}-{i}.zip"
        i += 1
    manifest = {
        "format": 1,
        "created": datetime.now().isoformat(timespec="seconds"),
        "computer": os.environ.get("COMPUTERNAME", ""),
        "name": name,
        "projects": projects,
        "molecules": molecules,
    }
    if password:
        zf = pyzipper.AESZipFile(target, "w", encryption=pyzipper.WZ_AES)
        zf.setpassword(password.encode("utf-8"))
    else:
        zf = zipfile.ZipFile(target, "w")
    with zf:
        zf.write(_db_path, "app.db", compress_type=zipfile.ZIP_DEFLATED)
        img_dir = images_dir()
        if img_dir.is_dir():
            for p in sorted(img_dir.iterdir()):
                if p.is_file():
                    # Aus ChemDraw eingefügte Bilder sind unkomprimierte
                    # Bitmaps — gepackt wird die Transferdatei um ein
                    # Vielfaches kleiner (verschlüsselt wird unabhängig davon)
                    zf.write(p, f"images/{p.name}",
                             compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr(TRANSFER_MANIFEST, json.dumps(manifest, indent=2))
    return {"file": str(target), "size": target.stat().st_size,
            "projects": projects, "molecules": molecules,
            "encrypted": bool(password), "name": name}


def import_transfer(zip_path: Path, password: str | None = None) -> dict:
    """Liest eine Transferdatei ein: sichert den aktuellen Stand als Backup und
    ersetzt dann Datenbank + Bilder. Wirft ValueError bei ungültiger Datei,
    TransferPasswordError bei fehlendem oder falschem Passwort — beides wird
    geprüft, BEVOR der aktuelle Stand angefasst wird."""
    pw = password.encode("utf-8") if password else None
    try:
        # AESZipFile liest auch unverschlüsselte ZIPs -> ein Weg für beide Fälle
        with pyzipper.AESZipFile(zip_path) as zf:
            names = set(zf.namelist())
            if "app.db" not in names:
                raise ValueError("app.db missing")
            if any(info.flag_bits & 0x1 for info in zf.infolist()) and not pw:
                raise TransferPasswordError("required")
            if pw:
                zf.setpassword(pw)
            try:
                zf.read("app.db")  # validiert das Passwort vor jeder Änderung
                manifest = (json.loads(zf.read(TRANSFER_MANIFEST))
                            if TRANSFER_MANIFEST in names else {})
            except RuntimeError:  # zipfile/pyzipper: "Bad password for file …"
                raise TransferPasswordError("wrong")
    # pyzipper bringt eine eigene BadZipFile-Klasse mit -> beide abfangen
    except (zipfile.BadZipFile, pyzipper.BadZipFile,
            json.JSONDecodeError, UnicodeDecodeError):
        raise ValueError("not a transfer file")
    if not isinstance(manifest, dict):
        manifest = {}
    # Der bisherige Stand bleibt als gekennzeichnetes "-import"-Backup
    # wiederherstellbar (eigene Rotation -> garantierter Rückweg)
    create_backup(tag="import")
    _engine.dispose()
    _restore_zip_backup(zip_path, pw)  # gleiches Format wie ZIP-Backups: app.db + images/
    # Die Datei kann von einer anderen App-Version stammen -> Schema angleichen;
    # Bildpfade des Quell-PCs werden dabei auf den hiesigen images-Ordner bezogen
    rewritten = _migrate_schema()
    projects, molecules = _counts()
    return {"projects": projects, "molecules": molecules, "rewritten": rewritten,
            "created": manifest.get("created"), "computer": manifest.get("computer"),
            "name": manifest.get("name")}


# ---------- Undo-Stapel (Snapshot vor jeder ändernden Aktion) ----------

def _undo_dir() -> Path:
    return _db_path.parent / "undo"


def _undo_snapshots() -> list[Path]:
    """Vorhandene Snapshots, älteste zuerst. Der Ordner wird nur beim ersten
    Mal gelesen; danach führen push/discard/pop die Liste selbst nach — nur
    dieser Prozess schreibt hinein (wer die Sperre hält, schreibt allein)."""
    global _undo_seq, _undo_count
    if _undo_count is not None:
        return _undo_cache
    d = _undo_dir()
    vorhanden = sorted(
        p for p in (d.glob("undo-*.db") if d.exists() else [])
        if re.fullmatch(r"undo-(\d+)\.db", p.name)
    )
    _undo_cache[:] = vorhanden
    _undo_count = len(vorhanden)
    if _undo_seq is None:
        _undo_seq = max((int(re.fullmatch(r"undo-(\d+)\.db", p.name)[1])
                         for p in vorhanden), default=0)
    return _undo_cache


def _forget_undo_state() -> None:
    """Merkliste verwerfen (Datenordner gewechselt, Sperre übernommen) —
    beim nächsten Zugriff wird der Ordner wieder gelesen."""
    global _undo_seq, _undo_count
    _undo_seq = _undo_count = None
    _undo_cache.clear()


def push_undo_snapshot() -> Path | None:
    """Vor einer ändernden Aktion aufrufen; gibt den Snapshot-Pfad zurück."""
    global _undo_seq, _undo_count
    if _db_path is None or _read_only or not _db_path.exists():
        return None
    with _state_lock:
        snaps = _undo_snapshots()
        d = _undo_dir()
        d.mkdir(parents=True, exist_ok=True)
        _undo_seq += 1
        snap = d / f"undo-{_undo_seq:08d}.db"
        shutil.copy2(_db_path, snap)
        snaps.append(snap)
        while len(snaps) > MAX_UNDO:
            snaps.pop(0).unlink(missing_ok=True)
        _undo_count = len(snaps)
        return snap


def discard_undo_snapshot(snap: Path) -> None:
    """Snapshot verwerfen, wenn die Aktion fehlgeschlagen ist (nichts geändert)."""
    global _undo_count
    with _state_lock:
        snap.unlink(missing_ok=True)
        snaps = _undo_snapshots()
        if snaps and snaps[-1] == snap:
            snaps.pop()
            _undo_count = len(snaps)


def undo_count() -> int:
    if _db_path is None:
        return 0
    with _state_lock:
        return len(_undo_snapshots())


def pop_undo() -> bool:
    """Stellt den jüngsten Snapshot wieder her. False, wenn keiner vorhanden."""
    global _undo_count
    with _state_lock:
        snaps = _undo_snapshots() if _db_path else []
        if not snaps:
            return False
        latest = snaps[-1]
        _engine.dispose()
        shutil.copy2(latest, _db_path)
        latest.unlink()
        snaps.pop()
        _undo_count = len(snaps)
        return True
