"""Verlinkte Dateien wiederfinden, wenn sie umbenannt wurden.

Die App kopiert Messdaten nicht, sie merkt sich ihren Pfad. Benennt jemand
die Datei im Ordner um, zeigt der gespeicherte Pfad ins Leere — bisher blieb
dann nur die Warnung „Pfad existiert nicht mehr" und neues Verlinken von Hand.

Dateisysteme geben jeder Datei aber eine Kennung, die das Umbenennen
überlebt (Windows: Datenträger + Datei-Index, sonst Gerät + Inode). Die App
merkt sich diese Kennung zu jedem verlinkten Pfad (Tabelle link_ids) und
sucht, sobald ein Pfad verschwunden ist, im selben Ordner die Datei mit
derselben Kennung. Wird sie gefunden, schreibt die App den neuen Namen in
die Datenbank — der Verweis bleibt also heil, samt Beschriftung, Notizen und
Status. Für verlinkte Ordner gilt dasselbe.

Beide Schritte kosten Zugriffe auf die Freigabe und sind deshalb gedeckelt:

* Kennungen nachtragen läuft im Hintergrund und nur einmal je Datei — das
  Auflisten eines Ordners liefert die Kennung unter Windows nicht mit, es
  braucht ein os.stat je Datei. Ändert sich die Datei (Größe oder Zeit),
  wird die Kennung beim nächsten Neuladen aufgefrischt.
* Gesucht wird erst wieder, wenn sich am Ordner etwas geändert hat (seine
  Änderungszeit). Ein endgültig gelöschter Verweis durchsucht seinen Ordner
  also nicht bei jedem Neuladen erneut.

Wo das Dateisystem keine Kennung liefert (st_ino == 0, etwa auf manchen
Netzfreigaben), bleibt alles beim Alten: der Pfad wird als tot gemeldet.
"""
import os
import queue
import stat as stat_mod
import threading

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, object_session

from . import db, paths
from .models import DataEntry, EntryFile, LinkId, Molecule

# Felder, die auf Dateien und Ordner außerhalb der App zeigen. Die Bilder der
# App (data/images) stehen bewusst nicht dabei — die verwaltet sie selbst.
_ENTRY_FIELDS = ("folder_path", "file_path", "svg_path", "svg2_path")

# Obergrenze der Einzelprüfungen je Suche. Gut sortiert steht der Treffer
# vorne; ein Ordner mit tausenden Dateien soll die Anzeige nicht aufhalten.
_MAX_LOOKUPS = 80

_lock = threading.Lock()
_queue: "queue.Queue[str] | None" = None
_worker: threading.Thread | None = None

# Prozessweite Merklisten. Sie gelten für den offenen Datensatz; wechselt der
# Datenordner, werden sie verworfen (_forget_if_other_db).
_known: set[tuple[str, int, int]] = set()  # (Pfad, Größe, Zeit) — Kennung ist aktuell
_searched: dict[str, int] = {}  # Pfad -> Änderungszeit des Ordners beim erfolglosen Suchen
_known_db: str | None = None


# ---------- Kennung ----------

def file_id(st: os.stat_result) -> str | None:
    """Kennung der Datei hinter einem stat — None, wenn das Dateisystem
    keine liefert (dann lässt sich nichts wiederfinden)."""
    if not st.st_ino:
        return None
    return f"{st.st_dev}:{st.st_ino}"


def _stat(path: str) -> os.stat_result | None:
    """Frisches os.stat. Bewusst ohne die Merkliste aus paths: die bekommt
    ihre Werte teils aus dem Auflisten von Ordnern, und dabei bleibt die
    Kennung unter Windows leer."""
    try:
        return os.stat(path)
    except (OSError, ValueError):
        return None


# ---------- Abgleich beim Serialisieren ----------

