"""Tests für das Word-Dokument der Versuchsvorschrift.

Der Maßstab ist die Vorlage procedure_FluIBioxHOTf.docx: derselbe Aufbau,
dieselbe Auszeichnung. Die beiden NMR-Tests vergleichen deshalb Zeichen für
Zeichen mit dem, was in der Vorlage steht.
"""
import re
import sqlite3
import struct
import zipfile

import pytest
from fastapi.testclient import TestClient

from app import chem_text, db, olecf
from app.main import app

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


@pytest.fixture()
def client(tmp_path):
    db.init_db(tmp_path / "test.db")
    with TestClient(app) as c:
        yield c


# ---------- Auszeichnung der Analytiktexte ----------

def marked(runs) -> str:
    """Textstücke als lesbare Zeichenkette: ⟨Auszeichnung:Text⟩."""
    out = []
    for r in runs:
        flags = ("B" if r.bold else "") + ("I" if r.italic else "") + (r.vert or "")
        out.append(f"⟨{flags}:{r.text}⟩" if flags else r.text)
    return "".join(out).replace(" ", " ")


def test_1h_nmr_wird_wie_in_der_vorlage_gesetzt():
    text = ("1H NMR (501 MHz, CDCl3, 298 K) δ [ppm] = 8.41 (s, 1H, triazole-CH), "
            "7.85 (d, J = 8.1 Hz, 4H, Ar-CH), 5.12 (s, 4H, CH2).")
    assert marked(chem_text.nmr(text)) == (
        "⟨Bsup:1⟩⟨B:H NMR⟩ (501 MHz, CDCl⟨sub:3⟩, 298 K) δ [ppm] = "
        "8.41 (s, 1H, triazole-C⟨I:H⟩), 7.85 (d, ⟨I:J⟩ = 8.1 Hz, 4H, Ar-C⟨I:H⟩), "
        "5.12 (s, 4H, C⟨I:H⟩⟨sub:2⟩)."
    )


def test_13c_nmr_kursiviert_den_kohlenstoff_statt_des_wasserstoffs():
    text = ("13C NMR (126 MHz, CDCl3 298 K) = 138.9 (Ar-Cq), 129.7 (Ar-CH), "
            "84.2 (CH2), 70.5 (Cq(sp3)).")
    assert marked(chem_text.nmr(text)) == (
        "⟨Bsup:13⟩⟨B:C NMR⟩ (126 MHz, CDCl⟨sub:3⟩ 298 K) = 138.9 (Ar-⟨I:C⟩⟨sub:q⟩), "
        "129.7 (Ar-⟨I:C⟩H), 84.2 (⟨I:C⟩H⟨sub:2⟩), 70.5 (⟨I:C⟩⟨sub:q⟩(sp⟨sup:3⟩))."
    )


def test_integral_und_multiplizitaet_bleiben_unausgezeichnet():
    """Nur das letzte Feld einer Klammer ist die Zuordnung — „1H" ist ein
    Integral und darf nicht kursiv werden."""
    assert marked(chem_text.nmr("1H NMR (400 MHz) δ = 7.26 (s, 3H).")) == (
        "⟨Bsup:1⟩⟨B:H NMR⟩ (400 MHz) δ = 7.26 (s, 3H)."
    )


def test_doppelpunkt_wird_nicht_hochgestellt():
    """Regression: „[+-−]" ist ein Zeichenbereich von „+" bis „−" und traf
    unter anderem den Doppelpunkt — „[cm-1]:" wurde dadurch verstümmelt."""
    assert marked(chem_text.bold("IR (solid) [cm-1]:")) == (
        "⟨B:IR (solid) [cm⟩⟨Bsup:-1⟩⟨B:]:⟩"
    )


