"""Setzt Analytik-Notizen typografisch — so, wie sie in der Vorlage stehen.

In der App stehen die Analytikergebnisse als reiner Text im Notizfeld:

    1H NMR (501 MHz, CDCl3, 298 K) δ [ppm] = 8.41 (s, 1H, triazole-CH), …

Im Word-Dokument steht derselbe Satz gesetzt:

    ¹H NMR (501 MHz, CDCl₃, 298 K) δ [ppm] = 8.41 (s, 1H, triazole-C*H*), …

Also: Kopf fett mit hochgestellter Massenzahl, Indexziffern in Formeln tief,
das Kopplungs-*J* kursiv und in der Zuordnung der beobachtete Kern kursiv
(bei ¹H das H, bei ¹³C das C). Genau diese Regeln stehen hier.

Hat die Notiz eigene Formatierung (das Notizfeld kann fett/kursiv/hoch/tief),
gewinnt die — dann wird nichts geraten, sondern übernommen.

Nichts hiervon verändert Zahlen oder Wortlaut: es werden ausschließlich
Auszeichnungen vergeben und geschützte Leerzeichen zwischen Zahl und Einheit
gesetzt (damit „7.5 Hz" im Blocksatz nicht umbricht).
"""
import re
from html.parser import HTMLParser

from .docx_write import Run

NBSP = " "

# Kopfzeile eines NMR-Datensatzes: „1H NMR", „13C NMR", „13C{1H} NMR",
# auch mit Bindestrich („1H-NMR").
NMR_HEAD = re.compile(r"^\s*(\d{1,3})\s*([A-Z][a-z]?)"
                      r"(\s*\{\s*\d{1,3}\s*[A-Z][a-z]?\s*\})?"
                      r"\s*-?\s*NMR\b")
# Massenzahl im Kopf: Ziffern unmittelbar vor einem Elementsymbol
_MASS_NUMBER = re.compile(r"(\d+)(?=[A-Z])")
# Hochgestellte Ziffern für die Anzeige in der App (im Word-Dokument macht
# das die Auszeichnung selbst, siehe head())
_SUPERSCRIPT = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")

# Bezeichnung eines eigenen Eintrags, die eine NMR-Messung meint: Massenzahl,
# Element und der Name des Experiments. Daran erkennt der Word-Export, dass ein
# „Sonstiges"-Eintrag wie ¹H und ¹³C gesetzt werden soll — „19F NMR",
# „31P{1H} NMR" oder „1H,15N HMBC" ja, „XRay" oder „Elementaranalyse" nein.
_EXPERIMENTS = ("NMR|COSY|HSQC|HMQC|HMBC|NOESY|ROESY|TOCSY|DEPT|DOSY|HOESY|INEPT")
NMR_LABEL = re.compile(rf"^\s*\d{{1,3}}\s*[A-Z][a-z]?.*\b(?:{_EXPERIMENTS})\b")

# Kopfzeilen der übrigen Datentypen — daran wird erkannt, ob die Notiz die
# Beschriftung schon selbst mitbringt oder ob sie nur den Wert enthält.
HEAD_PATTERNS = {
    "ir": re.compile(r"^\s*IR\b", re.I),
    "ms": re.compile(r"^\s*(HR[-\s]?MS|HRMS|MS|ESI|EI|MALDI)\b", re.I),
    "mp": re.compile(r"^\s*(m\.\s*p\.|mp\b|melting\s+point|schmelzpunkt)", re.I),
}

# Elementsymbole, hinter denen Ziffern ein Index sind. Bewusst eine feste
# Liste: sonst würde aus einer Probennummer wie „JA294" ein „A₂₉₄".
ELEMENTS = {
    "H", "D", "T", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne", "Na", "Mg",
    "Al", "Si", "P", "S", "Cl", "Ar", "K", "Ca", "Sc", "Ti", "V", "Cr", "Mn",
    "Fe", "Co", "Ni", "Cu", "Zn", "Ga", "Ge", "As", "Se", "Br", "Kr", "Rb",
    "Sr", "Y", "Zr", "Nb", "Mo", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn",
    "Sb", "Te", "I", "Xe", "Cs", "Ba", "La", "Ce", "Hf", "Ta", "W", "Re",
    "Os", "Ir", "Pt", "Au", "Hg", "Tl", "Pb", "Bi",
}

# Einheiten, vor denen ein geschütztes Leerzeichen steht. „s" und „min" fehlen
# absichtlich — „s" ist im NMR die Multiplizität Singulett.
UNITS = ("Hz", "kHz", "MHz", "ppm", "K", "°C", "nm", "cm", "mm", "mg", "µg",
         "g", "mL", "µL", "mmol", "µmol", "mol", "equiv", "eq", "h")
