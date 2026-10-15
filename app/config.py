r"""PC-spezifische Einstellungen der App (config.json neben start.bat).

Die Datei gehört zum jeweiligen Rechner, nicht zum Datensatz — sie wird
weder verteilt noch beim Update ersetzt. Enthält bisher nur, wo der
Datenordner liegt (Datenbank, Bilder, Undo, Backups). Ohne Datei bzw. ohne
Eintrag gilt wie bisher: data\ und backups\ im App-Ordner.

    {"data_dir": "H:\\Uni\\Promotion\\Characterization-Data"}

Ein Datenordner auf einem Netzlaufwerk ermöglicht das Arbeiten von mehreren
PCs mit demselben Datensatz (siehe db.py: Sperrdatei gegen gleichzeitiges
Schreiben, paths.py: laufwerksunabhängige Pfade).

Zweiter möglicher Eintrag: `inkscape_path` — nur nötig, wenn Inkscape nicht
an einem der üblichen Orte liegt. Der Word-Export braucht es, um zu jedem
SVG-Spektrum das Rasterbild zu erzeugen, das Word als Rückfall verlangt
(siehe svg_raster.py).

    {"data_dir": "H:\\…", "inkscape_path": "D:\\Inkscape\\bin\\inkscape.exe"}

Als gepacktes Programm (Characterization.exe, PyInstaller) liegt der
Programmordner woanders als die Daten: config.json, data\ und backups\
kommen nach %LOCALAPPDATA%\Characterization — ein Update ersetzt den
Programmordner komplett, ohne die Daten zu berühren.
"""
import json
import os
import sys
from pathlib import Path

# Programmdateien (static\, wordskel\, VERSION)
BASE_DIR = Path(__file__).resolve().parent.parent
FROZEN = getattr(sys, "frozen", False)
# Alles, was die App schreibt; aus dem Quellordner wie bisher der App-Ordner.
# CHARACTERIZATION_HOME lenkt das um (Ausprobieren eines Builds mit
# Wegwerf-Daten, ohne den echten Datensatz anzufassen).
if os.environ.get("CHARACTERIZATION_HOME"):
    HOME_DIR = Path(os.environ["CHARACTERIZATION_HOME"]).resolve()
elif FROZEN:
    HOME_DIR = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "Characterization"
else:
    HOME_DIR = BASE_DIR
CONFIG_PATH = HOME_DIR / "config.json"
DEFAULT_DATA_DIR = HOME_DIR / "data"
DEFAULT_BACKUP_DIR = HOME_DIR / "backups"


def load() -> dict:
    """Inhalt der config.json (leer, wenn nicht vorhanden oder unlesbar)."""
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def save(cfg: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")


def data_dir() -> Path:
    """Konfigurierter Datenordner (relative Angaben beziehen sich auf den
    App-Ordner); Standard: data\\ im App-Ordner."""
    raw = (load().get("data_dir") or "").strip()
    if not raw:
        return DEFAULT_DATA_DIR
    p = Path(raw)
    return p if p.is_absolute() else (HOME_DIR / p).resolve()


def backup_dir() -> Path:
    """Backups liegen beim Standard-Datenordner wie bisher in backups\\ im
    App-Ordner, bei einem eigenen Datenordner darin (backups\\) — so wandern
    sie mit dem Datensatz und sind von jedem PC aus dieselben."""
    raw = (load().get("backup_dir") or "").strip()
    if raw:
        p = Path(raw)
        return p if p.is_absolute() else (HOME_DIR / p).resolve()
    d = data_dir()
    return DEFAULT_BACKUP_DIR if d == DEFAULT_DATA_DIR else d / "backups"


def set_data_dir(path: Path | None) -> None:
    """Datenordner festlegen (None = zurück zum Standard)."""
    cfg = load()
    if path is None or path == DEFAULT_DATA_DIR:
        cfg.pop("data_dir", None)
    else:
        cfg["data_dir"] = str(path)
    save(cfg)
