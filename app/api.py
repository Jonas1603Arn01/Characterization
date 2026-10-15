import os
import re
import signal
import zlib
from datetime import datetime
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from . import chem_text, db, nuclei, osutil, paths, relink, richtext, updater
from .chem import compute_from_smiles
from .datatypes import DATA_TYPES, DEFAULT_TYPES, NMR_FIELDS
from .db import get_session
from .dialogs import DialogBusyError, open_dialog
from .models import DataEntry, EntryFile, EntryNote, Molecule, Project

router = APIRouter(prefix="/api")


def get_lang(x_lang: str = Header(default="en", alias="X-Lang")) -> str:
    return "de" if x_lang.lower().startswith("de") else "en"


def T(lang: str, de: str, en: str) -> str:
    return en if lang == "en" else de


def path_exists(p: str | None) -> bool | None:
    """None = kein Pfad gesetzt; sonst ob der Pfad (noch) existiert."""
    return paths.exists(p) if p else None


def image_abs(value: str | None) -> str | None:
    """Bild-/CDX-Verweis der DB als absoluter Pfad (App-eigene Bilder stehen
    nur mit Dateinamen in der DB, siehe db.image_file)."""
    p = db.image_file(value)
    return str(p) if p else None


def link_out(p: str | None) -> str | None:
    """Verlinkter Pfad in Anzeigeform (UNC -> lokaler Laufwerksbuchstabe)."""
    return paths.to_display(p) if p else None


def link_in(p: str | None) -> str | None:
    """Verlinkter Pfad in Speicherform (Netzlaufwerk -> UNC); leer -> None.

    Nebenbei merkt sich die App die Dateikennung dazu (im Hintergrund) —
    damit findet sie die Datei wieder, wenn sie später umbenannt wird."""
    p = (p or "").strip()
    stored = paths.to_portable(p) if p else None
    if stored:
        relink.remember(stored)
    return stored


def cdx_stale(image_path: str | None, cdx_path: str | None) -> bool:
    """True, wenn die mitgespeicherte ChemDraw-Datei neuer ist als das beim
    Einfügen abgelegte Bild — sie wurde in ChemDraw bearbeitet und gespeichert,
    das Bild ist veraltet. 1 s Toleranz, weil Bild und .cdx beim Einfügen
    unmittelbar nacheinander geschrieben werden. Erwartet absolute Pfade.

    Nimmt die Zeiten aus paths.stat, also aus derselben Abfrage, die schon
    die Existenz beantwortet hat — kein zusätzlicher Zugriff."""
    if not image_path or not cdx_path:
        return False
    bild, cdx = paths.stat(image_path), paths.stat(cdx_path)
    if bild is None or cdx is None:
        return False
    return cdx.st_mtime > bild.st_mtime + 1.0


def image_version(path: str | None) -> str | None:
    """Kennung des aktuellen Bildstands aus Dateiname, Größe und
    Änderungszeit — die Oberfläche hängt sie an die Bild-URL. Ein neues Bild
    bekommt damit eine neue URL; ein unverändertes behält seine und darf im
    Browser bleiben, statt bei jeder Änderung am Molekül (Farbe, DOI …) erneut
    vom Datenordner gelesen zu werden — die eingefügten ChemDraw-BMPs sind
    mehrere MB groß. Kommt aus paths.stat, also ohne zusätzlichen Zugriff."""
    st = paths.stat(path)
    if st is None:
        return None
    name = zlib.crc32(os.path.basename(path).encode("utf-8"))
    return f"{name:08x}-{st.st_size:x}-{st.st_mtime_ns:x}"


# ---------- Serialisierung ----------

def visible_entries(mol: Molecule) -> list[DataEntry]:
    """Bei einem Öl ist der Schmelzpunkt nicht anwendbar und wird ausgeblendet
    (der Eintrag bleibt in der DB, taucht bei Umschalten auf Feststoff wieder auf)."""
    hide_mp = mol.physical_state == "oil"
    return [e for e in mol.entries if not (hide_mp and e.type_code == "mp")]


def completeness(mol: Molecule) -> tuple[str, int, int]:
    """(Zustand, benötigt, davon vorhanden): complete = alle benötigten
    vorhanden, sonst incomplete; ohne benötigte Einträge: na. Rein aus den
    Einträgen bestimmt — greift bewusst auf keine Datei zu, damit das
    Dashboard ohne Netzzugriff auskommt."""
    required = [e for e in visible_entries(mol) if e.required]
    present = sum(1 for e in required if e.status == "present")
    if not required:
        state = "na"
    elif present < len(required):
        state = "incomplete"
    else:
        state = "complete"
    return state, len(required), present


def molecule_paths(mol: Molecule) -> list[str]:
    """Alle Pfade, die die Serialisierung dieses Moleküls prüfen wird — für
    die Vorabprüfung (paths.prefetch). Fehlt hier einer, wird er später
    einzeln geprüft; das Ergebnis ist dasselbe, nur langsamer."""
    entries = visible_entries(mol)
    out = [mol.si_path]
    for kind in _IMAGE_ATTR:
        out.append(image_abs(getattr(mol, _IMAGE_ATTR[kind])))
        out.append(image_abs(getattr(mol, _CDX_ATTR[kind])))
    out += [p for e in entries for p in (e.folder_path, e.file_path, e.svg_path, e.svg2_path)]
    out += [f.path for e in entries for f in e.files]
    return [p for p in out if p]


def molecule_summary(mol: Molecule) -> dict:
    """Molekül samt Einträgen für die Oberfläche. Prüft dabei alle verlinkten
    Pfade — innerhalb eines scan_scope, damit jeder Pfad höchstens einmal
    angefasst wird (die toten Verweise werden aus denselben Pfaden gezählt).

    Vor der Ausgabe sucht relink.sync umbenannte Dateien wieder und trägt den
    neuen Namen ein; ausgeliefert wird also schon der reparierte Stand."""
    with paths.scan_scope():
        paths.prefetch(molecule_paths(mol))
        relink.sync(mol)
        return _molecule_summary(mol)


def _molecule_summary(mol: Molecule) -> dict:
    entries = visible_entries(mol)
    state, required_count, present_count = completeness(mol)
    # Drei Bild-Slots (Struktur, Reaktionsschema, Reaktionsgleichung), je mit
    # optionaler ChemDraw-Datei: <kind>_path/_exists/_version,
    # <kind>_cdx_path/_exists, <kind>_stale
    slots: dict = {}
    all_paths = [mol.si_path]
    for kind in _IMAGE_ATTR:
        img = image_abs(getattr(mol, _IMAGE_ATTR[kind]))
        cdx = image_abs(getattr(mol, _CDX_ATTR[kind]))
        all_paths += [img, cdx]
        slots[f"{kind}_path"] = link_out(img)
        slots[f"{kind}_exists"] = path_exists(img)
        slots[f"{kind}_version"] = image_version(img)
        slots[f"{kind}_cdx_path"] = link_out(cdx)
        slots[f"{kind}_cdx_exists"] = path_exists(cdx)
        slots[f"{kind}_stale"] = cdx_stale(img, cdx)
    all_paths += [p for e in entries for p in (e.folder_path, e.file_path, e.svg_path, e.svg2_path)]
    all_paths += [f.path for e in entries for f in e.files]
    broken_paths = sum(1 for p in all_paths if p and not paths.exists(p))
    return {
        "id": mol.id,
        "project_id": mol.project_id,
        "name": mol.name,
        "name_html": mol.name_html,
        "smiles": mol.smiles,
        "formula": mol.formula,
        "exact_mass": mol.exact_mass,
        **slots,
        "literature_known": mol.literature_known,
        "doi": mol.doi,
        "citation": mol.citation,
        "citation_html": mol.citation_html,
        "si_path": link_out(mol.si_path),
        "si_exists": path_exists(mol.si_path),
        "si_local": paths.is_local_only(mol.si_path),
        "physical_state": mol.physical_state,
        "color": mol.color,
        "consistency": mol.consistency,
        "sample_available": mol.sample_available,
        "sample_number": mol.sample_number,
        "sample_comment": mol.sample_comment,
        "sample_comment_html": mol.sample_comment_html,
        "broken_paths": broken_paths,
        "completeness": state,
        "required_count": required_count,
        "present_count": present_count,
        "updated_at": mol.updated_at.isoformat(),
        "entries": [entry_dict(e) for e in entries],
    }


