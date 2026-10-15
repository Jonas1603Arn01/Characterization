"""Baut aus einem Molekül ein Word-Dokument im Aufbau der Vorlage
(procedure_FluIBioxHOTf.docx). Der Aufbau dort — und damit hier:

    FluIBiox • HOTf XX:            Name des Moleküls, dann die Verbindungsnummer
    ┌──────────────────────┐
    │  Reaktionsgleichung  │       randlose Tabelle mit dem ChemDraw-Objekt
    └──────────────────────┘
    A dried pressure Schlenk-…     Durchführungsfeld der Versuchsvorschrift
    ¹H NMR (501 MHz, …) δ = …      Notiz des jeweiligen Datentyps, gesetzt
    ¹³C NMR (126 MHz, …) = …
    ¹⁹F NMR (471 MHz, …) δ = …     weitere Kerne als eigene Einträge (s. u.)
    IR (solid) [cm⁻¹]: ṽ = …
    HR-MS-ESI(+) calc. …, found …
    m. p. …
    ── Seitenumbruch ──
    [Spektrum]                     je SVG des Moleküls, 16 cm breit
    Figure 1: ¹H NMR (…) of XX.

Was fehlt, wird nicht erfunden, sondern rot als „[einfügen]" markiert — so,
wie es in der Vorlage von Hand gemacht wurde. Alles, was das Dokument an
Zahlen und Wortlaut enthält, stammt unverändert aus der Datenbank.

Eigene Einträge („Sonstiges") kommen nur mit gesetztem Häkchen ins Dokument
(DataEntry.in_document); beim Anlegen wird es aus der Bezeichnung vorbelegt.
Meint die Bezeichnung eine NMR-Messung („19F NMR", „31P{1H} NMR",
„1H,15N HMBC"), wird der Eintrag genau wie ¹H und ¹³C behandelt: Textzeile
hinter dem ¹³C, Spektren mit derselben Bildunterschrift, Messbedingungen aus
seiner eigenen Notiz. Jeder andere angehakte Eintrag (Elementaranalyse,
Röntgenstruktur …) bekommt seine Zeile am Ende des Analytikblocks, mit der
Bezeichnung als fetter Beschriftung.
"""
import re
import struct
from io import BytesIO
from pathlib import Path

from . import chem_text, db, docx_write, olecf, osutil, paths, svg_raster
from .docx_write import Document, Run
from .export import sanitize, unique_path
from .models import DataEntry, Molecule

PLACEHOLDER_COLOR = "FF0000"
NUMBER_PLACEHOLDER = "XX"
_NUMBER_IN_TEXT = re.compile(rf"\b({NUMBER_PLACEHOLDER})\b")

# Reihenfolge der Analytikzeilen wie in der Vorlage (dort steht IR vor MS,
# anders als im Datentyp-Katalog). 2D-NMR bekommt keine Textzeile, nur
# Abbildungen.
LINE_ORDER = ["nmr_1h", "nmr_13c", "ir", "ms", "mp"]

IMAGE_SUFFIXES = {".svg", ".png", ".emf", ".jpg", ".jpeg"}

# Die Reaktionsgleichung wird auf 70 % ihrer natürlichen Größe gesetzt — so
# steht sie in der Vorlage (dort 291 pt statt der gezeichneten 415 pt).
EQUATION_SCALE = 0.70

# Feste Beschriftungen der Zeilen ohne eigene Notiz-Kopfzeile
_MS_LABEL = "HR-MS-ESI(+)"
_MS_TAIL = " calc. [M+H]+, found "
_MP_LABEL = "m. p."

# Kopfzeile, die eine Notiz schon selbst mitbringt — dieser Teil wird fett
_NOTE_LABEL = {
    "ir": re.compile(r"^\s*IR\b[^:]*:", re.I),
    "ms": re.compile(r"^\s*(HR[-\s]?MS[^\s,]*|HRMS[^\s,]*|MS[^\s,]*)", re.I),
    "mp": re.compile(r"^\s*(m\.\s*p\.|mp\.?|melting\s+point|schmelzpunkt)", re.I),
}