def test_ladung_und_deuteriertes_loesungsmittel():
    assert marked(chem_text.plain("calc. [M+H]+.")) == "calc. [M+H]⟨sup:+⟩."
    assert marked(chem_text.nmr("13C{1H} NMR (126 MHz, DMSO-d6) δ = 1.0 (Cq).")) == (
        "⟨Bsup:13⟩⟨B:C{⟩⟨Bsup:1⟩⟨B:H} NMR⟩ (126 MHz, DMSO-⟨I:d⟩⟨sub:6⟩) δ = 1.0 (⟨I:C⟩⟨sub:q⟩)."
    )


def test_probennummer_wird_nicht_als_formel_gelesen():
    """Nur echte Elementsymbole bekommen Indexziffern — „JA294" bliebe sonst
    als „A₂₉₄" stehen."""
    assert marked(chem_text.plain("Probe JA294 gemessen")) == "Probe JA294 gemessen"


def test_eigene_formatierung_der_notiz_gewinnt():
    runs = chem_text.note("1H NMR frei", "<b>1</b>H <i>frei</i>", "nmr_1h")
    assert marked(runs) == "⟨B:1⟩H ⟨I:frei⟩"


def test_messbedingungen_auch_ohne_komma_vor_der_temperatur():
    assert chem_text.conditions("13C NMR (126 MHz, CDCl3 298 K) = 1.0") == {
        "frequency": "126", "solvent": "CDCl3", "temperature": "298",
    }


def test_geschuetztes_leerzeichen_zwischen_zahl_und_einheit():
    runs = chem_text.nmr("1H NMR (400 MHz) δ = 7.26 (d, J = 7.5 Hz, 1H, ArH).")
    assert " Hz" in "".join(r.text for r in runs)
    assert " MHz" in "".join(r.text for r in runs)


# ---------- OLE-Container ----------

def _read_cfb(data: bytes) -> dict[str, bytes]:
    """Kleiner unabhängiger Leser, um den Schreiber gegenzuprüfen."""
    sector = 1 << struct.unpack_from("<H", data, 30)[0]
    mini = 1 << struct.unpack_from("<H", data, 32)[0]
    cutoff = struct.unpack_from("<I", data, 56)[0]
    n_fat = struct.unpack_from("<I", data, 44)[0]

    def sect(n: int) -> bytes:
        return data[512 + n * sector:512 + (n + 1) * sector]

    fat = b"".join(sect(struct.unpack_from("<I", data, 76 + 4 * i)[0])
                   for i in range(n_fat))

    def chain(table: bytes, start: int) -> list[int]:
        out = []
        while start < 0xFFFFFFFA:
            assert start not in out, "Schleife in der Sektorkette"
            out.append(start)
            start = struct.unpack_from("<I", table, 4 * start)[0]
        return out

    directory = b"".join(sect(s) for s in
                         chain(fat, struct.unpack_from("<I", data, 48)[0]))
    entries = []
    for i in range(0, len(directory), 128):
        e = directory[i:i + 128]
        length = struct.unpack_from("<H", e, 64)[0]
        if length:
            entries.append((e[:length - 2].decode("utf-16-le"),
                            struct.unpack_from("<I", e, 116)[0],
                            struct.unpack_from("<Q", e, 120)[0]))
    ministream = b"".join(sect(s) for s in chain(fat, entries[0][1]))
    minifat = b"".join(sect(s) for s in
                       chain(fat, struct.unpack_from("<I", data, 60)[0]))
    out = {}
    for name, start, size in entries[1:]:
        if size < cutoff:
            raw = b"".join(ministream[s * mini:(s + 1) * mini]
                           for s in chain(minifat, start))
        else:
            raw = b"".join(sect(s) for s in chain(fat, start))
        out[name] = raw[:size]
    return out


def test_chemdraw_objekt_enthaelt_die_zeichnung_unveraendert():
    cdx = b"VjCD0100" + bytes(range(256)) * 60  # größer als der Mini-Grenzwert
    emf = b"\x01\x00\x00\x00" + bytes(9000)
    streams = _read_cfb(olecf.chemdraw_object(cdx, emf))
    assert streams["CONTENTS"] == cdx
    assert streams["\x03EPRINT"] == emf
    assert b"ChemDraw_x64.Document.6.0" in streams["\x01CompObj"].replace(b"\x00", b"")