def entry_dict(e: DataEntry) -> dict:
    return {
        "id": e.id,
        "type_code": e.type_code,
        "custom_label": e.custom_label,
        # Eigene Einträge: meint die Bezeichnung eine NMR-Messung? Dann zeigt
        # die App sie gesetzt („¹⁹F NMR") und gibt dem Eintrag dieselben
        # Felder wie ¹H und ¹³C.
        "is_nmr": e.type_code == "other" and chem_text.is_nmr_label(e.custom_label),
        "display_label": chem_text.typeset(e.custom_label) if e.type_code == "other" else None,
        "required": e.required,
        "status": e.effective_status,
        "folder_path": link_out(e.folder_path),
        "folder_exists": path_exists(e.folder_path),
        "folder_local": paths.is_local_only(e.folder_path),
        "folder_label": e.folder_label,
        "file_path": link_out(e.file_path),
        "file_exists": path_exists(e.file_path),
        "file_local": paths.is_local_only(e.file_path),
        "file_label": e.file_label,
        "svg_path": link_out(e.svg_path),
        "svg_exists": path_exists(e.svg_path),
        "svg_local": paths.is_local_only(e.svg_path),
        "svg_label": e.svg_label,
        "svg2_path": link_out(e.svg2_path),
        "svg2_exists": path_exists(e.svg2_path),
        "svg2_local": paths.is_local_only(e.svg2_path),
        "svg2_label": e.svg2_label,
        "files": [entry_file_dict(f) for f in e.files],
        "notes": [note_dict(n) for n in e.notes],
        "mp_value": e.mp_value,
        "in_document": e.in_document,
        "updated_at": e.updated_at.isoformat(),
    }


def note_dict(n: EntryNote) -> dict:
    """text = Klartext (immer), html = formatierte Fassung (None bei reinen
    Textnotizen — das Frontend zeigt dann den Text)."""
    return {"id": n.id, "text": n.text, "html": n.html}


def get_or_404(session: Session, model, obj_id: int, lang: str = "en"):
    obj = session.get(model, obj_id)
    if obj is None:
        raise HTTPException(
            404,
            T(lang, f"{model.__name__} {obj_id} nicht gefunden",
              f"{model.__name__} {obj_id} not found"),
        )
    return obj


# ---------- Datentyp-Katalog ----------

@router.get("/datatypes")
def list_datatypes():
    return DATA_TYPES


@router.get("/nuclei")
def list_nuclei():
    """Was die App beim Anlegen eines weiteren NMR-Kerns anbietet: der Katalog
    (Bezeichnung, Nachkommastellen, „{¹H}"-Vorbelegung) und die Felder, die so
    ein Eintrag bekommt — dieselben wie ¹H und ¹³C."""
    return {"nuclei": nuclei.NUCLEI, "fields": NMR_FIELDS}


# ---------- Projekte ----------

class ProjectIn(BaseModel):
    name: str


@router.get("/projects")
def list_projects(session: Session = Depends(get_session)):
    # sort_order per Drag & Drop; Bestandsdaten (alle 0) bleiben alphabetisch.
    # Dateien und Notizen werden mitgeladen (selectinload) — sonst holt sie die
    # Serialisierung je Eintrag einzeln nach, was auf einem Datenordner im Netz
    # hunderte Einzelabfragen bedeutet.
    entry_load = selectinload(Project.molecules).selectinload(Molecule.entries)
    projects = session.scalars(
        select(Project)
        .options(
            entry_load.selectinload(DataEntry.files),
            entry_load.selectinload(DataEntry.notes),
        )
        .order_by(Project.sort_order, Project.name)
    ).all()
    # Ein Geltungsbereich für die ganze Liste: jeder Pfad wird höchstens
    # einmal geprüft, auch wenn mehrere Moleküle denselben verlinken. Die
    # Vorabprüfung erledigt sie gebündelt und nebenläufig — vor allem die
    # Bilder, die alle im selben images-Ordner liegen.
    with paths.scan_scope():
        paths.prefetch(p for pr in projects for m in pr.molecules
                       for p in molecule_paths(m))
        return [
            {
                "id": p.id,
                "name": p.name,
                "molecules": [molecule_summary(m) for m in p.molecules],
            }
            for p in projects
        ]


@router.post("/projects", status_code=201)
def create_project(
    data: ProjectIn, session: Session = Depends(get_session), lang: str = Depends(get_lang)
):
    name = data.name.strip()
    if not name:
        raise HTTPException(422, T(lang, "Projektname darf nicht leer sein",
                                   "Project name must not be empty"))
    if session.scalar(select(Project).where(Project.name == name)):
        raise HTTPException(409, T(lang, f"Projekt „{name}“ existiert bereits",
                                   f"Project “{name}” already exists"))
    # Neue Projekte kommen ans Ende der (per Drag & Drop sortierbaren) Liste
    max_order = session.scalar(select(func.max(Project.sort_order))) or 0
    project = Project(name=name, sort_order=max_order + 1)
    session.add(project)
    session.commit()
    return {"id": project.id, "name": project.name, "molecules": []}


class ProjectOrderIn(BaseModel):
    order: list[int]  # alle Projekt-IDs in gewünschter Reihenfolge


@router.post("/projects/reorder")
def reorder_projects(
    data: ProjectOrderIn, session: Session = Depends(get_session), lang: str = Depends(get_lang)
):
    projects = session.scalars(select(Project)).all()
    if sorted(data.order) != sorted(p.id for p in projects):
        raise HTTPException(422, T(lang, "Reihenfolge muss jedes Projekt genau einmal enthalten",
                                   "Order must contain every project exactly once"))
    pos = {pid: i for i, pid in enumerate(data.order)}
    for p in projects:
        p.sort_order = pos[p.id]
    session.commit()
    return {"ok": True}


@router.delete("/projects/{project_id}", status_code=204)
def delete_project(
    project_id: int, session: Session = Depends(get_session), lang: str = Depends(get_lang)
):
    session.delete(get_or_404(session, Project, project_id, lang))
    session.commit()


# ---------- Moleküle ----------

class MoleculeIn(BaseModel):
    project_id: int
    name: str = ""
    # Formatierter Name als HTML — hat Vorrang vor `name`, dessen Klartext
    # dann daraus abgeleitet wird (siehe richtext.field)
    name_html: str | None = None
    smiles: str | None = None


class MoleculePatch(BaseModel):
    name: str | None = None
    name_html: str | None = None  # formatierter Name; Vorrang vor `name`
    smiles: str | None = None  # "" entfernt den SMILES
    image_path: str | None = None  # "" entfernt das Strukturbild
    scheme_path: str | None = None  # "" entfernt das Reaktionsschema
    equation_path: str | None = None  # "" entfernt die Reaktionsgleichung
    literature_known: bool | None = None
    doi: str | None = None  # "" entfernt die DOI
    citation: str | None = None  # Literaturzitat als Freitext; "" entfernt es
    citation_html: str | None = None  # formatiertes Zitat; Vorrang vor `citation`
    si_path: str | None = None  # Supporting Information (PDF/Word); "" entfernt sie
    project_id: int | None = None  # verschiebt das Molekül in ein anderes Projekt
    physical_state: str | None = None  # "solid" | "oil" | "" (löscht)
    color: str | None = None
    consistency: str | None = None
    sample_available: bool | None = None  # noch Substanz übrig?
    sample_number: str | None = None  # "" entfernt die Probennummer
    sample_comment: str | None = None  # "" entfernt den Vermerk
    sample_comment_html: str | None = None  # formatierter Vermerk; Vorrang vor `sample_comment`


# Formatierbare Freitextfelder des Moleküls: Klartextspalte -> HTML-Spalte.
# Wer nur den Klartext schickt (ältere Oberfläche, Skripte), entfernt damit
# auch die Formatierung — sonst passten die beiden nicht mehr zusammen.
_RICH_FIELDS = {"citation": "citation_html", "sample_comment": "sample_comment_html"}


def _molecule_name(name: str | None, name_html: str | None) -> tuple[str, str | None]:
    """(Klartextname, formatierter Name oder None) aus dem, was geschickt wurde."""
    if name_html is not None:
        text, html_value = richtext.field(name_html, single_line=True)
        return text or "", html_value
    return (name or "").strip(), None