def _T(lang: str, de: str, en: str) -> str:
    return en if lang == "en" else de


def _number() -> Run:
    """Die Verbindungsnummer — bis auf Weiteres ein roter Platzhalter."""
    return Run(NUMBER_PLACEHOLDER, bold=True, color=PLACEHOLDER_COLOR)


def _mark_numbers(runs: list[Run] | None) -> list[Run] | None:
    """Ein „XX" im Durchführungstext ist die Verbindungsnummer und wird wie
    im Titel gesetzt: fett und rot. So sind im fertigen Dokument alle Stellen
    rot, an denen die Nummer noch einzusetzen ist."""
    if not runs:
        return runs
    out: list[Run] = []
    for r in runs:
        for i, part in enumerate(_NUMBER_IN_TEXT.split(r.text)):
            if i % 2:
                out.append(_number())
            elif part:
                out.append(Run(part, r.bold, r.italic, r.vert, r.color))
    return out


def _missing(lang: str) -> Run:
    return Run(_T(lang, "[einfügen]", "[insert]"), color=PLACEHOLDER_COLOR)


def _display_name(name: str) -> str:
    """Der Malpunkt für Salze wird im Dokument als Aufzählungspunkt gesetzt —
    „FluIBiox * HOTf" wird zu „FluIBiox • HOTf", wie in der Vorlage."""
    return re.sub(r"\s\*\s", " • ", name)


def _title_runs(mol: Molecule) -> list[Run]:
    """Der Molekülname für die Überschrift — mit seiner Formatierung
    (kursives N-, tiefgestellte Indizes), wenn er eine hat."""
    if not mol.name_html:
        return [Run(_display_name(mol.name))]
    return [Run(_display_name(r.text), r.bold, r.italic, r.vert, r.color)
            for r in chem_text.from_html(mol.name_html)]


def _included(entries: dict[str, list[DataEntry]]) -> tuple[list[DataEntry], list[DataEntry]]:
    """Die eigenen Einträge mit gesetztem Word-Häkchen, aufgeteilt danach,
    wohin sie gehören: weitere NMR-Kerne stehen bei den anderen NMR-Zeilen
    hinter dem ¹³C, alles Übrige (Elementaranalyse, Röntgenstruktur …) hinter
    dem Schmelzpunkt am Ende des Analytikblocks."""
    chosen = [e for e in entries.get("other", []) if e.in_document]
    nmr = [e for e in chosen if chem_text.is_nmr_label(e.custom_label)]
    return nmr, [e for e in chosen if e not in nmr]


def _entries(mol: Molecule) -> dict[str, list[DataEntry]]:
    out: dict[str, list[DataEntry]] = {}
    for e in mol.entries:
        # Schmelzpunkt ist bei einem Öl nicht relevant — wie im übrigen Export
        if mol.physical_state == "oil" and e.type_code == "mp":
            continue
        if not e.required:  # „nicht benötigt" kommt nicht ins Dokument
            continue
        out.setdefault(e.type_code, []).append(e)
    return out


def _note_runs(entry: DataEntry | None) -> list[Run] | None:
    """Notizen eines Eintrags als gesetzte Textstücke (mehrere Notizen werden
    durch Leerzeichen getrennt); None, wenn es keine gibt."""
    if entry is None:
        return None
    runs: list[Run] = []
    for n in entry.notes:
        if not (n.text or "").strip() and not (n.html or "").strip():
            continue
        if runs:
            runs.append(Run(" "))
        runs += chem_text.note(n.text or "", n.html, entry.type_code)
    return runs or None


