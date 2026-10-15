from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    # Anzeige-Reihenfolge (per Drag & Drop änderbar); Gleichstand -> Name
    sort_order: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    molecules: Mapped[list["Molecule"]] = relationship(
        back_populates="project", cascade="all, delete-orphan",
        order_by="Molecule.sort_order, Molecule.id",
    )


class Molecule(Base):
    __tablename__ = "molecules"
    __table_args__ = (UniqueConstraint("project_id", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    name: Mapped[str] = mapped_column(String)
    # Formatierte Fassungen (kursiv/fett/hoch-/tiefgestellt) als bereinigtes
    # HTML, siehe richtext.field; None = ungeformt. Die Klartextspalte daneben
    # bleibt immer gefüllt (Ordnernamen, Info.txt, Suche, Namensgleichheit).
    name_html: Mapped[str | None] = mapped_column(String, default=None)
    smiles: Mapped[str | None] = mapped_column(String, default=None)
    formula: Mapped[str | None] = mapped_column(String, default=None)
    exact_mass: Mapped[float | None] = mapped_column(default=None)
    image_path: Mapped[str | None] = mapped_column(String, default=None)
    scheme_path: Mapped[str | None] = mapped_column(String, default=None)  # Reaktionsschema
    equation_path: Mapped[str | None] = mapped_column(String, default=None)  # Reaktionsgleichung
    # Beim Einfügen aus ChemDraw mitgespeicherte Originaldatei (.cdx) je Bild-Slot —
    # damit bleibt die Struktur in ChemDraw weiterbearbeitbar
    image_cdx_path: Mapped[str | None] = mapped_column(String, default=None)
    scheme_cdx_path: Mapped[str | None] = mapped_column(String, default=None)
    equation_cdx_path: Mapped[str | None] = mapped_column(String, default=None)
    literature_known: Mapped[bool] = mapped_column(default=False)
    doi: Mapped[str | None] = mapped_column(String, default=None)
    citation: Mapped[str | None] = mapped_column(String, default=None)  # Literaturzitat (Freitext)
    citation_html: Mapped[str | None] = mapped_column(String, default=None)
    # Verlinkte Supporting Information (PDF/Word) der Literaturstelle —
    # extern verlinkt wie Eintragsdateien (UNC-Speicherform, s. paths.py)
    si_path: Mapped[str | None] = mapped_column(String, default=None)
    physical_state: Mapped[str | None] = mapped_column(String, default=None)  # "solid" | "oil"
    color: Mapped[str | None] = mapped_column(String, default=None)
    consistency: Mapped[str | None] = mapped_column(String, default=None)
    # Restsubstanz vorhanden? Unvollständige Moleküle werden dann gelb statt
    # rot markiert (Messung nachholbar); dazu Probennummer + Vermerk
    sample_available: Mapped[bool] = mapped_column(default=False)
    sample_number: Mapped[str | None] = mapped_column(String, default=None)
    sample_comment: Mapped[str | None] = mapped_column(String, default=None)
    sample_comment_html: Mapped[str | None] = mapped_column(String, default=None)
    # Anzeige-Reihenfolge innerhalb des Projekts (per Drag & Drop änderbar)
    sort_order: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    project: Mapped[Project] = relationship(back_populates="molecules")
    entries: Mapped[list["DataEntry"]] = relationship(
        back_populates="molecule", cascade="all, delete-orphan", order_by="DataEntry.id"
    )


class DataEntry(Base):
    """Ein Datentyp-Eintrag eines Moleküls.

    Drei effektive Zustände: required=False -> "n. z.";
    required=True -> status "present" oder "missing".
    """

    __tablename__ = "data_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    molecule_id: Mapped[int] = mapped_column(ForeignKey("molecules.id"))
    type_code: Mapped[str] = mapped_column(String)
    custom_label: Mapped[str | None] = mapped_column(String, default=None)  # nur "other"
    required: Mapped[bool] = mapped_column(default=True)
    status: Mapped[str] = mapped_column(String, default="missing")  # missing | present
    folder_path: Mapped[str | None] = mapped_column(String, default=None)
    file_path: Mapped[str | None] = mapped_column(String, default=None)
    # Drittes festes Feld (nur NMR): das exportierte Spektrum als SVG
    svg_path: Mapped[str | None] = mapped_column(String, default=None)
    # Viertes festes Feld (nur 2D-NMR): zweites Spektrum — svg = HSQC, svg2 = HMBC
    svg2_path: Mapped[str | None] = mapped_column(String, default=None)
    # Eigene Beschriftung der festen Felder; None -> Standard-Label des Datentyps
    folder_label: Mapped[str | None] = mapped_column(String, default=None)
    file_label: Mapped[str | None] = mapped_column(String, default=None)
    svg_label: Mapped[str | None] = mapped_column(String, default=None)
    svg2_label: Mapped[str | None] = mapped_column(String, default=None)
    text_note: Mapped[str | None] = mapped_column(String, default=None)
    mp_value: Mapped[float | None] = mapped_column(default=None)  # Schmelzpunkt in °C
    # Nur "other": kommt dieser Eintrag ins Word-Dokument? Feste Datentypen
    # sind immer dabei; bei eigenen Einträgen entscheidet das Häkchen, das
    # beim Anlegen aus der Bezeichnung vorbelegt wird (NMR ja, sonst nein).
    in_document: Mapped[bool] = mapped_column(default=False)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    molecule: Mapped[Molecule] = relationship(back_populates="entries")
    files: Mapped[list["EntryFile"]] = relationship(
        back_populates="entry", cascade="all, delete-orphan", order_by="EntryFile.id"
    )
    notes: Mapped[list["EntryNote"]] = relationship(
        back_populates="entry", cascade="all, delete-orphan", order_by="EntryNote.id"
    )

    @property
    def effective_status(self) -> str:
        return self.status if self.required else "na"


class EntryFile(Base):
    """Zusätzliche Datei-Referenz eines Eintrags (beliebig viele)."""

    __tablename__ = "entry_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    entry_id: Mapped[int] = mapped_column(ForeignKey("data_entries.id"))
    path: Mapped[str] = mapped_column(String)
    label: Mapped[str | None] = mapped_column(String, default=None)  # frei benennbar
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    entry: Mapped[DataEntry] = relationship(back_populates="files")


class EntryNote(Base):
    """Freitext-Notiz eines Eintrags (beliebig viele, einzeln löschbar)."""

    __tablename__ = "entry_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    entry_id: Mapped[int] = mapped_column(ForeignKey("data_entries.id"))
    text: Mapped[str] = mapped_column(String, default="")
    # Formatierte Fassung (fett/kursiv/hoch-/tiefgestellt) als bereinigtes HTML,
    # siehe richtext.py; None = reine Textnotiz. `text` bleibt immer der
    # Klartext dazu (Export, ältere App-Versionen).
    html: Mapped[str | None] = mapped_column(String, default=None)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    entry: Mapped[DataEntry] = relationship(back_populates="notes")


class LinkId(Base):
    """Dateikennung zu einem verlinkten Pfad (siehe app/relink.py).

    Dateisysteme geben jeder Datei eine Kennung, die das Umbenennen überlebt
    (Windows: Datenträger + Datei-Index, sonst Gerät + Inode). Damit findet
    die App eine umbenannte Datei in ihrem Ordner wieder, statt den Verweis
    als tot zu melden. Größe und Änderungszeit stehen daneben, um zu
    erkennen, wann die Kennung neu zu ermitteln ist.
    """

    __tablename__ = "link_ids"

    path: Mapped[str] = mapped_column(String, primary_key=True)  # Speicherform (UNC)
    file_id: Mapped[str] = mapped_column(String, index=True)  # "<Datenträger>:<Index>"
    size: Mapped[int] = mapped_column(default=0)
    mtime_ns: Mapped[int] = mapped_column(default=0)
    is_dir: Mapped[bool] = mapped_column(default=False)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)
