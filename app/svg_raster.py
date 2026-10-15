"""Rastert SVG-Spektren in PNGs — als Rückfallbilder für Word.

Word bettet SVGs immer doppelt ein: das SVG selbst (scharf in jeder
Vergrößerung, das sieht man im Dokument) und ein PNG derselben Größe als
Rückfall für alles, was kein SVG kann. Das PNG muss also mitgeliefert
werden, auch wenn es normalerweise niemand zu Gesicht bekommt.

Gerastert wird mit Inkscape, weil die Spektren aus MNova ohnehin über
Inkscape laufen (die Dateien tragen dessen Signatur) und Muster, eingebettete
Rasterbilder und Schriften dabei stimmen. Der Pfad wird selbst gesucht;
`inkscape_path` in der config.json übersteuert das. Fehlt Inkscape, entsteht
ein weißes Bild der richtigen Größe — im Word-Dokument bleibt das SVG
sichtbar, gemeldet wird es trotzdem.

Gearbeitet wird auf den schon gelesenen SVG-Bytes und in einem lokalen
Temp-Ordner: liest Inkscape direkt von der Netzfreigabe, dauert ein Spektrum
gut 30 statt gut 2 Sekunden. Mehrere Spektren laufen nebenläufig, weil jeder
Aufruf ein eigener Prozess ist.
"""
import re
import shutil
import subprocess
import tempfile
import uuid
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import config

# Breite des Rückfallbilds in Pixel: bei 16 cm Satzbreite rund 250 dpi —
# dieselbe Größenordnung, die Word selbst beim Einfügen erzeugt.
FALLBACK_WIDTH_PX = 1600

_CANDIDATES = [
    Path(r"C:\Program Files\Inkscape\bin\inkscape.exe"),
    Path(r"C:\Program Files\Inkscape\inkscape.exe"),
    Path(r"C:\Program Files (x86)\Inkscape\bin\inkscape.exe"),
]

# Längenangaben in SVG: Zahl mit optionaler Einheit
_LENGTH = re.compile(r"^\s*([-+0-9.eE]+)\s*(px|pt|pc|mm|cm|in|%)?\s*$")
_PER_UNIT = {None: 1.0, "px": 1.0, "pt": 96 / 72, "pc": 16.0,
             "mm": 96 / 25.4, "cm": 96 / 2.54, "in": 96.0}


def find_inkscape() -> Path | None:
    """Pfad zu Inkscape (config.json „inkscape_path" hat Vorrang) oder None."""
    raw = (config.load().get("inkscape_path") or "").strip()
    if raw:
        p = Path(raw)
        return p if p.is_file() else None
    for p in _CANDIDATES:
        if p.is_file():
            return p
    found = shutil.which("inkscape")
    return Path(found) if found else None


def _length(value: str | None) -> float | None:
    """SVG-Länge in Pixel; None bei Prozentangaben oder Unsinn."""
    if not value:
        return None
    m = _LENGTH.match(value)
    if not m or m.group(2) == "%":
        return None
    try:
        return float(m.group(1)) * _PER_UNIT[m.group(2)]
    except (ValueError, KeyError):
        return None


def aspect_ratio(svg: bytes) -> float:
    """Höhe geteilt durch Breite. Bevorzugt die width/height-Angaben des
    SVG, sonst die viewBox; ohne beides 3:4 als neutrale Annahme."""
    try:
        root = ET.fromstring(svg)
    except ET.ParseError:
        return 0.75
    w, h = _length(root.get("width")), _length(root.get("height"))
    if not w or not h:
        box = (root.get("viewBox") or "").replace(",", " ").split()
        if len(box) == 4:
            try:
                w, h = float(box[2]), float(box[3])
            except ValueError:
                w = h = None
    return h / w if w and h and w > 0 else 0.75


def _white_png(width: int, height: int) -> bytes:
    from io import BytesIO

    from PIL import Image

    buf = BytesIO()
    Image.new("RGB", (max(1, width), max(1, height)), "white").save(buf, "PNG")
    return buf.getvalue()


def _run_inkscape(inkscape: Path, svg: bytes, name: str,
                  width_px: int) -> tuple[bytes | None, str | None]:
    work = Path(tempfile.gettempdir()) / f"svg-raster-{uuid.uuid4().hex}"
    src, out = work.with_suffix(".svg"), work.with_suffix(".png")
    try:
        src.write_bytes(svg)
        proc = subprocess.run(
            [str(inkscape), "--export-type=png", f"--export-filename={out}",
             f"--export-width={width_px}", str(src)],
            capture_output=True, timeout=180, stdin=subprocess.DEVNULL,
            # ohne Konsolenfenster (das gepackte Programm hat selbst keins)
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if proc.returncode == 0 and out.is_file() and out.stat().st_size:
            return out.read_bytes(), None
        detail = (proc.stderr or b"").decode("utf-8", "replace").strip().splitlines()
        reason = detail[-1] if detail else f"exit code {proc.returncode}"
    except (OSError, subprocess.SubprocessError) as e:
        reason = str(e) or type(e).__name__
    finally:
        for p in (src, out):
            try:
                p.unlink(missing_ok=True)
            except OSError:
                pass
    return None, f"Inkscape could not rasterize {name} ({reason})"


def to_png(svg: bytes, name: str = "spectrum.svg",
           width_px: int = FALLBACK_WIDTH_PX) -> tuple[bytes, str | None]:
    """Rastert ein SVG; gibt (PNG-Bytes, Warnung) zurück. Die Warnung ist
    None, wenn Inkscape gerastert hat, sonst der Grund für das weiße Bild."""
    return to_pngs([(name, svg)], width_px)[0]


def to_pngs(items: list[tuple[str, bytes]],
            width_px: int = FALLBACK_WIDTH_PX) -> list[tuple[bytes, str | None]]:
    """Rastert mehrere SVGs nebenläufig — ein Inkscape-Prozess je Bild."""
    inkscape = find_inkscape()
    blank = ("Inkscape not found — the SVG is embedded, but its raster "
             "fallback image is blank")

    def one(item: tuple[str, bytes]) -> tuple[bytes, str | None]:
        name, svg = item
        height_px = max(1, round(width_px * aspect_ratio(svg)))
        if inkscape is None:
            return _white_png(width_px, height_px), blank
        png, reason = _run_inkscape(inkscape, svg, name, width_px)
        if png is not None:
            return png, None
        return _white_png(width_px, height_px), (
            f"{reason} — the SVG is embedded, but its raster fallback image is blank"
        )

    if len(items) < 2:
        return [one(i) for i in items]
    with ThreadPoolExecutor(max_workers=min(4, len(items))) as pool:
        return list(pool.map(one, items))
