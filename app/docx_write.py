"""Schreibt Word-Dateien (.docx) — genau so viel OOXML, wie die Vorlage braucht.

Eine .docx ist ein ZIP aus XML-Teilen. Die unveränderlichen davon
(Formatvorlagen, Design, Schriftentabelle, Einstellungen) liegen als fertige
Dateien in `wordskel/` und stammen aus der Vorlage — dadurch sehen erzeugte
Dokumente exakt aus wie ein von Hand geschriebenes. Erzeugt werden hier nur
`document.xml` samt Beziehungen, Bildern und eingebetteten Objekten.

Bewusst ohne python-docx: die drei Dinge, auf die es hier ankommt — SVG mit
Rasterrückfall, eingebettetes ChemDraw-Objekt und das SEQ-Feld der
Abbildungsnummer — kann python-docx alle nicht, dafür wäre ohnehin
Roh-XML nötig. So bleibt es bei null zusätzlichen Abhängigkeiten.
"""
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

SKEL_DIR = Path(__file__).resolve().parent / "wordskel"

EMU_PER_CM = 360000
# Satzbreite der Vorlage: A4 (21 cm) minus 2 × 2,5 cm Rand
TEXT_WIDTH_EMU = 5760720

_NS = (
    'xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" '
    'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
    'xmlns:o="urn:schemas-microsoft-com:office:office" '
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
    'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" '
    'xmlns:v="urn:schemas-microsoft-com:vml" '
    'xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" '
    'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
    'xmlns:w10="urn:schemas-microsoft-com:office:word" '
    'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
    'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" '
    'xmlns:w15="http://schemas.microsoft.com/office/word/2012/wordml" '
    'mc:Ignorable="w14 w15 wp14"'
)

# Seiteneinrichtung der Vorlage: A4 hoch, Ränder 2,5/2,5/2,5/2,0 cm
_SECT_PR = (
    '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
    '<w:pgMar w:top="1417" w:right="1417" w:bottom="1134" w:left="1417" '
    'w:header="708" w:footer="708" w:gutter="0"/>'
    '<w:cols w:space="708"/><w:docGrid w:linePitch="360"/></w:sectPr>'
)

_CONTENT_TYPES_HEAD = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
)
_MEDIA_TYPES = {
    "png": "image/png",
    "svg": "image/svg+xml",
    "emf": "image/x-emf",
    "bin": "application/vnd.openxmlformats-officedocument.oleObject",
}
_OVERRIDES = [
    ("/word/document.xml", "wordprocessingml.document.main+xml"),
    ("/word/styles.xml", "wordprocessingml.styles+xml"),
    ("/word/settings.xml", "wordprocessingml.settings+xml"),
    ("/word/fontTable.xml", "wordprocessingml.fontTable+xml"),
    ("/word/theme/theme1.xml", "theme+xml"),
]

_REL_IMAGE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
_REL_OLE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/oleObject"

# Der VML-Formtyp, in dem Word das Vorschaubild eines OLE-Objekts zeigt
_SHAPETYPE = (
    '<v:shapetype id="_x0000_t75" coordsize="21600,21600" o:spt="75" '
    'o:preferrelative="t" path="m@4@5l@4@11@9@11@9@5xe" filled="f" stroked="f">'
    '<v:stroke joinstyle="miter"/><v:formulas>'
    '<v:f eqn="if lineDrawn pixelLineWidth 0"/><v:f eqn="sum @0 1 0"/>'
    '<v:f eqn="sum 0 0 @1"/><v:f eqn="prod @2 1 2"/>'
    '<v:f eqn="prod @3 21600 pixelWidth"/><v:f eqn="prod @3 21600 pixelHeight"/>'
    '<v:f eqn="sum @0 0 1"/><v:f eqn="prod @6 1 2"/>'
    '<v:f eqn="prod @7 21600 pixelWidth"/><v:f eqn="sum @8 21600 0"/>'
    '<v:f eqn="prod @7 21600 pixelHeight"/><v:f eqn="sum @10 21600 0"/>'
    '</v:formulas><v:path o:extrusionok="f" gradientshapeok="t" o:connecttype="rect"/>'
    '<o:lock v:ext="edit" aspectratio="t"/></v:shapetype>'
)


_VERT_ALIGN = {"sup": "superscript", "sub": "subscript"}