def apply_smiles(mol: Molecule, smiles: str | None, lang: str) -> None:
    smiles = (smiles or "").strip()
    if not smiles:
        mol.smiles = mol.formula = mol.exact_mass = None
        return
    try:
        mol.formula, mol.exact_mass = compute_from_smiles(smiles)
    except ValueError:
        raise HTTPException(422, T(lang, f"Ungültiger SMILES: {smiles!r}",
                                   f"Invalid SMILES: {smiles!r}"))
    mol.smiles = smiles


@router.post("/molecules", status_code=201)
def create_molecule(
    data: MoleculeIn, session: Session = Depends(get_session), lang: str = Depends(get_lang)
):
    project = get_or_404(session, Project, data.project_id, lang)
    name, name_html = _molecule_name(data.name, data.name_html)
    if not name:
        raise HTTPException(422, T(lang, "Molekülname darf nicht leer sein",
                                   "Molecule name must not be empty"))
    if any(m.name == name for m in project.molecules):
        raise HTTPException(409, T(lang, f"Molekül „{name}“ existiert bereits in diesem Projekt",
                                   f"Molecule “{name}” already exists in this project"))
    mol = Molecule(project_id=project.id, name=name, name_html=name_html,
                   sort_order=_next_mol_order(session, project.id))
    apply_smiles(mol, data.smiles, lang)
    mol.entries = [DataEntry(type_code=code) for code in DEFAULT_TYPES]
    session.add(mol)
    session.commit()
    return molecule_summary(mol)


def _next_mol_order(session: Session, project_id: int) -> int:
    """Neue bzw. verschobene Moleküle kommen ans Ende des Projekts."""
    max_order = session.scalar(
        select(func.max(Molecule.sort_order)).where(Molecule.project_id == project_id)
    )
    return (max_order or 0) + 1


class MoleculeOrderIn(BaseModel):
    order: list[int]  # alle Molekül-IDs EINES Projekts in gewünschter Reihenfolge


@router.post("/molecules/reorder")
def reorder_molecules(
    data: MoleculeOrderIn, session: Session = Depends(get_session), lang: str = Depends(get_lang)
):
    if not data.order:
        raise HTTPException(422, T(lang, "Reihenfolge darf nicht leer sein",
                                   "Order must not be empty"))
    project = get_or_404(session, Molecule, data.order[0], lang).project
    if sorted(data.order) != sorted(m.id for m in project.molecules):
        raise HTTPException(422, T(
            lang,
            "Reihenfolge muss alle Moleküle des Projekts genau einmal enthalten",
            "Order must contain every molecule of the project exactly once",
        ))
    pos = {mid: i for i, mid in enumerate(data.order)}
    for m in project.molecules:
        m.sort_order = pos[m.id]
    session.commit()
    return {"ok": True}


@router.get("/molecules/{molecule_id}")
def get_molecule(
    molecule_id: int, session: Session = Depends(get_session), lang: str = Depends(get_lang)
):
    return molecule_summary(get_or_404(session, Molecule, molecule_id, lang))


@router.patch("/molecules/{molecule_id}")
def update_molecule(
    molecule_id: int, data: MoleculePatch,
    session: Session = Depends(get_session), lang: str = Depends(get_lang),
):
    mol = get_or_404(session, Molecule, molecule_id, lang)
    target_project = mol.project
    if data.project_id is not None and data.project_id != mol.project_id:
        target = get_or_404(session, Project, data.project_id, lang)
        if any(m.name == mol.name for m in target.molecules):
            raise HTTPException(409, T(
                lang,
                f"Molekül „{mol.name}“ existiert bereits im Projekt „{target.name}“",
                f"Molecule “{mol.name}” already exists in project “{target.name}”",
            ))
        mol.project_id = target.id
        mol.sort_order = _next_mol_order(session, target.id)  # ans Ende des Ziels
        target_project = target
    if data.name is not None or data.name_html is not None:
        name, name_html = _molecule_name(data.name, data.name_html)
        if not name:
            raise HTTPException(422, T(lang, "Molekülname darf nicht leer sein",
                                       "Molecule name must not be empty"))
        if name != mol.name and any(
            m.id != mol.id and m.name == name for m in target_project.molecules
        ):
            raise HTTPException(409, T(
                lang,
                f"Molekül „{name}“ existiert bereits in diesem Projekt",
                f"Molecule “{name}” already exists in this project",
            ))
        mol.name = name
        mol.name_html = name_html
    if data.smiles is not None:
        apply_smiles(mol, data.smiles, lang)
    for kind, field in _IMAGE_ATTR.items():
        if field in data.model_fields_set:
            setattr(mol, field, link_in(getattr(data, field)))  # extern gewählte Bilddatei
            # Bild gewechselt/entfernt -> die mitgespeicherte ChemDraw-Datei
            # gehört zum alten Bild und wird mit entfernt
            _set_cdx_path(mol, kind, None)
    if data.literature_known is not None:
        mol.literature_known = data.literature_known
    if "doi" in data.model_fields_set:
        mol.doi = (data.doi or "").strip() or None
    if "si_path" in data.model_fields_set:
        mol.si_path = link_in(data.si_path)  # Netzlaufwerk -> UNC
    if "physical_state" in data.model_fields_set:
        state = (data.physical_state or "").strip().lower()
        if state not in ("", "solid", "oil"):
            raise HTTPException(422, T(lang, "Ungültiger Aggregatzustand",
                                       "Invalid physical state"))
        mol.physical_state = state or None
    if data.sample_available is not None:
        mol.sample_available = data.sample_available
    for field in ("color", "consistency", "sample_number"):
        if field in data.model_fields_set:
            setattr(mol, field, (getattr(data, field) or "").strip() or None)
    for field, html_field in _RICH_FIELDS.items():
        if html_field in data.model_fields_set:
            text, html_value = richtext.field(getattr(data, html_field))
            setattr(mol, field, text)
            setattr(mol, html_field, html_value)
        elif field in data.model_fields_set:
            setattr(mol, field, (getattr(data, field) or "").strip() or None)
            setattr(mol, html_field, None)
    session.commit()
    return molecule_summary(mol)


@router.delete("/molecules/{molecule_id}", status_code=204)
def delete_molecule(
    molecule_id: int, session: Session = Depends(get_session), lang: str = Depends(get_lang)
):
    session.delete(get_or_404(session, Molecule, molecule_id, lang))
    session.commit()


# Drei Bild-Slots pro Molekül: Strukturbild, Reaktionsschema (z. B. aus
# ChemDraw mit ausgerechneten Äquivalenten) und Reaktionsgleichung. Gleiche
# Logik, eigenes DB-Feld. Eigene Routen je Slot — ein {kind}-Pfadparameter
# würde /entries und /export verschlucken (422 statt Weiterreichen an die
# spätere Route).
_IMAGE_ATTR = {"image": "image_path", "scheme": "scheme_path", "equation": "equation_path"}
# Beim Einfügen aus ChemDraw mitgespeicherte .cdx-Originaldatei je Slot
_CDX_ATTR = {"image": "image_cdx_path", "scheme": "scheme_cdx_path",
             "equation": "equation_cdx_path"}
# Dateinamen-Präfix der von der App gespeicherten Bilder je Slot
_IMAGE_PREFIX = {"image": "mol", "scheme": "scheme", "equation": "equation"}
_NO_IMAGE_MSG = {
    "image": ("Kein Strukturbild vorhanden", "No structure image available"),
    "scheme": ("Kein Reaktionsschema vorhanden", "No reaction scheme available"),
    "equation": ("Keine Reaktionsgleichung vorhanden", "No reaction equation available"),
}


def _no_image_error(kind: str, lang: str) -> HTTPException:
    return HTTPException(404, T(lang, *_NO_IMAGE_MSG[kind]))


# Ausgeliefert wird nur, was auch wirklich ein Bild ist — sonst könnte über
# einen auf eine Fremddatei gesetzten Bildpfad jede Datei als „Bild" abgerufen
# werden. Content-Type wird bewusst gesetzt (kein Raten aus der Endung).
_IMAGE_MEDIA_TYPES = {
    "png": "image/png", "jpg": "image/jpeg", "gif": "image/gif",
    "bmp": "image/bmp", "webp": "image/webp",
}


# Fragt die Oberfläche ein Bild mit seiner aktuellen Versionskennung ab
# (?v=, siehe image_version), ist der Inhalt unter dieser URL unveränderlich:
# ändert sich die Datei, ändert sich die Kennung und damit die URL.
_IMAGE_CACHE = "private, max-age=31536000, immutable"