@pytest.mark.parametrize("size", [1, 63, 64, 65, 4095, 4096, 4097, 20000])
def test_container_haelt_stroeme_jeder_groesse(size):
    """Der Grenzwert zwischen Mini- und Normalsektoren liegt bei 4096 Bytes —
    beide Wege müssen dasselbe zurückgeben."""
    payload = bytes((i * 7) % 251 for i in range(size))
    streams = _read_cfb(olecf.build([("A", payload), ("BB", b"x" * 5000)]))
    assert streams["A"] == payload
    assert streams["BB"] == b"x" * 5000


# ---------- Das erzeugte Dokument ----------

def _molecule(client, **fields):
    project = client.post("/api/projects", json={"name": "P"}).json()
    mol = client.post("/api/molecules",
                      json={"project_id": project["id"], "name": "M-1"}).json()
    if fields:
        client.patch(f"/api/molecules/{mol['id']}", json=fields)
    return mol


def _build(client, mol, tmp_path):
    target = tmp_path / "word"
    target.mkdir(exist_ok=True)
    r = client.post(f"/api/molecules/{mol['id']}/word",
                    json={"target_dir": str(target)})
    assert r.status_code == 200, r.text
    result = r.json()
    with zipfile.ZipFile(result["file"]) as z:
        document = z.read("word/document.xml").decode("utf-8")
        names = z.namelist()
    return result, document, names


def _paragraphs(document: str) -> list[str]:
    body = document[document.index("<w:body>"):]
    return [re.sub(r"<[^>]+>", "", p) for p in
            re.findall(r"<w:p(?: [^>]*)?>.*?</w:p>", body, re.S)]


def test_dokument_hat_den_aufbau_der_vorlage(client, tmp_path):
    mol = _molecule(client, physical_state="solid")
    entries = {e["type_code"]: e for e in
               client.get(f"/api/molecules/{mol['id']}").json()["entries"]}
    client.post(f"/api/entries/{entries['nmr_1h']['id']}/notes",
                json={"text": "1H NMR (400 MHz, CDCl3, 298 K) δ [ppm] = 7.26 (s, 1H, ArH)."})
    result, document, names = _build(client, mol, tmp_path)

    assert result["warnings"] == []
    texts = _paragraphs(document)
    # Überschrift, Durchführung, ¹H, IR, HR-MS, m. p. — in dieser Reihenfolge
    assert texts[0] == "M-1 XX:"
    assert texts[1] == "[insert procedure]"
    assert texts[2].startswith("1H NMR (400 MHz")
    assert "IR (solid) [cm-1]: ṽ = [insert]" in texts
    assert "HR-MS-ESI(+) calc. [M+H]+, found [insert]." in texts
    assert "m. p. [insert]" in texts
    # Die unveränderlichen Teile stammen aus der Vorlage
    assert {"word/styles.xml", "word/theme/theme1.xml"} <= set(names)


def test_hochstellung_heisst_im_dokument_superscript(client, tmp_path):
    """Regression: OOXML kennt nur „superscript"/„subscript" — mit „sup"
    verwirft Word die Auszeichnung stillschweigend."""
    mol = _molecule(client)
    _, document, _ = _build(client, mol, tmp_path)
    assert 'w:vertAlign w:val="superscript"' in document
    assert 'w:val="sup"' not in document


def test_fehlende_angaben_werden_rot_markiert(client, tmp_path):
    mol = _molecule(client)
    _, document, _ = _build(client, mol, tmp_path)
    # Jeder Platzhalter trägt die Warnfarbe der Vorlage
    for marker in ("[insert]", "[insert procedure]", "XX"):
        assert marker in document
    assert document.count('w:color w:val="FF0000"') >= 4


