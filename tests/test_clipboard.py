"""Tests für das serverseitige Einfügen aus der Windows-Zwischenablage."""
import base64
import os
import struct
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import clipboard_win, db, main, olecf
from app.clipboard_win import dib_to_bmp
from app.main import app

PNG_1x1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)

# Minimale „CDX-Datei": nur der Magic-Header zählt für die App
CDX_BYTES = clipboard_win.CDX_MAGIC + b"\x00" * 16


@pytest.fixture()
def client(tmp_path):
    db.init_db(tmp_path / "test.db")
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def mol(client):
    project = client.post("/api/projects", json={"name": "P"}).json()
    return client.post(
        "/api/molecules", json={"project_id": project["id"], "name": "M-1"}
    ).json()


# ---------- DIB -> BMP ----------

def make_dib(bit_count=32, compression=0, clr_used=0, extra=b"\x00\x00\x00\x00"):
    """Minimaler BITMAPINFOHEADER (1×1 Pixel) + Pixel-/Palettendaten."""
    header = struct.pack(
        "<IiiHHIIiiII",
        40, 1, 1, 1, bit_count, compression, len(extra), 0, 0, clr_used, 0,
    )
    return header + extra


def test_dib_to_bmp_plain_32bit():
    dib = make_dib()
    bmp = dib_to_bmp(dib)
    assert bmp.startswith(b"BM")
    assert len(bmp) == 14 + len(dib)
    offset, = struct.unpack_from("<I", bmp, 10)
    assert offset == 14 + 40  # keine Palette, keine Masken


def test_dib_to_bmp_bitfields_offset():
    # BI_BITFIELDS: die drei Farbmasken liegen hinter dem Header
    dib = make_dib(compression=3, extra=b"\x00" * 16)
    offset, = struct.unpack_from("<I", dib_to_bmp(dib), 10)
    assert offset == 14 + 40 + 12


def test_dib_to_bmp_palette_offset():
    # 8 Bit ohne biClrUsed -> volle 256-Farben-Palette
    dib = make_dib(bit_count=8, extra=b"\x00" * (256 * 4 + 4))
    offset, = struct.unpack_from("<I", dib_to_bmp(dib), 10)
    assert offset == 14 + 40 + 256 * 4


def test_dib_to_bmp_rejects_garbage():
    assert dib_to_bmp(b"") is None
    assert dib_to_bmp(b"\x00" * 20) is None
    assert dib_to_bmp(b"\xff" * 60) is None  # absurde Headergröße


# ---------- Endpoint ----------

@pytest.mark.parametrize("kind,field", [("image", "image_path"), ("scheme", "scheme_path"),
                                        ("equation", "equation_path")])
def test_clipboard_paste_stores_image(client, mol, monkeypatch, kind, field):
    monkeypatch.setattr(clipboard_win, "read_clipboard_image", lambda: PNG_1x1)
    r = client.post(f"/api/molecules/{mol['id']}/{kind}/clipboard")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data[f"{kind}_exists"] is True
    assert data[field].endswith(".png")


def test_clipboard_paste_empty_clipboard(client, mol, monkeypatch):
    monkeypatch.setattr(clipboard_win, "read_clipboard_image", lambda: None)
    r = client.post(f"/api/molecules/{mol['id']}/scheme/clipboard")
    assert r.status_code == 422
    assert "no image" in r.json()["detail"]


def test_clipboard_paste_non_image_bytes(client, mol, monkeypatch):
    monkeypatch.setattr(clipboard_win, "read_clipboard_image", lambda: b"kein bild")
    r = client.post(f"/api/molecules/{mol['id']}/scheme/clipboard")
    assert r.status_code == 422


# ---------- EMF -> BMP (ChemDraw-Strg+C legt nur Vektorgrafik + CDX ab) ----------