def _serve_image(
    session: Session, molecule_id: int, kind: str, lang: str, v: str | None = None
) -> FileResponse:
    mol = get_or_404(session, Molecule, molecule_id, lang)
    path = image_abs(getattr(mol, _IMAGE_ATTR[kind]))
    if not path or not Path(path).is_file():
        raise _no_image_error(kind, lang)
    try:
        with open(path, "rb") as fh:
            head = fh.read(32)
    except OSError:
        raise _no_image_error(kind, lang)
    ext = _detect_image_ext(head)
    if ext is None:
        # Hinterlegter Pfad ist keine Bilddatei -> nicht ausliefern
        raise _no_image_error(kind, lang)
    resp = FileResponse(path, media_type=_IMAGE_MEDIA_TYPES[ext])
    # Nur wenn die Kennung zum Stand passt, den der Server gerade sieht — sonst
    # (Anfrage mit veralteter Kennung) bliebe unter ihrer URL ein falsches Bild
    # im Browser liegen.
    if v and v == image_version(path):
        resp.headers["Cache-Control"] = _IMAGE_CACHE
    return resp


@router.get("/molecules/{molecule_id}/image")
def molecule_image(
    molecule_id: int, v: str | None = None,
    session: Session = Depends(get_session), lang: str = Depends(get_lang),
):
    return _serve_image(session, molecule_id, "image", lang, v)


@router.get("/molecules/{molecule_id}/scheme")
def molecule_scheme(
    molecule_id: int, v: str | None = None,
    session: Session = Depends(get_session), lang: str = Depends(get_lang),
):
    return _serve_image(session, molecule_id, "scheme", lang, v)


@router.get("/molecules/{molecule_id}/equation")
def molecule_equation(
    molecule_id: int, v: str | None = None,
    session: Session = Depends(get_session), lang: str = Depends(get_lang),
):
    return _serve_image(session, molecule_id, "equation", lang, v)


# ---------- Bild aus der Zwischenablage einfügen ----------

MAX_IMAGE_BYTES = 25 * 1024 * 1024  # 25 MB

_IMAGE_SIGNATURES = [
    (b"\x89PNG\r\n\x1a\n", "png"),
    (b"\xff\xd8\xff", "jpg"),
    (b"GIF87a", "gif"),
    (b"GIF89a", "gif"),
    (b"BM", "bmp"),
]


def _detect_image_ext(data: bytes) -> str | None:
    """Bildformat anhand der Magic Bytes bestimmen (None = kein bekanntes Bild)."""
    for sig, ext in _IMAGE_SIGNATURES:
        if data.startswith(sig):
            return ext
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def _images_dir() -> Path:
    return db.images_dir()


def _remove_managed_image(image_path: str | None) -> None:
    """Ein früher eingefügtes Bild aufräumen — aber nur Dateien im verwalteten
    images-Ordner; extern gewählte Bilddateien bleiben unberührt."""
    if not image_path:
        return
    try:
        p = db.image_file(image_path).resolve()
        if p.is_file() and p.parent == _images_dir().resolve():
            p.unlink()
    except OSError:
        pass


def _save_image_data(
    session: Session, mol: Molecule, kind: str, data: bytes, lang: str,
    cdx: bytes | None = None, keep_cdx: bool = False,
) -> dict:
    """Speichert Bilddaten im Projekt und setzt sie als Strukturbild
    bzw. Reaktionsschema. Eine mitgelieferte ChemDraw-Datei (cdx) wird
    daneben abgelegt; ohne cdx wird eine alte .cdx entfernt, damit sie
    nicht zu einem inzwischen anderen Bild gehört. keep_cdx=True lässt
    die vorhandene .cdx unangetastet (Neu-Rendern AUS ihr)."""
    if not data:
        raise HTTPException(422, T(lang, "Kein Bild empfangen", "No image received"))
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(413, T(lang, "Bild ist zu groß (max. 25 MB)",
                                   "Image is too large (max. 25 MB)"))
    ext = _detect_image_ext(data)
    if ext is None:
        raise HTTPException(422, T(lang, "Inhalt der Zwischenablage ist kein Bild",
                                   "Clipboard content is not an image"))
    images = _images_dir()
    images.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    base = f"{_IMAGE_PREFIX[kind]}-{mol.id}-{stamp}"
    # Die Windows-Uhr tickt grob — zwei Einfügungen können denselben Stempel
    # bekommen; gleicher Name würde die alte Datei zur neuen machen und beim
    # Aufräumen löschen. Daher Namen (inkl. .cdx-Partner) eindeutig machen.
    target = images / f"{base}.{ext}"
    i = 2
    while target.exists() or target.with_suffix(".cdx").exists():
        target = images / f"{base}-{i}.{ext}"
        i += 1
    # Zwischen dem Schreiben der Datei und dem Commit darf das Aufräumen
    # verwaister Bilder (Backup, Transfer-Export) nicht dazwischenfunken —
    # es fände eine Datei vor, die noch in keiner Datenbank steht.
    with db.image_lock:
        target.write_bytes(data)
        attr = _IMAGE_ATTR[kind]
        _remove_managed_image(getattr(mol, attr))  # alte, von der App gespeicherte Datei ersetzen
        setattr(mol, attr, db.managed_name(target))  # nur Dateiname -> PC-unabhängig
        if not keep_cdx:
            cdx_target = None
            if cdx:
                cdx_target = target.with_suffix(".cdx")
                cdx_target.write_bytes(cdx)
            _set_cdx_path(mol, kind, cdx_target)
        session.commit()
    return molecule_summary(mol)


def _set_cdx_path(mol: Molecule, kind: str, target: Path | None) -> None:
    """Setzt bzw. löscht die zum Bild-Slot gehörende ChemDraw-Datei;
    eine zuvor von der App gespeicherte .cdx wird mit aufgeräumt."""
    attr = _CDX_ATTR[kind]
    _remove_managed_image(getattr(mol, attr))
    setattr(mol, attr, db.managed_name(target) if target else None)


async def _upload_image(
    session: Session, molecule_id: int, kind: str, request: Request, lang: str
) -> dict:
    """Nimmt Bilddaten als rohen Request-Body entgegen (Browser-Zwischenablage,
    Drag & Drop)."""
    mol = get_or_404(session, Molecule, molecule_id, lang)
    return _save_image_data(session, mol, kind, await request.body(), lang)


def _clipboard_module(lang: str):
    """Zwischenablage des Systems: clipboard_win bzw. clipboard_mac (gleiche
    Lese-Funktionen). Andere Systeme: nur, was der Browser selbst als Bild
    sieht (app.js lädt es direkt hoch)."""
    if osutil.IS_WIN:
        from . import clipboard_win
        return clipboard_win
    if osutil.IS_MAC:
        from . import clipboard_mac
        return clipboard_mac
    raise HTTPException(422, T(lang, "Zwischenablage enthält kein Bild",
                               "Clipboard contains no image"))


def _paste_from_clipboard(session: Session, molecule_id: int, kind: str, lang: str) -> dict:
    """Liest die Zwischenablage (Windows/macOS) serverseitig — sieht auch Formate, die
    der Browser nicht durchreicht (z. B. ChemDraws „Copy as PNG"). Liegt
    zusätzlich ChemDraws natives CDX-Format an, wird es als .cdx-Datei
    mitgespeichert (Struktur bleibt in ChemDraw weiterbearbeitbar)."""
    clip = _clipboard_module(lang)

    mol = get_or_404(session, Molecule, molecule_id, lang)
    try:
        data = clip.read_clipboard_image()
    except OSError:
        data = None
    if data is None:
        raise HTTPException(422, T(lang, "Zwischenablage enthält kein Bild",
                                   "Clipboard contains no image"))
    try:
        cdx = clip.read_clipboard_cdx()
    except OSError:
        cdx = None
    # ChemDraw legt auch das SMILES mit ab: ein leeres SMILES-Feld wird beim
    # Einfügen des STRUKTURbilds vorbefüllt (ein Schema enthält mehrere
    # Moleküle — dessen SMILES wäre falsch). Ein vorhandenes SMILES bleibt.
    if kind == "image" and not mol.smiles:
        try:
            smiles = clip.read_clipboard_smiles()
        except OSError:
            smiles = None
        if smiles:
            try:
                mol.formula, mol.exact_mass = compute_from_smiles(smiles)
                mol.smiles = smiles
            except ValueError:
                pass  # exotisches/ungültiges SMILES -> Feld einfach leer lassen
    return _save_image_data(session, mol, kind, data, lang, cdx=cdx)


