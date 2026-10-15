"""Liest Bilder direkt aus der Windows-Zwischenablage (ctypes, ohne Zusatzpakete).

Browser reichen beim Einfügen nur Standardformate durch (CF_DIB, kopierte
Dateien). Programme wie ChemDraw („Copy as PNG") legen Bilder aber unter
registrierten Formaten wie "PNG" ab — die sind für Webseiten unsichtbar.
Da der Server auf demselben Rechner läuft, holt dieses Modul sie direkt ab.

Reihenfolge: fertige Bilddaten ("PNG"/"JFIF"/"GIF"), dann DIB-Bitmaps
(als BMP verpackt), zuletzt eine kopierte Bilddatei (CF_HDROP).
"""
import ctypes
import struct
import time
from ctypes import wintypes
from pathlib import Path

CF_DIB = 8
CF_ENHMETAFILE = 14
CF_HDROP = 15
CF_DIBV5 = 17

# Registrierte Formate, die bereits fertige Bilddateien enthalten
RAW_FORMATS = ("PNG", "image/png", "JFIF", "GIF")

# ChemDraw legt beim Kopieren zusätzlich sein natives CDX-Format ab —
# damit lässt sich die Struktur später in ChemDraw weiterbearbeiten.
CDX_FORMAT = "ChemDraw Interchange Format"
CDX_MAGIC = b"VjCD0100"  # Dateikopf jeder CDX-Datei

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}

_user32 = ctypes.windll.user32
_kernel32 = ctypes.windll.kernel32
_shell32 = ctypes.windll.shell32
_gdi32 = ctypes.windll.gdi32

# Auf 64-Bit sind Handles Pointer — ohne restype/argtypes würde ctypes
# sie zu 32-Bit-Ints beschneiden.
_user32.OpenClipboard.argtypes = [wintypes.HWND]
_user32.OpenClipboard.restype = wintypes.BOOL
_user32.CloseClipboard.restype = wintypes.BOOL
_user32.IsClipboardFormatAvailable.argtypes = [wintypes.UINT]
_user32.IsClipboardFormatAvailable.restype = wintypes.BOOL
_user32.GetClipboardData.argtypes = [wintypes.UINT]
_user32.GetClipboardData.restype = wintypes.HANDLE
_user32.RegisterClipboardFormatW.argtypes = [wintypes.LPCWSTR]
_user32.RegisterClipboardFormatW.restype = wintypes.UINT
_kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
_kernel32.GlobalLock.restype = ctypes.c_void_p
_kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
_kernel32.GlobalUnlock.restype = wintypes.BOOL
_kernel32.GlobalSize.argtypes = [wintypes.HGLOBAL]
_kernel32.GlobalSize.restype = ctypes.c_size_t
_shell32.DragQueryFileW.argtypes = [wintypes.HANDLE, wintypes.UINT,
                                    wintypes.LPWSTR, wintypes.UINT]
_shell32.DragQueryFileW.restype = wintypes.UINT
_user32.EmptyClipboard.restype = wintypes.BOOL
_user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
_user32.SetClipboardData.restype = wintypes.HANDLE
_user32.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR,
                                    wintypes.DWORD, ctypes.c_int, ctypes.c_int,
                                    ctypes.c_int, ctypes.c_int, wintypes.HWND,
                                    wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID]
_user32.CreateWindowExW.restype = wintypes.HWND
_user32.DestroyWindow.argtypes = [wintypes.HWND]
_user32.DestroyWindow.restype = wintypes.BOOL
_kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
_kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
_kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
_kernel32.GlobalFree.restype = wintypes.HGLOBAL


# ---------- Enhanced Metafile (EMF) rendern ----------
# ChemDraw legt beim normalen Kopieren KEIN Pixelbild ab, sondern nur eine
# Vektorgrafik (CF_ENHMETAFILE) + sein CDX-Format. Das EMF wird hier per GDI
# in eine Bitmap gerendert, damit auch normales Strg+C aus ChemDraw einfügbar ist.