def _labelled_line(entry: DataEntry | None, kind: str, fallback_label: str,
                   fallback_tail: str, lang: str) -> list[Run]:
    """Eine Analytikzeile: fette Beschriftung, dann der Wert.

    Bringt die Notiz ihre Beschriftung selbst mit („IR (ATR) [cm-1]: …"),
    wird genau die fett gesetzt und der Rest übernommen. Sonst wird die
    Beschriftung der Vorlage davorgestellt und die Notiz — oder ein roter
    Platzhalter — als Wert eingesetzt.
    """
    note = _note_runs(entry)
    plain = "".join(r.text for r in note) if note else ""
    head = _NOTE_LABEL[kind].match(plain) if note else None
    if head:
        cut = head.end()
        return chem_text.bold(plain[:cut]) + chem_text.plain(plain[cut:])
    runs = chem_text.bold(fallback_label) + chem_text.plain(fallback_tail)
    return runs + (note if note else [_missing(lang)])


def _measurement_line(entry: DataEntry, code: str, lang: str) -> list[Run]:
    """Eine Messzeile (¹H, ¹³C, weitere Kerne, angehakte eigene Einträge).
    Die Notiz bringt ihre Kopfzeile („13C NMR (126 MHz…") üblicherweise mit;
    fehlt sie, wird die Methodenbezeichnung davorgesetzt, damit die Zeile
    nicht ohne Beschriftung dasteht."""
    runs = _note_runs(entry)
    if not runs:
        return _method_runs(code, "", entry) + [Run(" "), _missing(lang)]
    if chem_text.NMR_HEAD.match("".join(r.text for r in runs)):
        return runs
    return _method_runs(code, "", entry) + [Run(" ")] + runs


def _ir_line(mol: Molecule, entry: DataEntry | None, lang: str) -> list[Run]:
    state = {"solid": "solid", "oil": "oil"}.get(mol.physical_state or "")
    label = f"IR ({state}) [cm-1]:" if state else "IR [cm-1]:"
    return _labelled_line(entry, "ir", label, " ṽ = ", lang)


def _mp_line(entry: DataEntry | None, lang: str) -> list[Run]:
    if entry is not None and entry.mp_value is not None and not _note_runs(entry):
        return chem_text.bold(_MP_LABEL) + [Run(f" {entry.mp_value:g} °C")]
    return _labelled_line(entry, "mp", _MP_LABEL, " ", lang)


# ---------- Grafik ----------

def _emf_size_pt(emf: bytes) -> tuple[float, float] | None:
    """Natürliche Größe eines EMF in Punkt (aus rclFrame, in 1/100 mm)."""
    if len(emf) < 40 or emf[:4] != b"\x01\x00\x00\x00":
        return None
    left, top, right, bottom = struct.unpack_from("<4i", emf, 24)
    w_mm, h_mm = (right - left) / 100, (bottom - top) / 100
    if w_mm <= 0 or h_mm <= 0:
        return None
    return w_mm / 25.4 * 72, h_mm / 25.4 * 72


def _bitmap_as_png(path: Path) -> tuple[bytes, float, float] | None:
    """Gespeichertes Bild als PNG samt natürlicher Größe in Punkt — der
    Rückfall, wenn ChemDraw kein EMF liefern kann."""
    try:
        from PIL import Image

        with Image.open(path) as img:
            dpi = img.info.get("dpi") or (300, 300)
            buf = BytesIO()
            img.convert("RGB").save(buf, "PNG")
            return (buf.getvalue(), img.width / (dpi[0] or 300) * 72,
                    img.height / (dpi[1] or 300) * 72)
    except (OSError, ValueError):
        return None


