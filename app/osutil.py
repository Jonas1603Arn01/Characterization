"""Was zwischen Windows, macOS und Linux verschieden ist.

Die App ist auf Windows zu Hause: Zwischenablage (clipboard_win) und
ChemDraw-Fernsteuerung (chemdraw_render) gibt es nur dort. Auf macOS und
Linux werden diese Module gar nicht erst importiert — die Aufrufer prüfen
IS_WIN und melden stattdessen, dass die Funktion Windows braucht.
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
