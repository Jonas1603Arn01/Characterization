"""Updates des gepackten Programms von GitHub Releases.

Ablauf: Beim Start fragt die Oberfläche GET /api/update — einmal pro
Programmstart wird dann nachgesehen, welche Version auf GitHub die neueste
ist (über die Weiterleitung von …/releases/latest, ohne API und damit ohne
Abfragegrenze). Ist sie neuer, bietet die Oberfläche das Update an; erst die
Bestätigung (POST /api/update/install) lädt die Datei für dieses System,
prüft sie gegen SHA256SUMS.txt des Releases, packt sie neben dem Programm
aus und startet ein kleines Hilfsskript. Dann beendet sich die App wie mit
„Quit“ (Backup, Sperre frei); das Skript wartet darauf, tauscht den
Programmordner bzw. die .app aus und startet die neue Version. Geht etwas
schief, bleibt die alte Version unverändert und läuft weiter bzw. wird
wieder gestartet.

Die Daten liegen getrennt vom Programm (config.HOME_DIR) und werden nicht
berührt. Abschalten: "update_check": false in config.json.
"""
import hashlib
import os
import re
import shutil
import ssl
import subprocess
import sys
import threading
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

from . import config

REPO = "Jonas1603Arn01/Characterization"
SITE = f"https://github.com/{REPO}"
HEADERS = {"User-Agent": "Characterization-updater"}
TIMEOUT = 15
CHUNK = 256 * 1024

_lock = threading.Lock()
# status: idle -> checking -> none | available -> downloading -> installing
#         -> restarting; error (Update gescheitert, alte Version läuft weiter)
_state: dict = {"status": "idle"}


def current_version() -> str:
    # CHARACTERIZATION_FAKE_VERSION: nur für tools/update_test.py (gibt eine
    # ältere Version vor, damit das Update auf das aktuelle Release greift)
    fake = os.environ.get("CHARACTERIZATION_FAKE_VERSION")
    if fake:
        return fake
    try:
        return (config.BASE_DIR / "VERSION").read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def parse(version: str) -> tuple[int, int, int] | None:
    m = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", (version or "").strip())
    return tuple(int(x) for x in m.groups()) if m else None


def asset_name(version: str) -> str | None:
    if sys.platform == "win32":
        return f"Characterization-{version}-windows.zip"
    if sys.platform == "darwin":
        return f"Characterization-{version}-macos-arm64.zip"
    return None


def install_target() -> Path | None:
    """Was ausgetauscht wird: Windows der Programmordner, macOS die .app.
    None, wenn nicht gepackt oder nicht austauschbar (macOS startet eine nicht
    nach „Programme“ verschobene App aus einer schreibgeschützten Kopie)."""
    if not getattr(sys, "frozen", False):
        return None
    exe = Path(sys.executable).resolve()
    if sys.platform == "win32":
        return exe.parent
    if sys.platform == "darwin":
        app = exe.parents[2]
        if app.suffix == ".app" and "AppTranslocation" not in str(app):
            return app
    return None


def _ssl_context() -> ssl.SSLContext:
    # Windows: Zertifikatsspeicher des Systems (kennt auch Uni-/Firmen-Proxys);
    # macOS: das gepackte Python bringt keine mit -> certifi
    ctx = ssl.create_default_context()
    if sys.platform == "darwin":
        try:
            import certifi
            ctx.load_verify_locations(certifi.where())
        except (ImportError, OSError):
            pass
    return ctx


def _open(url: str, method: str = "GET"):
    req = urllib.request.Request(url, method=method, headers=HEADERS)
    return urllib.request.urlopen(req, timeout=TIMEOUT, context=_ssl_context())


def _set(**kw) -> None:
    with _lock:
        _state.update(kw)


def status() -> dict:
    with _lock:
        return dict(_state)


def check() -> dict:
    """Neueste Version auf GitHub — nur beim ersten Aufruf je Programmstart,
    danach der gemerkte Stand. Offline oder GitHub gestört: still kein Update."""
    with _lock:
        if _state["status"] != "idle":
            return dict(_state)
        _state["status"] = "checking"
    current = current_version()
    if (install_target() is None or parse(current) is None or not asset_name(current)
            or config.load().get("update_check") is False):
        _set(status="none", supported=False, current=current)
        return status()
    try:
        with _open(f"{SITE}/releases/latest") as r:
            release_url = r.geturl()          # …/releases/tag/v1.4.0
        tag = release_url.rstrip("/").rsplit("/", 1)[-1]
        latest = tag.lstrip("v")
        if parse(latest) is None or parse(latest) <= parse(current):
            _set(status="none", supported=True, current=current, latest=latest)
            return status()
        url = f"{SITE}/releases/download/{tag}/{asset_name(latest)}"
        with _open(url, method="HEAD"):
            pass                              # gibt es den Download für dieses System?
        _set(status="available", supported=True, current=current, latest=latest,
             tag=tag, url=url, release_url=release_url)
    except (OSError, ValueError) as e:
        print(f"update check failed: {e}", file=sys.stderr)
        _set(status="none", supported=True, current=current, error=str(e))
    return status()