def test_nicht_benoetigte_datentypen_kommen_nicht_ins_dokument(client, tmp_path):
    mol = _molecule(client)
    entries = {e["type_code"]: e for e in
               client.get(f"/api/molecules/{mol['id']}").json()["entries"]}
    client.patch(f"/api/entries/{entries['ir']['id']}", json={"required": False})
    _, document, _ = _build(client, mol, tmp_path)
    assert "IR (" not in document
    assert "m. p." in document  # die übrigen bleiben


def test_durchfuehrung_wird_formal_gesetzt(client, tmp_path):
    """Das Durchführungsfeld ist Fließtext: Formeln bekommen Indizes und
    zwischen Zahl und Einheit steht ein geschütztes Leerzeichen, damit im
    Blocksatz nichts auseinandergerissen wird."""
    mol = _molecule(client)
    entries = {e["type_code"]: e for e in
               client.get(f"/api/molecules/{mol['id']}").json()["entries"]}
    client.post(f"/api/entries/{entries['procedure']['id']}/notes", json={
        "text": "Charged with XX (2.00 g, 5.00 mmol, 1.0 equiv) and CH2Cl2 (50 mL), "
                "stirred for 12 h at 80 °C.",
    })
    _, document, _ = _build(client, mol, tmp_path)

    text = _paragraphs(document)[1]
    assert "2.00 g" in text and "5.00 mmol" in text
    assert "1.0 equiv" in text and "50 mL" in text
    assert "12 h" in text and "80 °C" in text
    # CH2Cl2: die beiden Ziffern stehen als eigene, tiefgestellte Textstücke
    assert '<w:vertAlign w:val="subscript"/></w:rPr><w:t xml:space="preserve">2</w:t>' in document


def test_xx_in_der_durchfuehrung_wird_zur_verbindungsnummer(client, tmp_path):
    mol = _molecule(client)
    entries = {e["type_code"]: e for e in
               client.get(f"/api/molecules/{mol['id']}").json()["entries"]}
    client.post(f"/api/entries/{entries['procedure']['id']}/notes",
                json={"text": "yielded XX as a solid."})
    _, document, _ = _build(client, mol, tmp_path)

    body = document[document.index("<w:body>"):]
    paragraph = re.findall(r"<w:p(?: [^>]*)?>.*?</w:p>", body, re.S)[1]
    # fett und rot wie im Titel — nicht als gewöhnlicher Text
    assert '<w:b/><w:color w:val="FF0000"/></w:rPr><w:t xml:space="preserve">XX</w:t>' in paragraph


def test_eigene_formatierung_der_durchfuehrung_bleibt_und_wird_ergaenzt(client, tmp_path):
    """Anders als bei den Analytiknotizen wird die Durchführung auch dann
    gesetzt, wenn im Feld schon von Hand formatiert wurde — niemand stellt
    die Indizes von CH₂Cl₂ per Hand."""
    mol = _molecule(client)
    entries = {e["type_code"]: e for e in
               client.get(f"/api/molecules/{mol['id']}").json()["entries"]}
    client.post(f"/api/entries/{entries['procedure']['id']}/notes",
                json={"html": "in <b>CH2Cl2</b> for 12 h"})
    _, document, _ = _build(client, mol, tmp_path)

    body = document[document.index("<w:body>"):]
    paragraph = re.findall(r"<w:p(?: [^>]*)?>.*?</w:p>", body, re.S)[1]
    assert "12 h" in paragraph                       # ergänzt
    assert '<w:b/><w:vertAlign w:val="subscript"/>' in paragraph  # fett UND tiefgestellt