def sync(mol: Molecule) -> None:
    """Vor dem Ausliefern eines Moleküls: verschwundene Pfade wiederfinden
    und fehlende Kennungen nachtragen lassen. Erwartet einen geöffneten
    paths.scan_scope — die Existenz jedes Pfads steht dort schon fest, hier
    entstehen also nur für tote Pfade neue Zugriffe."""
    if db.is_read_only():
        return  # der lesende PC schreibt nichts, auch keine Reparatur
    session = object_session(mol)
    if session is None:
        return
    _forget_if_other_db(session)
    geheilt = False
    nachtragen: list[str] = []
    for obj, attr, path in list(_links(mol)):
        st = paths.stat(path)
        if st is None:
            gefunden = _find_renamed(session, path)
            if gefunden:
                _rewrite(session, path, *gefunden)
                geheilt = True
        elif (path, st.st_size, st.st_mtime_ns) not in _known:
            nachtragen.append(path)
    if geheilt:
        session.commit()
    if nachtragen:
        _enqueue(nachtragen)


def _links(mol: Molecule):
    """Alle extern verlinkten Pfade des Moleküls als (Objekt, Feld, Pfad)."""
    if mol.si_path:
        yield mol, "si_path", mol.si_path
    for e in mol.entries:
        for attr in _ENTRY_FIELDS:
            p = getattr(e, attr)
            if p:
                yield e, attr, p
        for f in e.files:
            if f.path:
                yield f, "path", f.path


def _find_renamed(session: Session, path: str) -> tuple[str, os.stat_result] | None:
    """Die umbenannte Datei zu einem toten Pfad — (neuer Pfad, stat) oder None."""
    rec = session.get(LinkId, path)
    if rec is None or not rec.file_id:
        return None  # ohne gemerkte Kennung ist nichts zu suchen
    folder = os.path.dirname(path)
    if not folder or folder == path:
        return None
    ordner = paths.stat(folder)
    if ordner is None:
        return None  # der Ordner selbst ist weg — dann wurde nicht umbenannt
    if _searched.get(path) == ordner.st_mtime_ns:
        return None  # seit der letzten erfolglosen Suche unverändert
    treffer = _search(folder, rec)
    if treffer is None:
        _searched[path] = ordner.st_mtime_ns
    else:
        _searched.pop(path, None)
    return treffer


def _search(folder: str, rec: LinkId) -> tuple[str, os.stat_result] | None:
    try:
        with os.scandir(folder) as it:
            eintraege = [(e.path, e.is_dir(), _entry_stat(e)) for e in it]
    except (OSError, ValueError):
        return None
    endung = os.path.splitext(rec.path)[1].lower()

    def rang(item) -> tuple:
        pfad, _is_dir, st = item
        # Beim Umbenennen bleiben Größe und Änderungszeit gleich — solche
        # Kandidaten zuerst, dann die mit passender Endung.
        gleich = st is not None and st.st_size == rec.size and st.st_mtime_ns == rec.mtime_ns
        passend = os.path.splitext(pfad)[1].lower() == endung
        return (0 if gleich else 1, 0 if passend else 1, pfad)

    kandidaten = sorted((x for x in eintraege if x[1] == rec.is_dir), key=rang)
    for pfad, _is_dir, _st in kandidaten[:_MAX_LOOKUPS]:
        st = _stat(pfad)
        if st is not None and file_id(st) == rec.file_id:
            return pfad, st
    return None


def _entry_stat(entry: os.DirEntry) -> os.stat_result | None:
    try:
        return entry.stat()  # Größe und Zeiten liefert Windows beim Auflisten mit
    except OSError:
        return None


def _rewrite(session: Session, alt: str, neu: str, st: os.stat_result) -> None:
    """Den neuen Namen überall eintragen, wo der alte Pfad stand — dieselbe
    Datei kann mehrfach verlinkt sein (mehrere Moleküle, mehrere Einträge)."""
    for m in session.scalars(select(Molecule).where(Molecule.si_path == alt)):
        m.si_path = neu
    bedingung = or_(*(getattr(DataEntry, a) == alt for a in _ENTRY_FIELDS))
    for e in session.scalars(select(DataEntry).where(bedingung)):
        for a in _ENTRY_FIELDS:
            if getattr(e, a) == alt:
                setattr(e, a, neu)
    for f in session.scalars(select(EntryFile).where(EntryFile.path == alt)):
        f.path = neu
    _store(session, [(neu, st)])
    alt_rec = session.get(LinkId, alt)
    if alt_rec is not None:
        session.delete(alt_rec)
    _known.difference_update({k for k in _known if k[0] == alt})
    _searched.pop(alt, None)
    paths.note(neu, st)  # der neue Pfad ist geprüft: kein weiterer Zugriff nötig