@dataclass
class Run:
    """Ein Textstück mit seiner Auszeichnung. `vert` ist None, „sup" oder
    „sub"; `color` ist ein RGB-Hex ohne Raute (Platzhalter sind rot)."""

    text: str
    bold: bool = False
    italic: bool = False
    vert: str | None = None
    color: str | None = None

    def xml(self) -> str:
        props = ""
        if self.bold:
            props += "<w:b/>"
        if self.italic:
            props += "<w:i/>"
        if self.color:
            props += f'<w:color w:val="{self.color}"/>'
        if self.vert:
            props += f'<w:vertAlign w:val="{_VERT_ALIGN[self.vert]}"/>'
        rpr = f"<w:rPr>{_FONT}{props}</w:rPr>"
        # Zeilenumbrüche in Notizen werden zu echten Umbrüchen im Absatz
        parts = []
        for i, chunk in enumerate(self.text.split("\n")):
            if i:
                parts.append("<w:br/>")
            if chunk:
                parts.append(f'<w:t xml:space="preserve">{escape(chunk)}</w:t>')
        return f"<w:r>{rpr}{''.join(parts)}</w:r>" if parts else ""


# Die Vorlage setzt Calibri ausdrücklich je Textstück (das Design läge sonst
# bei Aptos). Genau das wird hier durchgehend gemacht — in der Vorlage war es
# nur an einigen Absätzen vergessen worden.
_FONT = '<w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/>'


def runs_xml(runs: list[Run]) -> str:
    return "".join(r.xml() for r in runs)