def _add_equation(doc: Document, mol: Molecule, lang: str,
                  warnings: list[str]) -> None:
    """Reaktionsgleichung als eingebettetes ChemDraw-Objekt in einer
    randlosen Tabelle — die Anordnung der Vorlage."""
    cdx_path = db.image_file(mol.equation_cdx_path)
    img_path = db.image_file(mol.equation_path)
    cdx = None
    if cdx_path and cdx_path.is_file():
        cdx = cdx_path.read_bytes()
    elif mol.equation_cdx_path:
        warnings.append(_T(lang, "ChemDraw-Datei der Reaktionsgleichung nicht gefunden",
                           "ChemDraw file of the reaction equation not found"))

    emf = None
    if cdx_path and cdx_path.is_file() and not osutil.IS_WIN:
        warnings.append(_T(
            lang,
            "Die Reaktionsgleichung als Vektorgrafik braucht ChemDraw unter "
            "Windows — das gespeicherte Bild wird verwendet",
            "The reaction equation as vector graphics needs ChemDraw on "
            "Windows — the stored image is used instead",
        ))
    elif cdx_path and cdx_path.is_file():
        # nur unter Windows: ChemDraw per COM (chemdraw_render)
        from . import chemdraw_render
        try:
            emf = chemdraw_render.export_emf(cdx_path)
        except chemdraw_render.RenderError as e:
            warnings.append(_T(
                lang,
                f"ChemDraw konnte die Reaktionsgleichung nicht als Vektorgrafik "
                f"ausgeben ({e}) — das gespeicherte Bild wird verwendet",
                f"ChemDraw could not export the reaction equation as vector "
                f"graphics ({e}) — the stored image is used instead",
            ))

    max_width = docx_write.TEXT_WIDTH_EMU / 12700  # EMU -> Punkt

    def fit(width: float, height: float) -> tuple[float, float]:
        """Auf 70 % verkleinern und, falls dann immer noch zu breit, auf die
        Satzbreite begrenzen."""
        width, height = width * EQUATION_SCALE, height * EQUATION_SCALE
        if width > max_width:
            width, height = max_width, height * max_width / width
        return width, height

    if emf:
        width, height = fit(*(_emf_size_pt(emf) or (max_width, max_width * 0.35)))
        if cdx:
            doc.ole_object_table(ole=olecf.chemdraw_object(cdx, emf), emf=emf,
                                 prog_id=olecf.CHEMDRAW_PROGID,
                                 width_pt=width, height_pt=height)
            return

    if not img_path or not img_path.is_file():
        if mol.equation_path or mol.equation_cdx_path:
            warnings.append(_T(lang, "Reaktionsgleichung nicht gefunden",
                               "Reaction equation not found"))
        return
    raster = _bitmap_as_png(img_path)
    if raster is None:
        warnings.append(_T(lang, "Reaktionsgleichung ist nicht lesbar",
                           "Reaction equation could not be read"))
        return
    png, width, height = raster
    width, height = fit(width, height)
    if cdx:
        # Kein EMF, aber die ChemDraw-Datei ist da: Objekt trotzdem einbetten
        # und das gespeicherte Bild als Ansicht nehmen — bearbeitbar bleibt es.
        doc.ole_object_table(ole=olecf.chemdraw_object(cdx), emf=png,
                             prog_id=olecf.CHEMDRAW_PROGID,
                             width_pt=width, height_pt=height)
    else:
        doc.picture(png=png, width_emu=round(width * 12700),
                    height_emu=round(height * 12700))


# ---------- Abbildungen ----------

def _spectra(mol: Molecule, entries: dict[str, list[DataEntry]]) -> list[tuple]:
    """Alle einzubettenden Spektrenbilder in Dokumentreihenfolge:
    (Datentyp, Beschriftung der Datei, Pfad, Eintrag). Feste Datentypen und
    zusätzliche NMR-Kerne; alle übrigen eigenen Einträge bleiben draußen.
    Je Eintrag zuerst die in den festen SVG-Feldern verlinkten Spektren (bei
    2D-NMR HSQC, dann HMBC), danach die Bilder unter den zusätzlichen Dateien."""
    out = []
    for entry in _document_entries(entries):
        fixed = [(entry.svg_path, entry.svg_label), (entry.svg2_path, entry.svg2_label)]
        for stored, label in fixed + [(f.path, f.label) for f in entry.files]:
            if not stored:
                continue
            p = Path(paths.to_display(stored) or stored)
            if p.suffix.lower() in IMAGE_SUFFIXES:
                out.append((entry.type_code, Path(label or p.stem).stem, p, entry))
    return out