# ---------- Kennungen nachtragen (Hintergrund) ----------

def remember(path: str) -> None:
    """Kennung eines gerade verlinkten Pfads nachtragen lassen. Wird beim
    Verlinken aufgerufen (api.link_in), damit das Wiederfinden ab dem ersten
    Moment greift — und nicht erst, wenn die App das Molekül wieder anzeigt."""
    if path and not db.is_read_only():
        _enqueue([path])


def _enqueue(pfade: list[str]) -> None:
    """Pfade zum Nachtragen der Kennung vormerken. Das kostet je Datei einen
    Zugriff auf die Freigabe und darf die Antwort nicht aufhalten."""
    global _queue, _worker
    with _lock:
        if _queue is None:
            _queue = queue.Queue()
            _worker = threading.Thread(target=_work, name="relink", daemon=True)
            _worker.start()
        for p in pfade:
            _queue.put(p)


def _work() -> None:
    while True:
        stapel = [_queue.get()]
        while True:  # alles nehmen, was schon wartet — eine Sitzung für alle
            try:
                stapel.append(_queue.get_nowait())
            except queue.Empty:
                break
        try:
            record(stapel)
        except Exception:
            pass  # Kennungen sind Komfort; ein Fehler hier darf nichts stören
        finally:
            for _ in stapel:
                _queue.task_done()


def record(pfade) -> int:
    """Kennungen der angegebenen Pfade ermitteln und merken. Liefert die
    Anzahl der geschriebenen Einträge (Tests rufen das direkt auf)."""
    if db.is_read_only():
        return 0
    gesehen: list[tuple[str, os.stat_result]] = []
    for p in dict.fromkeys(pfade):  # Reihenfolge behalten, Doppelte raus
        st = _stat(p)
        if st is not None and file_id(st):
            gesehen.append((p, st))
    if not gesehen:
        return 0
    session = db.new_session()
    if session is None:
        return 0
    try:
        _store(session, gesehen)
        session.commit()
    finally:
        session.close()
    return len(gesehen)


def _store(session: Session, gesehen: list[tuple[str, os.stat_result]]) -> None:
    """Kennungen in die Tabelle schreiben und in der Merkliste vermerken.
    Der Aufrufer schließt die Sitzung ab (commit)."""
    _forget_if_other_db(session)
    for p, st in gesehen:
        rec = session.get(LinkId, p)
        if rec is None:
            rec = LinkId(path=p)
            session.add(rec)
        rec.file_id = file_id(st)
        rec.size = st.st_size
        rec.mtime_ns = st.st_mtime_ns
        rec.is_dir = stat_mod.S_ISDIR(st.st_mode)
        _known.add((p, st.st_size, st.st_mtime_ns))


def flush(timeout: float = 10.0) -> None:
    """Warten, bis die vorgemerkten Kennungen geschrieben sind (Tests)."""
    q = _queue
    if q is None:
        return
    ende = threading.Event()
    threading.Thread(target=lambda: (q.join(), ende.set()), daemon=True).start()
    ende.wait(timeout)


def _forget_if_other_db(session: Session) -> None:
    """Merklisten gehören zum offenen Datensatz — beim Wechsel des
    Datenordners (und in Tests zwischen zwei Datenbanken) verfallen sie.

    Neu aufgebaut wird die Liste der bekannten Kennungen aus der Tabelle:
    sonst würde jeder App-Start alle verlinkten Dateien noch einmal einzeln
    anfassen, obwohl ihre Kennungen längst gespeichert sind."""
    global _known_db
    aktuell = str(db.db_file() or "")
    if aktuell == _known_db:
        return
    _known_db = aktuell
    _known.clear()
    _searched.clear()
    try:
        rows = session.execute(
            select(LinkId.path, LinkId.size, LinkId.mtime_ns)
        ).all()
    except Exception:
        return  # Tabelle noch nicht da (alter Datensatz) -> wird gleich angelegt
    _known.update((pfad, groesse, zeit) for pfad, groesse, zeit in rows)
