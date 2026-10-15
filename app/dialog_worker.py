"""Läuft als eigener Subprozess: öffnet einen nativen Auswahl-Dialog und
schreibt den gewählten Pfad nach stdout (leer = abgebrochen).

Als Subprozess, weil tkinter nur im Hauptthread eines Prozesses zuverlässig
ist — der FastAPI-Server bleibt davon unberührt.
"""
import sys
import tkinter as tk
from tkinter import filedialog

TEXTS = {
    "de": {
        "file": "Datei wählen", "folder": "Ordner wählen",
        "word": "Word-Dokumente", "pdf": "PDF-Dateien", "mnova": "MNova-Dateien",
        "svg": "SVG-Dateien",
        "si": "Supporting Information (PDF/Word)",
        "image": "Bilder (PNG/SVG)", "zip": "Transferdateien (ZIP)", "all": "Alle Dateien",
    },
    "en": {
        "file": "Select file", "folder": "Select folder",
        "word": "Word documents", "pdf": "PDF files", "mnova": "MNova files",
        "svg": "SVG files",
        "si": "Supporting information (PDF/Word)",
        "image": "Images (PNG/SVG)", "zip": "Transfer files (ZIP)", "all": "All files",
    },
}

PATTERNS = {
    "word": "*.docx *.doc",
    "pdf": "*.pdf",
    "si": "*.pdf *.docx *.doc",
    "mnova": "*.mnova",
    "svg": "*.svg",
    "image": "*.png *.svg",
    "zip": "*.zip",
}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    kind = sys.argv[1] if len(sys.argv) > 1 else "file"
    filter_key = sys.argv[2] if len(sys.argv) > 2 else "any"
    initial = sys.argv[3] if len(sys.argv) > 3 else ""
    lang = sys.argv[4] if len(sys.argv) > 4 else "en"
    txt = TEXTS.get(lang, TEXTS["en"])

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    if kind == "folder":
        path = filedialog.askdirectory(title=txt["folder"], initialdir=initial or None)
    else:
        filetypes = [(txt["all"], "*.*")]
        if filter_key in PATTERNS:
            filetypes.insert(0, (txt[filter_key], PATTERNS[filter_key]))
        path = filedialog.askopenfilename(
            title=txt["file"], initialdir=initial or None, filetypes=filetypes
        )
    root.destroy()
    if path:
        print(path)


if __name__ == "__main__":
    main()