def make_test_emf():
    """Kleines EMF per GDI: schwarzer Rechteckrand auf weißer Fläche."""
    import ctypes

    gdi = ctypes.windll.gdi32
    gdi.CreateEnhMetaFileW.restype = ctypes.c_void_p
    gdi.CreateEnhMetaFileW.argtypes = [ctypes.c_void_p] * 4
    gdi.CloseEnhMetaFile.restype = ctypes.c_void_p
    gdi.CloseEnhMetaFile.argtypes = [ctypes.c_void_p]
    gdi.Rectangle.argtypes = [ctypes.c_void_p] + [ctypes.c_int] * 4
    dc = gdi.CreateEnhMetaFileW(None, None, None, None)
    gdi.Rectangle(dc, 10, 10, 90, 40)
    return gdi.CloseEnhMetaFile(dc)


def test_emf_to_bmp_renders_vector_graphic():
    import ctypes

    hemf = make_test_emf()
    try:
        bmp = clipboard_win.emf_to_bmp(hemf)
    finally:
        ctypes.windll.gdi32.DeleteEnhMetaFile(ctypes.c_void_p(hemf))
    assert bmp and bmp.startswith(b"BM")
    offset, = struct.unpack_from("<I", bmp, 10)
    width, height = struct.unpack_from("<ii", bmp, 18)
    assert width > 10 and abs(height) > 10
    # Pixel prüfen: weißer Hintergrund UND schwarzer Rand vorhanden
    rgb = {struct.unpack_from("<I", bmp, offset + i * 4)[0] & 0xFFFFFF
           for i in range(width * abs(height))}
    assert 0xFFFFFF in rgb
    assert 0x000000 in rgb


def test_emf_to_bmp_rejects_bad_handle():
    assert clipboard_win.emf_to_bmp(0xDEAD) is None


# ---------- ChemDraw-Datei (.cdx) neben dem Bild mitspeichern ----------

def paste(client, mol, kind, monkeypatch, cdx):
    monkeypatch.setattr(clipboard_win, "read_clipboard_image", lambda: PNG_1x1)
    monkeypatch.setattr(clipboard_win, "read_clipboard_cdx", lambda: cdx)
    r = client.post(f"/api/molecules/{mol['id']}/{kind}/clipboard")
    assert r.status_code == 200, r.text
    return r.json()


@pytest.mark.parametrize("kind", ["image", "scheme", "equation"])
def test_clipboard_paste_stores_cdx_alongside(client, mol, monkeypatch, kind):
    data = paste(client, mol, kind, monkeypatch, CDX_BYTES)
    assert data[f"{kind}_cdx_exists"] is True
    cdx_path = Path(data[f"{kind}_cdx_path"])
    assert cdx_path.suffix == ".cdx"
    assert cdx_path.read_bytes() == CDX_BYTES
    # Bild und CDX liegen im selben verwalteten Ordner
    assert cdx_path.parent == Path(data[f"{kind}_path"]).parent


def test_paste_without_cdx_clears_stale_cdx(client, mol, monkeypatch):
    old = Path(paste(client, mol, "image", monkeypatch, CDX_BYTES)["image_cdx_path"])
    data = paste(client, mol, "image", monkeypatch, None)  # z. B. Screenshot
    assert data["image_cdx_path"] is None
    assert not old.exists()  # gehörte zum alten Bild -> aufgeräumt


def test_patch_image_path_clears_cdx(client, mol, monkeypatch, tmp_path):
    old = Path(paste(client, mol, "image", monkeypatch, CDX_BYTES)["image_cdx_path"])
    extern = tmp_path / "extern.png"
    extern.write_bytes(PNG_1x1)
    r = client.patch(f"/api/molecules/{mol['id']}", json={"image_path": str(extern)})
    assert r.status_code == 200
    assert r.json()["image_cdx_path"] is None
    assert not old.exists()


# ---------- Bildauslieferung: nur echte Bilder ----------

def test_serve_pasted_image(client, mol, monkeypatch):
    paste(client, mol, "image", monkeypatch, None)
    r = client.get(f"/api/molecules/{mol['id']}/image")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
    assert r.content == PNG_1x1


