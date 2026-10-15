"""Was zwischen Windows und macOS verschieden ist.

Zwischenablage: clipboard_win bzw. clipboard_mac (gleiche Lese-Funktionen).
ChemDraw fernsteuern (chemdraw_render, COM) geht nur unter Windows — die
Aufrufer prüfen IS_WIN und melden sonst, wie es von Hand geht. Andere
Systeme (nur run.py zum Entwickeln) bekommen das, was der Browser kann.
"""
import os
import subprocess
import sys

IS_WIN = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"

# Hilfsprogramme (Dialog-Worker, Inkscape) ohne Konsolenfenster starten;
# die Konstante gibt es nur unter Windows, anderswo ist es kein Thema
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def open_path(path: str) -> None:
    """Datei mit dem Standardprogramm bzw. Ordner im Dateimanager öffnen."""
    if IS_WIN:
        os.startfile(path)
    elif IS_MAC:
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])
