"""Native Auswahl-Dialoge für den Server: startet app.dialog_worker als Subprozess."""
import subprocess
import sys
import threading
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

_lock = threading.Lock()
_last_dir = ""  # Startordner für den nächsten Dialog


class DialogBusyError(Exception):
    pass


def open_dialog(kind: str, filter_key: str = "any", initial: str = "", lang: str = "en") -> str | None:
    """Gibt den gewählten Pfad zurück (Windows-Schreibweise) oder None bei Abbruch."""
    global _last_dir
    if not _lock.acquire(blocking=False):
        raise DialogBusyError
    try:
        start = initial if initial and Path(initial).exists() else _last_dir
        # Im gepackten Programm ist sys.executable die Characterization.exe
        # selbst; sie startet mit --dialog den Worker statt der App (desktop.py)
        worker = ["--dialog"] if getattr(sys, "frozen", False) else ["-m", "app.dialog_worker"]
        result = subprocess.run(
            [sys.executable, *worker, kind, filter_key, start, lang],
            capture_output=True, text=True, encoding="utf-8", cwd=BASE_DIR,
            stdin=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW,
        )
        raw = (result.stdout or "").strip()
        if not raw:
            return None
        path = Path(raw)
        _last_dir = str(path if kind == "folder" else path.parent)
        return str(path)
    finally:
        _lock.release()