def test_weiterer_nmr_kern_wird_wie_1h_und_13c_gesetzt(client, tmp_path):
    """Ein eigener Eintrag, dessen Bezeichnung eine NMR-Messung meint, läuft
    durch dasselbe Schema: Zeile hinter dem ¹³C, Spektrum mit Bildunterschrift
    und Bedingungen aus seiner eigenen Notiz."""
    mol = _molecule(client)
    entries = {e["type_code"]: e for e in
               client.get(f"/api/molecules/{mol['id']}").json()["entries"]}
    client.post(f"/api/entries/{entries['nmr_13c']['id']}/notes",
                json={"text": "13C NMR (126 MHz, CDCl3, 298 K) = 138.9 (Ar-Cq)."})
    fluor = client.post(f"/api/molecules/{mol['id']}/entries",
                        json={"custom_label": "19F NMR"}).json()
    client.post(f"/api/entries/{fluor['id']}/notes",
                json={"text": "19F NMR (471 MHz, CDCl3, 298 K) δ [ppm] = -63.2 (s, 3F, CF3)."})
    svg = tmp_path / "19F.svg"
    svg.write_bytes(b'<svg xmlns="http://www.w3.org/2000/svg" width="200mm" height="100mm"/>')
    client.post(f"/api/entries/{fluor['id']}/files", json={"path": str(svg)})

    result, document, _ = _build(client, mol, tmp_path)
    texts = _paragraphs(document)

    # Reihenfolge: Titel, Durchführung, ¹H, ¹³C, ¹⁹F, IR, …
    assert texts[3].startswith("13C NMR")
    assert texts[4].startswith("19F NMR")
    assert texts[5].startswith("IR")
    # Kopf fett mit hochgestellter Massenzahl, CF₃ tiefgestellt
    assert '<w:b/><w:vertAlign w:val="superscript"/></w:rPr><w:t xml:space="preserve">19</w:t>' in document
    # Bildunterschrift mit den Bedingungen aus der eigenen Notiz
    assert result["spectra"] == 1
    assert "471 MHz" in document
    assert any("19F NMR" in p and "of" in p for p in texts if p.startswith("Figure"))


def test_nur_nmr_bezeichnungen_zaehlen_als_weiterer_kern():
    assert chem_text.is_nmr_label("19F NMR")
    assert chem_text.is_nmr_label("31P{1H} NMR")
    assert chem_text.is_nmr_label("1H,15N HMBC")
    assert not chem_text.is_nmr_label("XRay")
    assert not chem_text.is_nmr_label("Elementaranalyse")
    assert not chem_text.is_nmr_label("HPLC")
    assert not chem_text.is_nmr_label(None)


def test_eigene_eintraege_bleiben_ohne_haekchen_draussen(client, tmp_path):
    """Ein eigener Eintrag, dessen Bezeichnung keine Messung meint, ist beim
    Anlegen nicht angehakt und bleibt komplett draußen."""
    mol = _molecule(client)
    entry = client.post(f"/api/molecules/{mol['id']}/entries",
                        json={"custom_label": "XRay"}).json()
    assert entry["in_document"] is False
    client.post(f"/api/entries/{entry['id']}/notes", json={"text": "nur Konnektivität"})
    svg = tmp_path / "xray.svg"
    svg.write_bytes(b'<svg xmlns="http://www.w3.org/2000/svg" width="10mm" height="10mm"/>')
    client.post(f"/api/entries/{entry['id']}/files", json={"path": str(svg)})

    result, document, names = _build(client, mol, tmp_path)
    assert "XRay" not in document
    assert "Konnektivität" not in document
    assert result["spectra"] == 0
    assert not any(n.endswith(".svg") for n in names)


def test_haekchen_holt_einen_eigenen_eintrag_ins_dokument(client, tmp_path):
    """Mit gesetztem Häkchen bekommt auch eine Nicht-NMR-Messung ihre Zeile —
    Bezeichnung fett, dann die Notiz — und ihre Bilder als Abbildung."""
    mol = _molecule(client)
    entry = client.post(f"/api/molecules/{mol['id']}/entries",
                        json={"custom_label": "Elemental analysis"}).json()
    client.post(f"/api/entries/{entry['id']}/notes",
                json={"text": "calc. C 52.4, H 4.1; found C 52.2, H 4.3."})
    svg = tmp_path / "ea.svg"
    svg.write_bytes(b'<svg xmlns="http://www.w3.org/2000/svg" width="200mm" height="100mm"/>')
    client.post(f"/api/entries/{entry['id']}/files", json={"path": str(svg)})

    patched = client.patch(f"/api/entries/{entry['id']}", json={"in_document": True})
    assert patched.status_code == 200 and patched.json()["in_document"] is True

    result, document, _ = _build(client, mol, tmp_path)
    texts = _paragraphs(document)
    # Zeile steht am Ende des Analytikblocks, hinter dem Schmelzpunkt
    assert texts.index("Elemental analysis calc. C 52.4, H 4.1; found C 52.2, H 4.3.") > \
        texts.index("m. p. [insert]")
    assert result["spectra"] == 1
    assert any(p.startswith("Figure ") and "Elemental analysis" in p for p in texts)