def _document_entries(entries: dict[str, list[DataEntry]]) -> list[DataEntry]:
    """Die Einträge in Dokumentreihenfolge: ¹H, ¹³C, weitere Kerne, 2D,
    IR, MS, Schmelzpunkt, sonstige angehakte Einträge."""
    order = LINE_ORDER[:2] + ["nmr_2d"] + LINE_ORDER[2:]
    nmr, rest = _included(entries)
    out: list[DataEntry] = []
    for code in order:
        out += entries.get(code, [])
        if code == "nmr_13c":  # zusätzliche Kerne direkt hinter das ¹³C
            out += nmr
    return out + rest


def _entry_conditions(entry: DataEntry | None) -> dict[str, str]:
    """Messbedingungen aus der Notiz genau dieses Eintrags."""
    runs = _note_runs(entry)
    return chem_text.conditions("".join(r.text for r in runs)) if runs else {}


def _conditions(entries: dict[str, list[DataEntry]]) -> dict[str, dict[str, str]]:
    """Messbedingungen von ¹H und ¹³C — die 2D-Bildunterschrift setzt sich
    aus beiden zusammen."""
    return {code: _entry_conditions((entries.get(code) or [None])[0])
            for code in ("nmr_1h", "nmr_13c")}


def _condition_runs(cond: dict[str, str], frequency: str | None) -> list[Run]:
    """« (501 MHz, CDCl₃, 298 K)» — was fehlt, bleibt weg."""
    parts: list[list[Run]] = []
    if frequency:
        parts.append([Run(f"{frequency} MHz")])
    if cond.get("solvent"):
        parts.append(chem_text.plain(cond["solvent"]))
    if cond.get("temperature"):
        parts.append([Run(f"{cond['temperature']} K")])
    if not parts:
        return []
    runs = [Run(" (")]
    for i, p in enumerate(parts):
        if i:
            runs.append(Run(", "))
        runs += p
    runs.append(Run(")"))
    return runs


def _method_runs(code: str, label: str, entry: DataEntry | None = None) -> list[Run]:
    """Fette Methodenbezeichnung — Massenzahlen hochgestellt."""
    if code == "nmr_1h":
        return chem_text.head("1H NMR")
    if code == "nmr_13c":
        return chem_text.head("13C NMR")
    if code == "nmr_2d":
        # Steht der Kern schon in der Dateibeschriftung („1H,15N HMBC"),
        # bleibt sie stehen; sonst ist es das übliche H,C-Experiment.
        return chem_text.head(label if chem_text.is_nmr_label(label)
                              else f"1H,13C {label}")
    if entry is not None and entry.type_code == "other":
        # Bei eigenen Einträgen beschriftet der Eintragsname, nicht der
        # Dateiname — „Elemental analysis" sagt mehr als „ea"
        if chem_text.is_nmr_label(entry.custom_label):
            return chem_text.head(entry.custom_label)
        return [Run(entry.custom_label or label, bold=True)]
    return [Run(label, bold=True)]


def _caption(doc: Document, number: int, code: str, label: str,
             entry: DataEntry, cond: dict[str, dict[str, str]], lang: str) -> None:
    if code == "nmr_2d":
        one, thirteen = cond["nmr_1h"], cond["nmr_13c"]
        base = one or thirteen
        pair = [f for f in (one.get("frequency"), thirteen.get("frequency")) if f]
        freq = "/".join(pair) if len(pair) == 2 else (pair[0] if pair else None)
    else:
        # ¹H, ¹³C und zusätzliche Kerne: die Bedingungen stehen in der
        # Notiz des Eintrags selbst
        base = _entry_conditions(entry)
        freq = base.get("frequency")
    after = _method_runs(code, label, entry) + _condition_runs(base, freq)
    after += [Run(" of "), _number(), Run(".")]
    doc.caption([Run("Figure ", bold=True)],
                doc.sequence_field("Figure", number, bold=True),
                [Run(": ", bold=True)] + after)


# ---------- Einstiegspunkt ----------

