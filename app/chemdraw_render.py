"""Rendert eine gespeicherte ChemDraw-Datei (.cdx) neu in ein Pixelbild.

Wird die per „ChemDraw ⬈" geöffnete .cdx in ChemDraw bearbeitet und
gespeichert, ist das beim Einfügen abgelegte Pixelbild veraltet. Das einzige
Programm, das die Zeichnung originalgetreu rendert, ist ChemDraw selbst —
es wird hier per COM-Automation ferngesteuert: Datei in der laufenden
Instanz öffnen (per COM geöffnete Dokumente sind dort unsichtbar, der
Nutzer merkt nichts; läuft keine Instanz, wird eine gestartet), als EMF
exportieren und das EMF mit derselben GDI-Routine wie beim Einfügen
rendern (clipboard_win.emf_to_bmp: 300 dpi, weißer Hintergrund).

Eigenheiten der ChemDraw-COM-API (per Experiment ermittelt):
- Document.Close() kehrt erfolgreich zurück, schließt aber nichts.
  Zuverlässig schließt nur WM_CLOSE an das unsichtbare Dokumentfenster
  (Klasse "CSWInvisible", Fenstertitel = Dateiname).
- SaveAs bindet das Dokument an die Zieldatei um — der Fenstertitel ist
  danach der Name der EMF-Datei, nicht mehr der .cdx.
"""
import ctypes
import os
import tempfile
import threading
import uuid
from ctypes import wintypes
from pathlib import Path

from .clipboard_win import emf_to_bmp

PROGID = "ChemDraw.Application"
KCD_FORMAT_EMF = 1279675717  # kCDFormatEnhMetafile aus ChemDraws CDFormat-Enum

WM_CLOSE = 0x0010

_user32 = ctypes.windll.user32
_gdi32 = ctypes.windll.gdi32
_gdi32.GetEnhMetaFileW.argtypes = [wintypes.LPCWSTR]
_gdi32.GetEnhMetaFileW.restype = wintypes.HANDLE
_gdi32.DeleteEnhMetaFile.argtypes = [wintypes.HANDLE]
_gdi32.DeleteEnhMetaFile.restype = wintypes.BOOL

# ChemDraw verkraftet keine parallelen Automation-Aufrufe — serialisieren
_lock = threading.Lock()


class RenderError(Exception):
    """ChemDraw konnte die Datei nicht neu rendern (nicht installiert,
    Lizenzproblem, defekte Datei …) — Details in der Meldung."""


def _close_invisible_document(title: str) -> None:
    """Schließt die unsichtbaren ChemDraw-Dokumentfenster mit diesem Titel."""
    proto = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def cb(hwnd, _lparam):
        cls = ctypes.create_unicode_buffer(64)
        _user32.GetClassNameW(hwnd, cls, 64)
        if cls.value == "CSWInvisible":
            txt = ctypes.create_unicode_buffer(260)
            _user32.GetWindowTextW(hwnd, txt, 260)
            if txt.value == title:
                _user32.SendMessageW(hwnd, WM_CLOSE, 0, 0)
        return True

    _user32.EnumWindows(proto(cb), 0)


def _export_emf(cdx_path: Path, emf_path: Path) -> None:
    """Öffnet die .cdx unsichtbar in ChemDraw und exportiert sie als EMF."""
    import comtypes
    import comtypes.client

    comtypes.CoInitialize()
    created = False
    try:
        app = comtypes.client.GetActiveObject(PROGID, dynamic=True)
    except OSError:
        app = comtypes.client.CreateObject(PROGID, dynamic=True)
        created = True
        try:
            app.Visible = False
        except Exception:
            pass
    try:
        doc = app.Documents.Open(str(cdx_path))
        if doc is None:
            raise RenderError(f"ChemDraw could not open the file: {cdx_path}")
        try:
            doc.SaveAs(str(emf_path), KCD_FORMAT_EMF)
        finally:
            try:
                doc.Modified = False  # kein „Speichern?“-Dialog beim Schließen
            except Exception:
                pass
            _close_invisible_document(doc.Name)
    finally:
        if created:
            try:
                app.Quit()
            except Exception:
                pass


def export_emf(cdx_path: Path) -> bytes:
    """Exportiert die ChemDraw-Datei als EMF und gibt die Dateibytes zurück.

    Für den Word-Export: das EMF ist die Vektorfassung, die Word im Dokument
    anzeigt — das eingebettete ChemDraw-Objekt daneben macht es per
    Doppelklick weiter bearbeitbar. Wirft RenderError wie render_cdx.
    """
    emf_path = Path(tempfile.gettempdir()) / f"cdx-emf-{uuid.uuid4().hex}.emf"
    with _lock:
        try:
            _export_emf(cdx_path, emf_path)
        except RenderError:
            raise
        except Exception as e:
            raise RenderError(str(e) or type(e).__name__)
    try:
        if not emf_path.is_file() or not emf_path.stat().st_size:
            raise RenderError("ChemDraw did not write an EMF file")
        return emf_path.read_bytes()
    finally:
        try:
            os.unlink(emf_path)
        except OSError:
            pass


def render_cdx(cdx_path: Path) -> bytes:
    """Rendert die ChemDraw-Datei in fertige BMP-Bilddateibytes —
    gleiche Qualität und gleicher weißer Hintergrund wie beim Einfügen.
    Wirft RenderError, wenn ChemDraw oder das Rendern scheitert."""
    emf_path = Path(tempfile.gettempdir()) / f"cdx-render-{uuid.uuid4().hex}.emf"
    with _lock:
        try:
            _export_emf(cdx_path, emf_path)
        except RenderError:
            raise
        except Exception as e:
            raise RenderError(str(e) or type(e).__name__)
    try:
        if not emf_path.is_file() or emf_path.stat().st_size == 0:
            raise RenderError("ChemDraw did not write an EMF file")
        hemf = _gdi32.GetEnhMetaFileW(str(emf_path))
        if not hemf:
            raise RenderError("EMF file is not readable")
        try:
            bmp = emf_to_bmp(hemf)
        finally:
            _gdi32.DeleteEnhMetaFile(hemf)
        if not bmp:
            raise RenderError("EMF could not be rendered to an image")
        return bmp
    finally:
        try:
            os.unlink(emf_path)
        except OSError:
            pass
