"""Katalog der NMR-Kerne, die als eigener Eintrag dazukommen können.

¹H, ¹³C und 2D-NMR sind feste Datentypen (datatypes.py). Jeder weitere Kern
— ¹⁹F, ³¹P, ¹¹B … — wird als eigener Eintrag angelegt. Dass so ein Eintrag im
Word-Dokument wie ¹H und ¹³C gesetzt wird, hängt allein an seiner
Bezeichnung („19F NMR", siehe chem_text.is_nmr_label). Damit man diese
Bezeichnung nicht von Hand richtig treffen muss, steht hier, was die App zur
Auswahl anbietet:

  mass       — Massenzahl, symbol — Elementsymbol
  name       — Elementname für die Auswahlliste (zweisprachig)
  ratio      — Messfrequenz in Prozent der ¹H-Frequenz (IUPAC Ξ). Daraus wird
               die Frequenz der Kopfzeile berechnet: 500.1 MHz ¹H → 471 MHz ¹⁹F
  digits     — übliche Nachkommastellen der Verschiebungen; stellt den
               Rundungsknopf des Notizfelds ein (bei ¹³C ist es 1)
  decoupled  — wird der Kern üblicherweise ¹H-entkoppelt gemessen? Dann ist
               das Häkchen „{¹H}" beim Anlegen vorbelegt

Gespeichert wird immer die einfache Schreibweise („31P{1H} NMR") — daran
hängen die Erkennung im Export und die Suche. Hochgestellt wird erst bei der
Anzeige (chem_text.typeset) und im Word-Dokument (chem_text.head).
"""
import re

# Kern, Elementname (de/en), Ξ in %, Nachkommastellen, ¹H-entkoppelt üblich
_CATALOG = [
    (19, "F", "Fluor", "Fluorine", 94.094011, 2, False),
    (31, "P", "Phosphor", "Phosphorus", 40.480742, 1, True),
    (11, "B", "Bor", "Boron", 32.083974, 1, False),
    (29, "Si", "Silicium", "Silicon", 19.867187, 1, True),
    (15, "N", "Stickstoff", "Nitrogen", 10.136767, 1, True),
    (7, "Li", "Lithium", "Lithium", 38.863797, 2, False),
    (2, "H", "Deuterium", "Deuterium", 15.350609, 2, False),
    (27, "Al", "Aluminium", "Aluminium", 26.056859, 1, False),
    (77, "Se", "Selen", "Selenium", 19.071513, 1, True),
    (119, "Sn", "Zinn", "Tin", 37.290632, 1, True),
    (125, "Te", "Tellur", "Tellurium", 31.549769, 1, True),
    (195, "Pt", "Platin", "Platinum", 21.496784, 0, False),
    (103, "Rh", "Rhodium", "Rhodium", 3.186447, 0, True),
    (51, "V", "Vanadium", "Vanadium", 26.302948, 0, False),
    (95, "Mo", "Molybdän", "Molybdenum", 6.516926, 0, False),
    (113, "Cd", "Cadmium", "Cadmium", 22.193175, 1, True),
    (199, "Hg", "Quecksilber", "Mercury", 17.910822, 1, True),
    (205, "Tl", "Thallium", "Thallium", 57.683838, 0, False),
    (207, "Pb", "Blei", "Lead", 20.920599, 1, True),
    (23, "Na", "Natrium", "Sodium", 26.451900, 1, False),
    (17, "O", "Sauerstoff", "Oxygen", 13.556457, 1, False),
    (35, "Cl", "Chlor", "Chlorine", 9.797909, 1, False),
]

# ¹H und ¹³C stehen nicht zur Auswahl (feste Datentypen), werden für die
# Frequenzrechnung aber gebraucht: aus „126 MHz ¹³C" folgt „501 MHz ¹H".
_FIXED = [(1, "H", 100.0), (13, "C", 25.145020)]

NUCLEI = [
    {"mass": mass, "symbol": symbol, "code": f"{mass}{symbol} NMR",
     "name": {"de": de, "en": en}, "ratio": ratio, "digits": digits,
     "decoupled": decoupled}
    for mass, symbol, de, en, ratio, digits, decoupled in _CATALOG
]

# Massenzahl+Symbol -> Ξ, für alle Kerne inklusive ¹H und ¹³C
RATIOS = {(mass, symbol): ratio for mass, symbol, ratio in _FIXED}
RATIOS.update({(n["mass"], n["symbol"]): n["ratio"] for n in NUCLEI})

