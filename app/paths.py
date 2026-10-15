"""Laufwerksunabhängige Pfade für verlinkte Dateien.

Verlinkte Messdaten liegen typischerweise auf Netzlaufwerken (H:, T:, …).
Der Laufwerksbuchstabe ist aber eine Eigenschaft des jeweiligen PCs — auf
einem anderen Rechner kann dieselbe Freigabe unter einem anderen Buchstaben
hängen oder gar nicht gemappt sein. Deshalb speichert die App Pfade auf
Netzlaufwerken in UNC-Form (\\\\server\\freigabe\\…), die überall im selben
Netz gültig ist, und zeigt sie zur besseren Lesbarkeit wieder mit dem
lokalen Buchstaben an, wenn die Freigabe hier gemappt ist.

Pfade auf lokalen Laufwerken (C:\\…) lassen sich nicht übersetzen; sie
bleiben wie sie sind und werden in der Oberfläche als „nur auf diesem PC"
markiert.
"""
import concurrent.futures
import contextvars
import ctypes
import os
import re
import sys
import time
from contextlib import contextmanager

_IS_WIN = sys.platform == "win32"

# GetDriveType-Werte
DRIVE_REMOVABLE, DRIVE_FIXED, DRIVE_REMOTE, DRIVE_CDROM, DRIVE_RAMDISK = 2, 3, 4, 5, 6
_LOCAL_TYPES = {DRIVE_REMOVABLE, DRIVE_FIXED, DRIVE_CDROM, DRIVE_RAMDISK}

_DRIVE_RE = re.compile(r"^([A-Za-z]):[\\/]")
_UNC_RE = re.compile(r"^\\\\([^\\/]+)[\\/]([^\\/]+)")

_CACHE_TTL = 60.0  # Laufwerkszuordnungen ändern sich praktisch nie während der Sitzung
_drive_cache: tuple[float, dict[str, str]] | None = None


def _drive_type(letter: str) -> int:
    if not _IS_WIN:
        return 0
    return ctypes.windll.kernel32.GetDriveTypeW(f"{letter}:\\")


def _mapped_drives() -> dict[str, str]:
    """Netzlaufwerke dieses PCs: Buchstabe -> UNC-Wurzel, z. B.
    {'H': '\\\\server\\home'}. Wird 60 s gecacht."""
    global _drive_cache
    now = time.monotonic()
    if _drive_cache and now - _drive_cache[0] < _CACHE_TTL:
        return _drive_cache[1]
    mapping: dict[str, str] = {}
    if _IS_WIN:
        from ctypes import wintypes

        mpr = ctypes.windll.mpr
        buf = ctypes.create_unicode_buffer(1024)
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        for i in range(26):
            if not bitmask & (1 << i):
                continue
            letter = chr(65 + i)
            if _drive_type(letter) != DRIVE_REMOTE:
                continue
            n = wintypes.DWORD(len(buf))
            if mpr.WNetGetConnectionW(f"{letter}:", buf, ctypes.byref(n)) == 0:
                unc = buf.value.rstrip("\\")
                if unc.startswith("\\\\"):
                    mapping[letter] = unc
    _drive_cache = (now, mapping)
    return mapping


def to_portable(path: str | None) -> str | None:
    """Speicherform: 'H:\\Uni\\x' -> '\\\\server\\home\\Uni\\x', wenn H: ein
    Netzlaufwerk ist. Alle anderen Pfade bleiben unverändert."""
    if not path:
        return path
    m = _DRIVE_RE.match(path)
    if not m:
        return path
    unc = _mapped_drives().get(m[1].upper())
    if not unc:
        return path
    rest = path[m.end():].replace("/", "\\")
    return unc + ("\\" + rest if rest else "\\")


def to_display(path: str | None) -> str | None:
    """Anzeigeform: UNC-Pfad -> lokaler Laufwerksbuchstabe, falls die
    Freigabe auf diesem PC gemappt ist; sonst unverändert."""
    if not path or not path.startswith("\\\\"):
        return path
    low = path.lower()
    for letter, unc in _mapped_drives().items():
        u = unc.lower()
        if low == u or low.startswith(u + "\\"):
            rest = path[len(unc):]
            return f"{letter}:{rest or chr(92)}"
    return path