@router.post("/molecules/{molecule_id}/image")
async def upload_molecule_image(
    molecule_id: int, request: Request,
    session: Session = Depends(get_session), lang: str = Depends(get_lang),
):
    return await _upload_image(session, molecule_id, "image", request, lang)


@router.post("/molecules/{molecule_id}/scheme")
async def upload_molecule_scheme(
    molecule_id: int, request: Request,
    session: Session = Depends(get_session), lang: str = Depends(get_lang),
):
    return await _upload_image(session, molecule_id, "scheme", request, lang)


@router.post("/molecules/{molecule_id}/equation")
async def upload_molecule_equation(
    molecule_id: int, request: Request,
    session: Session = Depends(get_session), lang: str = Depends(get_lang),
):
    return await _upload_image(session, molecule_id, "equation", request, lang)


@router.post("/molecules/{molecule_id}/image/clipboard")
def paste_molecule_image(
    molecule_id: int,
    session: Session = Depends(get_session), lang: str = Depends(get_lang),
):
    return _paste_from_clipboard(session, molecule_id, "image", lang)


@router.post("/molecules/{molecule_id}/scheme/clipboard")
def paste_molecule_scheme(
    molecule_id: int,
    session: Session = Depends(get_session), lang: str = Depends(get_lang),
):
    return _paste_from_clipboard(session, molecule_id, "scheme", lang)


@router.post("/molecules/{molecule_id}/equation/clipboard")
def paste_molecule_equation(
    molecule_id: int,
    session: Session = Depends(get_session), lang: str = Depends(get_lang),
):
    return _paste_from_clipboard(session, molecule_id, "equation", lang)


def _refresh_from_cdx(session: Session, molecule_id: int, kind: str, lang: str) -> dict:
    """Rendert das Bild neu aus der mitgespeicherten ChemDraw-Datei — nötig,
    wenn die .cdx über „ChemDraw ⬈" bearbeitet und gespeichert wurde. Die
    .cdx selbst bleibt unverändert; nur das Pixelbild wird ersetzt."""
    if not osutil.IS_WIN:
        # ChemDraw lässt sich nur unter Windows fernsteuern (COM)
        raise HTTPException(501, T(lang,
                                   "Zeichnung in ChemDraw kopieren und hier einfügen, "
                                   "um das Bild zu aktualisieren",
                                   "Copy the drawing in ChemDraw and paste it here "
                                   "to update the picture"))
    from . import chemdraw_render

    mol = get_or_404(session, Molecule, molecule_id, lang)
    cdx = getattr(mol, _CDX_ATTR[kind])
    cdx = image_abs(cdx)
    if not cdx or not Path(cdx).is_file():
        raise HTTPException(409, T(lang, "Keine ChemDraw-Datei zu diesem Bild vorhanden",
                                   "No ChemDraw file stored for this image"))
    try:
        data = chemdraw_render.render_cdx(Path(cdx))
    except chemdraw_render.RenderError as e:
        raise HTTPException(502, T(lang,
                                   f"ChemDraw konnte das Bild nicht neu erzeugen: {e}",
                                   f"ChemDraw could not re-render the image: {e}"))
    _save_image_data(session, mol, kind, data, lang, keep_cdx=True)
    # Das neue Bild trägt den Zeitstempel der .cdx: „veraltet" heißt ab jetzt
    # wieder strikt „cdx später geändert" — sonst hielte eine .cdx mit
    # Zukunfts-Zeitstempel (Kopie/Backup) das Bild dauerhaft für veraltet
    # und das automatische Neu-Rendern liefe endlos.
    try:
        m = Path(cdx).stat().st_mtime
        os.utime(image_abs(getattr(mol, _IMAGE_ATTR[kind])), (m, m))
    except OSError:
        pass
    return molecule_summary(mol)


@router.post("/molecules/{molecule_id}/image/refresh")
def refresh_molecule_image(
    molecule_id: int,
    session: Session = Depends(get_session), lang: str = Depends(get_lang),
):
    return _refresh_from_cdx(session, molecule_id, "image", lang)


@router.post("/molecules/{molecule_id}/scheme/refresh")
def refresh_molecule_scheme(
    molecule_id: int,
    session: Session = Depends(get_session), lang: str = Depends(get_lang),
):
    return _refresh_from_cdx(session, molecule_id, "scheme", lang)


@router.post("/molecules/{molecule_id}/equation/refresh")
def refresh_molecule_equation(
    molecule_id: int,
    session: Session = Depends(get_session), lang: str = Depends(get_lang),
):
    return _refresh_from_cdx(session, molecule_id, "equation", lang)


@router.post("/molecules/{molecule_id}/{kind}/copy")
def copy_chemdraw(
    molecule_id: int, kind: str,
    session: Session = Depends(get_session), lang: str = Depends(get_lang),
):
    """Legt die zum Bild-Slot gespeicherte ChemDraw-Zeichnung in die
    Windows-Zwischenablage — wie Kopieren in ChemDraw selbst. Ändert nichts
    am Datensatz (daher weder Undo-Schritt noch im Lesemodus gesperrt)."""
    if not (osutil.IS_WIN or osutil.IS_MAC):
        raise HTTPException(501, T(lang,
                                   "ChemDraw-Zeichnungen kopieren geht nur unter Windows und macOS",
                                   "Copying ChemDraw drawings needs Windows or macOS"))

    if kind not in _CDX_ATTR:
        raise HTTPException(404, T(lang, "Unbekannter Bild-Slot", "Unknown image slot"))
    mol = get_or_404(session, Molecule, molecule_id, lang)
    cdx_path = image_abs(getattr(mol, _CDX_ATTR[kind]))
    try:
        cdx = Path(cdx_path).read_bytes() if cdx_path else None
    except OSError:
        cdx = None
    if not cdx:
        raise HTTPException(409, T(lang, "Keine ChemDraw-Datei zu diesem Bild vorhanden",
                                   "No ChemDraw file stored for this image"))
    # Das Bild kommt als Ansicht mit — außer die .cdx wurde seitdem in
    # ChemDraw geändert, dann zeigt es einen alten Stand
    image_path = image_abs(getattr(mol, _IMAGE_ATTR[kind]))
    image = None
    if image_path and not cdx_stale(image_path, cdx_path):
        try:
            image = Path(image_path).read_bytes()
        except OSError:
            pass
    try:
        if osutil.IS_WIN:
            from . import clipboard_win
            clipboard_win.write_clipboard(clipboard_win.chemdraw_formats(cdx, image))
        else:
            from . import clipboard_mac
            clipboard_mac.write_chemdraw(cdx, image)
    except OSError as e:
        raise HTTPException(503, T(lang, f"Zwischenablage nicht beschreibbar: {e}",
                                   f"Could not write to the clipboard: {e}"))
    return {"ok": True}


# ---------- Einträge ----------

class EntryPatch(BaseModel):
    required: bool | None = None
    status: str | None = None  # "present" | "missing"
    custom_label: str | None = None
    # Datenfelder: "" bzw. null löscht den Wert (zählt nur, wenn im Request enthalten)
    folder_path: str | None = None
    file_path: str | None = None
    svg_path: str | None = None
    svg2_path: str | None = None
    # Umbenennung der festen Felder: "" stellt das Standard-Label wieder her
    folder_label: str | None = None
    file_label: str | None = None
    svg_label: str | None = None
    svg2_label: str | None = None
    mp_value: float | None = None
    # Nur "other": ins Word-Dokument übernehmen?
    in_document: bool | None = None


class OtherEntryIn(BaseModel):
    custom_label: str