# Ein Gerät, das „500 MHz" heißt, misst ¹H tatsächlich bei rund 500.13 MHz —
# die runde Zahl ist der Name des Magneten, nicht die Messfrequenz. Geschrieben
# wird in der Kopfzeile aber die runde Zahl, und daraus muss die Frequenz der
# anderen Kerne folgen: ohne diesen Versatz käme für ¹⁹F 470 statt der üblichen
# 471 MHz heraus, für ³¹P 202 statt 202. Liegt die zurückgerechnete
# ¹H-Frequenz nahe genug an einer Gerätebezeichnung (Vielfaches von 50 MHz),
# wird deshalb mit deren tatsächlicher Frequenz weitergerechnet.
_NOMINAL_STEP = 50
_NOMINAL_OFFSET = 0.13

# Erster Kern einer Bezeichnung: „31P{1H} NMR" -> (31, "P"),
# „1H,15N HMBC" -> (1, "H")
_FIRST_NUCLEUS = re.compile(r"^\s*(\d{1,3})\s*([A-Z][a-z]?)")

# Fester Datentyp -> Bezeichnung, mit der er im Dokument steht
TYPE_LABELS = {"nmr_1h": "1H NMR", "nmr_13c": "13C NMR"}


def label(mass: int, symbol: str, *, decoupled: bool = False) -> str:
    """Bezeichnung, wie sie gespeichert wird: „31P NMR" bzw. „31P{1H} NMR"."""
    return f"{mass}{symbol}{'{1H}' if decoupled else ''} NMR"


def nucleus_of(label_text: str | None) -> tuple[int, str] | None:
    """Welchen Kern meint diese Bezeichnung? („19F NMR" -> (19, "F"))"""
    match = _FIRST_NUCLEUS.match(label_text or "")
    return (int(match.group(1)), match.group(2)) if match else None


def find(label_text: str | None) -> dict | None:
    """Katalogeintrag zu einer Bezeichnung — None, wenn der Kern nicht im
    Katalog steht (dann bleibt es bei den allgemeinen Vorgaben)."""
    key = nucleus_of(label_text)
    return next((n for n in NUCLEI if (n["mass"], n["symbol"]) == key), None)


def frequency(label_text: str | None, proton_mhz: float) -> str | None:
    """Messfrequenz dieses Kerns an einem Gerät mit `proton_mhz` ¹H-Frequenz,
    auf ganze MHz gerundet — so, wie sie in der Kopfzeile steht. Unbekannter
    Kern: None, dann bleibt die Frequenz in der Kopfzeile weg."""
    key = nucleus_of(label_text)
    ratio = RATIOS.get(key) if key else None
    return None if ratio is None else f"{round(proton_mhz * ratio / 100):g}"


def proton_frequency(label_text: str | None, measured_mhz: str | float) -> float | None:
    """Rückrechnung: Aus „126 MHz" an einem ¹³C-Datensatz folgt ein Gerät mit
    rund 501 MHz ¹H-Frequenz. Damit lässt sich die Frequenz jedes anderen
    Kerns angeben, auch wenn kein ¹H-Datensatz erfasst ist."""
    key = nucleus_of(label_text)
    ratio = RATIOS.get(key) if key else None
    try:
        measured = float(measured_mhz)
    except (TypeError, ValueError):
        return None
    if not ratio:
        return None
    # Die Angabe ist auf ganze MHz gerundet; hochgerechnet auf ¹H wird daraus
    # eine Unschärfe von einer halben Stelle geteilt durch das Kernverhältnis
    # („126 MHz" am ¹³C meint 125.5 bis 126.5 MHz, also 499 bis 503 MHz ¹H).
    return _nominal(measured * 100 / ratio, 50 / ratio + _NOMINAL_OFFSET)


def _nominal(proton_mhz: float, tolerance: float) -> float:
    """Zurückgerechnete ¹H-Frequenz auf die Gerätebezeichnung einrasten:
    500.0 (aus „500 MHz") und 501.1 (aus „126 MHz" am ¹³C) meinen beide das
    500er-Gerät und damit 500.13 MHz. Eine Frequenz, die zu keiner
    Gerätebezeichnung passt, bleibt, wie sie ist."""
    nominal = round(proton_mhz / _NOMINAL_STEP) * _NOMINAL_STEP
    if nominal and abs(proton_mhz - nominal) <= tolerance:
        return nominal + _NOMINAL_OFFSET
    return proton_mhz
