from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit

import anyio.to_thread
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.responses import JSONResponse, Response

from . import db
from .api import router

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

# Wird vom Weitergabe-Skript in die verteilte Kopie geschrieben;
# im Entwicklungsordner existiert die Datei nicht (-> leere Version).
VERSION_FILE = Path(__file__).resolve().parent.parent / "VERSION"


class NoCacheStaticFiles(StaticFiles):
    """Liefert HTML/CSS/JS ohne Browser-Cache aus, damit Aktualisierungen der
    lokalen App nach einem einfachen Neuladen sofort sichtbar sind."""

    def is_not_modified(self, response_headers, request_headers) -> bool:
        return False  # nie 304 -> Browser holt immer die aktuelle Datei

    def file_response(self, *args, **kwargs) -> Response:
        resp = super().file_response(*args, **kwargs)
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return resp

# Aktionen, die die Datenbank ändern, bekommen vorher einen Undo-Snapshot
_MUTATING_PREFIXES = ("/api/projects", "/api/molecules", "/api/entries",
                      "/api/notes", "/api/files")


def is_undoable(method: str, path: str) -> bool:
    if method not in ("POST", "PATCH", "DELETE"):
        return False
    # Der Export ändert die DB nicht; das Word-Dokument schon — es wird beim
    # Eintrag „Versuchsvorschrift" verlinkt und ist daher rückgängig zu machen.
    # Kopieren in die Zwischenablage ändert ebenfalls nichts.
    if path.endswith(("/export", "/copy")):
        return False
    if path.endswith("/restore"):  # Wiederherstellen soll rückgängig machbar sein
        return True
    return path.startswith(_MUTATING_PREFIXES)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Das Start-Backup läuft nebenher: der Server nimmt Anfragen an, sobald
    # Sperre und Migrationen durch sind (run.py öffnet dann den Browser)
    db.ensure_db(background_backup=True)
    yield
    # Backup beim Beenden (regulaerer Shutdown, z. B. Strg+C / Fenster der App),
    # danach Sperre im Datenordner freigeben
    db.create_backup(only_if_changed=True)
    db.close_db()


# Im Lesemodus (Datensatz wird gerade auf einem anderen PC bearbeitet) sind
# nur Aktionen erlaubt, die den Datenordner nicht verändern: Öffnen von
# Dateien, Auswahl-Dialoge, Exporte in fremde Ordner, Übernahme der Sperre,
# Kopieren in die Zwischenablage.
_READ_ONLY_ALLOWED = ("/api/open", "/api/dialog", "/api/lock/", "/api/settings/",
                      "/api/shutdown")


def is_blocked_read_only(method: str, path: str) -> bool:
    if method not in ("POST", "PATCH", "DELETE"):
        return False
    if path.startswith(_READ_ONLY_ALLOWED) or path.endswith(("/export", "/copy")):
        return False
    # Vor jeder Änderung die Sperrdatei prüfen: ein anderer PC könnte die
    # Sperre inzwischen übernommen haben (oder freigegeben)
    return not db.refresh_lock_state()


app = FastAPI(title="Characterization", lifespan=lifespan)


# Die App ist rein lokal (nur an 127.0.0.1 gebunden). Ein fremder Hostname im
# Host-Header stammt nicht vom Nutzer, sondern von einer Webseite, die per
# DNS-Rebinding auf 127.0.0.1 zeigt — solche Anfragen werden abgewiesen.
# Loopback mit beliebigem Port ist erlaubt (App: 8710, Test-Server: 8711).
_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
ALLOWED_HOSTS: set[str] = set(_LOOPBACK_HOSTS)  # Tests ergänzen "testserver"


def _hostname(value: str, is_url: bool) -> str:
    """Reiner Hostname (klein, ohne Port/Klammern) aus einem Host-Header
    (is_url=False) oder aus einer Origin-/Referer-URL (is_url=True)."""
    if not value:
        return ""
    parsed = urlsplit(value if is_url else "//" + value.strip())
    return (parsed.hostname or "").lower()


@app.middleware("http")
async def local_only_guard(request: Request, call_next):
    """Schützt gegen DNS-Rebinding (fremder Host-Header) und CSRF (fremder
    Origin bei ändernden Anfragen). Der Browser setzt Host bzw. Origin selbst
    und lässt sie durch Webseiten nicht fälschen — beide gehören daher zur
    Ziel-App und müssen lokal sein."""
    if _hostname(request.headers.get("host", ""), is_url=False) not in ALLOWED_HOSTS:
        return JSONResponse({"detail": "Forbidden host"}, status_code=403)
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        # Origin wird bei ändernden Cross-Origin-Anfragen immer mitgesendet;
        # fehlt er ganz, ist es kein Browser-Cross-Site-Request (Host schützt bereits).
        source = request.headers.get("origin") or request.headers.get("referer") or ""
        if source and _hostname(source, is_url=True) not in ALLOWED_HOSTS:
            return JSONResponse({"detail": "Forbidden origin"}, status_code=403)
    return await call_next(request)


# Die beiden folgenden Middlewares lesen bzw. schreiben im Datenordner. Liegt
# der auf einem Netzlaufwerk, dauert das spürbar — und weil Middlewares in der
# Event-Loop laufen, stünden solange ALLE anderen Anfragen still (die
# Oberfläche lädt Projekte, Dashboard und Undo-Stand gleichzeitig). Deshalb
# wandern die blockierenden Aufrufe in einen Arbeitsthread.

@app.middleware("http")
async def read_only_guard(request: Request, call_next):
    if await anyio.to_thread.run_sync(
        is_blocked_read_only, request.method, request.url.path
    ):
        holder = db.lock_holder() or {}
        who = holder.get("computer") or "?"
        de = request.headers.get("x-lang", "en").lower().startswith("de")
        msg = (f"Nur lesend: Der Datensatz wird gerade auf „{who}“ bearbeitet"
               if de else f"Read-only: the dataset is currently being edited on “{who}”")
        return JSONResponse({"detail": msg}, status_code=423)
    return await call_next(request)


@app.middleware("http")
async def undo_snapshot_middleware(request: Request, call_next):
    snap = None
    if is_undoable(request.method, request.url.path):
        snap = await anyio.to_thread.run_sync(db.push_undo_snapshot)
    response = await call_next(request)
    # Fehlgeschlagene Aktionen haben nichts geändert -> Snapshot verwerfen
    if snap is not None and response.status_code >= 400:
        await anyio.to_thread.run_sync(db.discard_undo_snapshot, snap)
    return response


@app.get("/api/version")
def get_version() -> dict:
    try:
        return {"version": VERSION_FILE.read_text(encoding="utf-8").strip()}
    except OSError:
        return {"version": ""}


app.include_router(router)
app.mount("/", NoCacheStaticFiles(directory=STATIC_DIR, html=True), name="static")