class Document:
    """Sammelt Absätze, Bilder und eingebettete Objekte und schreibt sie als
    .docx. Beziehungs-IDs und Dateinamen werden fortlaufend vergeben."""

    def __init__(self) -> None:
        self._body: list[str] = []
        self._rels: list[tuple[str, str, str]] = []  # (rId, Typ, Ziel)
        self._parts: dict[str, bytes] = {}  # Pfad im ZIP -> Inhalt
        self._next_rel = 1
        self._next_media = 1
        self._next_ole = 1
        self._next_shape = 1025
        self._next_docpr = 1

    # ---------- Beziehungen und Binärteile ----------

    def _add_part(self, folder: str, ext: str, data: bytes, rel_type: str) -> str:
        if folder == "media":
            name = f"image{self._next_media}.{ext}"
            self._next_media += 1
        else:
            name = f"oleObject{self._next_ole}.{ext}"
            self._next_ole += 1
        self._parts[f"word/{folder}/{name}"] = data
        rid = f"rId{self._next_rel}"
        self._next_rel += 1
        self._rels.append((rid, rel_type, f"{folder}/{name}"))
        return rid

    # ---------- Absätze ----------

    def paragraph(self, runs: list[Run], *, jc: str | None = None,
                  style: str | None = None, keep_next: bool = False,
                  bold_off: bool = False) -> None:
        """Ein Absatz. `bold_off` hebt die Fettschrift einer fetten
        Formatvorlage (Beschriftung) für die Absatzmarke auf."""
        props = ""
        if style:
            props += f'<w:pStyle w:val="{style}"/>'
        if keep_next:
            props += "<w:keepNext/>"
        if jc:
            props += f'<w:jc w:val="{jc}"/>'
        rpr = _FONT + ('<w:b w:val="0"/>' if bold_off else "")
        props += f"<w:rPr>{rpr}</w:rPr>"
        self._body.append(f"<w:p><w:pPr>{props}</w:pPr>{runs_xml(runs)}</w:p>")

    def page_break(self) -> None:
        self._body.append(
            f'<w:p><w:pPr><w:rPr>{_FONT}</w:rPr></w:pPr>'
            f'<w:r><w:rPr>{_FONT}</w:rPr><w:br w:type="page"/></w:r></w:p>'
        )

    def sequence_field(self, name: str, cached: int = 1, *,
                       bold: bool = False) -> str:
        """SEQ-Feld („Figure 1"). Word zählt beim Aktualisieren selbst durch —
        so bleibt die Nummerierung heil, wenn mehrere Dokumente
        hintereinandergesetzt werden. `cached` ist die Nummer, die bis dahin
        angezeigt wird, also die richtige für dieses Dokument allein."""
        rpr = f"<w:rPr>{_FONT}{'<w:b/>' if bold else ''}</w:rPr>"
        return (
            f'<w:r>{rpr}<w:fldChar w:fldCharType="begin"/></w:r>'
            f'<w:r>{rpr}<w:instrText xml:space="preserve"> SEQ {name} \\* ARABIC </w:instrText></w:r>'
            f'<w:r>{rpr}<w:fldChar w:fldCharType="separate"/></w:r>'
            f"<w:r>{rpr}<w:t>{cached}</w:t></w:r>"
            f'<w:r>{rpr}<w:fldChar w:fldCharType="end"/></w:r>'
        )

    def caption(self, before: list[Run], field: str, after: list[Run]) -> None:
        """Bildunterschrift in der Formatvorlage „Beschriftung": Text, dann
        das eingesetzte SEQ-Feld, dann der Rest."""
        props = ('<w:pStyle w:val="Beschriftung"/>'
                 f'<w:rPr>{_FONT}<w:b w:val="0"/></w:rPr>')
        self._body.append(
            f"<w:p><w:pPr>{props}</w:pPr>"
            f"{runs_xml(before)}{field}{runs_xml(after)}</w:p>"
        )

    # ---------- Grafik ----------

    def picture(self, *, png: bytes, svg: bytes | None = None,
                width_emu: int, height_emu: int, keep_next: bool = False) -> None:
        """Bild in eigenem Absatz. Ist `svg` gesetzt, wird es als
        Vektorfassung mitgegeben (Word zeigt dann das SVG, das PNG ist der
        Rückfall) — genau wie beim Einfügen eines SVG von Hand."""
        png_id = self._add_part("media", "png", png, _REL_IMAGE)
        ext = ""
        if svg:
            svg_id = self._add_part("media", "svg", svg, _REL_IMAGE)
            ext = (
                '<a:extLst><a:ext uri="{96DAC541-7B7A-43D3-8B79-37D633B846F1}">'
                '<asvg:svgBlip xmlns:asvg="http://schemas.microsoft.com/office/drawing/2016/SVG/main" '
                f'r:embed="{svg_id}"/></a:ext></a:extLst>'
            )
        doc_pr = self._next_docpr
        self._next_docpr += 1
        drawing = (
            '<w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
            f'<wp:extent cx="{width_emu}" cy="{height_emu}"/>'
            '<wp:effectExtent l="0" t="0" r="0" b="0"/>'
            f'<wp:docPr id="{doc_pr}" name="Grafik {doc_pr}"/>'
            '<wp:cNvGraphicFramePr><a:graphicFrameLocks '
            'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
            'noChangeAspect="1"/></wp:cNvGraphicFramePr>'
            '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
            '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            f'<pic:nvPicPr><pic:cNvPr id="{doc_pr}" name=""/><pic:cNvPicPr/></pic:nvPicPr>'
            f'<pic:blipFill><a:blip r:embed="{png_id}">{ext}</a:blip>'
            '<a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0"/>'
            f'<a:ext cx="{width_emu}" cy="{height_emu}"/></a:xfrm>'
            '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
            '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing>'
        )
        props = ("<w:keepNext/>" if keep_next else "") + f"<w:rPr>{_FONT}</w:rPr>"
        self._body.append(
            f"<w:p><w:pPr>{props}</w:pPr>"
            f'<w:r><w:rPr>{_FONT}<w:noProof/></w:rPr>{drawing}</w:r></w:p>'
        )

    def ole_object_table(self, *, ole: bytes, emf: bytes, prog_id: str,
                         width_pt: float, height_pt: float) -> None:
        """Eingebettetes Objekt (ChemDraw), zentriert in einer randlosen
        Tabelle — die Anordnung der Vorlage. Angezeigt wird das EMF; per
        Doppelklick öffnet Word das Objekt in ChemDraw."""
        emf_id = self._add_part("media", "emf", emf, _REL_IMAGE)
        ole_id = self._add_part("embeddings", "bin", ole, _REL_OLE)
        shape = f"_x0000_i{self._next_shape}"
        object_id = f"_{1850000000 + self._next_shape}"
        self._next_shape += 1
        obj = (
            f'<w:object w:dxaOrig="{round(width_pt * 20)}" '
            f'w:dyaOrig="{round(height_pt * 20)}">'
            f'{_SHAPETYPE}'
            f'<v:shape id="{shape}" type="#_x0000_t75" '
            f'style="width:{width_pt:.4g}pt;height:{height_pt:.4g}pt" o:ole="">'
            f'<v:imagedata r:id="{emf_id}" o:title=""/></v:shape>'
            f'<o:OLEObject Type="Embed" ProgID="{prog_id}" ShapeID="{shape}" '
            f'DrawAspect="Content" ObjectID="{object_id}" r:id="{ole_id}"/>'
            "</w:object>"
        )
        self._body.append(
            '<w:tbl><w:tblPr><w:tblW w:w="0" w:type="auto"/><w:tblBorders>'
            + "".join(f'<w:{s} w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                      for s in ("top", "left", "bottom", "right", "insideH", "insideV"))
            + '</w:tblBorders><w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" '
            'w:firstColumn="1" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/></w:tblPr>'
            '<w:tblGrid><w:gridCol w:w="9062"/></w:tblGrid><w:tr><w:tc>'
            '<w:tcPr><w:tcW w:w="9062" w:type="dxa"/></w:tcPr>'
            f'<w:p><w:pPr><w:jc w:val="center"/><w:rPr>{_FONT}</w:rPr></w:pPr>'
            f'<w:r><w:rPr>{_FONT}</w:rPr>{obj}</w:r></w:p>'
            "</w:tc></w:tr></w:tbl>"
        )

    # ---------- Speichern ----------

    def _document_xml(self) -> bytes:
        body = "".join(self._body) + _SECT_PR
        xml = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
               f"<w:document {_NS}><w:body>{body}</w:body></w:document>")
        return xml.encode("utf-8")

    def _rels_xml(self) -> bytes:
        base = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
        fixed = [
            (f"rId{self._next_rel}", f"{base}/styles", "styles.xml"),
            (f"rId{self._next_rel + 1}", f"{base}/settings", "settings.xml"),
            (f"rId{self._next_rel + 2}", f"{base}/fontTable", "fontTable.xml"),
            (f"rId{self._next_rel + 3}", f"{base}/theme", "theme/theme1.xml"),
        ]
        items = "".join(
            f'<Relationship Id="{rid}" Type="{typ}" Target="{target}"/>'
            for rid, typ, target in self._rels + fixed
        )
        return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                f"{items}</Relationships>").encode("utf-8")

    def _content_types_xml(self) -> bytes:
        used = {Path(p).suffix.lstrip(".").lower() for p in self._parts}
        defaults = "".join(
            f'<Default Extension="{ext}" ContentType="{_MEDIA_TYPES[ext]}"/>'
            for ext in sorted(used) if ext in _MEDIA_TYPES
        )
        overrides = "".join(
            f'<Override PartName="{part}" ContentType='
            f'"application/vnd.openxmlformats-officedocument.{kind}"/>'
            for part, kind in _OVERRIDES
        )
        overrides += ('<Override PartName="/docProps/core.xml" ContentType='
                      '"application/vnd.openxmlformats-package.core-properties+xml"/>')
        return (_CONTENT_TYPES_HEAD + defaults + overrides + "</Types>").encode("utf-8")

    def _core_xml(self, title: str) -> bytes:
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<cp:coreProperties '
            'xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/" '
            'xmlns:dcterms="http://purl.org/dc/terms/" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            f"<dc:title>{escape(title)}</dc:title>"
            f'<dcterms:created xsi:type="dcterms:W3CDTF">{stamp}</dcterms:created>'
            f'<dcterms:modified xsi:type="dcterms:W3CDTF">{stamp}</dcterms:modified>'
            "</cp:coreProperties>"
        ).encode("utf-8")

    def save(self, path: Path, title: str = "") -> None:
        root_rels = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/'
            '2006/relationships/officeDocument" Target="word/document.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/'
            '2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
            "</Relationships>"
        ).encode("utf-8")
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("[Content_Types].xml", self._content_types_xml())
            z.writestr("_rels/.rels", root_rels)
            z.writestr("docProps/core.xml", self._core_xml(title))
            z.writestr("word/document.xml", self._document_xml())
            z.writestr("word/_rels/document.xml.rels", self._rels_xml())
            for name in ("styles.xml", "settings.xml", "fontTable.xml",
                         "theme/theme1.xml"):
                z.writestr(f"word/{name}", (SKEL_DIR / "word" / name).read_bytes())
            for part, data in self._parts.items():
                z.writestr(part, data)