@router.patch("/entries/{entry_id}")
def update_entry(
    entry_id: int, data: EntryPatch,
    session: Session = Depends(get_session), lang: str = Depends(get_lang),
):
    entry = get_or_404(session, DataEntry, entry_id, lang)
    if data.status is not None:
        if data.status not in ("present", "missing"):
            raise HTTPException(422, T(lang, "Status muss 'present' oder 'missing' sein",
                                       "Status must be 'present' or 'missing'"))
        entry.status = data.status
    if data.required is not None:
        entry.required = data.required
    if data.custom_label is not None:
        if entry.type_code != "other":
            raise HTTPException(422, T(lang, "Nur Sonstiges-Einträge sind umbenennbar",
                                       "Only custom entries can be renamed"))
        entry.custom_label = data.custom_label.strip() or entry.custom_label
    for field in ("folder_path", "file_path", "svg_path", "svg2_path"):
        if field in data.model_fields_set:
            setattr(entry, field, link_in(getattr(data, field)))  # Netzlaufwerk -> UNC
    for field in ("folder_label", "file_label", "svg_label", "svg2_label"):
        if field in data.model_fields_set:
            setattr(entry, field, (getattr(data, field) or "").strip() or None)
    if "mp_value" in data.model_fields_set:
        entry.mp_value = data.mp_value
    if data.in_document is not None:
        if entry.type_code != "other":
            raise HTTPException(422, T(
                lang,
                "Feste Datentypen sind immer im Word-Dokument",
                "Standard data types are always in the Word document"))
        entry.in_document = data.in_document
    session.commit()
    return entry_dict(entry)


@router.post("/molecules/{molecule_id}/entries", status_code=201)
def add_other_entry(
    molecule_id: int, data: OtherEntryIn,
    session: Session = Depends(get_session), lang: str = Depends(get_lang),
):
    mol = get_or_404(session, Molecule, molecule_id, lang)
    label = data.custom_label.strip()
    if not label:
        raise HTTPException(422, T(lang, "Name für Sonstiges-Eintrag darf nicht leer sein",
                                   "Name for custom entry must not be empty"))
    # Vorbelegung des Word-Häkchens: NMR-Messungen gehören ins Dokument,
    # alles andere (Röntgenstruktur, Elementaranalyse …) erst auf Wunsch
    entry = DataEntry(molecule_id=mol.id, type_code="other", custom_label=label,
                      in_document=chem_text.is_nmr_label(label))
    session.add(entry)
    session.commit()
    return entry_dict(entry)


def _nmr_label(entry: DataEntry) -> str | None:
    """Die Bezeichnung, mit der dieser Eintrag im Dokument steht — None, wenn
    er keine (eindimensionale) NMR-Messung ist."""
    if entry.type_code in nuclei.TYPE_LABELS:
        return nuclei.TYPE_LABELS[entry.type_code]
    if entry.type_code == "other" and chem_text.is_nmr_label(entry.custom_label):
        return entry.custom_label
    return None


def _measured_conditions(mol: Molecule) -> dict:
    """Messbedingungen, die für dieses Molekül schon irgendwo erfasst sind:
    Lösungsmittel und Temperatur wörtlich aus der ersten NMR-Notiz, die sie
    nennt, und die ¹H-Frequenz des Geräts — aus „126 MHz" an einem
    ¹³C-Datensatz folgt sie genauso wie aus dem ¹H-Datensatz selbst.
    Was nirgends steht, fehlt hier: erfunden wird nichts."""
    out: dict = {}
    order = {"nmr_1h": 0, "nmr_13c": 1}
    for entry in sorted(mol.entries, key=lambda e: order.get(e.type_code, 2)):
        label = _nmr_label(entry)
        if not label or not entry.notes:
            continue
        cond = chem_text.conditions(entry.notes[0].text)
        for key in ("solvent", "temperature"):
            if cond.get(key) and key not in out:
                out[key] = cond[key]
        if cond.get("frequency") and "proton_mhz" not in out:
            mhz = nuclei.proton_frequency(label, cond["frequency"])
            if mhz:
                out["proton_mhz"] = mhz
    return out


@router.get("/entries/{entry_id}/head")
def entry_head(
    entry_id: int, session: Session = Depends(get_session), lang: str = Depends(get_lang)
):
    """Vorschlag für die Kopfzeile einer NMR-Notiz — „19F NMR (471 MHz, CDCl3,
    298 K) δ [ppm] = ". Die Frequenz folgt aus dem Kernverhältnis und der
    ¹H-Frequenz des Geräts, Lösungsmittel und Temperatur stehen wörtlich so,
    wie sie bei den schon erfassten Kernen dieses Moleküls stehen. Ist nichts
    davon bekannt, bleibt es bei der Bezeichnung — die App setzt den Vorschlag
    nur auf Knopfdruck ein, geschrieben wird nie von allein."""
    entry = get_or_404(session, DataEntry, entry_id, lang)
    label = _nmr_label(entry)
    if not label:
        raise HTTPException(422, T(lang, "Kein NMR-Eintrag", "Not an NMR entry"))
    cond = _measured_conditions(entry.molecule)
    parts = []
    freq = (nuclei.frequency(label, cond["proton_mhz"])
            if cond.get("proton_mhz") else None)
    if freq:
        parts.append(f"{freq} MHz")
    if cond.get("solvent"):
        parts.append(cond["solvent"])
    if cond.get("temperature"):
        parts.append(f"{cond['temperature']} K")
    head = label + (f" ({', '.join(parts)})" if parts else "")
    return {"text": f"{head} δ [ppm] = "}


@router.delete("/entries/{entry_id}", status_code=204)
def delete_entry(
    entry_id: int, session: Session = Depends(get_session), lang: str = Depends(get_lang)
):
    entry = get_or_404(session, DataEntry, entry_id, lang)
    if entry.type_code != "other":
        raise HTTPException(422, T(
            lang,
            "Nur Sonstiges-Einträge können gelöscht werden — Standardtypen stattdessen auf „n. z.“ stellen",
            "Only custom entries can be deleted — set standard types to “n/a” instead",
        ))
    session.delete(entry)
    session.commit()


# ---------- Notizen (beliebig viele pro Eintrag) ----------

class NoteIn(BaseModel):
    text: str = ""
    # Formatierte Fassung (fett/kursiv/hoch-/tiefgestellt) als HTML — wird
    # serverseitig bereinigt; der Klartext (text) wird daraus abgeleitet.
    # Ohne html: reine Textnotiz.
    html: str | None = None


def _apply_note(note: EntryNote, data: NoteIn) -> None:
    if data.html is not None:
        clean = richtext.sanitize(data.html)
        note.text = richtext.to_text(clean)
        # Ohne Formatierung bleibt es eine reine Textnotiz (kompakter, und
        # ältere App-Versionen sehen exakt dasselbe)
        note.html = None if richtext.is_plain(clean) else clean
    else:
        note.text = data.text
        note.html = None


@router.post("/entries/{entry_id}/notes", status_code=201)
def add_note(
    entry_id: int, data: NoteIn,
    session: Session = Depends(get_session), lang: str = Depends(get_lang),
):
    entry = get_or_404(session, DataEntry, entry_id, lang)
    note = EntryNote(entry_id=entry.id)
    _apply_note(note, data)
    session.add(note)
    session.commit()
    return note_dict(note)


@router.patch("/notes/{note_id}")
def update_note(
    note_id: int, data: NoteIn,
    session: Session = Depends(get_session), lang: str = Depends(get_lang),
):
    note = get_or_404(session, EntryNote, note_id, lang)
    _apply_note(note, data)
    session.commit()
    return note_dict(note)


@router.delete("/notes/{note_id}", status_code=204)
def delete_note(
    note_id: int, session: Session = Depends(get_session), lang: str = Depends(get_lang)
):
    session.delete(get_or_404(session, EntryNote, note_id, lang))
    session.commit()


# ---------- Zusätzliche Datei-Referenzen (beliebig viele pro Eintrag) ----------

class EntryFileIn(BaseModel):
    path: str
    label: str | None = None


class EntryFilePatch(BaseModel):
    label: str | None = None  # "" entfernt die Bezeichnung
    path: str | None = None  # neue Datei wählen (Verlinkung ändern); leer -> 422


def entry_file_dict(f: EntryFile) -> dict:
    return {"id": f.id, "path": link_out(f.path), "label": f.label,
            "exists": path_exists(f.path), "local": paths.is_local_only(f.path)}


@router.post("/entries/{entry_id}/files", status_code=201)
def add_entry_file(
    entry_id: int, data: EntryFileIn,
    session: Session = Depends(get_session), lang: str = Depends(get_lang),
):
    entry = get_or_404(session, DataEntry, entry_id, lang)
    path = link_in(data.path)  # Netzlaufwerk -> UNC
    if not path:
        raise HTTPException(422, T(lang, "Pfad darf nicht leer sein", "Path must not be empty"))
    f = EntryFile(entry_id=entry.id, path=path, label=(data.label or "").strip() or None)
    session.add(f)
    session.commit()
    return entry_file_dict(f)