def test_serve_picked_external_image(client, mol, tmp_path):
    # „Bild auswählen" hinterlegt einen externen Pfad — muss weiter ausgeliefert werden
    extern = tmp_path / "struktur.png"
    extern.write_bytes(PNG_1x1)
    client.patch(f"/api/molecules/{mol['id']}", json={"image_path": str(extern)})
    r = client.get(f"/api/molecules/{mol['id']}/image")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"


def test_serve_refuses_non_image_file(client, mol, tmp_path):
    """Ein auf eine Fremddatei gesetzter Bildpfad darf nicht als Bild
    ausgeliefert werden (kein Auslesen beliebiger Dateien über /image)."""
    secret = tmp_path / "geheim.docx"
    secret.write_text("vertrauliche Forschungsdaten")
    client.patch(f"/api/molecules/{mol['id']}", json={"image_path": str(secret)})
    r = client.get(f"/api/molecules/{mol['id']}/image")
    assert r.status_code == 404
    assert "vertrauliche" not in r.text


# ---------- SMILES-Vorbefüllung beim Einfügen ----------

def paste_with_smiles(client, mol, kind, monkeypatch, smiles):
    monkeypatch.setattr(clipboard_win, "read_clipboard_image", lambda: PNG_1x1)
    monkeypatch.setattr(clipboard_win, "read_clipboard_smiles", lambda: smiles)
    r = client.post(f"/api/molecules/{mol['id']}/{kind}/clipboard")
    assert r.status_code == 200, r.text
    return r.json()


def test_paste_prefills_empty_smiles(client, mol, monkeypatch):
    data = paste_with_smiles(client, mol, "image", monkeypatch, "CCO")
    assert data["smiles"] == "CCO"
    assert data["formula"] == "C2H6O"
    assert data["exact_mass"] == pytest.approx(46.0419, abs=0.001)


def test_paste_keeps_existing_smiles(client, mol, monkeypatch):
    client.patch(f"/api/molecules/{mol['id']}", json={"smiles": "c1ccccc1"})
    data = paste_with_smiles(client, mol, "image", monkeypatch, "CCO")
    assert data["smiles"] == "c1ccccc1"


def test_scheme_paste_does_not_touch_smiles(client, mol, monkeypatch):
    # Ein Reaktionsschema enthält mehrere Moleküle — kein Vorbefüllen
    data = paste_with_smiles(client, mol, "scheme", monkeypatch, "CCO")
    assert data["smiles"] is None


def test_paste_ignores_invalid_smiles(client, mol, monkeypatch):
    data = paste_with_smiles(client, mol, "image", monkeypatch, "kein(((smiles")
    assert data["smiles"] is None
    assert data["image_exists"] is True  # Einfügen klappt trotzdem


def test_export_includes_cdx(client, mol, monkeypatch, tmp_path):
    paste(client, mol, "image", monkeypatch, CDX_BYTES)
    target = tmp_path / "export"
    target.mkdir()
    r = client.post(f"/api/molecules/{mol['id']}/export",
                    json={"target_dir": str(target)})
    assert r.status_code == 200, r.text
    base = target / "P" / "M-1"
    assert (base / "Structure.png").is_file()
    assert (base / "Structure.cdx").read_bytes() == CDX_BYTES


# ---------- ChemDraw-Zeichnung in die Zwischenablage kopieren ----------

@pytest.fixture()
def written(monkeypatch):
    """Fängt ab, was in die Zwischenablage käme (Format -> Bytes)."""
    got = {}
    monkeypatch.setattr(clipboard_win, "write_clipboard", lambda formats: got.update(formats))
    return got