def test_haekchen_nur_bei_eigenen_eintraegen(client, tmp_path):
    """Feste Datentypen sind immer im Dokument — das Häkchen dort abzulehnen
    ist ehrlicher, als es stillschweigend zu ignorieren."""
    mol = _molecule(client)
    entries = {e["type_code"]: e for e in
               client.get(f"/api/molecules/{mol['id']}").json()["entries"]}
    r = client.patch(f"/api/entries/{entries['ir']['id']}", json={"in_document": False})
    assert r.status_code == 422


def test_haekchen_ist_bei_nmr_bezeichnungen_vorbelegt(client):
    mol = _molecule(client)
    for label, expected in [("19F NMR", True), ("31P{1H} NMR", True),
                            ("XRay", False), ("Elementaranalyse", False)]:
        entry = client.post(f"/api/molecules/{mol['id']}/entries",
                            json={"custom_label": label}).json()
        assert entry["in_document"] is expected, label


def test_svg_feld_des_nmr_eintrags_wird_eingebettet(client, tmp_path):
    """Das im festen SVG-Feld verlinkte Spektrum wandert wie eine
    zusätzliche Bilddatei ins Dokument."""
    mol = _molecule(client)
    entries = {e["type_code"]: e for e in
               client.get(f"/api/molecules/{mol['id']}").json()["entries"]}
    for name in ("1H.svg", "nachtrag.svg"):
        (tmp_path / name).write_bytes(
            b'<svg xmlns="http://www.w3.org/2000/svg" width="200mm" '
            b'height="100mm" viewBox="0 0 200 100"></svg>')
    client.patch(f"/api/entries/{entries['nmr_1h']['id']}",
                 json={"svg_path": str(tmp_path / "1H.svg")})
    client.post(f"/api/entries/{entries['nmr_1h']['id']}/files",
                json={"path": str(tmp_path / "nachtrag.svg")})
    result, document, names = _build(client, mol, tmp_path)

    assert result["spectra"] == 2
    assert "asvg:svgBlip" in document


def test_oel_bekommt_keinen_schmelzpunkt(client, tmp_path):
    mol = _molecule(client, physical_state="oil")
    _, document, _ = _build(client, mol, tmp_path)
    assert "m. p." not in document
    assert "IR (oil)" in document


def test_malpunkt_im_namen_wird_zum_aufzaehlungspunkt(client, tmp_path):
    project = client.post("/api/projects", json={"name": "P2"}).json()
    mol = client.post("/api/molecules",
                      json={"project_id": project["id"], "name": "FluIBiox * HOTf"}).json()
    _, document, _ = _build(client, mol, tmp_path)
    assert "FluIBiox • HOTf" in document


def test_formatierter_name_behaelt_kursiv_und_tiefstellung(client, tmp_path):
    project = client.post("/api/projects", json={"name": "P3"}).json()
    mol = client.post("/api/molecules", json={
        "project_id": project["id"], "name_html": "<i>N</i>-Ph<sub>3</sub>P * HOTf"}).json()
    _, document, _ = _build(client, mol, tmp_path)
    assert _paragraphs(document)[0] == "N-Ph3P • HOTf XX:"
    title = re.search(r"<w:p(?: [^>]*)?>.*?</w:p>", document[document.index("<w:body>"):], re.S)[0]
    runs = re.findall(r"<w:r>(.*?)</w:r>", title, re.S)
    def props(text):
        return next(r for r in runs if f">{text}</w:t>" in r)
    assert "<w:i/>" in props("N")
    assert '<w:vertAlign w:val="subscript"/>' in props("3")
    assert "<w:i/>" not in props("-Ph") and "vertAlign" not in props("P • HOTf ")


