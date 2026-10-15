"""Katalog der Datentypen pro Molekül.

`fields` beschreibt die festen Eingabefelder des Typs (zusätzliche Dateien
und Notizen sind bei jedem Typ beliebig viele möglich):
  key     — folder | file | svg | svg2 | value (Spalte im DataEntry)
  filter  — Dateifilter für den nativen Dialog (nur key=file/svg)
  suggest — beim Befüllen dieses Felds schlägt das UI vor, den Status
            auf „vorhanden“ zu stellen (bei NMR zählt die MNova-Datei,
            der Mess-Ordner nicht)
`multi` erlaubt mehrere Instanzen pro Molekül (nur "Sonstiges").
`note` beschriftet das Notizfeld abweichend und blendet es dauerhaft ein
(`note.always`) — bei der Versuchsvorschrift ist das Notizfeld der
Durchführungstext, der so ohne Umweg über „+ Notiz" bereitsteht und
formatiert ins Word-Dokument wandert.
Labels sind zweisprachig (de/en); das Frontend wählt per Sprachumschalter.
"""

# Die drei festen Felder jeder NMR-Messung. Sie gelten auch für zusätzliche
# Kerne, die als eigener Eintrag angelegt werden („19F NMR", siehe nuclei.py) —
# so bekommt ein ¹⁹F-Eintrag dieselben Felder wie ¹H und ¹³C, statt nur des
# allgemeinen „Datei"-Felds von „Sonstiges".
NMR_FIELDS = [
    {"key": "folder", "label": {"de": "Mess-Ordner", "en": "Data folder"}},
    {"key": "file", "label": {"de": "MNova-Datei", "en": "MNova file"}, "filter": "mnova", "suggest": True},
    {"key": "svg", "label": {"de": "SVG-Spektrum", "en": "SVG spectrum"}, "filter": "svg"},
]

# 2D-NMR: statt eines SVG-Spektrums je eins für HSQC und HMBC
NMR_2D_FIELDS = NMR_FIELDS[:2] + [
    {"key": "svg", "label": {"de": "HSQC-Spektrum", "en": "HSQC spectrum"}, "filter": "svg"},
    {"key": "svg2", "label": {"de": "HMBC-Spektrum", "en": "HMBC spectrum"}, "filter": "svg"},
]

DATA_TYPES = [
    {"code": "procedure", "label": {"de": "Versuchsvorschrift", "en": "Procedure"}, "multi": False,
     "note": {"always": True,
              "label": {"de": "Durchführung", "en": "Procedure"},
              "placeholder": {
                  "de": "Durchführung — wandert formatiert ins Word-Dokument",
                  "en": "Procedure — carried into the Word document with its formatting"}},
     "fields": [
        {"key": "file", "label": {"de": "Word-Datei", "en": "Word file"}, "filter": "word", "suggest": True},
    ]},
    {"code": "nmr_1h", "label": {"de": "¹H-NMR", "en": "¹H NMR"}, "multi": False, "fields": NMR_FIELDS},
    {"code": "nmr_13c", "label": {"de": "¹³C-NMR", "en": "¹³C NMR"}, "multi": False, "fields": NMR_FIELDS},
    {"code": "nmr_2d", "label": {"de": "2D-NMR", "en": "2D NMR"}, "multi": False, "fields": NMR_2D_FIELDS},
    {"code": "ms", "label": {"de": "Massenspektrometrie", "en": "Mass spectrometry"}, "multi": False, "fields": [
        {"key": "file", "label": {"de": "Word-Datei", "en": "Word file"}, "filter": "word", "suggest": True},
    ]},
    {"code": "ir", "label": {"de": "IR-Spektrum", "en": "IR spectrum"}, "multi": False, "fields": [
        {"key": "file", "label": {"de": "PDF-Datei", "en": "PDF file"}, "filter": "pdf", "suggest": True},
    ]},
    {"code": "mp", "label": {"de": "Schmelzpunkt", "en": "Melting point"}, "multi": False, "fields": [
        {"key": "value", "label": {"de": "Schmelzpunkt (°C)", "en": "Melting point (°C)"}, "suggest": True},
    ]},
    {"code": "other", "label": {"de": "Sonstiges", "en": "Other"}, "multi": True, "fields": [
        {"key": "file", "label": {"de": "Datei", "en": "File"}, "filter": "any", "suggest": True},
    ]},
]

TYPE_CODES = {t["code"] for t in DATA_TYPES}
# TYPE_LABELS["de"]["nmr_1h"] -> "¹H-NMR"
TYPE_LABELS = {
    lang: {t["code"]: t["label"][lang] for t in DATA_TYPES} for lang in ("de", "en")
}
# Typen, die beim Anlegen eines Moleküls automatisch angelegt werden
DEFAULT_TYPES = [t["code"] for t in DATA_TYPES if not t["multi"]]
