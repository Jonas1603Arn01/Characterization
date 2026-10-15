"""Formatierte Notizen: fett, kursiv, hoch- und tiefgestellt.

Der Browser liefert das Notizfeld als HTML (contenteditable). Hier wird es
auf eine feste Handvoll Tags reduziert — alles andere (Skripte, Styles,
Fremd-Markup aus Word) fliegt raus, der Text bleibt. Aus dem bereinigten
HTML wird zusätzlich der Klartext abgeleitet, der weiterhin in
entry_notes.text steht: für Export (Notizen.txt/Info.txt), ältere
App-Versionen und alles, was kein HTML versteht. Hoch-/Tiefgestelltes wird
dabei, wo Unicode es hergibt, in echte Hoch-/Tiefstellungszeichen
übersetzt („CDCl₃", „¹³C") — so bleibt die Information auch im Klartext.
"""
import html
import re
from html.parser import HTMLParser

ALLOWED_TAGS = {"b", "i", "sup", "sub", "br"}
# Gebräuchliche Synonyme, die Browser/Word erzeugen, auf die erlaubte Form bringen
TAG_ALIASES = {"strong": "b", "em": "i"}

# Minuszeichen (U+2212) und Halbgeviertstrich zählen wie der Bindestrich —
# Word und Webseiten setzen „cm⁻¹" gern mit einem davon. Gleiche Tabelle im
# Frontend (app.js, SUP_CHARS/SUB_CHARS) für die einfachen Eingabefelder.
SUPERSCRIPT = str.maketrans("0123456789+-−–=()n", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁻⁻⁼⁽⁾ⁿ")
SUBSCRIPT = str.maketrans("0123456789+-−–=()aeoxhklmnpst",
                          "₀₁₂₃₄₅₆₇₈₉₊₋₋₋₌₍₎ₐₑₒₓₕₖₗₘₙₚₛₜ")


class _Sanitizer(HTMLParser):
    """Baut das HTML aus erlaubten Tags neu auf; unbekannte Tags werden
    entfernt (ihr Text bleibt), Attribute grundsätzlich verworfen. Offene
    Tags werden am Ende geschlossen, damit das Ergebnis wohlgeformt ist."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.open: list[str] = []
        self.text: list[str] = []  # Klartext-Ableitung, parallel aufgebaut
        self.skip = 0  # innerhalb von <script>/<style>: Inhalt komplett verwerfen

    def _tag(self, name: str) -> str | None:
        name = TAG_ALIASES.get(name.lower(), name.lower())
        return name if name in ALLOWED_TAGS else None

    def handle_starttag(self, tag, attrs):
        if tag.lower() in ("script", "style"):
            self.skip += 1
            return
        name = self._tag(tag)
        if name is None:
            # Blockelemente aus Fremd-Markup als Zeilenumbruch behandeln
            if tag.lower() in ("div", "p", "li", "tr") and self.out and self.out[-1] != "<br>":
                self._br()
            return
        if name == "br":
            self._br()
            return
        if name in self.open:
            return  # doppelt verschachtelt (<b><b>) -> ignorieren
        self.open.append(name)
        self.out.append(f"<{name}>")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag.lower() in ("script", "style"):
            self.skip = max(0, self.skip - 1)
            return
        name = self._tag(tag)
        if name is None or name == "br" or name not in self.open:
            return
        # Bis zum passenden Tag schließen (falsch verschachtelt -> trotzdem sauber)
        while self.open:
            top = self.open.pop()
            self.out.append(f"</{top}>")
            if top == name:
                break

    def handle_data(self, data):
        if not data or self.skip:
            return
        self.out.append(html.escape(data, quote=False))
        if "sup" in self.open:
            data = data.translate(SUPERSCRIPT)
        elif "sub" in self.open:
            data = data.translate(SUBSCRIPT)
        self.text.append(data)

    def _br(self) -> None:
        self.out.append("<br>")
        self.text.append("\n")

    def close(self):
        super().close()
        while self.open:
            self.out.append(f"</{self.open.pop()}>")


def sanitize(raw: str | None) -> str:
    """Bereinigtes HTML (nur b, i, sup, sub, br; keine Attribute). Leere
    Formatierungen und überzählige Zeilenumbrüche am Ende werden entfernt."""
    return _parse(raw)[0]


def to_text(raw: str | None) -> str:
    """Klartext aus (rohem oder bereinigtem) HTML — Zeilenumbrüche für <br>,
    Unicode-Hoch-/Tiefstellung für <sup>/<sub>."""
    return _parse(raw)[1]


def _parse(raw: str | None) -> tuple[str, str]:
    if not raw:
        return "", ""
    # Zeilenumbrüche zählen wie <br>: das Notizfeld (white-space: pre-wrap)
    # legt eingefügten Text mit echten \n ab, Enter erzeugt <br>.
    raw = raw.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")
    p = _Sanitizer()
    p.feed(raw)
    p.close()
    out = "".join(p.out)
    # Leere Tags (<b></b>) und Umbrüche am Ende, die contenteditable gerne anhängt
    for tag in ("b", "i", "sup", "sub"):
        while f"<{tag}></{tag}>" in out:
            out = out.replace(f"<{tag}></{tag}>", "")
    while out.endswith("<br>"):
        out = out[:-4]
    text = "".join(p.text).rstrip("\n")
    return out, text


def text_to_html(text: str | None) -> str:
    """Klartext (alte Notizen ohne HTML) in die HTML-Form bringen."""
    if not text:
        return ""
    return html.escape(text, quote=False).replace("\r\n", "\n").replace("\n", "<br>")


def is_plain(html_value: str) -> bool:
    """True, wenn das bereinigte HTML keine Formatierung enthält (dann wird
    die Notiz weiterhin als reiner Text gespeichert)."""
    return "<" not in html_value.replace("<br>", "")


def field(raw: str | None, single_line: bool = False) -> tuple[str | None, str | None]:
    """Formatierbares Molekülfeld (Name, Zitat, Probenvermerk) als
    (Klartext, HTML). Leer -> (None, None); ohne Formatierung ist das HTML
    None, das Feld bleibt dann ein reines Textfeld wie bisher. Einzeilig
    (Molekülname) werden Zeilenumbrüche zu Leerzeichen."""
    clean = sanitize(raw)
    if single_line:
        clean = re.sub(r"\s*<br>\s*", " ", clean)
    text = to_text(clean).strip()
    if not text:
        return None, None
    return text, None if is_plain(clean) else clean.strip()