def test_spektren_werden_als_svg_mit_rasterrueckfall_eingebettet(client, tmp_path):
    mol = _molecule(client)
    entries = {e["type_code"]: e for e in
               client.get(f"/api/molecules/{mol['id']}").json()["entries"]}
    svg = tmp_path / "1H.svg"
    svg.write_bytes(b'<svg xmlns="http://www.w3.org/2000/svg" width="200mm" '
                    b'height="100mm" viewBox="0 0 200 100"></svg>')
    client.post(f"/api/entries/{entries['nmr_1h']['id']}/files",
                json={"path": str(svg)})
    result, document, names = _build(client, mol, tmp_path)

    assert result["spectra"] == 1
    assert any(n.endswith(".svg") for n in names)
    assert any(n.endswith(".png") for n in names)  # Rückfallbild
    assert "asvg:svgBlip" in document
    assert "Figure " in document
    # Ohne Inkscape (siehe conftest) ist das Rückfallbild weiß — das wird gemeldet
    assert any("fallback" in w for w in result["warnings"])
    # Breite = Satzbreite, Höhe im Seitenverhältnis des SVG (200 × 100 mm)
    assert 'cx="5760720" cy="2880360"' in document


def test_nachgeruestetes_haekchen_erhaelt_das_bisherige_verhalten(tmp_path):
    """Beim Nachrüsten der Spalte muss die bisherige Regel festgeschrieben
    werden: eigene Einträge mit NMR-Bezeichnung waren schon im Dokument und
    bleiben angehakt, alle anderen nicht."""
    old = tmp_path / "old.db"
    con = sqlite3.connect(old)
    con.executescript("""
        CREATE TABLE projects (id INTEGER PRIMARY KEY, name VARCHAR UNIQUE, sort_order INTEGER NOT NULL DEFAULT 0, created_at DATETIME);
        CREATE TABLE molecules (id INTEGER PRIMARY KEY, project_id INTEGER, name VARCHAR, smiles VARCHAR,
            formula VARCHAR, exact_mass FLOAT, image_path VARCHAR, sort_order INTEGER NOT NULL DEFAULT 0,
            created_at DATETIME, updated_at DATETIME);
        CREATE TABLE data_entries (id INTEGER PRIMARY KEY, molecule_id INTEGER, type_code VARCHAR,
            custom_label VARCHAR, required BOOLEAN NOT NULL DEFAULT 1, status VARCHAR NOT NULL DEFAULT 'missing',
            folder_path VARCHAR, file_path VARCHAR, text_note VARCHAR, mp_value FLOAT, updated_at DATETIME);
        CREATE TABLE entry_files (id INTEGER PRIMARY KEY, entry_id INTEGER, path VARCHAR, updated_at DATETIME);
        CREATE TABLE entry_notes (id INTEGER PRIMARY KEY, entry_id INTEGER, text VARCHAR NOT NULL DEFAULT '', updated_at DATETIME);
        INSERT INTO projects (id, name, created_at) VALUES (1, 'Alt', '2026-01-01 00:00:00');
        INSERT INTO molecules (id, project_id, name, created_at, updated_at) VALUES (1, 1, 'M-alt', '2026-01-01 00:00:00', '2026-01-01 00:00:00');
        INSERT INTO data_entries (id, molecule_id, type_code, custom_label, updated_at)
            VALUES (1, 1, 'other', '19F NMR', '2026-01-01 00:00:00'),
                   (2, 1, 'other', 'XRay', '2026-01-01 00:00:00'),
                   (3, 1, 'nmr_1h', NULL, '2026-01-01 00:00:00');
    """)
    con.commit()
    con.close()

    db.init_db(old)
    con = sqlite3.connect(old)
    rows = dict(con.execute("SELECT id, in_document FROM data_entries"))
    con.close()
    assert rows == {1: 1, 2: 0, 3: 0}


