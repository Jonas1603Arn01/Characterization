"""Gemeinsame Test-Absicherung: Tests dürfen nie die echte
Windows-Zwischenablage lesen oder beschreiben oder das echte ChemDraw fernsteuern —
Standard: leer bzw. Fehler. Einzelne Tests überschreiben das per
monkeypatch mit eigenen Daten."""
import pytest

from app import chemdraw_render, clipboard_win, main, svg_raster

# Der FastAPI-TestClient spricht die App als Host "testserver" an — der
# lokale Host-Schutz (main.local_only_guard) muss das für Tests zulassen.
main.ALLOWED_HOSTS.add("testserver")


@pytest.fixture(autouse=True)
def empty_clipboard(monkeypatch):
    monkeypatch.setattr(clipboard_win, "read_clipboard_image", lambda: None)
    monkeypatch.setattr(clipboard_win, "read_clipboard_cdx", lambda: None)
    monkeypatch.setattr(clipboard_win, "read_clipboard_smiles", lambda: None)
    monkeypatch.setattr(clipboard_win, "write_clipboard", lambda formats: None)


@pytest.fixture(autouse=True)
def no_chemdraw(monkeypatch):
    def fail(path):
        raise chemdraw_render.RenderError("ChemDraw ist in Tests deaktiviert")

    monkeypatch.setattr(chemdraw_render, "render_cdx", fail)
    monkeypatch.setattr(chemdraw_render, "export_emf", fail)


@pytest.fixture(autouse=True)
def no_inkscape(monkeypatch):
    """Tests rastern nie mit dem echten Inkscape — der Word-Export nimmt dann
    das weiße Rückfallbild und meldet das als Hinweis."""
    monkeypatch.setattr(svg_raster, "find_inkscape", lambda: None)