def is_local_only(path: str | None) -> bool:
    """Absoluter Pfad auf einem lokalen Laufwerk (Festplatte, USB-Stick) —
    von anderen PCs aus nicht erreichbar."""
    if not path or path.startswith("\\\\"):
        return False
    m = _DRIVE_RE.match(path)
    if not m:
        return False
    if not _IS_WIN:
        return True
    return _drive_type(m[1].upper()) in _LOCAL_TYPES


# ---------- Existenzprüfung mit Schonung nicht erreichbarer Server ----------

_DOWN_TTL = 30.0
_down: dict[str, float] = {}  # Freigabe-Wurzel (klein) -> Zeitpunkt „nicht erreichbar"


# Innerhalb einer Antwort wird jeder Pfad höchstens einmal angefasst: die
# Molekülliste fragt denselben Pfad mehrfach ab (einmal für <feld>_exists,
# einmal beim Zählen der toten Verweise, bei Bildern zusätzlich für den
# Vergleich mit der ChemDraw-Datei). Gemerkt wird das Ergebnis von os.stat,
# damit Existenz und Änderungszeit aus einem einzigen Zugriff kommen. Über
# eine Antwort hinaus wird nichts gemerkt — die Anzeige bleibt so aktuell
# wie bisher.
_MISSING = "missing"  # Merkwert für „geprüft, gibt es nicht"

_memo: contextvars.ContextVar[dict | None] = contextvars.ContextVar(
    "paths_memo", default=None
)


@contextmanager
def scan_scope():
    """Geltungsbereich der Merkliste (eine Anfrage). Verschachtelt sich
    gefahrlos: ein innerer Aufruf benutzt die Liste des äußeren weiter."""
    if _memo.get() is not None:
        yield  # schon in einem Geltungsbereich -> nichts zu tun
        return
    token = _memo.set({})
    try:
        yield
    finally:
        _memo.reset(token)


def stat(path: str | None) -> os.stat_result | None:
    """os.stat des Pfads oder None, wenn es ihn nicht gibt. Grundlage für
    exists() und für Zeitvergleiche (Bild ↔ ChemDraw-Datei)."""
    if not path:
        return None
    memo = _memo.get()
    if memo is None:
        return _stat_uncached(path)
    hit = memo.get(path)
    if hit is None:
        hit = memo[path] = _stat_uncached(path) or _MISSING
    return None if hit is _MISSING else hit


def note(path: str, st: os.stat_result) -> None:
    """Ein schon ermitteltes os.stat in die Merkliste legen. Wer eine Datei
    gerade angefasst hat (z. B. beim Wiederfinden einer umbenannten Datei),
    spart der Serialisierung so einen weiteren Zugriff auf die Freigabe."""
    memo = _memo.get()
    if memo is not None:
        memo[path] = st


def exists(path: str | None) -> bool:
    """Wie os.path.exists, aber: ist ein Server nicht erreichbar (Laptop
    außerhalb des Netzes), wird das 30 s gemerkt und für alle weiteren Pfade
    auf dieser Freigabe sofort False geliefert — sonst würde jede Prüfung in
    den SMB-Timeout laufen und die Molekülliste minutenlang hängen."""
    return stat(path) is not None


def _stat_uncached(path: str) -> os.stat_result | None:
    m = _UNC_RE.match(path)
    if not m:
        return _plain_stat(path)
    root = m[0].lower()
    since = _down.get(root)
    now = time.monotonic()
    if since is not None and now - since < _DOWN_TTL:
        return None
    st = _plain_stat(path)
    if st is not None:
        _down.pop(root, None)
        return st
    if not _share_reachable(m[0], root):
        _down[root] = now
    return None


def _plain_stat(path: str) -> os.stat_result | None:
    try:
        return os.stat(path)
    except (OSError, ValueError):  # ValueError: z. B. Null-Byte im Pfad
        return None


def _share_reachable(share: str, root: str) -> bool:
    """Ob die Freigabe selbst erreichbar ist. Innerhalb einer Anfrage wird
    das einmal geprüft — sonst kostet jeder tote Pfad einer Freigabe zwei
    Zugriffe statt einem."""
    memo = _memo.get()
    if memo is None:
        return os.path.exists(share)
    key = ("share", root)
    hit = memo.get(key)
    if hit is None:
        hit = memo[key] = os.path.exists(share)
    return hit


# ---------- Vorabprüfung ganzer Pfadlisten ----------