class ENHMETAHEADER(ctypes.Structure):
    _fields_ = [
        ("iType", wintypes.DWORD),
        ("nSize", wintypes.DWORD),
        ("rclBounds", wintypes.RECT),
        ("rclFrame", wintypes.RECT),      # Zielrahmen in 0,01 mm
        ("dSignature", wintypes.DWORD),
        ("nVersion", wintypes.DWORD),
        ("nBytes", wintypes.DWORD),
        ("nRecords", wintypes.DWORD),
        ("nHandles", wintypes.WORD),
        ("sReserved", wintypes.WORD),
        ("nDescription", wintypes.DWORD),
        ("offDescription", wintypes.DWORD),
        ("nPalEntries", wintypes.DWORD),
        ("szlDevice", wintypes.SIZE),
        ("szlMillimeters", wintypes.SIZE),
    ]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", ctypes.c_long),
        ("biHeight", ctypes.c_long),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", ctypes.c_long),
        ("biYPelsPerMeter", ctypes.c_long),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


_gdi32.GetEnhMetaFileHeader.argtypes = [wintypes.HANDLE, wintypes.UINT,
                                        ctypes.POINTER(ENHMETAHEADER)]
_gdi32.GetEnhMetaFileHeader.restype = wintypes.UINT
_gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
_gdi32.CreateCompatibleDC.restype = wintypes.HDC
_gdi32.CreateDIBSection.argtypes = [wintypes.HDC, ctypes.POINTER(BITMAPINFOHEADER),
                                    wintypes.UINT, ctypes.POINTER(ctypes.c_void_p),
                                    wintypes.HANDLE, wintypes.DWORD]
_gdi32.CreateDIBSection.restype = wintypes.HBITMAP
_gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
_gdi32.SelectObject.restype = wintypes.HGDIOBJ
_gdi32.PatBlt.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int,
                          ctypes.c_int, ctypes.c_int, wintypes.DWORD]
_gdi32.PatBlt.restype = wintypes.BOOL
_gdi32.PlayEnhMetaFile.argtypes = [wintypes.HDC, wintypes.HANDLE,
                                   ctypes.POINTER(wintypes.RECT)]
_gdi32.PlayEnhMetaFile.restype = wintypes.BOOL
_gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
_gdi32.DeleteObject.restype = wintypes.BOOL
_gdi32.DeleteDC.argtypes = [wintypes.HDC]
_gdi32.DeleteDC.restype = wintypes.BOOL
_gdi32.GdiFlush.restype = wintypes.BOOL

EMF_DPI = 300        # Render-Auflösung für Vektorgrafiken
EMF_MAX_PX = 4000    # Kantenlängen-Deckel gegen absurde Rahmenangaben
WHITENESS = 0x00FF0062  # PatBlt-Rasteroperation: Fläche weiß füllen


def emf_to_bmp(hemf) -> bytes | None:
    """Rendert ein Enhanced Metafile mit weißem Hintergrund in eine
    32-Bit-BMP (fertige Dateibytes) — None, wenn das Rendern scheitert."""
    hdr = ENHMETAHEADER()
    if not _gdi32.GetEnhMetaFileHeader(hemf, ctypes.sizeof(hdr), ctypes.byref(hdr)):
        return None
    w = hdr.rclFrame.right - hdr.rclFrame.left   # in 0,01 mm
    h = hdr.rclFrame.bottom - hdr.rclFrame.top
    if w <= 0 or h <= 0:
        return None
    scale = min(EMF_DPI / 2540, EMF_MAX_PX / max(w, h))  # Pixel pro 0,01 mm
    width = max(1, round(w * scale))
    height = max(1, round(h * scale))

    bmi = BITMAPINFOHEADER(biSize=40, biWidth=width, biHeight=-height,  # top-down
                           biPlanes=1, biBitCount=32, biCompression=0,
                           biSizeImage=width * height * 4)
    dc = _gdi32.CreateCompatibleDC(None)
    if not dc:
        return None
    bits = ctypes.c_void_p()
    bmp = _gdi32.CreateDIBSection(dc, ctypes.byref(bmi), 0, ctypes.byref(bits), None, 0)
    if not bmp or not bits:
        _gdi32.DeleteDC(dc)
        return None
    try:
        old = _gdi32.SelectObject(dc, bmp)
        _gdi32.PatBlt(dc, 0, 0, width, height, WHITENESS)
        rect = wintypes.RECT(0, 0, width, height)
        ok = _gdi32.PlayEnhMetaFile(dc, hemf, ctypes.byref(rect))
        _gdi32.GdiFlush()
        pixels = ctypes.string_at(bits, width * height * 4)
        _gdi32.SelectObject(dc, old)
    finally:
        _gdi32.DeleteObject(bmp)
        _gdi32.DeleteDC(dc)
    return dib_to_bmp(bytes(bmi) + pixels) if ok else None


