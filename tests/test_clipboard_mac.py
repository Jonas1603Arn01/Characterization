"""macOS-Zwischenablage (app/clipboard_mac.py) mit der echten NSPasteboard.

ChemDraw selbst gibt es auf den Testrechnern nicht — nachgestellt wird, was
es beim Kopieren ablegt: die CDX-Zeichnung unter einem eigenen Typnamen
(hier bewusst ein erfundener, denn die App erkennt CDX am Dateikopf), die
Vektorgrafik als PDF und das SMILES. Überschreibt die Zwischenablage des
Rechners, auf dem die Tests laufen.
"""
import io
import sys
from pathlib import Path

import pytest

if sys.platform != "darwin":
    pytest.skip("nur unter macOS", allow_module_level=True)

from AppKit import NSPasteboard  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from Foundation import NSData  # noqa: E402
from PIL import Image  # noqa: E402

from app import clipboard_mac, config, db  # noqa: E402
from app.main import app  # noqa: E402

CDX = clipboard_mac.CDX_MAGIC + b"\x01\x02" * 20
CHEMDRAW_LIKE_TYPE = "com.example.chemdraw-like"


@pytest.fixture(autouse=True)
def own_config(tmp_path, monkeypatch):
    """Der gemerkte ChemDraw-Typ landet in config.json — nie in der echten."""
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "config.json")


@pytest.fixture()
def client(tmp_path):
    db.init_db(tmp_path / "test.db")
    with TestClient(app) as c:
        yield c


def put(items: dict[str, bytes]) -> None:
    pb = NSPasteboard.generalPasteboard()
    pb.clearContents()
    pb.declareTypes_owner_(list(items), None)
    for typ, data in items.items():
        assert pb.setData_forType_(NSData.dataWithBytes_length_(data, len(data)), typ)


def pdf_drawing() -> bytes:
    """Steht für ChemDraws Vektorbild: PDF-Seite 2 × 1 Zoll."""
    img = Image.new("RGB", (144, 72), "white")
    for x in range(20, 124):
        img.putpixel((x, 36), (0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, "PDF", resolution=72)
    return buf.getvalue()


def png(size=(10, 10)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, "red").save(buf, "PNG")
    return buf.getvalue()


def size_of(data: bytes) -> tuple[int, int]:
    with Image.open(io.BytesIO(data)) as im:
        return im.size


def test_reads_what_chemdraw_puts_on_the_clipboard():
    put({CHEMDRAW_LIKE_TYPE: CDX, "com.adobe.pdf": pdf_drawing(), "SMILES": b"CCO\x00"})
    assert clipboard_mac.read_clipboard_cdx() == CDX
    assert config.load()["mac_cdx_pasteboard_type"] == CHEMDRAW_LIKE_TYPE
    image = clipboard_mac.read_clipboard_image()
    assert image.startswith(b"\x89PNG")
    w, h = size_of(image)
    assert 550 <= w <= 650 and 275 <= h <= 325  # 2 × 1 Zoll mit 300 dpi
    assert clipboard_mac.read_clipboard_smiles() == "CCO"


def test_plain_text_is_neither_drawing_nor_image():
    put({"public.utf8-plain-text": b"hello"})
    assert clipboard_mac.read_clipboard_cdx() is None
    assert clipboard_mac.read_clipboard_image() is None
    assert clipboard_mac.read_clipboard_smiles() is None


def test_copy_then_paste_gives_back_drawing_and_picture():
    picture = png()
    clipboard_mac.write_chemdraw(CDX, picture)
    assert clipboard_mac.read_clipboard_cdx() == CDX
    assert clipboard_mac.read_clipboard_image() == picture


def test_copy_uses_the_type_chemdraw_was_seen_with():
    put({CHEMDRAW_LIKE_TYPE: CDX})
    clipboard_mac.read_clipboard_cdx()
    clipboard_mac.write_chemdraw(CDX, None)
    types = [str(t) for t in NSPasteboard.generalPasteboard().types()]
    assert CHEMDRAW_LIKE_TYPE in types


def test_paste_and_copy_through_the_app(client):
    project = client.post("/api/projects", json={"name": "P"}).json()
    mol = client.post("/api/molecules", json={"project_id": project["id"], "name": "M-1"}).json()
    assert client.get("/api/version").json()["platform"] == "darwin"

    put({CHEMDRAW_LIKE_TYPE: CDX, "com.adobe.pdf": pdf_drawing(), "SMILES": b"CCO\x00"})
    r = client.post(f"/api/molecules/{mol['id']}/image/clipboard")
    assert r.status_code == 200, r.text
    data = r.json()
    assert Path(data["image_cdx_path"]).read_bytes() == CDX
    assert data["smiles"] == "CCO" and data["formula"] == "C2H6O"

    put({"public.utf8-plain-text": b"something else"})
    r = client.post(f"/api/molecules/{mol['id']}/image/copy")
    assert r.status_code == 200, r.text
    assert clipboard_mac.read_clipboard_cdx() == CDX