def test_word_export_zaehlt_als_aenderung():
    """Das Dokument wird beim Eintrag „Versuchsvorschrift" verlinkt, ändert
    also den Datensatz: im Lesemodus gesperrt und mit Strg+Z zurücknehmbar."""
    from app.main import is_blocked_read_only, is_undoable

    assert is_undoable("POST", "/api/molecules/1/word")
    assert not is_undoable("POST", "/api/molecules/1/export")


def test_dokument_wird_unter_versuchsvorschrift_verlinkt(client, tmp_path):
    mol = _molecule(client)
    result, _, _ = _build(client, mol, tmp_path)
    assert result["linked"] == "entry"

    entries = {e["type_code"]: e for e in
               client.get(f"/api/molecules/{mol['id']}").json()["entries"]}
    assert entries["procedure"]["file_path"] == result["file"]
    # Der Status wird nicht mitgesetzt — er bleibt in dieser App Handarbeit
    assert entries["procedure"]["status"] == "missing"


def test_vorhandene_verlinkung_wird_nicht_ueberschrieben(client, tmp_path):
    mol = _molecule(client)
    entries = {e["type_code"]: e for e in
               client.get(f"/api/molecules/{mol['id']}").json()["entries"]}
    alt = tmp_path / "handgeschrieben.docx"
    alt.write_text("x")
    client.patch(f"/api/entries/{entries['procedure']['id']}",
                 json={"file_path": str(alt)})

    result, _, _ = _build(client, mol, tmp_path)
    assert result["linked"] == "extra"

    procedure = next(e for e in client.get(f"/api/molecules/{mol['id']}").json()["entries"]
                     if e["type_code"] == "procedure")
    assert procedure["file_path"] == str(alt)  # unverändert
    assert [f["path"] for f in procedure["files"]] == [result["file"]]


def test_reaktionsgleichung_wird_auf_70_prozent_gesetzt(client, tmp_path, monkeypatch):
    """Wie in der Vorlage: die gezeichnete Größe, auf 70 % verkleinert."""
    from app import chemdraw_render, word_export

    # EMF-Kopf mit rclFrame = 10 × 5 cm (Angaben in 1/100 mm)
    emf = bytearray(200)
    emf[0:4] = b"\x01\x00\x00\x00"
    struct.pack_into("<4i", emf, 24, 0, 0, 10000, 5000)
    monkeypatch.setattr(chemdraw_render, "export_emf", lambda p: bytes(emf))
    monkeypatch.setattr(word_export.db, "image_file", lambda v: tmp_path / "eq.cdx")
    (tmp_path / "eq.cdx").write_bytes(b"VjCD0100" + bytes(9000))

    mol = _molecule(client)
    client.patch(f"/api/molecules/{mol['id']}", json={"equation_path": "eq.png"})
    _, document, _ = _build(client, mol, tmp_path)

    # 10 cm = 283.46 pt, davon 70 % = 198.4 pt
    assert "width:198.4pt" in document
    assert "height:99.21pt" in document


def test_mikro_einheiten_bekommen_geschuetztes_leerzeichen():
    """µ aus der Sonderzeichenpalette: Mikrozeichen (U+00B5) und griechisches
    My (U+03BC) gelten beide als Einheitenvorsatz, µmol eingeschlossen."""
    text = "".join(r.text for r in chem_text.procedure(
        "5.0 \u00b5mol in 20 \u03bcL at \u221278 \u00b0C"))
    nbsp = chem_text.NBSP
    assert f"5.0{nbsp}\u00b5mol" in text
    assert f"20{nbsp}\u03bcL" in text
    assert f"\u221278{nbsp}\u00b0C" in text