# Netzzugriffe sind Wartezeit, keine Rechenzeit — mehrere gleichzeitig kosten
# kaum mehr als einer. Mehr Breite bringt danach nichts und belastet die
# Freigabe unnötig.
_PREFETCH_WORKERS = 16


def prefetch(candidates) -> None:
    """Alle Pfade einer Antwort vorab prüfen und in die Merkliste legen.

    Zwei Beschleunigungen gegenüber Einzelprüfungen:
    * Liegen mehrere Pfade im selben Ordner (typisch: der images-Ordner mit
      allen Struktur- und ChemDraw-Dateien), wird der Ordner einmal gelesen,
      statt jede Datei einzeln zu erfragen.
    * Der Rest läuft nebenläufig.

    Das füllt nur die Merkliste vor: was hier nicht landet, wird später wie
    bisher einzeln geprüft. Ohne Geltungsbereich passiert nichts.
    """
    memo = _memo.get()
    if memo is None:
        return
    offen = {p for p in candidates if p and p not in memo}
    if not offen:
        return

    nach_ordner: dict[str, list[str]] = {}
    einzeln: list[str] = []
    for path in offen:
        parent = _parent_of(path)
        if parent is None:
            einzeln.append(path)
        else:
            nach_ordner.setdefault(parent, []).append(path)
    # Einen Ordner zu lesen lohnt erst ab zwei gesuchten Pfaden darin
    sammel = {d: ps for d, ps in nach_ordner.items() if len(ps) > 1}
    for d, ps in nach_ordner.items():
        if d not in sammel:
            einzeln.extend(ps)

    aufgaben = [(_scan_dir, d, ps) for d, ps in sammel.items()]
    aufgaben += [(_scan_one, p, None) for p in einzeln]
    if len(aufgaben) == 1:
        fn, arg, extra = aufgaben[0]
        memo.update(fn(arg, extra))
        return
    breite = min(_PREFETCH_WORKERS, len(aufgaben))
    with concurrent.futures.ThreadPoolExecutor(max_workers=breite) as pool:
        for ergebnis in pool.map(lambda a: a[0](a[1], a[2]), aufgaben):
            memo.update(ergebnis)


def _parent_of(path: str) -> str | None:
    """Ordner eines Pfads — None, wenn er sich nicht sauber in Ordner und
    Namen zerlegen lässt (Laufwerkswurzel, abschließender Trenner, die
    Freigabe selbst). Solche Pfade werden einzeln geprüft."""
    parent, name = os.path.split(path)
    if not parent or not name or parent == path:
        return None
    if path.startswith("\\\\") and not _UNC_RE.match(parent):
        return None  # \\server\freigabe selbst hat keinen lesbaren Ordner
    return parent


def _scan_dir(folder: str, paths_in_folder: list[str]) -> dict:
    """Einen Ordner einmal lesen und daraus alle gesuchten Pfade beantworten.
    Windows liefert beim Auflisten Größe und Zeiten gleich mit — der
    Vergleich Bild ↔ ChemDraw-Datei kostet damit keinen weiteren Zugriff."""
    try:
        with os.scandir(folder) as it:
            eintraege = {e.name: e for e in it}
    except (OSError, ValueError):
        # Ordner nicht lesbar (fehlt, keine Rechte, Server weg) -> einzeln
        # prüfen; nur so greift auch die Erkennung toter Freigaben
        return {p: (_stat_uncached(p) or _MISSING) for p in paths_in_folder}
    # Windows-Dateisysteme unterscheiden keine Groß-/Kleinschreibung, os.stat
    # findet die Datei dort auch bei abweichender Schreibweise. Anderswo wäre
    # eine Suche ohne Rücksicht darauf falsch.
    klein = {n.lower(): e for n, e in eintraege.items()} if _IS_WIN else {}
    ergebnis: dict = {}
    for path in paths_in_folder:
        name = os.path.basename(path)
        eintrag = eintraege.get(name) or klein.get(name.lower())
        st = None
        if eintrag is not None:
            try:
                st = eintrag.stat()  # folgt Verknüpfungen, genau wie os.stat
            except OSError:
                st = None  # z. B. eine ins Leere zeigende Verknüpfung
        ergebnis[path] = st or _MISSING
    return ergebnis


def _scan_one(path: str, _unbenutzt) -> dict:
    return {path: (_stat_uncached(path) or _MISSING)}