@pytest.mark.parametrize("kind", ["image", "scheme", "equation"])
def test_copy_puts_chemdraw_formats_on_clipboard(client, mol, monkeypatch, written, kind):
    paste(client, mol, kind, monkeypatch, CDX_BYTES)
    r = client.post(f"/api/molecules/{mol['id']}/{kind}/copy")
    assert r.status_code == 200, r.text
    assert written[clipboard_win.CDX_FORMAT] == CDX_BYTES
    ole = written[clipboard_win.EMBED_SOURCE]
    assert ole.startswith(bytes.fromhex("d0cf11e0a1b11ae1")) and CDX_BYTES in ole
    desc = written[clipboard_win.OBJECT_DESCRIPTOR]
    size, clsid = struct.unpack_from("<I16s", desc)
    assert size == len(desc) and clsid == olecf.CHEMDRAW_CLSID
    assert struct.unpack_from("<I", written[clipboard_win.CF_DIB])[0] == 40
    # kein „PNG": damit fügte Word bei Strg+V das Bild statt des Objekts ein
    assert "PNG" not in written


def test_copy_picture_keeps_300_dpi_size():
    """Word bemisst das eingefügte Objekt nach der Bildauflösung — ein aus
    ChemDraw eingefügtes Bild (300 dpi, ohne Angabe) käme sonst zu groß an."""
    w, h = 600, 300
    header = struct.pack("<IiiHHIIiiII", 40, w, -h, 1, 32, 0, w * h * 4, 0, 0, 0, 0)
    bmp = dib_to_bmp(header + b"\xff" * (w * h * 4))
    formats = dict(clipboard_win.chemdraw_formats(CDX_BYTES, bmp))
    size = struct.unpack_from("<ii", formats[clipboard_win.OBJECT_DESCRIPTOR], 24)
    assert size == (5080, 2540)  # 2 × 1 Zoll in 0,01 mm
    ppm, = struct.unpack_from("<i", formats[clipboard_win.CF_DIB], 24)
    assert ppm == round(300 / 0.0254)


def test_copy_without_readable_picture_still_copies_drawing():
    formats = dict(clipboard_win.chemdraw_formats(CDX_BYTES, b"kein bild"))
    assert formats[clipboard_win.CDX_FORMAT] == CDX_BYTES
    assert clipboard_win.EMBED_SOURCE in formats
    assert clipboard_win.CF_DIB not in formats


def test_copy_without_cdx_is_refused(client, mol, monkeypatch, written):
    paste(client, mol, "image", monkeypatch, None)
    r = client.post(f"/api/molecules/{mol['id']}/image/copy")
    assert r.status_code == 409
    assert written == {}


def test_copy_unknown_slot(client, mol, written):
    assert client.post(f"/api/molecules/{mol['id']}/spectrum/copy").status_code == 404


def test_copy_leaves_out_outdated_picture(client, mol, monkeypatch, written):
    """Wurde die .cdx nachträglich in ChemDraw geändert, zeigt das Bild einen
    alten Stand — dann nur die Zeichnung selbst kopieren."""
    data = paste(client, mol, "image", monkeypatch, CDX_BYTES)
    later = Path(data["image_path"]).stat().st_mtime + 60
    os.utime(data["image_cdx_path"], (later, later))
    assert client.post(f"/api/molecules/{mol['id']}/image/copy").status_code == 200
    assert written[clipboard_win.CDX_FORMAT] == CDX_BYTES
    assert clipboard_win.CF_DIB not in written


def test_copy_reports_busy_clipboard(client, mol, monkeypatch):
    paste(client, mol, "image", monkeypatch, CDX_BYTES)

    def busy(formats):
        raise OSError("clipboard is in use by another program")

    monkeypatch.setattr(clipboard_win, "write_clipboard", busy)
    r = client.post(f"/api/molecules/{mol['id']}/image/copy")
    assert r.status_code == 503
    assert "in use" in r.json()["detail"]


def test_copy_is_no_undo_step_and_allowed_read_only(monkeypatch):
    path = "/api/molecules/1/equation/copy"
    assert not main.is_undoable("POST", path)
    monkeypatch.setattr(main.db, "refresh_lock_state", lambda: False)  # Lesemodus
    assert not main.is_blocked_read_only("POST", path)
