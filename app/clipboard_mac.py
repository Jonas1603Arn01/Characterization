"""macOS-Zwischenablage (NSPasteboard über PyObjC) — das Gegenstück zu
clipboard_win: Bild und ChemDraw-Zeichnung (CDX) lesen, ChemDraw-Zeichnung
schreiben.

Unter welchem Typnamen ChemDraw für Mac sein CDX ablegt, ist nicht
dokumentiert. Gelesen wird es deshalb am Dateikopf (CDX_MAGIC), egal unter
welchem Typ; der gefundene Typ wird gemerkt (config.json
„mac_cdx_pasteboard_type") und beim Kopieren als erster benutzt. Jeder
Lesevorgang schreibt die angebotenen Typen ins app.log — damit lässt sich
nachvollziehen, was ChemDraw tatsächlich liefert.

Nur unter macOS importieren (siehe osutil.IS_MAC).
"""
import io
import sys

import objc
from AppKit import (
    NSBitmapImageRep,
    NSColor,
    NSCompositingOperationSourceOver,
    NSDeviceRGBColorSpace,
    NSGraphicsContext,
    NSImage,
    NSPasteboard,
    NSRectFill,
)
from Foundation import NSData, NSMakeRect, NSZeroRect

from . import config

CDX_MAGIC = b"VjCD0100"  # wie clipboard_win
# Kandidaten fürs Schreiben, solange noch kein echter ChemDraw-Typ gesehen
# wurde: UTI der .cdx-Dateien und der Windows-Formatname (den macOS als
# eigenen Typ führt)
CDX_TYPES = (
    "com.perkinelmer.chemdraw.cdx",
    "com.cambridgesoft.chemdraw.cdx",
    "ChemDraw Interchange Format",
)
SMILES_TYPES = ("SMILES", "chemical/x-daylight-smiles")
PNG = "public.png"
TIFF = "public.tiff"
RENDER_DPI = 300   # Vektorgrafik (ChemDraw kopiert als PDF) wie unter Windows
MAX_PX = 4000      # Kantenlängen-Deckel


def _pasteboard():
    return NSPasteboard.generalPasteboard()


def _data(pb, typ: str) -> bytes | None:
    data = pb.dataForType_(typ)
    return bytes(data) if data is not None and data.length() else None


def _types(pb) -> list[str]:
    types = [str(t) for t in (pb.types() or [])]
    print(f"clipboard types: {types}", file=sys.stderr)
    return types


def _render_png(pb) -> bytes | None:
    """Was immer NSImage aus der Zwischenablage machen kann (PDF, TIFF, …)
    als PNG mit 300 dpi auf weißem Grund."""
    img = NSImage.alloc().initWithPasteboard_(pb)
    if img is None:
        return None
    w, h = img.size()
    if w <= 0 or h <= 0:
        return None
    scale = min(RENDER_DPI / 72, MAX_PX / max(w, h))
    pw, ph = max(1, round(w * scale)), max(1, round(h * scale))
    rep = NSBitmapImageRep.alloc().initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
        None, pw, ph, 8, 4, True, False, NSDeviceRGBColorSpace, 0, 0)
    ctx = NSGraphicsContext.graphicsContextWithBitmapImageRep_(rep)
    NSGraphicsContext.saveGraphicsState()
    try:
        NSGraphicsContext.setCurrentContext_(ctx)
        NSColor.whiteColor().set()
        NSRectFill(NSMakeRect(0, 0, pw, ph))
        img.drawInRect_fromRect_operation_fraction_(
            NSMakeRect(0, 0, pw, ph), NSZeroRect, NSCompositingOperationSourceOver, 1.0)
        ctx.flushGraphics()
    finally:
        NSGraphicsContext.restoreGraphicsState()
    png = rep.representationUsingType_properties_(4, None)  # NSBitmapImageFileTypePNG
    return bytes(png) if png is not None else None


def read_clipboard_image() -> bytes | None:
    """Bild aus der Zwischenablage als PNG (bzw. die abgelegte Bilddatei)."""
    with objc.autorelease_pool():
        pb = _pasteboard()
        types = _types(pb)
        if PNG in types:
            data = _data(pb, PNG)
            if data:
                return data
        if TIFF in types:
            data = _data(pb, TIFF)
            if data:
                from PIL import Image
                buf = io.BytesIO()
                with Image.open(io.BytesIO(data)) as im:
                    im.save(buf, "PNG")
                return buf.getvalue()
        # nur Vektorgrafik (ChemDraw: PDF) -> rendern
        return _render_png(pb)


def read_clipboard_cdx() -> bytes | None:
    """ChemDraw-Zeichnung (CDX) — erkannt am Dateikopf, unter welchem Typ
    auch immer sie liegt."""
    with objc.autorelease_pool():
        pb = _pasteboard()
        types = _types(pb)
        known = (config.load().get("mac_cdx_pasteboard_type") or "").strip()
        likely = [t for t in types if t == known or "cdx" in t.lower() or "chemdraw" in t.lower()]
        for typ in likely + [t for t in types if t not in likely]:
            if typ in (PNG, TIFF) or typ.startswith("public.") and typ != "public.data":
                continue
            data = _data(pb, typ)
            if data and data.startswith(CDX_MAGIC):
                if typ != known:
                    cfg = config.load()
                    cfg["mac_cdx_pasteboard_type"] = typ
                    config.save(cfg)
                print(f"ChemDraw drawing found as {typ!r}", file=sys.stderr)
                return data
        return None


def read_clipboard_smiles() -> str | None:
    """SMILES, falls ChemDraw es mit ablegt (wie unter Windows), sonst None."""
    with objc.autorelease_pool():
        pb = _pasteboard()
        for typ in _types(pb):
            if typ in SMILES_TYPES or "smiles" in typ.lower():
                data = _data(pb, typ)
                if data:
                    return data.split(b"\x00", 1)[0].decode("ascii", "ignore").strip() or None
        return None


def write_chemdraw(cdx: bytes, image: bytes | None) -> None:
    """ChemDraw-Zeichnung in die Zwischenablage — ChemDraw fügt sie
    bearbeitbar ein, alle anderen Programme bekommen das Bild."""
    known = (config.load().get("mac_cdx_pasteboard_type") or "").strip()
    cdx_types = [known] if known else []
    cdx_types += [t for t in CDX_TYPES if t != known]
    with objc.autorelease_pool():
        pb = _pasteboard()
        pb.clearContents()
        types = cdx_types + ([PNG] if image else [])
        pb.declareTypes_owner_(types, None)
        cdx_data = NSData.dataWithBytes_length_(cdx, len(cdx))
        for typ in cdx_types:
            if not pb.setData_forType_(cdx_data, typ):
                raise OSError(f"clipboard refused type {typ}")
        if image:
            png = _as_png(image)
            pb.setData_forType_(NSData.dataWithBytes_length_(png, len(png)), PNG)


def _as_png(image: bytes) -> bytes:
    if image.startswith(b"\x89PNG"):
        return image
    from PIL import Image
    buf = io.BytesIO()
    with Image.open(io.BytesIO(image)) as im:
        im.convert("RGB").save(buf, "PNG")
    return buf.getvalue()