def _open_clipboard(retries: int = 5, hwnd=None) -> bool:
    """Die Zwischenablage ist ein globales Betriebsmittel — kurz belegt
    (z. B. vom kopierenden Programm) schlägt Öffnen fehl, daher Wiederholen."""
    for _ in range(retries):
        if _user32.OpenClipboard(hwnd):
            return True
        time.sleep(0.05)
    return False


def _global_bytes(fmt: int) -> bytes | None:
    handle = _user32.GetClipboardData(fmt)
    if not handle:
        return None
    ptr = _kernel32.GlobalLock(handle)
    if not ptr:
        return None
    try:
        size = _kernel32.GlobalSize(handle)
        return ctypes.string_at(ptr, size) if size else None
    finally:
        _kernel32.GlobalUnlock(handle)


def dib_to_bmp(dib: bytes) -> bytes | None:
    """Ein DIB aus der Zwischenablage ist eine BMP-Datei ohne Dateikopf —
    den 14-Byte-BITMAPFILEHEADER hier voranstellen. Der Pixel-Offset muss
    Farbtabelle und (bei BI_BITFIELDS) die drei Farbmasken einrechnen."""
    if len(dib) < 40:
        return None
    header_size, = struct.unpack_from("<I", dib, 0)
    if header_size < 40 or header_size > len(dib):
        return None
    bit_count, = struct.unpack_from("<H", dib, 14)
    compression, = struct.unpack_from("<I", dib, 16)
    clr_used, = struct.unpack_from("<I", dib, 32)
    colors = clr_used or ((1 << bit_count) if bit_count <= 8 else 0)
    offset = 14 + header_size + colors * 4
    if header_size == 40 and compression == 3:  # BI_BITFIELDS
        offset += 12
    return b"BM" + struct.pack("<IHHI", 14 + len(dib), 0, 0, offset) + dib


def _first_dropped_file() -> Path | None:
    handle = _user32.GetClipboardData(CF_HDROP)
    if not handle:
        return None
    buf = ctypes.create_unicode_buffer(2048)
    n = _shell32.DragQueryFileW(handle, 0, buf, 2048)
    return Path(buf.value) if n else None


def read_clipboard_image() -> bytes | None:
    """Bild aus der Zwischenablage als fertige Bilddatei-Bytes (PNG/JPG/GIF/BMP…)
    oder None, wenn keins vorhanden ist."""
    if not _open_clipboard():
        return None
    try:
        for name in RAW_FORMATS:
            fmt = _user32.RegisterClipboardFormatW(name)
            if fmt and _user32.IsClipboardFormatAvailable(fmt):
                data = _global_bytes(fmt)
                if data:
                    return data
        # Windows synthetisiert CF_DIB auch aus CF_BITMAP/CF_DIBV5
        for fmt in (CF_DIB, CF_DIBV5):
            if _user32.IsClipboardFormatAvailable(fmt):
                dib = _global_bytes(fmt)
                bmp = dib_to_bmp(dib) if dib else None
                if bmp:
                    return bmp
        # Nur Vektorgrafik vorhanden (ChemDraw-Strg+C, Office-Formen) -> rendern
        if _user32.IsClipboardFormatAvailable(CF_ENHMETAFILE):
            hemf = _user32.GetClipboardData(CF_ENHMETAFILE)
            if hemf:
                bmp = emf_to_bmp(hemf)
                if bmp:
                    return bmp
        if _user32.IsClipboardFormatAvailable(CF_HDROP):
            path = _first_dropped_file()
            if path and path.suffix.lower() in IMAGE_SUFFIXES and path.is_file():
                return path.read_bytes()
        return None
    finally:
        _user32.CloseClipboard()