# µ kommt in zwei Formen vor: als Mikrozeichen (U+00B5 — AltGr+M und die
# Einheiten der Sonderzeichenpalette) und als griechisches My (U+03BC).
# Beide bekommen das geschützte Leerzeichen.
_UNIT_SPACE = re.compile(r"(\d)\s+(" + "|".join(re.escape(u).replace("µ", "[µμ]")
                                              for u in UNITS) + r")(?![A-Za-z])")

_CM_MINUS = re.compile(r"cm\s*([-−–]\s*1)")
# Der Bindestrich muss maskiert sein: „[+-−]" wäre ein Zeichenbereich von
# „+" bis „−" und träfe unter anderem den Doppelpunkt.
_CHARGE = re.compile(r"\]\s*([+\-−]\d?|\d[+\-−])")
_DEUTERATED = re.compile(r"-\s*d\s*(\d+)")
_SYMBOL_INDEX = re.compile(r"([A-Z][a-z]?)(\d+)")
_ITALIC_J = re.compile(r"(?<![A-Za-z])J(?![A-Za-z])")
_SP_HYBRID = re.compile(r"sp(\d)")

# Felder, die keine Zuordnung sind: reine Integrale („4H"), Multiplizitäten
# („s", „dd") und alles mit einem Gleichheitszeichen („J = 7.5 Hz").
_INTEGRAL = re.compile(r"^\d+\s*[A-Z][a-z]?$")
_MULTIPLICITY = re.compile(r"^(br\s*)?[a-z]{1,4}$")


# ---------- Notizen mit eigener Formatierung ----------

class _RunParser(HTMLParser):
    """Wandelt das bereinigte Notiz-HTML (nur b/i/sup/sub/br) in Textstücke."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.runs: list[Run] = []
        self.open: list[str] = []

    def _emit(self, text: str) -> None:
        if not text:
            return
        vert = "sup" if "sup" in self.open else "sub" if "sub" in self.open else None
        self.runs.append(Run(text, bold="b" in self.open, italic="i" in self.open,
                             vert=vert))

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == "br":
            self._emit("\n")
        elif tag in ("b", "i", "sup", "sub"):
            self.open.append(tag)

    def handle_startendtag(self, tag, attrs):
        if tag.lower() == "br":
            self._emit("\n")

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in self.open:
            self.open.remove(tag)

    def handle_data(self, data):
        self._emit(data)


def from_html(html: str) -> list[Run]:
    """Formatierte Notiz unverändert übernehmen."""
    p = _RunParser()
    p.feed(html)
    p.close()
    return [r for r in p.runs if r.text]


# ---------- Bausteine ----------

def _merge(runs: list[Run]) -> list[Run]:
    """Benachbarte Stücke gleicher Auszeichnung zusammenfassen — das hält das
    erzeugte XML lesbar und Word setzt sauberer um."""
    out: list[Run] = []
    for r in runs:
        if not r.text:
            continue
        last = out[-1] if out else None
        if (last and last.bold == r.bold and last.italic == r.italic
                and last.vert == r.vert and last.color == r.color):
            last.text += r.text
        else:
            out.append(Run(r.text, r.bold, r.italic, r.vert, r.color))
    return out


def _split_top_level(s: str, sep: str) -> list[str]:
    """Teilt an `sep`, aber nur außerhalb von Klammern."""
    parts, depth, start = [], 0, 0
    for i, ch in enumerate(s):
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth = max(0, depth - 1)
        elif ch == sep and depth == 0:
            parts.append(s[start:i])
            start = i + 1
    parts.append(s[start:])
    return parts


def _groups(s: str):
    """Zerlegt in Text und Klammergruppen der obersten Ebene:
    ergibt Paare (ist_gruppe, inhalt) — beim Text ohne, bei der Gruppe ohne
    die Klammern selbst."""
    out, depth, start = [], 0, 0
    for i, ch in enumerate(s):
        if ch == "(":
            if depth == 0:
                out.append((False, s[start:i]))
                start = i + 1
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                out.append((True, s[start:i]))
                start = i + 1
            depth = max(0, depth)
    out.append((False, s[start:]))
    return [(g, t) for g, t in out if t or g]


def _plain(text: str, *, italic_j: bool = False) -> list[Run]:
    """Formeln, Ladungen und Einheiten setzen — ohne Zuordnungsregeln."""
    text = _UNIT_SPACE.sub(rf"\1{NBSP}\2", text)
    out: list[Run] = []
    buf: list[str] = []
    i, n = 0, len(text)

    def flush() -> None:
        if buf:
            out.append(Run("".join(buf)))
            buf.clear()

    while i < n:
        m = _CM_MINUS.match(text, i)
        if m:
            buf.append("cm")
            flush()
            out.append(Run(m.group(1).replace(" ", ""), vert="sup"))
            i = m.end()
            continue
        m = _CHARGE.match(text, i)
        if m:
            buf.append("]")
            flush()
            out.append(Run(m.group(1).replace(" ", ""), vert="sup"))
            i = m.end()
            continue
        m = _DEUTERATED.match(text, i)
        if m:
            buf.append("-")
            flush()
            out.append(Run("d", italic=True))
            out.append(Run(m.group(1), vert="sub"))
            i = m.end()
            continue
        m = _SYMBOL_INDEX.match(text, i)
        if m and m.group(1) in ELEMENTS:
            buf.append(m.group(1))
            flush()
            out.append(Run(m.group(2), vert="sub"))
            i = m.end()
            continue
        if italic_j:
            m = _ITALIC_J.match(text, i)
            if m:
                flush()
                out.append(Run("J", italic=True))
                i = m.end()
                continue
        buf.append(text[i])
        i += 1
    flush()
    return out


def _assignment(text: str, nucleus: str) -> list[Run]:
    """Zuordnung setzen: beobachteter Kern kursiv, Indexziffern und das „q"
    quartärer Kohlenstoffe tief, die Hybridisierung in „sp3" hoch."""
    out: list[Run] = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        m = _SP_HYBRID.match(text, i)
        if m:
            out.append(Run("sp"))
            out.append(Run(m.group(1), vert="sup"))
            i = m.end()
            continue
        if ch.isupper():
            symbol = ch
            nxt = text[i + 1] if i + 1 < n else ""
            # „Cq" ist kein Elementsymbol, sondern C mit tiefgestelltem q
            if nxt.islower() and not (ch in "CH" and nxt == "q"):
                symbol += nxt
            out.append(Run(symbol, italic=(symbol == nucleus)))
            i += len(symbol)
            j = i
            while j < n and (text[j].isdigit() or (text[j] == "q" and symbol in "CH")):
                j += 1
            if j > i and symbol in ELEMENTS:
                out.append(Run(text[i:j], vert="sub"))
                i = j
            continue
        out.append(Run(ch))
        i += 1
    return out