def start_install(on_ready) -> dict:
    """Update im Hintergrund laden und vorbereiten; on_ready() beendet danach
    die App (Backup + Sperre frei), das Hilfsskript übernimmt den Austausch."""
    with _lock:
        if _state["status"] not in ("available", "error") or "url" not in _state:
            raise RuntimeError("no update available")
        _state.update(status="downloading", progress=0.0, error=None)
    threading.Thread(target=_install, args=(on_ready,), name="update", daemon=True).start()
    return status()


def _install(on_ready) -> None:
    st = status()
    target = install_target()
    work = config.HOME_DIR / "update"
    new = None
    try:
        if target is None or not os.access(target.parent, os.W_OK):
            raise OSError(f"no write access to {target.parent if target else '?'}")
        shutil.rmtree(work, ignore_errors=True)
        work.mkdir(parents=True)
        archive = work / asset_name(st["latest"])
        _download(st["url"], archive)
        _verify(st["tag"], archive)
        _set(status="installing")
        new = _unpack(archive, target)
        _start_helper(target, new, work)
        _set(status="restarting")
        print(f"update to {st['latest']} prepared, restarting", file=sys.stderr)
        on_ready()
    except Exception as e:  # alte Version bleibt und läuft weiter
        print(f"update failed: {e}", file=sys.stderr)
        if new is not None:
            shutil.rmtree(_staging_root(target, new), ignore_errors=True)
        _set(status="error", error=str(e) or type(e).__name__)


def _download(url: str, dest: Path) -> None:
    with _open(url) as r, open(dest, "wb") as f:
        total = int(r.headers.get("Content-Length") or 0)
        done = 0
        while chunk := r.read(CHUNK):
            f.write(chunk)
            done += len(chunk)
            if total:
                _set(progress=round(done / total, 3))


def _verify(tag: str, archive: Path) -> None:
    """Prüfsumme aus SHA256SUMS.txt des Releases (ältere Releases haben keine)."""
    try:
        with _open(f"{SITE}/releases/download/{tag}/SHA256SUMS.txt") as r:
            sums = r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return
        raise
    expected = {name.strip().lstrip("*"): digest.lower()
                for digest, name in (line.split(None, 1) for line in sums.splitlines() if line.strip())}
    want = expected.get(archive.name)
    if not want:
        raise OSError(f"{archive.name} is not listed in SHA256SUMS.txt")
    h = hashlib.sha256()
    with open(archive, "rb") as f:
        while chunk := f.read(CHUNK):
            h.update(chunk)
    if h.hexdigest() != want:
        raise OSError("checksum mismatch - download damaged")


def _unpack(archive: Path, target: Path) -> Path:
    """Neue Version neben die alte (gleiches Laufwerk -> Austausch per
    Umbenennen). Liefert den Pfad der neuen Version."""
    if sys.platform == "darwin":
        stage = target.parent / ".Characterization-update"
        shutil.rmtree(stage, ignore_errors=True)
        stage.mkdir()
        # ditto erhält Symlinks, Rechte und Signatur im Bundle
        subprocess.run(["ditto", "-x", "-k", str(archive), str(stage)], check=True)
        new = stage / "Characterization" / "Characterization.app"
        if not (new / "Contents" / "MacOS" / "Characterization").is_file():
            raise OSError("update archive has no Characterization.app")
        return new
    new = target.with_name(target.name + ".new")
    shutil.rmtree(new, ignore_errors=True)
    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            parts = Path(info.filename).parts[1:]  # oberster Ordner "Characterization/"
            if not parts or ".." in parts:
                continue
            dest = new.joinpath(*parts)
            if info.is_dir():
                dest.mkdir(parents=True, exist_ok=True)
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, open(dest, "wb") as out:
                shutil.copyfileobj(src, out, CHUNK)
    if not (new / "Characterization.exe").is_file():
        raise OSError("update archive has no Characterization.exe")
    return new


def _staging_root(target: Path, new: Path) -> Path:
    return new.parent.parent if sys.platform == "darwin" else new