def read_clipboard_cdx() -> bytes | None:
    """ChemDraw-Struktur (CDX) aus der Zwischenablage, oder None wenn keine
    vorhanden ist. GlobalSize liefert die Allokationsgröße — mögliche
    Füll-Bytes am Ende sind für CDX-Leser unschädlich (Chunk-Format)."""
    if not _open_clipboard():
        return None
    try:
        fmt = _user32.RegisterClipboardFormatW(CDX_FORMAT)
        if not fmt or not _user32.IsClipboardFormatAvailable(fmt):
            return None
        data = _global_bytes(fmt)
        return data if data and data.startswith(CDX_MAGIC) else None
    finally:
        _user32.CloseClipboard()


def read_clipboard_smiles() -> str | None:
    """SMILES-Text, den ChemDraw beim Kopieren zusätzlich ablegt
    (null-terminiertes ASCII), oder None."""
    if not _open_clipboard():
        return None
    try:
        fmt = _user32.RegisterClipboardFormatW("SMILES")
        if not fmt or not _user32.IsClipboardFormatAvailable(fmt):
            return None
        data = _global_bytes(fmt)
        if not data:
            return None
        return data.split(b"\x00", 1)[0].decode("ascii", "ignore").strip() or None
    finally:
        _user32.CloseClipboard()


# ---------- Schreiben: ChemDraw-Zeichnung in die Zwischenablage ----------
# Nachgebaut wird, was beim Kopieren aus ChemDraw ankommt: das CDX (ChemDraw
# fügt es bearbeitbar ein), ein eingebettetes ChemDraw-OLE-Objekt (Word und
# PowerPoint fügen es als ChemDraw-Objekt ein, per Doppelklick bearbeitbar)
# und ein Bild für alle anderen Programme — zugleich die Ansicht des Objekts.

EMBED_SOURCE = "Embed Source"            # OLE-Objekt als Compound File
OBJECT_DESCRIPTOR = "Object Descriptor"  # Klasse, Größe und Name dazu
CHEMDRAW_TYPE_NAME = "CS ChemDraw 64-bit Drawing"
COPY_SOURCE = "Characterization"
DVASPECT_CONTENT = 1
GMEM_MOVEABLE = 0x0002
_OBJECT_DESCRIPTOR_HEAD = 52


def object_descriptor(clsid: bytes, type_name: str, source: str,
                      width_himetric: int, height_himetric: int) -> bytes:
    """OBJECTDESCRIPTOR-Struktur (Größe in 0,01 mm, danach die beiden
    Namen als nullterminiertes UTF-16)."""
    names = type_name.encode("utf-16-le") + b"\0\0"
    src = source.encode("utf-16-le") + b"\0\0"
    head = _OBJECT_DESCRIPTOR_HEAD
    return struct.pack(
        "<I16sIiiiiIII", head + len(names) + len(src), clsid, DVASPECT_CONTENT,
        width_himetric, height_himetric, 0, 0, 0, head, head + len(names),
    ) + names + src


