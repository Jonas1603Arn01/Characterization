"""Export: kopiert alle verlinkten Daten nach
<Zielordner>/<Projekt>/<Molekül>/<Analytikmethode>/… und schreibt eine
Info-Datei. Notizen werden je Methode zusätzlich als .txt abgelegt. Nicht
mehr existierende Pfade werden übersprungen und als Warnung gemeldet.
"""
import re
import shutil
from datetime import datetime
from pathlib import Path

from . import db
from .datatypes import TYPE_LABELS
from .models import Molecule, Project

_INVALID = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize(name: str) -> str:
    return _INVALID.sub("_", name).strip(" .") or "unnamed"


def unique_path(p: Path) -> Path:
    if not p.exists():
        return p
    for i in range(2, 1000):
        candidate = p.with_name(f"{p.stem} ({i}){p.suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"Kein freier Name für {p}")


def export_molecule(mol: Molecule, target_dir: Path, lang: str = "en") -> dict:
    def T(de: str, en: str) -> str:
        return en if lang == "en" else de

    labels = TYPE_LABELS[lang]
    # <Zielordner>/<Projekt>/<Molekül>/, Analytikmethoden als Unterordner darin
    base = target_dir / sanitize(mol.project.name) / sanitize(mol.name)
    base.mkdir(parents=True, exist_ok=True)

    exported: list[str] = []
    warnings: list[str] = []
    stamp = datetime.now().strftime("%d.%m.%Y %H:%M" if lang == "de" else "%Y-%m-%d %H:%M")
    info: list[str] = [
        f"{T('Molekül', 'Molecule'):<14}{mol.name}",
        f"{T('Projekt', 'Project'):<14}{mol.project.name}",
        f"{'SMILES':<14}{mol.smiles or '—'}",
        f"{T('Summenformel', 'Formula'):<14}{mol.formula or '—'}",
        f"{T('Exakte Masse', 'Exact mass'):<14}{mol.exact_mass if mol.exact_mass is not None else '—'}",
        f"{T('Exportiert', 'Exported'):<14}{stamp}",
    ]
    if mol.physical_state:
        state = T("Feststoff", "solid") if mol.physical_state == "solid" else T("Öl", "oil")
        info.append(f"{T('Aggregatzustand', 'Physical state'):<14}{state}")
    if mol.color:
        info.append(f"{T('Farbe', 'Color'):<14}{mol.color}")
    if mol.consistency:
        info.append(f"{T('Beschaffenheit', 'Consistency'):<14}{mol.consistency}")
    if mol.literature_known:
        info.append(f"{T('Literatur', 'Literature'):<14}"
                    + T("literaturbekannt", "known compound")
                    + (f" — DOI: {mol.doi}" if mol.doi else ""))
        if mol.citation:
            info.append(f"{T('Zitat', 'Citation'):<14}{mol.citation}")
        if mol.si_path:
            info.append(f"{'SI':<14}{Path(mol.si_path).name}")
    if mol.sample_available:
        info.append(f"{T('Restsubstanz', 'Sample left'):<14}"
                    + (mol.sample_number or T("ja", "yes"))
                    + (f" — {mol.sample_comment}" if mol.sample_comment else ""))
    info.append("")

    def copy_into(src_str: str | None, dest_dir: Path, label: str, kind: str) -> None:
        if not src_str:
            return
        src = Path(src_str)
        if not src.exists():
            warnings.append(f"{label}: {kind} {T('nicht gefunden', 'not found')} — {src_str}")
            return
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = unique_path(dest_dir / src.name)
        if src.is_dir():
            shutil.copytree(src, dest)
        else:
            shutil.copy2(src, dest)
        exported.append(str(dest.relative_to(base)))

    for e in mol.entries:
        # Schmelzpunkt bei einem Öl nicht relevant -> nicht exportieren
        if mol.physical_state == "oil" and e.type_code == "mp":
            continue
        label = e.custom_label or labels[e.type_code]
        sub = base / sanitize(label)
        copy_into(e.file_path, sub, label, T("Datei", "file"))
        copy_into(e.svg_path, sub, label, T("Datei", "file"))
        copy_into(e.svg2_path, sub, label, T("Datei", "file"))
        copy_into(e.folder_path, sub, label, T("Ordner", "folder"))
        for f in e.files:  # zusätzliche Datei-Referenzen
            copy_into(f.path, sub, label, T("Datei", "file"))
        notes = [n.text.strip() for n in e.notes if n.text.strip()]
        if notes:
            # Notizen je Methode zusätzlich als eigene .txt-Datei
            sub.mkdir(parents=True, exist_ok=True)
            note_file = unique_path(sub / f"{T('Notizen', 'Notes')}.txt")
            note_file.write_text("\n\n".join(notes), encoding="utf-8")
            exported.append(str(note_file.relative_to(base)))
            info.append(f"{label} — {T('Notizen', 'notes')}:\n" + "\n".join(notes) + "\n")
        if e.mp_value is not None:
            info.append(f"{label}: {e.mp_value} °C\n")

    images = [
        (mol.image_path, T("Struktur", "Structure"),
         T("Strukturbild nicht gefunden", "Structure image not found")),
        (mol.scheme_path, T("Reaktionsschema", "Reaction scheme"),
         T("Reaktionsschema nicht gefunden", "Reaction scheme not found")),
        (mol.equation_path, T("Reaktionsgleichung", "Reaction equation"),
         T("Reaktionsgleichung nicht gefunden", "Reaction equation not found")),
        # Beim Einfügen aus ChemDraw mitgespeicherte Originaldateien (.cdx)
        (mol.image_cdx_path, T("Struktur", "Structure"),
         T("ChemDraw-Datei (Struktur) nicht gefunden",
           "ChemDraw file (structure) not found")),
        (mol.scheme_cdx_path, T("Reaktionsschema", "Reaction scheme"),
         T("ChemDraw-Datei (Reaktionsschema) nicht gefunden",
           "ChemDraw file (reaction scheme) not found")),
        (mol.equation_cdx_path, T("Reaktionsgleichung", "Reaction equation"),
         T("ChemDraw-Datei (Reaktionsgleichung) nicht gefunden",
           "ChemDraw file (reaction equation) not found")),
    ]
    for path_str, name, missing in images:
        if not path_str:
            continue
        src = db.image_file(path_str)  # App-eigene Bilder: nur Dateiname in der DB
        if src.exists():
            dest = unique_path(base / f"{name}{src.suffix}")
            shutil.copy2(src, dest)
            exported.append(dest.name)
        else:
            warnings.append(f"{missing} — {path_str}")

    # Supporting Information der Literaturstelle (PDF/Word) direkt in den Molekülordner
    if mol.si_path:
        si = Path(mol.si_path)
        if si.is_file():
            dest = unique_path(base / f"SI - {si.name}")
            shutil.copy2(si, dest)
            exported.append(dest.name)
        else:
            warnings.append(T("Supporting Information nicht gefunden",
                              "Supporting information not found") + f" — {mol.si_path}")

    (base / "Info.txt").write_text("\n".join(info), encoding="utf-8")
    exported.append("Info.txt")

    return {"target": str(base), "exported": exported, "warnings": warnings}


def export_project(project: Project, target_dir: Path, lang: str = "en") -> dict:
    """Exportiert alle Moleküle eines Projekts nach <Zielordner>/<Projekt>/…
    Warnungen werden pro Molekül vorangestellt gesammelt."""
    base = target_dir / sanitize(project.name)
    exported_total = 0
    warnings: list[str] = []
    for mol in project.molecules:
        res = export_molecule(mol, target_dir, lang)
        exported_total += len(res["exported"])
        warnings += [f"{mol.name}: {w}" for w in res["warnings"]]
    base.mkdir(parents=True, exist_ok=True)  # auch bei leerem Projekt anlegen
    return {
        "target": str(base),
        "molecule_count": len(project.molecules),
        "exported": exported_total,
        "warnings": warnings,
    }