def _start_helper(target: Path, new: Path, work: Path) -> None:
    """Hilfsskript starten, das nach dem Ende dieser App austauscht und die
    neue Version startet (mit denselben Argumenten, z. B. --server-only)."""
    env = dict(os.environ)
    env.pop("CHARACTERIZATION_FAKE_VERSION", None)
    log = config.HOME_DIR / "update.log"
    args = sys.argv[1:]
    if sys.platform == "win32":
        script = work / "update.ps1"
        script.write_text(_ps_script(os.getpid(), target, new, log, args), encoding="utf-8-sig")
        cmd = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
               "-WindowStyle", "Hidden", "-File", str(script)]
        flags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
        try:  # nicht mit dieser App beenden lassen (Job-Objekte)
            subprocess.Popen(cmd, env=env, creationflags=flags | subprocess.CREATE_BREAKAWAY_FROM_JOB,
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, close_fds=True)
        except OSError:
            subprocess.Popen(cmd, env=env, creationflags=flags, stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True)
    else:
        script = work / "update.sh"
        script.write_text(_sh_script(os.getpid(), target, new, log, args), encoding="utf-8")
        subprocess.Popen(["/bin/sh", str(script)], env=env, start_new_session=True,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, close_fds=True)


def _ps_quote(s: object) -> str:
    return "'" + str(s).replace("'", "''") + "'"


def _ps_script(pid: int, target: Path, new: Path, log: Path, args: list[str]) -> str:
    old = target.with_name(target.name + ".old")
    arglist = "@(" + ", ".join(_ps_quote(a) for a in args) + ")"
    return f"""# Characterization update helper (written by app/updater.py)
$target = {_ps_quote(target)}
$new = {_ps_quote(new)}
$old = {_ps_quote(old)}
$log = {_ps_quote(log)}
$exe = Join-Path $target 'Characterization.exe'
$arguments = {arglist}
function Log($m) {{ Add-Content -Path $log -Value "$(Get-Date -Format s) $m" }}
function Start-App {{
    if ($arguments.Count) {{ Start-Process -FilePath $exe -ArgumentList $arguments }}
    else {{ Start-Process -FilePath $exe }}
}}
Log 'waiting for the app to quit'
Wait-Process -Id {pid} -Timeout 300 -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 500
if (Test-Path $old) {{ Remove-Item $old -Recurse -Force -ErrorAction SilentlyContinue }}
$moved = $false
for ($i = 0; $i -lt 30 -and -not $moved; $i++) {{
    try {{ Rename-Item -Path $target -NewName (Split-Path $old -Leaf) -ErrorAction Stop; $moved = $true }}
    catch {{ Start-Sleep -Seconds 1 }}
}}
if (-not $moved) {{
    Log "old version is still in use - update skipped"
    Remove-Item $new -Recurse -Force -ErrorAction SilentlyContinue
    Start-App; exit 1
}}
try {{ Rename-Item -Path $new -NewName (Split-Path $target -Leaf) -ErrorAction Stop }}
catch {{
    Log "could not move the new version into place: $_"
    Rename-Item -Path $old -NewName (Split-Path $target -Leaf)
    Start-App; exit 1
}}
Remove-Item $old -Recurse -Force -ErrorAction SilentlyContinue
Log 'updated'
Start-App
"""


def _sh_quote(s: object) -> str:
    return "'" + str(s).replace("'", "'\\''") + "'"


def _sh_script(pid: int, target: Path, new: Path, log: Path, args: list[str]) -> str:
    old = target.with_name(target.name + ".old")
    stage = new.parent.parent
    argv = " ".join(_sh_quote(a) for a in args)
    # Mit Argumenten (Tests: --server-only) direkt starten, damit sie und die
    # Umgebung ankommen; sonst wie ein Doppelklick über "open". Als Funktion,
    # denn "… &; exit 1" wäre ein Syntaxfehler (und sh liest den ganzen
    # if-Block vorab — das Skript bräche dann vor dem Austausch ab).
    start_body = (f'"$target/Contents/MacOS/Characterization" {argv} >/dev/null 2>&1 &'
                  if args else 'open "$target"')
    return f"""#!/bin/sh
# Characterization update helper (written by app/updater.py)
target={_sh_quote(target)}
new={_sh_quote(new)}
old={_sh_quote(old)}
stage={_sh_quote(stage)}
log={_sh_quote(log)}
say() {{ echo "$(date '+%Y-%m-%dT%H:%M:%S') $1" >> "$log"; }}
start_app() {{
    {start_body}
}}
say 'waiting for the app to quit'
while kill -0 {pid} 2>/dev/null; do sleep 0.5; done
rm -rf "$old"
if ! mv "$target" "$old"; then
    say 'could not move the old version - update skipped'; rm -rf "$stage"; start_app; exit 1
fi
if ! mv "$new" "$target"; then
    say 'could not move the new version into place'; mv "$old" "$target"; rm -rf "$stage"; start_app; exit 1
fi
rm -rf "$old" "$stage"
say 'updated'
start_app
"""