@router.patch("/files/{file_id}")
def update_entry_file(
    file_id: int, data: EntryFilePatch,
    session: Session = Depends(get_session), lang: str = Depends(get_lang),
):
    f = get_or_404(session, EntryFile, file_id, lang)
    if "label" in data.model_fields_set:
        f.label = (data.label or "").strip() or None
    if "path" in data.model_fields_set:
        path = link_in(data.path)  # Netzlaufwerk -> UNC
        if not path:
            raise HTTPException(422, T(lang, "Pfad darf nicht leer sein",
                                       "Path must not be empty"))
        f.path = path
    session.commit()
    return entry_file_dict(f)


@router.delete("/files/{file_id}", status_code=204)
def delete_entry_file(
    file_id: int, session: Session = Depends(get_session), lang: str = Depends(get_lang)
):
    session.delete(get_or_404(session, EntryFile, file_id, lang))
    session.commit()


# ---------- Export ----------

class ExportIn(BaseModel):
    target_dir: str


@router.post("/molecules/{molecule_id}/export")
def export_molecule_endpoint(
    molecule_id: int, data: ExportIn,
    session: Session = Depends(get_session), lang: str = Depends(get_lang),
):
    from .export import export_molecule

    mol = get_or_404(session, Molecule, molecule_id, lang)
    target = Path(data.target_dir)
    if not target.is_dir():
        raise HTTPException(422, T(lang, f"Zielordner existiert nicht: {data.target_dir}",
                                   f"Target folder does not exist: {data.target_dir}"))
    return export_molecule(mol, target, lang)


@router.post("/projects/{project_id}/export")
def export_project_endpoint(
    project_id: int, data: ExportIn,
    session: Session = Depends(get_session), lang: str = Depends(get_lang),
):
    from .export import export_project

    project = get_or_404(session, Project, project_id, lang)
    target = Path(data.target_dir)
    if not target.is_dir():
        raise HTTPException(422, T(lang, f"Zielordner existiert nicht: {data.target_dir}",
                                   f"Target folder does not exist: {data.target_dir}"))
    return export_project(project, target, lang)


def _link_word_document(mol: Molecule, file: str) -> str:
    """Verlinkt das erzeugte Dokument beim Eintrag „Versuchsvorschrift".

    Ist dessen Word-Datei-Feld noch leer, kommt es dorthin — das ist der
    Regelfall beim ersten Erzeugen. Hängt dort schon eine andere Datei, wird
    das neue Dokument als zusätzliche Datei angehängt, statt die vorhandene
    Verlinkung zu überschreiben. Der Status bleibt unangetastet: er wird in
    dieser App immer von Hand gesetzt.
    """
    entry = next((e for e in mol.entries if e.type_code == "procedure"), None)
    if entry is None:
        return "none"
    stored = link_in(file)
    if not entry.file_path:
        entry.file_path = stored
        return "entry"
    if entry.file_path == stored or any(f.path == stored for f in entry.files):
        return "already"
    entry.files.append(EntryFile(path=stored, label=Path(file).name))
    return "extra"


@router.post("/molecules/{molecule_id}/word")
def word_export_endpoint(
    molecule_id: int, data: ExportIn,
    session: Session = Depends(get_session), lang: str = Depends(get_lang),
):
    """Schreibt die Versuchsvorschrift als Word-Dokument (Aufbau siehe
    word_export.py) und verlinkt es beim Eintrag „Versuchsvorschrift".

    Dauert länger als der übrige Export — ChemDraw gibt die
    Reaktionsgleichung als Vektorgrafik aus und Inkscape rastert die
    Spektren; FastAPI führt die Funktion in einem Thread aus."""
    from .word_export import export_word

    mol = get_or_404(session, Molecule, molecule_id, lang)
    # Ein leerer Zielordner wäre Path(".") und damit der App-Ordner —
    # ausdrücklich abweisen statt still dorthin zu schreiben.
    target = Path(data.target_dir.strip()) if data.target_dir.strip() else None
    if target is None or not target.is_dir():
        raise HTTPException(422, T(lang, f"Zielordner existiert nicht: {data.target_dir}",
                                   f"Target folder does not exist: {data.target_dir}"))
    with paths.scan_scope():
        result = export_word(mol, target, lang)
    result["linked"] = _link_word_document(mol, result["file"])
    session.commit()
    return result


# ---------- Weitergabe: Transferdatei für einen anderen PC ----------

class TransferExportIn(BaseModel):
    target_dir: str
    password: str | None = None  # optional: Transferdatei verschlüsseln
    name: str | None = None  # optional: Bezeichnung (Dateiname + Anzeige beim Einlesen)


class TransferImportIn(BaseModel):
    path: str
    password: str | None = None  # nötig bei verschlüsselten Transferdateien


@router.post("/transfer/export")
def transfer_export(data: TransferExportIn, lang: str = Depends(get_lang)):
    """Erstellt eine Transferdatei (Datenbank + Bilder), die auf einem anderen
    PC mit derselben App eingelesen werden kann — optional passwortgeschützt."""
    target = Path(data.target_dir)
    if not target.is_dir():
        raise HTTPException(422, T(lang, f"Zielordner existiert nicht: {data.target_dir}",
                                   f"Target folder does not exist: {data.target_dir}"))
    try:
        return db.export_transfer(target, password=data.password or None,
                                  name=data.name)
    except FileNotFoundError:
        raise HTTPException(409, T(lang, "Keine Datenbank zum Übertragen gefunden",
                                   "No database found to transfer"))


@router.post("/transfer/import")
def transfer_import(data: TransferImportIn, lang: str = Depends(get_lang)):
    """Liest eine Transferdatei ein und ersetzt den aktuellen Stand
    (vorher wird automatisch ein Backup erstellt). 401 signalisiert dem
    Frontend: Passwort nötig bzw. falsch — erneut mit Passwort aufrufen."""
    src = Path(data.path)
    if not src.is_file():
        raise HTTPException(404, T(lang, f"Datei nicht gefunden: {data.path}",
                                   f"File not found: {data.path}"))
    try:
        return db.import_transfer(src, password=data.password or None)
    except db.TransferPasswordError as e:
        if e.reason == "required":
            raise HTTPException(401, T(lang,
                                       "Diese Transferdatei ist passwortgeschützt — bitte Passwort eingeben:",
                                       "This transfer file is password-protected — please enter the password:"))
        raise HTTPException(401, T(lang, "Falsches Passwort — bitte erneut eingeben:",
                                   "Wrong password — please try again:"))
    except ValueError:
        raise HTTPException(422, T(
            lang,
            "Keine gültige Transferdatei (ZIP mit app.db erwartet)",
            "Not a valid transfer file (expected a ZIP containing app.db)",
        ))


# ---------- Backups & Undo ----------

@router.get("/backups")
def backups_list():
    return db.list_backups()


@router.post("/backups", status_code=201)
def backups_create(lang: str = Depends(get_lang)):
    name = db.create_backup()
    if name is None:
        raise HTTPException(409, T(lang, "Keine Datenbank zum Sichern gefunden",
                                   "No database found to back up"))
    return {"name": name}


@router.post("/backups/{name}/restore")
def backups_restore(name: str, lang: str = Depends(get_lang)):
    # "-import" = gekennzeichnetes Backup von unmittelbar vor einem Transfer-Import
    if not re.fullmatch(r"app-[0-9-]+(-import)?\.(db|zip)", name):
        raise HTTPException(422, T(lang, "Ungültiger Backup-Name", "Invalid backup name"))
    try:
        db.restore_backup(name)
    except FileNotFoundError:
        raise HTTPException(404, T(lang, f"Backup nicht gefunden: {name}",
                                   f"Backup not found: {name}"))
    return {"ok": True}


@router.get("/undo")
def undo_info():
    return {"available": db.undo_count()}


@router.post("/undo")
def undo_last(lang: str = Depends(get_lang)):
    if not db.pop_undo():
        raise HTTPException(409, T(lang, "Nichts zum Rückgängigmachen vorhanden",
                                   "Nothing to undo"))
    return {"ok": True}


# ---------- Öffnen im Explorer / Standardprogramm ----------

class OpenIn(BaseModel):
    path: str
    reveal: bool = False  # True: den Ordner der Datei zeigen statt die Datei zu starten