def export_word(mol: Molecule, target_dir: Path, lang: str = "en") -> dict:
    """Schreibt <Zielordner>/<Molekülname>.docx und meldet, was gefehlt hat."""
    warnings: list[str] = []
    entries = _entries(mol)
    doc = Document()

    # Überschrift: Name, dann die Verbindungsnummer
    title = _title_runs(mol)
    last = title[-1]
    if last.bold or last.italic or last.vert:
        title.append(Run(" "))
    else:
        last.text += " "  # ungeformter Name: ein Textstück wie bisher
    doc.paragraph(title + [_number(), Run(":")])

    _add_equation(doc, mol, lang, warnings)

    # Durchführung aus dem Textfeld des Eintrags „Versuchsvorschrift"
    procedure = _mark_numbers(_note_runs((entries.get("procedure") or [None])[0]))
    doc.paragraph(procedure or [Run(_T(lang, "[Durchführung einfügen]",
                                       "[insert procedure]"),
                                    color=PLACEHOLDER_COLOR)], jc="both")

    for entry in _document_entries(entries):
        code = entry.type_code
        if code == "nmr_2d":
            continue  # 2D-NMR hat in der Vorlage keine Textzeile, nur Abbildungen
        if code == "ir":
            doc.paragraph(_ir_line(mol, entry, lang))
        elif code == "ms":
            doc.paragraph(_labelled_line(entry, "ms", _MS_LABEL, _MS_TAIL, lang)
                          + [Run(".")])
        elif code == "mp":
            doc.paragraph(_mp_line(entry, lang))
        elif code == "other" and not chem_text.is_nmr_label(entry.custom_label):
            # kurze Zeile wie IR/MS/Schmelzpunkt, kein Blocksatz
            doc.paragraph(_measurement_line(entry, code, lang))
        else:  # ¹H, ¹³C und zusätzliche Kerne
            doc.paragraph(_measurement_line(entry, code, lang), jc="both")

    # ---------- Spektren ----------
    spectra = _spectra(mol, entries)
    svgs = [(p.name, p) for _, _, p, _ in spectra if p.suffix.lower() == ".svg"]
    data: dict[Path, bytes] = {}
    for name, p in svgs:
        try:
            data[p] = p.read_bytes()
        except OSError:
            warnings.append(_T(lang, f"Spektrum nicht gefunden — {p}",
                               f"Spectrum not found — {p}"))
    rasterized = dict(zip(
        [p for _, p in svgs if p in data],
        svg_raster.to_pngs([(p.name, data[p]) for _, p in svgs if p in data]),
    ))

    drawn = 0
    cond = _conditions(entries)
    for code, label, p, entry in spectra:
        if p.suffix.lower() == ".svg":
            if p not in data:
                continue
            png, warn = rasterized[p]
            if warn:
                warnings.append(warn)
            svg = data[p]
        else:
            try:
                raw = p.read_bytes()
            except OSError:
                warnings.append(_T(lang, f"Spektrum nicht gefunden — {p}",
                                   f"Spectrum not found — {p}"))
                continue
            if p.suffix.lower() == ".png":
                png, svg = raw, None
            else:
                converted = _bitmap_as_png(p)
                if converted is None:
                    warnings.append(_T(lang, f"Spektrum ist nicht lesbar — {p}",
                                       f"Spectrum could not be read — {p}"))
                    continue
                png, svg = converted[0], None
        if not drawn:
            doc.page_break()
        drawn += 1
        ratio = svg_raster.aspect_ratio(svg) if svg else _png_ratio(png)
        doc.picture(png=png, svg=svg, width_emu=docx_write.TEXT_WIDTH_EMU,
                    height_emu=round(docx_write.TEXT_WIDTH_EMU * ratio),
                    keep_next=True)
        _caption(doc, drawn, code, label, entry, cond, lang)

    target_dir.mkdir(parents=True, exist_ok=True)
    path = unique_path(target_dir / f"{sanitize(mol.name)}.docx")
    doc.save(path, title=mol.name)
    return {"file": str(path), "spectra": drawn, "warnings": warnings}


def _png_ratio(png: bytes) -> float:
    try:
        from PIL import Image

        with Image.open(BytesIO(png)) as img:
            return img.height / img.width if img.width else 0.75
    except (OSError, ValueError):
        return 0.75