def _picture(image: bytes) -> tuple[bytes, int, int] | None:
    """DIB des gespeicherten Bilds samt Größe in 0,01 mm — None, wenn es sich
    nicht lesen lässt. Die Auflösung steht im DIB: Word bemisst das eingefügte
    Objekt danach, ohne Angabe nähme es 96 dpi an und ein 300-dpi-Bild käme
    dreimal zu groß an. Aus ChemDraw eingefügte Bilder tragen keine Angabe
    (emf_to_bmp), sind aber mit EMF_DPI gerendert."""
    from io import BytesIO

    from PIL import Image

    try:
        with Image.open(BytesIO(image)) as im:
            im.load()
            dpi = (im.info.get("dpi") or (0, 0))[0]
            dpi = round(dpi) if dpi >= 72 else EMF_DPI
            if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
                rgba = im.convert("RGBA")
                rgb = Image.new("RGB", im.size, "white")
                rgb.paste(rgba, mask=rgba.getchannel("A"))
            else:
                rgb = im.convert("RGB")
    except Exception:
        return None
    bmp = BytesIO()
    rgb.save(bmp, "BMP", dpi=(dpi, dpi))
    width, height = rgb.size
    return (bmp.getvalue()[14:],  # DIB = BMP ohne Dateikopf
            round(width / dpi * 2540), round(height / dpi * 2540))


def chemdraw_formats(cdx: bytes, image: bytes | None) -> list[tuple[str | int, bytes]]:
    """Alle Formate für write_clipboard: die ChemDraw-eigenen zuerst, das Bild
    zuletzt (ohne lesbares Bild nur Zeichnung + Objekt).

    Das Bild bewusst NUR als DIB, nicht zusätzlich als „PNG": liegt PNG an,
    fügt Word bei Strg+V das Bild statt des ChemDraw-Objekts ein (gemessen,
    PowerPoint nimmt in beiden Fällen das Objekt). Ganz ohne Bild scheitert
    das Einfügen des Objekts in Word — das DIB ist zugleich seine Ansicht."""
    from . import olecf

    pic = _picture(image) if image else None
    width, height = (pic[1], pic[2]) if pic else (0, 0)
    formats: list[tuple[str | int, bytes]] = [
        (CDX_FORMAT, cdx),
        (EMBED_SOURCE, olecf.chemdraw_object(cdx)),
        (OBJECT_DESCRIPTOR, object_descriptor(olecf.CHEMDRAW_CLSID, CHEMDRAW_TYPE_NAME,
                                              COPY_SOURCE, width, height)),
    ]
    if pic:
        formats.append((CF_DIB, pic[0]))
    return formats


def write_clipboard(formats: list[tuple[str | int, bytes]]) -> None:
    """Ersetzt den Inhalt der Zwischenablage durch `formats` (Formatname oder
    CF_-Nummer → Bytes). Wirft OSError, wenn das nicht gelingt.

    Laut Windows-Doku scheitert SetClipboardData ohne Besitzerfenster —
    daher ein unsichtbares Hilfsfenster. Es darf danach sofort weg: die
    Speicherblöcke gehören ab SetClipboardData dem System."""
    hwnd = _user32.CreateWindowExW(0, "STATIC", None, 0, 0, 0, 0, 0, None, None, None, None)
    if not hwnd:
        raise OSError("could not create a window for the clipboard")
    try:
        if not _open_clipboard(retries=20, hwnd=hwnd):
            raise OSError("clipboard is in use by another program")
        try:
            if not _user32.EmptyClipboard():
                raise OSError("clipboard could not be emptied")
            for fmt, data in formats:
                if isinstance(fmt, str):
                    fmt = _user32.RegisterClipboardFormatW(fmt)
                handle = _kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
                ptr = _kernel32.GlobalLock(handle) if handle else None
                if not ptr:
                    if handle:
                        _kernel32.GlobalFree(handle)
                    raise OSError("not enough memory for the clipboard")
                ctypes.memmove(ptr, data, len(data))
                _kernel32.GlobalUnlock(handle)
                if not _user32.SetClipboardData(fmt, handle):
                    _kernel32.GlobalFree(handle)
                    raise OSError("clipboard did not accept the data")
        finally:
            _user32.CloseClipboard()
    finally:
        _user32.DestroyWindow(hwnd)