def _is_assignment(field: str, nucleus: str) -> bool:
    f = field.strip()
    if not f or "=" in f:
        return False
    if _INTEGRAL.match(f) or _MULTIPLICITY.match(f):
        return False
    return nucleus in f


def _signals(text: str, nucleus: str) -> list[Run]:
    """Signalliste: in jeder Klammergruppe ist das letzte Feld die Zuordnung."""
    out: list[Run] = []
    for is_group, content in _groups(text):
        if not is_group:
            out += _plain(content, italic_j=True)
            continue
        out.append(Run("("))
        fields = _split_top_level(content, ",")
        for k, field in enumerate(fields):
            if k:
                out.append(Run(","))
            last = k == len(fields) - 1
            if last and _is_assignment(field, nucleus):
                lead = len(field) - len(field.lstrip())
                out.append(Run(field[:lead]))
                out += _assignment(field.strip(), nucleus)
                out.append(Run(field[lead + len(field.strip()):]))
            else:
                out += _plain(field, italic_j=True)
        out.append(Run(")"))
    return out


# ---------- Einstiegspunkte ----------

def is_nmr_label(label: str | None) -> bool:
    """Meint diese Eintragsbezeichnung eine NMR-Messung? („19F NMR" ja,
    „Elementaranalyse" nein.)"""
    return bool(NMR_LABEL.match(label or ""))


def typeset(label: str | None) -> str:
    """Bezeichnung für die Anzeige in der App: Massenzahlen als hochgestellte
    Ziffern („19F NMR" → „¹⁹F NMR", „31P{1H} NMR" → „³¹P{¹H} NMR"). Gespeichert
    bleibt die einfache Schreibweise — daran hängen Export und Suche; einzig
    die Anzeige wird gesetzt, und nur bei NMR-Bezeichnungen (eine Probennummer
    wie „JA294" bleibt unangetastet)."""
    text = label or ""
    if not is_nmr_label(text):
        return text
    return _MASS_NUMBER.sub(lambda m: m.group(1).translate(_SUPERSCRIPT), text)