def _norm_path(p: str) -> str:
    """Vergleichbare Pfad-Normalform (aufgelöst, Windows-typisch case-insensitiv)."""
    p = paths.to_portable(p)  # H:\… und \\server\… meinen dieselbe Datei
    try:
        resolved = Path(p).resolve()
    except OSError:
        resolved = Path(p)
    return os.path.normcase(str(resolved))


def _linked_paths(session: Session) -> set[str]:
    """Alle in der Datenbank referenzierten Pfade (normalisiert). Nur diese darf
    /open öffnen — sonst wäre der Endpunkt ein Startbefehl für beliebige Dateien
    und Programme auf dem Rechner."""
    linked: set[str] = set()
    mols = session.scalars(
        select(Molecule).options(selectinload(Molecule.entries).selectinload(DataEntry.files))
    ).all()
    for m in mols:
        for attr in (*_IMAGE_ATTR.values(), *_CDX_ATTR.values()):
            p = getattr(m, attr)
            if p:
                linked.add(_norm_path(image_abs(p)))
        for e in m.entries:
            for p in (e.folder_path, e.file_path, e.svg_path, e.svg2_path):
                if p:
                    linked.add(_norm_path(p))
            for f in e.files:
                if f.path:
                    linked.add(_norm_path(f.path))
    return linked


@router.post("/open")
def open_path(
    data: OpenIn, session: Session = Depends(get_session), lang: str = Depends(get_lang)
):
    """Öffnet eine in der App verlinkte Datei mit dem Standardprogramm bzw. einen
    Ordner im Explorer. Mit reveal=True öffnet sich statt der Datei ihr Ordner —
    so landet man beim Klick auf einen Pfad im Ordner und nicht in Word & Co.
    Nur in der Datenbank hinterlegte Pfade sind erlaubt."""
    p = Path(data.path)
    if not p.exists():
        raise HTTPException(404, T(lang, f"Pfad existiert nicht mehr: {data.path}",
                                   f"Path no longer exists: {data.path}"))
    if _norm_path(data.path) not in _linked_paths(session):
        raise HTTPException(403, T(lang,
                                   "Nur in der App verlinkte Pfade dürfen geöffnet werden",
                                   "Only paths linked in the app may be opened"))
    if data.reveal and p.is_file():
        p = p.parent  # verlinkte Ordner bleiben sie selbst, Dateien zeigen ihren Ordner
    osutil.open_path(str(p))
    return {"ok": True}


# ---------- Native Auswahl-Dialoge ----------

class DialogIn(BaseModel):
    kind: Literal["file", "folder"]
    filter: str = "any"
    initial: str | None = None  # Startordner, z. B. Ordner des bisherigen Pfads


@router.post("/dialog")
def native_dialog(data: DialogIn, lang: str = Depends(get_lang)):
    """Öffnet einen nativen Auswahl-Dialog auf dem Rechner. Blockiert, bis
    der Nutzer gewählt oder abgebrochen hat (path=null bei Abbruch)."""
    initial = paths.to_display(data.initial or "")  # Dialog zeigt lieber H:\ als \\server\
    if initial and not Path(initial).is_dir():
        initial = str(Path(initial).parent)
    try:
        path = open_dialog(data.kind, data.filter, initial, lang)
    except DialogBusyError:
        raise HTTPException(409, T(lang, "Es ist bereits ein Auswahl-Dialog geöffnet",
                                   "A selection dialog is already open"))
    return {"path": path}


# ---------- Datenordner & Sperre (mehrere PCs) ----------

class DataDirIn(BaseModel):
    path: str


# Setzt desktop.py: schließt das Programmfenster (statt SIGTERM, s. u.)
on_quit = None


def request_shutdown() -> None:
    """Die App sauber beenden — wie Strg+C im Serverfenster: uvicorn fährt
    herunter, der Lifespan sichert (nur falls nötig) und gibt die Sperre frei,
    danach endet der Prozess, und das schwarze Fenster schließt sich.

    SIGTERM statt SIGINT: kommt zusätzlich ein Strg+C, hieße ein zweites
    SIGINT für uvicorn „sofort abbrechen“ — ohne Backup und Freigabe. Ohne
    uvicorn-Handler (Server nicht im Hauptthread) würde SIGTERM den Prozess
    dagegen hart beenden; dann wird die Sperre hier selbst freigegeben.

    Im eigenen Programmfenster (desktop.py) schließt stattdessen das Fenster;
    desktop.py fährt danach den Server regulär herunter."""
    if on_quit is not None:
        on_quit()
    elif callable(signal.getsignal(signal.SIGTERM)):
        signal.raise_signal(signal.SIGTERM)
    else:
        db.close_db()
        os._exit(0)


@router.post("/shutdown")
def shutdown(background: BackgroundTasks):
    """Beenden-Knopf. Gesichert wird schon hier und nicht erst im Lifespan,
    damit die Oberfläche melden kann, wann das Backup fertig ist — das
    Beenden-Backup im Lifespan findet danach nichts Neues mehr. Heruntergefahren
    wird erst, nachdem die Antwort beim Browser ist."""
    backup = db.create_backup(only_if_changed=True)
    background.add_task(request_shutdown)
    return {"backup": backup, "read_only": db.is_read_only()}


@router.get("/update")
def update_status():
    """Update-Stand des gepackten Programms; beim ersten Aufruf je
    Programmstart wird auf GitHub nachgesehen (app/updater.py)."""
    return updater.check()


@router.post("/update/install")
def update_install(lang: str = Depends(get_lang)):
    """Bestätigtes Update: im Hintergrund laden und vorbereiten, dann die App
    beenden wie mit „Quit“ — das Hilfsskript tauscht aus und startet neu.
    Fortschritt über GET /update."""
    def ready() -> None:
        db.create_backup(only_if_changed=True)
        request_shutdown()

    try:
        return updater.start_install(ready)
    except RuntimeError:
        raise HTTPException(409, T(lang, "Kein Update verfügbar", "No update available"))


@router.get("/status")
def app_status():
    """Datenordner, Lesemodus und wer den Datensatz gerade hält. Im Lesemodus
    wird dabei geprüft, ob die fremde Sperre inzwischen weg ist — dann wird
    still auf Schreiben umgeschaltet (die Oberfläche fragt regelmäßig nach)."""
    db.refresh_lock_state()
    return db.status()


@router.post("/lock/takeover")
def lock_takeover():
    """Sperre bewusst übernehmen, obwohl ein anderer PC sie noch hält."""
    db.take_over_lock()
    return db.status()


@router.post("/settings/data-dir")
def set_data_dir(data: DataDirIn, lang: str = Depends(get_lang)):
    """Datenordner wechseln (z. B. auf ein Netzlaufwerk, um von mehreren PCs
    zu arbeiten). Leerer Ordner: aktueller Datensatz wird hineinkopiert;
    Ordner mit Datensatz: dieser wird geöffnet."""
    target = Path(data.path.strip())
    if not target.is_absolute():
        raise HTTPException(422, T(lang, "Bitte einen vollständigen Ordnerpfad angeben",
                                   "Please give a full folder path"))
    if not target.parent.exists():
        raise HTTPException(422, T(lang, f"Ordner nicht erreichbar: {target.parent}",
                                   f"Folder not reachable: {target.parent}"))
    try:
        result = db.switch_data_dir(target)
    except OSError as e:
        raise HTTPException(500, T(lang, f"Datenordner konnte nicht gewechselt werden: {e}",
                                   f"Could not switch data folder: {e}"))
    return {**db.status(), **result}


# ---------- Dashboard ----------

@router.get("/dashboard")
def dashboard(session: Session = Depends(get_session)):
    """Zahlen der Kopfzeile. Bewusst ohne molecule_summary: die Kennzahlen
    hängen nur an den Einträgen, nicht an den verlinkten Dateien — so kommt
    das Dashboard ganz ohne Datei-/Netzzugriffe aus."""
    molecules = session.scalars(select(Molecule).options(selectinload(Molecule.entries))).all()
    total = len(molecules)
    complete = sum(1 for m in molecules if completeness(m)[0] == "complete")

    by_type: dict[str, dict[str, int]] = {}
    for mol in molecules:
        for e in visible_entries(mol):
            if not e.required:
                continue
            stats = by_type.setdefault(e.type_code, {"required": 0, "present": 0})
            stats["required"] += 1
            stats["present"] += e.status == "present"

    return {
        "total_molecules": total,
        "complete_molecules": complete,
        "by_type": by_type,
    }