def head(text: str, *, bold: bool = True) -> list[Run]:
    """Eine Methodenbezeichnung setzen: Massenzahlen hoch, Rest wie geschrieben
    („13C{1H} NMR" → ¹³C{¹H} NMR, „1H,15N HMBC" → ¹H,¹⁵N HMBC)."""
    out: list[Run] = []
    pos = 0
    for m in _MASS_NUMBER.finditer(text):
        out.append(Run(text[pos:m.start()], bold=bold))
        out.append(Run(m.group(1), bold=bold, vert="sup"))
        pos = m.end()
    out.append(Run(text[pos:], bold=bold))
    return _merge(out)


def nmr(text: str) -> list[Run]:
    """Ein NMR-Datensatz: fetter Kopf, gesetzte Bedingungen, gesetzte Signale."""
    match = NMR_HEAD.match(text)
    if not match:
        return _merge(_plain(text, italic_j=True))
    nucleus = match.group(2)
    out = head(match.group(0))

    rest = text[match.end():]
    # Vor dem ersten Gleichheitszeichen stehen die Messbedingungen, danach die
    # Signale — nur dort gelten die Zuordnungsregeln.
    parts = _split_top_level(rest, "=")
    if len(parts) > 1:
        out += _plain(parts[0])
        out.append(Run("="))
        out += _signals("=".join(parts[1:]), nucleus)
    else:
        out += _plain(rest)
    return _merge(out)


def plain(text: str) -> list[Run]:
    """Beliebiger Analytiktext ohne Zuordnungsregeln (IR, MS, Sonstiges)."""
    return _merge(_plain(text, italic_j=True))


def procedure(text: str, html: str | None = None) -> list[Run]:
    """Durchführungstext: Formeln (CH₂Cl₂), geschützte Leerzeichen zwischen
    Zahl und Einheit (2.00 g, 12 h, 80 °C). Kein kursives J — ein einzelnes
    „J" ist im Fließtext keine Kopplungskonstante.

    Anders als bei den Analytiknotizen wird hier auch dann gesetzt, wenn im
    Feld schon von Hand formatiert wurde: die Durchführung ist Fließtext mit
    vielen Zahlen und Formeln, und niemand stellt die Indizes von Hand. Was
    von Hand hoch- oder tiefgestellt wurde, bleibt unangetastet; fett und
    kursiv bleiben ohnehin erhalten.
    """
    out: list[Run] = []
    for r in from_html(html) if html else [Run(text or "")]:
        if r.vert:
            out.append(r)
            continue
        for part in _plain(r.text, italic_j=False):
            out.append(Run(part.text, bold=r.bold or part.bold,
                           italic=r.italic or part.italic, vert=part.vert))
    return _merge(out)


def note(text: str, html: str | None, kind: str) -> list[Run]:
    """Notiz als Textstücke — eigene Formatierung gewinnt, sonst wird nach
    den Regeln der Vorlage gesetzt."""
    if kind == "procedure":
        return procedure(text, html)
    if html:
        return _merge(from_html(html))
    text = text or ""
    if kind in ("nmr_1h", "nmr_13c", "nmr_2d") or NMR_HEAD.match(text):
        return nmr(text)
    return plain(text)


def bold(text: str) -> list[Run]:
    """Fette Beschriftung („m. p.") mit hochgestellten Ladungen/Exponenten."""
    return _merge([Run(r.text, bold=True, italic=r.italic, vert=r.vert)
                   for r in _plain(text)])


def conditions(text: str) -> dict[str, str]:
    """Messbedingungen aus einem NMR-Kopf lesen: Frequenz, Lösungsmittel,
    Temperatur. Fehlt etwas, fehlt der Schlüssel — die Bildunterschrift lässt
    ihn dann weg, statt etwas zu erfinden."""
    out: dict[str, str] = {}
    match = NMR_HEAD.match(text or "")
    rest = text[match.end():] if match else (text or "")
    group = next((c for g, c in _groups(rest) if g), "")
    if m := re.search(r"(\d+(?:\.\d+)?)\s*MHz", group):
        out["frequency"] = m.group(1)
    if m := re.search(r"(\d+)\s*K\b", group):
        out["temperature"] = m.group(1)
    for field in _split_top_level(group, ","):
        # Frequenz und Temperatur herausnehmen — in der Praxis steht die
        # Temperatur schon mal ohne Komma hinter dem Lösungsmittel
        # („CDCl3 298 K"), das ist dann trotzdem eine Lösungsmittelangabe.
        f = re.sub(r"\d+(?:\.\d+)?\s*MHz|\d+\s*K\b", "", field).strip(" ,;")
        if f and not f[0].isdigit():
            out["solvent"] = f
            break
    return out
