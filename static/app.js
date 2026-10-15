"use strict";

// ---------- Sprache / i18n ----------
const I18N = {
  de: {
    locale: "de-DE",
    search_ph: "Suche: Name, Formel, SMILES…",
    filter_all: "Alle",
    filter_complete: "Nur vollständige",
    filter_incomplete: "Nur unvollständige",
    new_project: "+ Projekt",
    stat_molecules: "Moleküle",
    stat_complete: "vollständig",
    add_molecule: "+ Molekül",
    delete_project: "Projekt löschen",
    count_molecules: (n) => `${n} Molekül${n === 1 ? "" : "e"}`,
    no_projects: "Noch keine Projekte — oben rechts „+ Projekt“ klicken.",
    no_hits: "Keine Treffer für Suche/Filter.",
    no_molecules: "Noch keine Moleküle.",
    progress: (a, b) => `${a}/${b} benötigte Daten vorhanden`,
    dead_paths: (n) => (n > 1 ? `${n} tote Pfade` : "1 toter Pfad"),
    dead_paths_title: "Verlinkte Pfade existieren nicht mehr — Detail öffnen",
    dlg_new_project: "Neues Projekt",
    project_name_ph: "Projektname",
    cancel: "Abbrechen",
    create: "Anlegen",
    dlg_new_mol: "Neues Molekül",
    mol_name_ph: "Name / ID (z. B. JA-042)",
    smiles_ph: "SMILES (optional)",
    mol_hint: "Summenformel und exakte Masse werden aus dem SMILES berechnet; die benötigten Datentypen lassen sich später im Detail anpassen.",
    theme_title: "Helles/dunkles Design umschalten",
    slot_image: "Struktur",
    slot_scheme: "Reaktionsschema",
    slot_equation: "Reaktionsgleichung",
    slot_empty: "Strg+V, Bild hierher ziehen oder „Wählen…“",
    pick_image: "Wählen…",
    paste_image: "Einfügen",
    paste_key: "Strg+V",
    paste_badge_title: "Strg+V fügt hier ein — Klick auf einen anderen Bereich wechselt das Ziel",
    not_an_image: "Keine Bilddatei",
    zoom_hint: "Klick: vergrößern",
    open_file: "Datei öffnen",
    clear_image: "Entfernen",
    image_missing: (p) => `⚠ Bilddatei nicht gefunden: ${p}`,
    open_cdx: "ChemDraw ⬈",
    open_cdx_title: (p) => `Beim Einfügen mitgespeicherte ChemDraw-Datei in ChemDraw öffnen\n${p}`,
    cdx_missing: (p) => `⚠ ChemDraw-Datei nicht gefunden: ${p}`,
    cdx_refreshing: "Bild wird aus der geänderten ChemDraw-Datei aktualisiert…",
    cdx_refresh_failed: (msg) => `⚠ Aktualisierung aus ChemDraw fehlgeschlagen: ${msg}`,
    copy_cdx: "Kopieren",
    copy_cdx_title: "ChemDraw-Zeichnung in die Zwischenablage kopieren — in ChemDraw bearbeitbar, in Word/PowerPoint als ChemDraw-Objekt einfügbar",
    copy_cdx_done: "✓ Kopiert",
    apply: "Übernehmen",
    exact_mass: "exakte Masse",
    state_na: "n. z.",
    state_na_title: "nicht zutreffend — zählt nicht zur Vollständigkeit",
    state_missing: "fehlt",
    state_present: "vorhanden",
    changed: "geändert",
    del_entry: "Eintrag löschen",
    not_linked: "nicht verlinkt",
    dead_path_title: "Pfad existiert nicht mehr",
    open_hint: "Doppelklick: Ordner öffnen",
    pick: "wählen…",
    change: "ändern…",
    unlink: "Verlinkung entfernen",
    text_ph: "Freitext, z. B. Shifts, Besonderheiten …",
    mp_ph: "z. B. 135.5",
    suggest: (label) => `„${label}“ jetzt als „vorhanden“ markieren?`,
    confirm_del_project: (name, n) => `Projekt „${name}“ mit ${n} Molekül(en) wirklich löschen?`,
    confirm_del_mol: (name) => `Molekül „${name}“ wirklich löschen?`,
    add_file: "+ Datei",
    add_note: "+ Notiz",
    file_label: "Datei",
    file_label_ph: "Bezeichnung…",
    note_label: "Notiz",
    in_document: "ins Word-Dokument",
    in_document_title: "Diesen Eintrag ins Word-Dokument übernehmen. Bei NMR-Messungen (z. B. „19F NMR“) ist das Häkchen beim Anlegen schon gesetzt; sie werden dann wie ¹H und ¹³C gesetzt.",
    del_note: "Notiz löschen",
    fmt_bold: "Fett (Strg+B)",
    fmt_italic: "Kursiv (Strg+I)",
    fmt_sup: "Hochgestellt (Strg+.)",
    fmt_sub: "Tiefgestellt (Strg+,)",
    fmt_round1: "Verschiebungen auf eine Nachkommastelle runden",
    fmt_round2: "Verschiebungen auf zwei Nachkommastellen runden",
    fmt_round_int: "Verschiebungen auf ganze Zahlen runden",
    fmt_round0: "Wellenzahlen auf ganze Zahlen runden",
    sym_title: "Sonderzeichen einfügen (−, °C, µ, α …)",
    sym_hint: "Klick fügt an der Cursorposition ein",
    sym_tab_common: "Häufig",
    sym_tab_greek: "Griechisch",
    sym_tab_scripts: "Hoch/tief",
    sym_tab_text: "Text",
    sym_recent: "Zuletzt verwendet",
    sym_signs: "Zeichen",
    sym_arrows: "Pfeile",
    sym_units: "Einheiten",
    sym_greek_lower: "Kleinbuchstaben",
    sym_greek_upper: "Großbuchstaben",
    sym_superscript: "Hochgestellt",
    sym_subscript: "Tiefgestellt",
    sym_punctuation: "Satzzeichen",
    sym_letters: "Buchstaben",
    quit: "Beenden",
    quit_title: "App beenden — vorher wird gesichert und der Datenordner für andere PCs freigegeben",
    quit_heading: "App beenden?",
    quit_text: "Vorher wird eine Sicherung erstellt (falls sich seit der letzten etwas geändert hat) und der Datenordner für andere PCs freigegeben. Das Fenster schließt sich danach von selbst.",
    quit_confirm: "Beenden",
    quit_running: "Sicherung wird erstellt … auf einem Netzlaufwerk kann das bis zu einer Minute dauern.",
    quit_done_heading: "App beendet",
    quit_done: (r) => (r.read_only ? "Die App war nur lesend geöffnet — keine Sicherung nötig."
      : r.backup ? `✓ Sicherung erstellt: ${r.backup}` : "✓ Seit der letzten Sicherung hat sich nichts geändert."),
    quit_done_hint: "Ist diese Seite noch offen, kannst du sie jetzt schließen; zum Weiterarbeiten die App wie gewohnt starten.",
    collapse_hint: "Ein-/ausklappen",
    drag_hint: "Klick: Details öffnen · Ziehen: Reihenfolge ändern oder in anderes Projekt verschieben",
    proj_drag_hint: "Ziehen: Reihenfolge der Projekte ändern",
    rename_hint: "Klick zum Umbenennen",
    phys_unset: "— Aggregatzustand —",
    phys_solid: "Feststoff",
    phys_oil: "Öl",
    color_ph: "Farbe (z. B. farblos)",
    consistency_ph: "Beschaffenheit (z. B. kristallin, viskos)",
    lit_known: "literaturbekannt",
    doi_ph: "DOI, z. B. 10.1021/jacs.0c01234",
    doi_open_hint: "Doppelklick: Paper öffnen",
    citation_ph: "Zitat, z. B. A. Müller, B. Schmidt, J. Am. Chem. Soc. 2020, 142, 1234–1240.",
    si_label: "SI",
    si_hint: "Supporting Information der Literaturstelle (PDF oder Word)",
    sample_left: "Substanz übrig",
    sample_number_ph: "Probennummer (z. B. JA-042-F2)",
    sample_comment_ph: "Vermerk, z. B. Verbindung nicht sauber genug …",
    sample_badge_title: "Noch Substanz übrig",
    proj_complete: (a, b) => `${a}/${b} vollständig`,
    other_ph: "Sonstiges hinzufügen (z. B. Elementaranalyse)",
    nucleus_pick: "— weiterer NMR-Kern —",
    nucleus_add: "NMR-Kern hinzufügen — Felder und Word-Häkchen wie bei ¹H und ¹³C",
    nucleus_decoupled: "{¹H}",
    nucleus_decoupled_title: "¹H-entkoppelt gemessen — steht so in der Bezeichnung („³¹P{¹H} NMR“)",
    nucleus_exists: (label) => `„${label}“ gibt es schon.`,
    fmt_head_title: "Kopfzeile mit Frequenz, Lösungsmittel und Temperatur einsetzen — übernommen von den schon erfassten Kernen dieses Moleküls",
    delete_molecule: "Molekül löschen",
    export: "Exportieren…",
    close: "Schließen",
    sec_props: "Eigenschaften",
    sec_entries: "Charakterisierungsdaten",
    export_ok: (n) => `✓ ${n} Element(e) exportiert nach`,
    export_warn: "⚠ Nicht gefunden (übersprungen):",
    export_project_ok: (mols, items) => `✓ ${mols} Molekül(e), ${items} Element(e) exportiert nach`,
    export_running: "Export läuft…",
    word_export: "Word-Dokument…",
    word_title: "Versuchsvorschrift als Word-Dokument schreiben — Reaktionsgleichung, Analytik und Spektren im Aufbau der Vorlage. Der Durchführungstext bleibt ein Platzhalter. Das fertige Dokument wird unter „Versuchsvorschrift“ verlinkt.",
    word_running: "Word-Dokument wird erstellt…",
    word_ok: (n) => `✓ Word-Dokument mit ${n} Spektr${n === 1 ? "um" : "en"} erstellt:`,
    word_linked: "unter „Versuchsvorschrift“ verlinkt",
    word_warn: "⚠ Hinweise:",
    undo_title: "Letzte Aktion rückgängig machen (Strg+Z)",
    backups: "Backups",
    backup_now: "Backup jetzt erstellen",
    backup_hint: "Automatische Backups (Datenbank + Bilder) beim Starten und Beenden der App; die letzten 10 bleiben erhalten. Sicherungen von unmittelbar vor dem Einlesen einer Transferdatei sind als „vor Import“ markiert und rotieren separat (letzte 20) — der Rückweg zum alten Datensatz bleibt so erhalten.",
    backup_import_tag: "vor Import",
    backup_created: "✓ Backup erstellt",
    restore: "Wiederherstellen",
    confirm_restore: (when) => `Backup vom ${when} wiederherstellen? Der aktuelle Stand wird ersetzt (mit ↩ bzw. Strg+Z rückgängig machbar).`,
    restore_done: "✓ Backup wiederhergestellt",
    no_backups: "Noch keine Backups vorhanden.",
    transfer_title: "Weitergabe an einen anderen PC",
    transfer_hint: "Transferdatei (Datenbank + Bilder) erstellen und auf einem anderen PC mit dieser App einlesen — dort sind Stand und Speicherort aller Daten sichtbar. Verlinkte Dateien wandern nicht mit; ihre Pfade bleiben als Verweis erhalten. Auf Wunsch mit Passwort schützbar.",
    transfer_export: "Transferdatei erstellen…",
    transfer_import: "Transferdatei einlesen…",
    transfer_running: "Übertragung läuft…",
    transfer_pw_prompt: "Optional: Passwort zum Schutz der Transferdatei (leer lassen = ohne Passwort). Es wird beim Einlesen auf dem anderen PC abgefragt.",
    transfer_name_prompt: "Optional: Bezeichnung für diese Transferdatei, z. B. „Stand Juli für Chef“ — sie wird Teil des Dateinamens und beim Einlesen angezeigt (leer lassen = nur Datum).",
    transfer_exported: (file, locked) =>
      `✓ Transferdatei erstellt${locked ? " (passwortgeschützt 🔒)" : ""}: ${file}`,
    confirm_import: (name) => `„${name}“ einlesen? Der aktuelle Stand auf diesem PC wird ersetzt (vorher wird automatisch ein Backup erstellt).`,
    transfer_imported: (r, when) =>
      `✓ ${r.name ? `„${r.name}“ eingelesen` : "Eingelesen"}: ${r.projects} Projekt(e), ${r.molecules} Molekül(e)` +
      (when ? ` — Stand vom ${when}` : "") +
      (r.computer ? ` (PC: ${r.computer})` : ""),
    local_path_title: "Liegt auf einem lokalen Laufwerk dieses PCs — von anderen PCs aus nicht erreichbar. Besser auf ein Netzlaufwerk verschieben und neu verlinken.",
    datadir_title: "Datenordner",
    datadir_hint: "Hier liegen Datenbank, Bilder und Backups. Um von mehreren PCs mit demselben Datensatz zu arbeiten, wähle einen Ordner auf einem Netzlaufwerk (z. B. H:\\…) und stelle auf jedem PC denselben Ordner ein. Ein leerer Ordner erhält eine Kopie des aktuellen Datensatzes; ein Ordner, der schon einen enthält, wird einfach geöffnet. Es arbeitet immer nur ein PC gleichzeitig schreibend — der andere sieht den Datensatz nur lesend.",
    datadir_label: "Aktuell:",
    datadir_change: "Datenordner wechseln…",
    datadir_confirm: (p) => `Ab jetzt mit dem Datenordner\n${p}\narbeiten?\n\nEnthält der Ordner bereits einen Datensatz, wird dieser geöffnet. Ist er leer, wird der aktuelle Datensatz (Datenbank + Bilder) hineinkopiert. Der bisherige Ordner bleibt unverändert liegen.`,
    datadir_switched: (p, copied) => `✓ Datenordner ist jetzt ${p}${copied ? " (Daten kopiert)" : ""}`,
    ro_text: (who, since) => `Nur lesend: Der Datensatz wird gerade auf „${who}“ bearbeitet${since ? ` (seit ${since})` : ""}. Änderungen sind hier erst möglich, wenn die App dort geschlossen wurde.`,
    ro_takeover: "Trotzdem übernehmen",
    ro_confirm_takeover: (who) => `Sperre von „${who}“ übernehmen? Nur sinnvoll, wenn die App dort nicht mehr läuft (z. B. nach Absturz) — sonst gehen dortige Änderungen verloren.`,
    short: { procedure: "Vorschrift", nmr_1h: "¹H", nmr_13c: "¹³C", nmr_2d: "2D", ms: "MS", ir: "IR", mp: "Smp." },
  },
  en: {
    locale: "en-US",
    search_ph: "Search: name, formula, SMILES…",
    filter_all: "All",
    filter_complete: "Complete only",
    filter_incomplete: "Incomplete only",
    new_project: "+ Project",
    stat_molecules: "Molecules",
    stat_complete: "complete",
    add_molecule: "+ Molecule",
    delete_project: "Delete project",
    count_molecules: (n) => `${n} molecule${n === 1 ? "" : "s"}`,
    no_projects: "No projects yet — click “+ Project” in the top right.",
    no_hits: "No matches for search/filter.",
    no_molecules: "No molecules yet.",
    progress: (a, b) => `${a}/${b} required data present`,
    dead_paths: (n) => (n > 1 ? `${n} broken paths` : "1 broken path"),
    dead_paths_title: "Linked paths no longer exist — open details",
    dlg_new_project: "New project",
    project_name_ph: "Project name",
    cancel: "Cancel",
    create: "Create",
    dlg_new_mol: "New molecule",
    mol_name_ph: "Name / ID (e.g. JA-042)",
    smiles_ph: "SMILES (optional)",
    mol_hint: "The molecular formula and exact mass are calculated from the SMILES; the required data types can be adjusted later in the detail view.",
    theme_title: "Toggle light/dark theme",
    slot_image: "Structure",
    slot_scheme: "Reaction scheme",
    slot_equation: "Reaction equation",
    slot_empty: "Ctrl+V, drop an image here or “Choose…”",
    pick_image: "Choose…",
    paste_image: "Paste",
    paste_key: "Ctrl+V",
    paste_badge_title: "Ctrl+V pastes here — click another slot to switch",
    not_an_image: "Not an image file",
    zoom_hint: "Click to enlarge",
    open_file: "Open file",
    clear_image: "Remove",
    image_missing: (p) => `⚠ Image file not found: ${p}`,
    open_cdx: "ChemDraw ⬈",
    open_cdx_title: (p) => `Open the ChemDraw file saved along with the paste in ChemDraw\n${p}`,
    cdx_missing: (p) => `⚠ ChemDraw file not found: ${p}`,
    cdx_refreshing: "Updating image from the edited ChemDraw file…",
    cdx_refresh_failed: (msg) => `⚠ Update from ChemDraw failed: ${msg}`,
    copy_cdx: "Copy",
    copy_cdx_title: "Copy the ChemDraw drawing to the clipboard — pastes editable into ChemDraw and as a ChemDraw object into Word/PowerPoint",
    copy_cdx_done: "✓ Copied",
    apply: "Apply",
    exact_mass: "exact mass",
    state_na: "n/a",
    state_na_title: "not applicable — not counted toward completeness",
    state_missing: "missing",
    state_present: "present",
    changed: "changed",
    del_entry: "Delete entry",
    not_linked: "not linked",
    dead_path_title: "Path no longer exists",
    open_hint: "Double-click to open the folder",
    pick: "choose…",
    change: "change…",
    unlink: "Remove link",
    text_ph: "Free text, e.g. shifts, remarks…",
    mp_ph: "e.g. 135.5",
    suggest: (label) => `Mark “${label}” as “present” now?`,
    confirm_del_project: (name, n) => `Delete project “${name}” with ${n} molecule(s)?`,
    confirm_del_mol: (name) => `Delete molecule “${name}”?`,
    add_file: "+ File",
    add_note: "+ Note",
    file_label: "File",
    file_label_ph: "Label…",
    note_label: "Note",
    in_document: "into Word document",
    in_document_title: "Include this entry in the Word document. For NMR measurements (e.g. “19F NMR”) the box is already ticked when you create the entry; they are then typeset like ¹H and ¹³C.",
    del_note: "Delete note",
    fmt_bold: "Bold (Ctrl+B)",
    fmt_italic: "Italic (Ctrl+I)",
    fmt_sup: "Superscript (Ctrl+.)",
    fmt_sub: "Subscript (Ctrl+,)",
    fmt_round1: "Round shifts to one decimal",
    fmt_round2: "Round shifts to two decimals",
    fmt_round_int: "Round shifts to whole numbers",
    fmt_round0: "Round wavenumbers to whole numbers",
    sym_title: "Insert special character (−, °C, µ, α …)",
    sym_hint: "Click to insert at the cursor",
    sym_tab_common: "Common",
    sym_tab_greek: "Greek",
    sym_tab_scripts: "Sup/sub",
    sym_tab_text: "Text",
    sym_recent: "Recently used",
    sym_signs: "Signs",
    sym_arrows: "Arrows",
    sym_units: "Units",
    sym_greek_lower: "Lowercase",
    sym_greek_upper: "Uppercase",
    sym_superscript: "Superscript",
    sym_subscript: "Subscript",
    sym_punctuation: "Punctuation",
    sym_letters: "Letters",
    quit: "Quit",
    quit_title: "Close the app — takes a backup first and releases the data folder for other PCs",
    quit_heading: "Quit the app?",
    quit_text: "A backup is taken first (if anything changed since the last one) and the data folder is released for other PCs. The window then closes by itself.",
    quit_confirm: "Quit",
    quit_running: "Creating backup … on a network drive this can take up to a minute.",
    quit_done_heading: "App closed",
    quit_done: (r) => (r.read_only ? "The app was open read-only — no backup needed."
      : r.backup ? `✓ Backup created: ${r.backup}` : "✓ Nothing changed since the last backup."),
    quit_done_hint: "If this page is still open, you can close it now; to keep working, start the app as usual.",
    collapse_hint: "Collapse/expand",
    drag_hint: "Click to open details · drag to reorder or move to another project",
    proj_drag_hint: "Drag to reorder projects",
    rename_hint: "Click to rename",
    phys_unset: "— Physical state —",
    phys_solid: "Solid",
    phys_oil: "Oil",
    color_ph: "Color (e.g. colorless)",
    consistency_ph: "Consistency (e.g. crystalline, viscous)",
    lit_known: "known in the literature",
    doi_ph: "DOI, e.g. 10.1021/jacs.0c01234",
    doi_open_hint: "Double-click to open the paper",
    citation_ph: "Citation, e.g. A. Miller, B. Smith, J. Am. Chem. Soc. 2020, 142, 1234–1240.",
    si_label: "SI",
    si_hint: "Supporting information of the reference (PDF or Word)",
    sample_left: "sample left",
    sample_number_ph: "Sample number (e.g. JA-042-F2)",
    sample_comment_ph: "Remark, e.g. compound not clean enough…",
    sample_badge_title: "Sample of this compound still left",
    proj_complete: (a, b) => `${a}/${b} complete`,
    other_ph: "Add custom entry (e.g. elemental analysis)",
    nucleus_pick: "— another NMR nucleus —",
    nucleus_add: "Add NMR nucleus — same fields and Word tick as ¹H and ¹³C",
    nucleus_decoupled: "{¹H}",
    nucleus_decoupled_title: "Measured ¹H-decoupled — appears in the label (“³¹P{¹H} NMR”)",
    nucleus_exists: (label) => `“${label}” already exists.`,
    fmt_head_title: "Insert the header with frequency, solvent and temperature — taken from the nuclei already recorded for this molecule",
    delete_molecule: "Delete molecule",
    export: "Export…",
    close: "Close",
    sec_props: "Properties",
    sec_entries: "Characterization data",
    export_ok: (n) => `✓ ${n} item(s) exported to`,
    export_warn: "⚠ Not found (skipped):",
    export_project_ok: (mols, items) => `✓ ${mols} molecule(s), ${items} item(s) exported to`,
    export_running: "Exporting…",
    word_export: "Word document…",
    word_title: "Write the procedure as a Word document — reaction equation, analytics and spectra in the layout of the template. The procedure text stays a placeholder. The finished document is linked under “Procedure”.",
    word_running: "Creating Word document…",
    word_ok: (n) => `✓ Word document created with ${n} spectr${n === 1 ? "um" : "a"}:`,
    word_linked: "linked under “Procedure”",
    word_warn: "⚠ Notes:",
    undo_title: "Undo last action (Ctrl+Z)",
    backups: "Backups",
    backup_now: "Create backup now",
    backup_hint: "Automatic backups (database + images) when the app starts and closes; the last 10 are kept. Backups taken right before importing a transfer file are marked “before import” and rotate separately (last 20) — so the way back to the old dataset is preserved.",
    backup_import_tag: "before import",
    backup_created: "✓ Backup created",
    restore: "Restore",
    confirm_restore: (when) => `Restore the backup from ${when}? The current state will be replaced (undoable via ↩ / Ctrl+Z).`,
    restore_done: "✓ Backup restored",
    no_backups: "No backups yet.",
    transfer_title: "Transfer to another PC",
    transfer_hint: "Create a transfer file (database + images) and import it on another PC running this app — it shows the status and storage location of all data there. Linked files do not travel along; their paths are kept as references. Can be password-protected on request.",
    transfer_export: "Create transfer file…",
    transfer_import: "Import transfer file…",
    transfer_running: "Transferring…",
    transfer_pw_prompt: "Optional: password to protect the transfer file (leave empty = no password). It will be asked for when importing on the other PC.",
    transfer_name_prompt: "Optional: a name for this transfer file, e.g. “July status for boss” — it becomes part of the file name and is shown when importing (leave empty = date only).",
    transfer_exported: (file, locked) =>
      `✓ Transfer file created${locked ? " (password-protected 🔒)" : ""}: ${file}`,
    confirm_import: (name) => `Import “${name}”? The current data on this PC will be replaced (a backup is created first).`,
    transfer_imported: (r, when) =>
      `✓ ${r.name ? `Imported “${r.name}”` : "Imported"}: ${r.projects} project(s), ${r.molecules} molecule(s)` +
      (when ? ` — data as of ${when}` : "") +
      (r.computer ? ` (PC: ${r.computer})` : ""),
    local_path_title: "Stored on a local drive of this PC — not reachable from other PCs. Better move it to a network drive and link it again.",
    datadir_title: "Data folder",
    datadir_hint: "Where the database, images and backups live. To work from several PCs with the same dataset, pick a folder on a network drive (e.g. H:\\…) and set the same folder on every PC. An empty folder receives a copy of the current dataset; a folder that already contains one is simply opened. Only one PC edits at a time — the other one sees the dataset read-only.",
    datadir_label: "Current:",
    datadir_change: "Change data folder…",
    datadir_confirm: (p) => `Work with the data folder\n${p}\nfrom now on?\n\nIf the folder already contains a dataset, it is opened. If it is empty, the current dataset (database + images) is copied into it. The previous folder stays untouched.`,
    datadir_switched: (p, copied) => `✓ Data folder is now ${p}${copied ? " (data copied)" : ""}`,
    ro_text: (who, since) => `Read-only: the dataset is currently being edited on “${who}”${since ? ` (since ${since})` : ""}. Changes are possible here once the app has been closed there.`,
    ro_takeover: "Take over anyway",
    ro_confirm_takeover: (who) => `Take over the lock from “${who}”? Only sensible if the app is no longer running there (e.g. after a crash) — otherwise changes made there will be lost.`,
    short: { procedure: "Proc.", nmr_1h: "¹H", nmr_13c: "¹³C", nmr_2d: "2D", ms: "MS", ir: "IR", mp: "m.p." },
  },
};

// Default language is English; the DE/EN toggle in the header persists the choice.
let lang = localStorage.getItem("lang") === "de" ? "de" : "en";
const t = (key) => I18N[lang][key];

// ---------- API ----------
// Ausweichtext, wenn der Server kein detail-Feld liefert
const httpError = (status) => (lang === "en" ? `Error ${status}` : `Fehler ${status}`);

// Arbeitsanzeige: dauert eine Anfrage länger als einen Augenblick, zeigt ein
// schmaler Balken am oberen Rand (auch über geöffneten Dialogen), dass die
// App arbeitet. Auswahl-Dialoge warten auf den Nutzer, die Statusabfrage
// läuft im Hintergrund — beide zählen nicht.
const BUSY_DELAY_MS = 150;
let busyCount = 0;
let busyTimer = null;

function trackBusy(delta) {
  busyCount += delta;
  if (busyCount > 0) {
    if (busyTimer === null) {
      busyTimer = setTimeout(() => {
        if (busyCount > 0) document.body.classList.add("busy");
      }, BUSY_DELAY_MS);
    }
    return;
  }
  clearTimeout(busyTimer);
  busyTimer = null;
  document.body.classList.remove("busy");
}

async function api(path, options = {}) {
  const quiet = path === "/dialog" || path === "/status";
  if (!quiet) trackBusy(1);
  try {
    return await apiRequest(path, options);
  } finally {
    if (!quiet) trackBusy(-1);
  }
}

async function apiRequest(path, options) {
  const resp = await fetch("/api" + path, {
    headers: { "Content-Type": "application/json", "X-Lang": lang },
    ...options,
  });
  if (!resp.ok) {
    let msg = httpError(resp.status);
    try { msg = (await resp.json()).detail || msg; } catch {}
    const err = new Error(msg);
    err.status = resp.status; // z. B. 401 = Passwort nötig/falsch (Transfer-Import)
    throw err;
  }
  return resp.status === 204 ? null : resp.json();
}

// ---------- Native Auswahl-Dialoge ----------
// Ein nativer Dialog nimmt den Fenster-Fokus und gibt ihn beim Schließen
// zurück. Das löst den focus-Listener aus (Rückkehr aus ChemDraw) und
// damit ein komplettes Neuladen — obwohl der Aufrufer gleich darauf selbst
// refresh() aufruft. Solche Fokus-Ereignisse werden deshalb nur vorgemerkt
// und nachgeholt, wenn bis zum Ende des Dialogs kein refresh() gelaufen ist
// (z. B. weil der Nutzer abgebrochen hat) — es geht also nichts verloren.
const DIALOG_FOCUS_GRACE_MS = 1500; // der Fokus kann kurz nach der Antwort zurückkommen
let dialogDepth = 0;      // laufende Auswahl-Dialoge
let focusPending = false; // vorgemerktes Fokus-Ereignis
let focusPendingSeq = 0;  // Stand von refreshSeq, als es vorgemerkt wurde

async function nativeDialog(body) {
  dialogDepth++;
  try {
    return await api("/dialog", { method: "POST", body: JSON.stringify(body) });
  } finally {
    setTimeout(() => {
      if (--dialogDepth > 0 || !focusPending) return;
      focusPending = false;
      // Nur nachholen, wenn seither wirklich nicht neu geladen wurde
      if (refreshSeq === focusPendingSeq && detailMolId !== null) refreshMolecule(detailMolId);
    }, DIALOG_FOCUS_GRACE_MS);
  }
}

// ---------- Zustand ----------
let projects = [];
let datatypes = [];
let typeFields = {};
// Katalog der NMR-Kerne, die als eigener Eintrag dazukommen können (api.list_nuclei):
// Bezeichnung, Nachkommastellen der Verschiebungen, „{¹H}"-Vorbelegung
let nuclei = [];
let lastDashboard = null;
let detailMolId = null; // aktuell geöffnetes Molekül
let refreshSeq = 0;     // zählt abgeschlossene refresh()-Läufe (siehe nativeDialog)
let dragMolId = null;   // Molekül, das gerade gezogen wird
let dragProjId = null;  // Projekt, das gerade gezogen wird (Reihenfolge ändern)

// Drei Bild-Slots im Detail: Strukturbild, Reaktionsschema, Reaktionsgleichung.
// pasteSlot bestimmt, wohin Strg+V einfügt (per Klick auf den Block wechselbar).
const IMG_SLOTS = ["image", "scheme", "equation"];
let pasteSlot = "image";

// Der Server liefert je Slot <slot>_path/_exists/_version, <slot>_cdx_path/_exists, <slot>_stale
function slotOf(mol, slot) {
  return {
    path: mol[`${slot}_path`], exists: mol[`${slot}_exists`], field: `${slot}_path`,
    cdx: mol[`${slot}_cdx_path`], cdxExists: mol[`${slot}_cdx_exists`], stale: mol[`${slot}_stale`],
  };
}

// Bild-URL mit der Versionskennung der Bilddatei: gleiche Datei -> gleiche
// URL, der Browser behält das Bild. (Früher hing die URL am Änderungsstempel
// des Moleküls — jede Kleinigkeit lud dann alle Bilder neu vom Datenordner.)
function imageUrl(mol, slot) {
  const v = mol[`${slot}_version`] || mol.updated_at;
  return `/api/molecules/${mol.id}/${slot}?v=${encodeURIComponent(v)}`;
}

// Eingeklappte Projekte überleben Neuladen (localStorage)
function collapsedSet() {
  try { return new Set(JSON.parse(localStorage.getItem("collapsedProjects") || "[]")); }
  catch { return new Set(); }
}

function toggleCollapsed(projId) {
  const set = collapsedSet();
  if (set.has(projId)) set.delete(projId); else set.add(projId);
  localStorage.setItem("collapsedProjects", JSON.stringify([...set]));
  renderProjects();
}

const $ = (sel) => document.querySelector(sel);

function typeLabel(code) {
  const dt = datatypes.find((d) => d.code === code);
  return dt ? dt.label[lang] : code;
}

function entryLabel(entry, short = false) {
  if (entry.type_code === "other") {
    // Der Server liefert die Bezeichnung gesetzt („19F NMR" -> „¹⁹F NMR");
    // auf der Kachel steht bei einer NMR-Messung nur der Kern.
    const label = entry.display_label || entry.custom_label || typeLabel("other");
    return short && entry.is_nmr ? label.replace(/\s*NMR$/, "") : label;
  }
  if (short) return t("short")[entry.type_code] || entry.type_code;
  return typeLabel(entry.type_code);
}

// Katalogeintrag zum Kern einer Bezeichnung („19F NMR" -> Fluor); unbekannter
// Kern -> undefined, dann bleibt es bei den allgemeinen Vorgaben.
function nucleusOf(entry) {
  if (!entry.is_nmr) return undefined;
  const key = (entry.custom_label || "").match(/^\s*(\d{1,3})\s*([A-Z][a-z]?)/);
  return key && nuclei.find((n) => n.code.startsWith(`${key[1]}${key[2]} `));
}

// Welche festen Felder hat dieser Eintrag? Ein zusätzlicher NMR-Kern bekommt
// dieselben wie ¹H und ¹³C (Mess-Ordner, MNova-Datei, SVG-Spektrum), nicht nur
// das allgemeine Datei-Feld von „Sonstiges".
function entryFields(entry) {
  if (entry.is_nmr && typeFields.other_nmr) return typeFields.other_nmr;
  return typeFields[entry.type_code] || [];
}

// ---------- Statische Texte übersetzen ----------
function applyStaticTexts() {
  document.documentElement.lang = lang;
  $("#search").placeholder = t("search_ph");
  const opts = $("#filter").options;
  opts[0].textContent = t("filter_all");
  opts[1].textContent = t("filter_complete");
  opts[2].textContent = t("filter_incomplete");
  $("#btn-new-project").textContent = t("new_project");

  $("#dlg-project h3").textContent = t("dlg_new_project");
  $("#project-name").placeholder = t("project_name_ph");
  $("#dlg-project [data-close]").textContent = t("cancel");
  $("#project-save").textContent = t("create");

  $("#dlg-molecule h3").textContent = t("dlg_new_mol");
  $("#mol-name").dataset.placeholder = t("mol_name_ph");
  $("#mol-smiles").placeholder = t("smiles_ph");
  $("#mol-hint").textContent = t("mol_hint");
  $("#dlg-molecule [data-close]").textContent = t("cancel");
  $("#mol-save").textContent = t("create");

  $("#btn-undo").title = t("undo_title");
  $("#btn-theme").title = t("theme_title");
  $("#btn-backup").textContent = t("backups");
  $("#btn-quit").textContent = t("quit");
  $("#btn-quit").title = t("quit_title");
  $("#dlg-quit [data-close]").textContent = t("cancel");
  $("#quit-confirm").textContent = t("quit_confirm");
  $("#dlg-backup h3").textContent = t("backups");
  $("#backup-hint").textContent = t("backup_hint");
  $("#backup-now").textContent = t("backup_now");
  $("#transfer-title").textContent = t("transfer_title");
  $("#transfer-hint").textContent = t("transfer_hint");
  $("#transfer-export").textContent = t("transfer_export");
  $("#transfer-import").textContent = t("transfer_import");
  $("#datadir-title").textContent = t("datadir_title");
  $("#datadir-hint").textContent = t("datadir_hint");
  $("#datadir-label").textContent = t("datadir_label");
  $("#datadir-change").textContent = t("datadir_change");
  $("#ro-takeover").textContent = t("ro_takeover");
  if (appStatus) renderStatus(appStatus);
  $("#dlg-backup [data-close]").textContent = t("close");

  for (const slot of IMG_SLOTS) {
    $(`#img-title-${slot}`).textContent = t(`slot_${slot}`);
    $(`#img-empty-text-${slot}`).textContent = t("slot_empty");
    $(`#img-pick-${slot}`).textContent = t("pick_image");
    $(`#img-paste-${slot}`).textContent = t("paste_image");
    $(`#img-clear-${slot}`).textContent = t("clear_image");
    $(`#img-cdx-${slot}`).textContent = t("open_cdx");
    $(`#img-copy-${slot}`).textContent = t("copy_cdx");
    const badge = $(`#paste-badge-${slot}`);
    badge.textContent = t("paste_key");
    badge.title = t("paste_badge_title");
  }
  $("#sec-props").textContent = t("sec_props");
  $("#sec-entries").textContent = t("sec_entries");
  $("#zoom-open").textContent = t("open_file");
  $("#dlg-zoom [data-close]").title = t("close");
  $("#lit-label").textContent = t("lit_known");
  $("#lit-doi").placeholder = t("doi_ph");
  $("#lit-doi").title = t("doi_open_hint");
  $("#lit-citation").dataset.placeholder = t("citation_ph");
  $("#sample-label").textContent = t("sample_left");
  $("#sample-number").placeholder = t("sample_number_ph");
  $("#sample-comment").dataset.placeholder = t("sample_comment_ph");
  const ps = $("#phys-state").options;
  ps[0].textContent = t("phys_unset");
  ps[1].textContent = t("phys_solid");
  ps[2].textContent = t("phys_oil");
  $("#phys-color").placeholder = t("color_ph");
  $("#phys-consistency").placeholder = t("consistency_ph");
  $("#detail-title").title = t("rename_hint");
  $("#detail-title").dataset.placeholder = t("mol_name_ph");
  $("#detail-smiles").placeholder = t("smiles_ph");
  $("#detail-smiles-save").textContent = t("apply");
  $("#other-label").placeholder = t("other_ph");
  renderNucleusPicker();
  $("#detail-delete").textContent = t("delete_molecule");
  $("#detail-export").textContent = t("export");
  $("#detail-word").textContent = t("word_export");
  $("#detail-word").title = t("word_title");
  $("#dlg-detail [data-close]").textContent = t("close");
}

// ---------- Laden & Rendern ----------
// Nach jeder Änderung wird neu geladen. Betrifft sie nur ein Molekül (fast
// alles im Detail-Dialog), reichen dieses Molekül und die Kopfzahlen — die
// ganze Projektliste mit allen Pfadprüfungen muss dafür nicht übers Netz.
// Die Läufe reihen sich hintereinander, damit ein Lauf, der vor einer
// Änderung begonnen hat, keinen neueren Stand überschreibt; was während eines
// Laufs angefordert wird, erledigt der nächste Lauf gesammelt.
let loadChain = Promise.resolve();
let nextLoad = null;        // geplanter, noch nicht begonnener Lauf
let nextLoadFull = false;
const nextLoadMols = new Set();

function scheduleLoad(molId) {
  if (molId == null) nextLoadFull = true;
  else nextLoadMols.add(molId);
  if (!nextLoad) {
    nextLoad = loadChain = loadChain.catch(() => {}).then(() => {
      nextLoad = null;
      const full = nextLoadFull;
      const ids = [...nextLoadMols];
      nextLoadFull = false;
      nextLoadMols.clear();
      return full ? loadAll() : loadMolecules(ids);
    });
  }
  return nextLoad;
}

// Alles neu laden (Projekte, Reihenfolge, Verschieben, Undo, Backups …)
function refresh() {
  return scheduleLoad(null);
}

// Nur ein Molekül neu laden (Änderungen im Detail-Dialog)
function refreshMolecule(molId) {
  return scheduleLoad(molId);
}

async function loadAll() {
  const [proj, dash, undoInfo] = await Promise.all([
    api("/projects"), api("/dashboard"), api("/undo"),
  ]);
  projects = proj;
  applyLoaded(dash, undoInfo);
}

async function loadMolecules(ids) {
  const [mols, dash, undoInfo] = await Promise.all([
    Promise.all(ids.map((id) => api(`/molecules/${id}`).catch((e) => {
      if (e.status === 404) return null;  // inzwischen gelöscht
      throw e;
    }))),
    api("/dashboard"), api("/undo"),
  ]);
  // Passt ein Molekül nicht mehr an seinen Platz (gelöscht, verschoben),
  // stimmt die Liste insgesamt nicht mehr -> komplett laden
  if (!mols.every(replaceMolecule)) return loadAll();
  applyLoaded(dash, undoInfo);
}

function replaceMolecule(mol) {
  if (!mol) return false;
  const proj = projects.find((p) => p.id === mol.project_id);
  const i = proj ? proj.molecules.findIndex((m) => m.id === mol.id) : -1;
  if (i < 0) return false;
  proj.molecules[i] = mol;
  return true;
}

function applyLoaded(dash, undoInfo) {
  lastDashboard = dash;
  $("#btn-undo").disabled = !undoInfo.available;
  renderDashboard(dash);
  renderProjects();
  if (detailMolId !== null) renderDetail();
  refreshSeq++;
}

function renderDashboard(dash) {
  const el = $("#dashboard");
  const pct = dash.total_molecules
    ? Math.round((100 * dash.complete_molecules) / dash.total_molecules) : 0;
  // Zwei betonte Hauptkacheln …
  let html = `
    <div class="stat-row">
      <div class="stat"><div class="num">${dash.total_molecules}</div><div class="label">${t("stat_molecules")}</div></div>
      <div class="stat">
        <div class="num">${dash.complete_molecules} <small style="font-weight:400;color:var(--text-dim)">(${pct} %)</small></div>
        <div class="label">${t("stat_complete")}</div>
        <div class="bar"><div style="width:${pct}%"></div></div>
      </div>
    </div>`;
  // … darunter die Methoden-Statistik als kompakte Pillen
  let methods = "";
  for (const dt of datatypes) {
    const s = dash.by_type[dt.code];
    if (!s) continue;
    const p = s.required ? Math.round((100 * s.present) / s.required) : 0;
    methods += `
      <div class="stat mini">
        <span class="num">${s.present}/${s.required}</span>
        <span class="label">${esc(dt.label[lang])}</span>
        <span class="bar"><div style="width:${p}%"></div></span>
      </div>`;
  }
  if (methods) html += `<div class="stat-row methods">${methods}</div>`;
  el.innerHTML = html;
}

function moleculeMatches(mol) {
  const q = $("#search").value.trim().toLowerCase();
  const f = $("#filter").value;
  if (f !== "all" && mol.completeness !== f) return false;
  if (!q) return true;
  return [mol.name, mol.formula, mol.smiles].some(
    (v) => v && foldScripts(v.toLowerCase()).includes(foldScripts(q))
  );
}

// Hoch-/tiefgestellte Ziffern zählen in der Suche wie normale: „CDCl3"
// findet auch den formatierten Namen „CDCl₃"
const RAISED_DIGITS = "⁰¹²³⁴⁵⁶⁷⁸⁹₀₁₂₃₄₅₆₇₈₉";
function foldScripts(s) {
  return s.replace(/[⁰¹²³⁴⁵⁶⁷⁸⁹₀₁₂₃₄₅₆₇₈₉]/g, (c) => String(RAISED_DIGITS.indexOf(c) % 10));
}

// Molekül-Karten werden wiederverwendet, solange sich ihr Molekül nicht
// geändert hat: Neuzeichnen nach einer Änderung (oder beim Tippen in der
// Suche) baut dann nur die geänderte Karte neu, statt alle samt Bildern.
let cardCache = new Map();  // Molekül-ID -> { sig, el }

function cachedCard(mol, next) {
  const sig = `${lang}|${JSON.stringify(mol)}`;
  const hit = cardCache.get(mol.id);
  let el;
  if (hit && hit.sig === sig) {
    el = hit.el;
    el.classList.remove("dragging", "insert-before", "insert-after");  // Reste eines Ziehens
  } else {
    el = molCard(mol);
  }
  next.set(mol.id, { sig, el });
  return el;
}

function renderProjects() {
  const el = $("#projects");
  el.innerHTML = "";
  if (!projects.length) {
    cardCache = new Map();
    el.innerHTML = `<div class="empty">${t("no_projects")}</div>`;
    return;
  }
  const nextCards = new Map();
  const collapsed = collapsedSet();
  for (const p of projects) {
    const mols = p.molecules.filter(moleculeMatches);
    const done = p.molecules.filter((m) => m.completeness === "complete").length;
    const total = p.molecules.length;
    const pct = total ? Math.round((100 * done) / total) : 0;
    const isCollapsed = collapsed.has(p.id);
    const progress = total ? `
      <span class="proj-progress ${done === total ? "all-done" : ""}">
        ${t("proj_complete")(done, total)}
        <span class="proj-bar"><span style="width:${pct}%"></span></span>
      </span>` : "";
    const sec = document.createElement("section");
    sec.className = "project" + (isCollapsed ? " collapsed" : "");
    sec.innerHTML = `
      <div class="project-head">
        <span class="grip" draggable="true" title="${t("proj_drag_hint")}">⠿</span>
        <button class="chev" data-toggle-proj="${p.id}" title="${t("collapse_hint")}">${isCollapsed ? "▸" : "▾"}</button>
        <h2 data-toggle-proj="${p.id}">${esc(p.name)} <span class="count">· ${t("count_molecules")(p.molecules.length)}</span></h2>
        ${progress}
        <button data-add-mol="${p.id}">${t("add_molecule")}</button>
        <button data-export-proj="${p.id}">${t("export")}</button>
        <button class="danger" data-del-proj="${p.id}">${t("delete_project")}</button>
      </div>
      <div class="proj-export-msg" data-msg-proj="${p.id}"></div>
      <div class="mol-grid"></div>`;
    const grid = sec.querySelector(".mol-grid");
    if (!isCollapsed) {
      for (const mol of mols) grid.appendChild(cachedCard(mol, nextCards));
      if (!mols.length) {
        grid.innerHTML = `<div class="hint">${p.molecules.length ? t("no_hits") : t("no_molecules")}</div>`;
      }
    }
    attachDropTarget(sec, p);
    attachProjectReorder(sec, p);
    el.appendChild(sec);
  }
  // Gerade ausgeblendete Karten (eingeklappt, weggefiltert) bleiben vorgemerkt
  for (const p of projects) {
    for (const mol of p.molecules) {
      if (!nextCards.has(mol.id) && cardCache.has(mol.id)) nextCards.set(mol.id, cardCache.get(mol.id));
    }
  }
  cardCache = nextCards;
}

// Projekt-Reihenfolge per Drag & Drop: gezogen wird am ⠿-Griff, eine
// Akzentlinie zeigt die Einfügeposition (oberhalb/unterhalb je Mausposition)
function attachProjectReorder(sec, project) {
  const grip = sec.querySelector(".grip");
  grip.addEventListener("dragstart", (ev) => {
    dragProjId = project.id;
    ev.dataTransfer.setData("text/plain", `proj:${project.id}`);
    ev.dataTransfer.effectAllowed = "move";
    ev.dataTransfer.setDragImage(sec, 24, 24);
    sec.classList.add("dragging");
  });
  grip.addEventListener("dragend", () => {
    dragProjId = null;
    document.querySelectorAll(".project").forEach((x) =>
      x.classList.remove("dragging", "insert-before", "insert-after"));
  });
  sec.addEventListener("dragover", (ev) => {
    if (dragProjId === null || dragProjId === project.id) return;
    ev.preventDefault();
    ev.dataTransfer.dropEffect = "move";
    const r = sec.getBoundingClientRect();
    const before = ev.clientY < r.top + r.height / 2;
    sec.classList.toggle("insert-before", before);
    sec.classList.toggle("insert-after", !before);
  });
  sec.addEventListener("dragleave", (ev) => {
    if (!sec.contains(ev.relatedTarget)) sec.classList.remove("insert-before", "insert-after");
  });
  sec.addEventListener("drop", async (ev) => {
    if (dragProjId === null || dragProjId === project.id) return;
    ev.preventDefault();
    const before = sec.classList.contains("insert-before");
    sec.classList.remove("insert-before", "insert-after");
    const ids = projects.map((p) => p.id).filter((id) => id !== dragProjId);
    const idx = ids.indexOf(project.id);
    ids.splice(before ? idx : idx + 1, 0, dragProjId);
    dragProjId = null;
    try {
      await api("/projects/reorder", { method: "POST", body: JSON.stringify({ order: ids }) });
      await refresh();
    } catch (e) {
      alert(e.message);
    }
  });
}

// Projekt-Sektion als Drop-Ziel für Molekül-Karten aus ANDEREN Projekten
// (innerhalb des eigenen Projekts wird stattdessen auf Karten umsortiert)
function attachDropTarget(sec, project) {
  sec.addEventListener("dragover", (ev) => {
    if (dragMolId === null) return;
    const dragged = findMol(dragMolId);
    if (!dragged || dragged.project_id === project.id) return;
    ev.preventDefault();
    ev.dataTransfer.dropEffect = "move";
    sec.classList.add("drop-target");
  });
  sec.addEventListener("dragleave", (ev) => {
    if (!sec.contains(ev.relatedTarget)) sec.classList.remove("drop-target");
  });
  sec.addEventListener("drop", async (ev) => {
    ev.preventDefault();
    sec.classList.remove("drop-target");
    const molId = Number(ev.dataTransfer.getData("text/plain")) || dragMolId;
    dragMolId = null;
    const mol = findMol(molId);
    if (!mol || mol.project_id === project.id) return;
    try {
      await api(`/molecules/${molId}`, {
        method: "PATCH",
        body: JSON.stringify({ project_id: project.id }),
      });
      await refresh();
    } catch (e) {
      alert(e.message);
    }
  });
}

// Ganzes Projekt exportieren (Zielordner wählen, alle Moleküle darunter)
async function exportProject(projId, btn) {
  const msg = document.querySelector(`[data-msg-proj="${projId}"]`);
  if (!msg) return;
  msg.className = "proj-export-msg";
  msg.textContent = "";
  btn.disabled = true;
  try {
    const res = await nativeDialog({ kind: "folder" });
    if (!res.path) return;
    msg.textContent = t("export_running");
    const result = await api(`/projects/${projId}/export`, {
      method: "POST",
      body: JSON.stringify({ target_dir: res.path }),
    });
    msg.innerHTML = `
      <div class="msg-ok">${t("export_project_ok")(result.molecule_count, result.exported)}<br><code>${esc(result.target)}</code></div>
      ${result.warnings.length ? `
        <div class="msg-warn">${t("export_warn")}
          <ul>${result.warnings.map((w) => `<li>${esc(w)}</li>`).join("")}</ul>
        </div>` : ""}`;
  } catch (e) {
    msg.className = "proj-export-msg error";
    msg.textContent = e.message;
  } finally {
    btn.disabled = false;
  }
}

function molCard(mol) {
  const card = document.createElement("div");
  // sample-left: unvollständig wird gelb statt rot markiert (Restsubstanz da)
  card.className = `mol-card ${mol.completeness}` + (mol.sample_available ? " sample-left" : "");
  card.dataset.molId = mol.id;
  card.draggable = true;
  card.title = t("drag_hint");
  card.addEventListener("dragstart", (ev) => {
    dragMolId = mol.id;
    ev.dataTransfer.setData("text/plain", String(mol.id));
    ev.dataTransfer.effectAllowed = "move";
    card.classList.add("dragging");
  });
  card.addEventListener("dragend", () => {
    card.classList.remove("dragging");
    document.querySelectorAll(".drop-target").forEach((x) => x.classList.remove("drop-target"));
    document.querySelectorAll(".mol-card").forEach((x) => x.classList.remove("insert-before", "insert-after"));
    // Klick direkt nach dem Ziehen nicht als Karten-Klick werten
    setTimeout(() => { dragMolId = null; }, 100);
  });
  attachMolReorder(card, mol);
  const meta = [mol.formula, mol.exact_mass ? mol.exact_mass.toFixed(4) : null]
    .filter(Boolean).join(" · ");
  const img = mol.image_path && mol.image_exists
    ? `<img class="mol-img" loading="lazy" alt="" src="${imageUrl(mol, "image")}">`
    : "";
  const warn = mol.broken_paths
    ? `<span class="warn-badge" title="${t("dead_paths_title")}">⚠ ${t("dead_paths")(mol.broken_paths)}</span>`
    : "";
  // Symbol zusätzlich zur Farbe (Rot-Grün-Schwäche + schnelleres Scannen)
  const sym = { present: "✓ ", missing: "○ ", na: "" };
  const chips = mol.entries
    .map((e) => `<span class="chip ${e.status}" title="${esc(entryLabel(e))}">${sym[e.status] || ""}${esc(entryLabel(e, true))}</span>`)
    .join("");
  const lit = mol.literature_known
    ? `<span class="lit-badge" title="${esc([mol.doi || t("lit_known"), mol.citation,
        mol.si_path ? `SI: ${mol.si_path}` : ""].filter(Boolean).join("\n"))}">Lit.</span>` : "";
  const sample = mol.sample_available
    ? `<span class="sample-badge" title="${esc([t("sample_badge_title"), mol.sample_number,
        mol.sample_comment].filter(Boolean).join("\n"))}">⚗${mol.sample_number ? " " + esc(mol.sample_number) : ""}</span>`
    : "";
  card.innerHTML = `
    ${img}
    <div class="mol-name">${mol.name_html || esc(mol.name)}${lit}${sample}</div>
    <div class="mol-meta">${esc(meta)}${warn ? " " + warn : ""}</div>
    <div class="chips">${chips}</div>
    <div class="progress">${t("progress")(mol.present_count, mol.required_count)}</div>`;
  return card;
}

// Reihenfolge innerhalb des Projekts: eine gezogene Karte des SELBEN Projekts
// wird vor/hinter dieser Karte einsortiert (Akzentlinie je Mausposition);
// Karten aus anderen Projekten laufen weiter über das Sektions-Drop (Verschieben)
function attachMolReorder(card, mol) {
  const sameProject = () => {
    if (dragMolId === null || dragMolId === mol.id) return false;
    const dragged = findMol(dragMolId);
    return dragged !== null && dragged.project_id === mol.project_id;
  };
  card.addEventListener("dragover", (ev) => {
    if (!sameProject()) return;
    ev.preventDefault();
    ev.stopPropagation();  // Sektion nicht als Verschiebe-Ziel markieren
    ev.dataTransfer.dropEffect = "move";
    const r = card.getBoundingClientRect();
    const before = ev.clientX < r.left + r.width / 2;
    card.classList.toggle("insert-before", before);
    card.classList.toggle("insert-after", !before);
  });
  card.addEventListener("dragleave", (ev) => {
    if (!card.contains(ev.relatedTarget)) card.classList.remove("insert-before", "insert-after");
  });
  card.addEventListener("drop", async (ev) => {
    if (!sameProject()) return;
    ev.preventDefault();
    ev.stopPropagation();
    const before = card.classList.contains("insert-before");
    card.classList.remove("insert-before", "insert-after");
    const proj = projects.find((p) => p.id === mol.project_id);
    const ids = proj.molecules.map((m) => m.id).filter((id) => id !== dragMolId);
    const idx = ids.indexOf(mol.id);
    ids.splice(before ? idx : idx + 1, 0, dragMolId);
    dragMolId = null;
    try {
      await api("/molecules/reorder", { method: "POST", body: JSON.stringify({ order: ids }) });
      await refresh();
    } catch (e) {
      alert(e.message);
    }
  });
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

// ---------- Verlinkte Pfade ----------
// Ein voller Pfad in einer schmalen Zeile ist unlesbar: abgeschnitten wird
// ausgerechnet der Dateiname, also der einzige Teil, der die Zeilen
// unterscheidet. Darum zeigen wir „Laufwerk … letzter Ordner" klein und
// gedimmt und den Datei-/Ordnernamen betont dahinter; der volle Pfad
// steht weiterhin im Tooltip.
const ICON_FILE =
  '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3" ' +
  'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
  '<path d="M9 1.8H4.4A1.4 1.4 0 0 0 3 3.2v9.6a1.4 1.4 0 0 0 1.4 1.4h7.2a1.4 1.4 0 0 0 1.4-1.4V5.8z"/>' +
  '<path d="M9 1.8v3.2a.8.8 0 0 0 .8.8H13"/></svg>';
const ICON_FOLDER =
  '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3" ' +
  'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
  '<path d="M2 4.2a1.2 1.2 0 0 1 1.2-1.2h2.9l1.5 1.7h5.2A1.2 1.2 0 0 1 14 5.9v6a1.2 1.2 0 0 1-1.2 1.2H3.2A1.2 1.2 0 0 1 2 11.9z"/></svg>';

// Trennt den letzten Pfadteil (Datei- oder Ordnername) vom Rest
function splitPath(value) {
  const norm = String(value || "").replace(/[\\/]+$/, "");
  const cut = Math.max(norm.lastIndexOf("\\"), norm.lastIndexOf("/"));
  if (cut < 0) return { dir: "", name: norm };
  return { dir: norm.slice(0, cut), name: norm.slice(cut + 1) };
}

// Kürzt den Ordnerteil auf „Wurzel … Elternordner" — Laufwerk bzw. Server
// bleibt sichtbar (lokal oder Netz?), dazu der unmittelbar übergeordnete Ordner
function shortDir(dir) {
  if (!dir) return "";
  const unc = /^\\\\/.test(dir);
  const sep = dir.includes("\\") || unc ? "\\" : "/";
  const parts = dir.replace(/^[\\/]+/, "").split(/[\\/]+/).filter(Boolean);
  const root = (unc ? sep + sep : "") + (parts.shift() || "");
  if (!parts.length) return root + sep;
  if (parts.length === 1) return root + sep + parts[0] + sep;
  return root + sep + "…" + sep + parts[parts.length - 1] + sep;
}

// Pfadanzeige einer Zeile; ohne Wert die gedimmte „nicht verlinkt"-Fassung
function pathEl(value, { folder = false, dead = false, hint = "" } = {}) {
  const el = document.createElement("span");
  el.className = "path" + (value ? " openable" : " unset") + (value && dead ? " dead" : "");
  if (!value) {
    el.innerHTML = `<span class="path-icon"></span><span class="path-name">${esc(t("not_linked"))}</span>`;
    if (hint) el.title = hint;
    return el;
  }
  const { dir, name } = splitPath(value);
  el.innerHTML =
    `<span class="path-icon">${folder ? ICON_FOLDER : ICON_FILE}</span>` +
    `<span class="path-dir">${esc(shortDir(dir))}</span>` +
    `<span class="path-name">${esc(name)}</span>`;
  el.title = `${value}\n${t("open_hint")}`;
  return el;
}

// Knöpfe am Zeilenende („ändern…", ✕) sammeln — sie stehen damit in allen
// Zeilen exakt untereinander und treten optisch zurück
function rowActions(row) {
  const box = document.createElement("div");
  box.className = "row-actions";
  row.appendChild(box);
  return box;
}

// ---------- Detail-Dialog ----------
function findMol(id) {
  for (const p of projects) {
    const m = p.molecules.find((m) => m.id === id);
    if (m) return m;
  }
  return null;
}

// Wert aus dem Serverstand übernehmen — außer in dem Feld, in dem gerade
// geschrieben wird: dessen Eingabe ist neuer und wird beim Verlassen
// gespeichert. Sonst wischte eine zwischendurch eintreffende Antwort (etwa
// die des gerade verlassenen Felds) das Getippte wieder weg.
function setValue(el, value) {
  if (el !== document.activeElement) el.value = value;
}

function renderDetail() {
  const mol = findMol(detailMolId);
  if (!mol) { $("#dlg-detail").close(); return; }
  setRich($("#detail-title"), mol.name_html, mol.name);
  setValue($("#detail-smiles"), mol.smiles || "");
  $("#detail-meta").textContent = mol.formula
    ? `${mol.formula} · ${t("exact_mass")} ${mol.exact_mass.toFixed(4)}` : "";

  // Aggregatzustand / Farbe / Beschaffenheit
  $("#phys-state").value = mol.physical_state || "";
  setValue($("#phys-color"), mol.color || "");
  setValue($("#phys-consistency"), mol.consistency || "");

  // Literaturbekannt + DOI
  $("#lit-known").checked = mol.literature_known;
  const doiInput = $("#lit-doi");
  setValue(doiInput, mol.doi || "");
  doiInput.style.display = mol.literature_known ? "" : "none";
  setRich($("#lit-citation"), mol.citation_html, mol.citation);
  $("#lit-cite-row").style.display = mol.literature_known ? "" : "none";
  renderSiRow(mol);

  // Substanz übrig: Probennummer + Vermerk nur bei gesetztem Haken
  $("#sample-available").checked = mol.sample_available;
  setValue($("#sample-number"), mol.sample_number || "");
  setRich($("#sample-comment"), mol.sample_comment_html, mol.sample_comment);
  $("#sample-number").style.display = mol.sample_available ? "" : "none";
  $("#sample-comment-row").style.display = mol.sample_available ? "" : "none";

  // Strukturbild + Reaktionsschema
  for (const slot of IMG_SLOTS) {
    const s = slotOf(mol, slot);
    const img = $(`#img-view-${slot}`);
    const hasImg = Boolean(s.path && s.exists);
    if (hasImg) {
      const url = imageUrl(mol, slot);
      if (img.getAttribute("src") !== url) img.src = url;
      img.style.display = "";
      img.title = `${s.path}\n${t("zoom_hint")}`;
    } else {
      img.removeAttribute("src");
      img.style.display = "none";
    }
    $(`#img-block-${slot}`).classList.toggle("has-img", hasImg);
    $(`#img-empty-${slot}`).style.display = hasImg ? "none" : "";
    $(`#img-clear-${slot}`).style.display = s.path ? "" : "none";
    // ChemDraw-Originaldatei (nur nach Einfügen aus ChemDraw vorhanden)
    const cdxBtn = $(`#img-cdx-${slot}`);
    cdxBtn.hidden = !(s.cdx && s.cdxExists);
    if (!cdxBtn.hidden) cdxBtn.title = t("open_cdx_title")(s.cdx);
    const copyBtn = $(`#img-copy-${slot}`);
    copyBtn.hidden = cdxBtn.hidden;
    copyBtn.title = t("copy_cdx_title");
    const warnings = [];
    if (s.path && !s.exists) warnings.push(t("image_missing")(s.path));
    if (s.cdx && s.cdxExists === false) warnings.push(t("cdx_missing")(s.cdx));
    const cdxKey = `${mol.id}:${slot}`;
    if (cdxRefreshing.has(cdxKey)) warnings.push(t("cdx_refreshing"));
    else if (s.stale && cdxFailed.has(cdxKey)) warnings.push(t("cdx_refresh_failed")(cdxFailed.get(cdxKey)));
    $(`#img-warn-${slot}`).textContent = warnings.join(" · ");
  }
  updatePasteTarget();
  refreshStaleCdx(mol);
  renderDetailEntries(mol);
}

// ---------- Einträge im Detail: nur Geändertes neu aufbauen ----------
// Eintragsblöcke und ihre Zeilen werden beim Neuladen nur dann neu gebaut,
// wenn sich ihre Daten geändert haben; alles andere bleibt als DOM-Knoten
// stehen. Wer gerade in einer Notiz schreibt, während die Antwort auf eine
// andere Änderung eintrifft, behält so Fokus, Cursor und das noch nicht
// Gespeicherte — und das Neuzeichnen kostet kaum noch etwas.
let detailNodes = new Map();  // Schlüssel -> { sig, node } des letzten Aufbaus
let detailNodesMol = null;    // Molekül, zu dem die gemerkten Knoten gehören

// Knoten zum Schlüssel: der gemerkte, wenn seine Daten gleich geblieben sind
// (oder keep() ihn trotz geänderter Daten für aktuell hält), sonst neu gebaut
function reuseNode(next, key, data, build, keep) {
  const sig = JSON.stringify(data);
  const hit = detailNodes.get(key);
  const node = hit && (hit.sig === sig || (keep && keep(hit.node))) ? hit.node : build();
  next.set(key, { sig, node });
  return node;
}

// Kinder auf die gewünschte Folge bringen, ohne bleibende Knoten zu bewegen
// (Herausnehmen und Wiedereinsetzen würde ihnen den Fokus nehmen)
function syncChildren(parent, nodes) {
  const want = new Set(nodes);
  for (const child of [...parent.children]) if (!want.has(child)) child.remove();
  nodes.forEach((node, i) => {
    if (parent.children[i] !== node) parent.insertBefore(node, parent.children[i] || null);
  });
}

function renderDetailEntries(mol) {
  if (detailNodesMol !== mol.id) {
    detailNodes = new Map();
    detailNodesMol = mol.id;
  }
  const box = $("#detail-entries");
  const active = document.activeElement;
  const activeKey = box.contains(active) ? active.dataset.fkey : undefined;
  const next = new Map();
  syncChildren(box, mol.entries.map((e) => entryBlock(e, next)));
  detailNodes = next;
  // Musste das Feld mit dem Fokus doch neu gebaut werden, dorthin zurück
  if (activeKey && !active.isConnected) {
    const again = box.querySelector(`[data-fkey="${CSS.escape(activeKey)}"]`);
    if (again) {
      again.focus();
      if (again.isContentEditable) {
        const sel = getSelection();
        sel.selectAllChildren(again);
        sel.collapseToEnd();
      }
    }
  }
}

// Zeigt die Notiz schon genau das, was der Server jetzt liefert? (Typisch
// direkt nach ihrem eigenen Speichern — dann bleibt das Feld samt Cursor stehen.)
function noteShows(row, n) {
  const ed = row.querySelector(".note-edit");
  if (!ed) return false;
  const probe = document.createElement("div");
  probe.innerHTML = n.html || textToHtml(n.text);
  return cleanNoteHtml(ed) === cleanNoteHtml(probe);
}

// Daten, die eine feste Feldzeile anzeigt (Pfad, Existenz, Laufwerk, Beschriftung)
function fieldData(e, f) {
  if (f.key === "value") return e.mp_value;
  return ["path", "exists", "local", "label"].map((k) => e[`${f.key}_${k}`]);
}

// ---------- Bild aus geänderter ChemDraw-Datei aktualisieren ----------
// Wurde die per „ChemDraw ⬈" geöffnete .cdx bearbeitet und gespeichert, ist
// das Bild veraltet (Server meldet image_stale/scheme_stale). Der Server
// rendert es dann über ChemDraw neu — automatisch, sobald das Detail offen
// ist bzw. das Fenster nach dem ChemDraw-Ausflug wieder den Fokus bekommt.
const cdxRefreshing = new Set(); // "molId:slot" mit laufender Aktualisierung
const cdxFailed = new Map();     // "molId:slot" -> Fehlermeldung (kein Auto-Retry)

async function refreshStaleCdx(mol) {
  for (const slot of IMG_SLOTS) {
    const s = slotOf(mol, slot);
    const key = `${mol.id}:${slot}`;
    if (!s.stale || !s.cdxExists || cdxRefreshing.has(key) || cdxFailed.has(key)) continue;
    cdxRefreshing.add(key);
    if (detailMolId === mol.id) $(`#img-warn-${slot}`).textContent = t("cdx_refreshing");
    try {
      await api(`/molecules/${mol.id}/${slot}/refresh`, { method: "POST" });
      cdxFailed.delete(key);
    } catch (e) {
      cdxFailed.set(key, e.message);
    } finally {
      cdxRefreshing.delete(key);
    }
    await refreshMolecule(mol.id);
  }
}

// Rückkehr aus ChemDraw: beim Fokuswechsel zurück ins App-Fenster nachsehen,
// ob eine .cdx inzwischen neuer ist als ihr Bild (refreshMolecule ->
// renderDetail -> refreshStaleCdx erledigt dann das Neu-Rendern)
window.addEventListener("focus", () => {
  if (detailMolId === null) return;
  if (dialogDepth > 0) {  // Fokus kommt vom Auswahl-Dialog, nicht von ChemDraw
    focusPending = true;
    focusPendingSeq = refreshSeq;
    return;
  }
  refreshMolecule(detailMolId);
});

// Ein Eintrag: Kopf (Status, Bezeichnung, Stempel) und Feldzeilen — jedes
// Teil wird nur neu gebaut, wenn sich seine Daten geändert haben
function entryBlock(e, next) {
  const wrap = reuseNode(next, `entry:${e.id}`, e.id, () => {
    const el = document.createElement("div");
    const fields = document.createElement("div");
    fields.className = "entry-fields";
    el.appendChild(fields);
    return el;
  });
  wrap.className = "entry" + (e.status === "na" ? " na" : "");
  const head = reuseNode(next, `head:${e.id}`,
    [lang, e.status, e.type_code, e.custom_label, e.display_label, e.is_nmr, e.updated_at],
    () => entryHead(e));
  const fields = wrap.querySelector(":scope > .entry-fields");

  const rows = [];
  // Eigene Einträge: kommen sie ins Word-Dokument? (Feste Datentypen immer)
  if (e.type_code === "other") {
    rows.push(reuseNode(next, `indoc:${e.id}`, [lang, e.in_document], () => inDocumentRow(e)));
  }
  for (const f of entryFields(e)) {
    rows.push(reuseNode(next, `field:${e.id}:${f.key}`, [lang, f, fieldData(e, f)], () => fieldRow(e, f)));
  }
  for (const f of e.files) {  // beliebig viele Dateien
    rows.push(reuseNode(next, `file:${f.id}`, [lang, f], () => extraFileRow(f)));
  }
  // Notizen hängen zusätzlich an Art und Bezeichnung des Eintrags (Rundungs-
  // und Kopfzeilen-Knopf); nach dem eigenen Speichern bleiben sie stehen
  const noteCtx = JSON.stringify([lang, e.type_code, e.custom_label, e.is_nmr]);
  const noteNode = (key, data, n) => reuseNode(next, key, [noteCtx, data], () => {
    const row = noteRow(n, e);
    row.dataset.ctx = noteCtx;
    return row;
  }, (row) => row.dataset.ctx === noteCtx && noteShows(row, n));
  for (const n of e.notes) rows.push(noteNode(`note:${n.id}`, n, n));  // beliebig viele Notizen
  // Datentypen mit dauerhaftem Notizfeld (Versuchsvorschrift -> Durchführung)
  // zeigen es auch dann, wenn noch nichts darin steht
  const noteSpec = (datatypes.find((d) => d.code === e.type_code) || {}).note;
  if (noteSpec && noteSpec.always && e.notes.length === 0) {
    const empty = { id: null, text: "", html: null };
    rows.push(noteNode(`note-new:${e.id}`, null, empty));
  }
  rows.push(reuseNode(next, `add:${e.id}`, lang, () => addButtonsRow(e)));

  syncChildren(fields, rows);
  syncChildren(wrap, [head, fields]);
  return wrap;
}

function entryHead(e) {
  const stamp = new Date(e.updated_at).toLocaleString(t("locale"), {
    dateStyle: "short", timeStyle: "short",
  });
  const head = document.createElement("div");
  head.className = "entry-head";
  head.innerHTML = `
    <span class="status-dot ${e.status}"></span>
    <div class="entry-label">
      ${esc(entryLabel(e))}
      <span class="stamp">${t("changed")} ${stamp}</span>
    </div>
    <div class="seg" data-entry="${e.id}">
      <button data-state="na" class="${e.status === "na" ? "on-na" : ""}" title="${t("state_na_title")}">${t("state_na")}</button>
      <button data-state="missing" class="${e.status === "missing" ? "on-missing" : ""}">${t("state_missing")}</button>
      <button data-state="present" class="${e.status === "present" ? "on-present" : ""}">${t("state_present")}</button>
    </div>
    ${e.type_code === "other" ? `<button class="icon-btn" data-del-entry="${e.id}" title="${t("del_entry")}">✕</button>` : ""}`;
  return head;
}

// Supporting Information (PDF/Word) der Literaturstelle: eine Datei je Molekül,
// nur bei „literaturbekannt" sichtbar; öffnen per Doppelklick, entfernen per ✕
function renderSiRow(mol) {
  const row = $("#lit-si-row");
  row.innerHTML = "";
  row.style.display = mol.literature_known ? "" : "none";
  if (!mol.literature_known) return;

  const label = document.createElement("span");
  label.className = "field-label";
  label.textContent = t("si_label");
  label.title = t("si_hint");
  row.appendChild(label);

  const current = mol.si_path;
  const path = pathEl(current, { dead: mol.si_exists === false, hint: t("si_hint") });
  if (current) {
    path.addEventListener("dblclick", () => guard("#detail-error", async () => {
      await api("/open", { method: "POST", body: JSON.stringify({ path: current, reveal: true }) });
    }));
  }
  row.appendChild(path);

  if (current && mol.si_exists === false) {
    const warn = document.createElement("span");
    warn.className = "warn-badge";
    warn.textContent = "⚠";
    warn.title = t("dead_path_title");
    row.appendChild(warn);
  } else if (current && mol.si_local) {
    row.appendChild(localBadge());
  }

  const acts = rowActions(row);
  const pick = document.createElement("button");
  pick.className = "btn-sm";
  pick.textContent = current ? t("change") : t("pick");
  pick.addEventListener("click", () => guard("#detail-error", async () => {
    pick.disabled = true;
    try {
      const res = await nativeDialog({ kind: "file", filter: "si", initial: current || null });
      if (!res.path) return;
      await api(`/molecules/${mol.id}`, {
        method: "PATCH",
        body: JSON.stringify({ si_path: res.path }),
      });
      await refreshMolecule(mol.id);
    } finally {
      pick.disabled = false;
    }
  }));
  acts.appendChild(pick);

  if (current) {
    const del = document.createElement("button");
    del.className = "icon-btn";
    del.textContent = "✕";
    del.title = t("unlink");
    del.addEventListener("click", () => guard("#detail-error", async () => {
      await api(`/molecules/${mol.id}`, { method: "PATCH", body: JSON.stringify({ si_path: "" }) });
      await refreshMolecule(mol.id);
    }));
    acts.appendChild(del);
  }
}

// Zusätzliche Datei-Referenz: frei benennbar, öffnen per Doppelklick, entfernen per ✕
function extraFileRow(f) {
  const molId = detailMolId;  // Zeilen gibt es nur im geöffneten Detail
  const row = document.createElement("div");
  row.className = "field-row";
  const label = document.createElement("input");
  label.className = "field-label file-label-input";
  label.value = f.label || "";
  label.placeholder = t("file_label_ph");
  label.dataset.fileId = f.id;
  label.dataset.fkey = `file:${f.id}`;
  label.addEventListener("blur", () => {
    if (label.value === (f.label || "")) return;
    guard("#detail-error", async () => {
      await api(`/files/${f.id}`, { method: "PATCH", body: JSON.stringify({ label: label.value }) });
      await refreshMolecule(molId);
    });
  });
  label.addEventListener("keydown", (ev) => { if (ev.key === "Enter") label.blur(); });
  row.appendChild(label);

  const path = pathEl(f.path, { dead: f.exists === false });
  path.addEventListener("dblclick", () => guard("#detail-error", async () => {
    await api("/open", { method: "POST", body: JSON.stringify({ path: f.path, reveal: true }) });
  }));
  row.appendChild(path);

  if (f.exists === false) {
    const warn = document.createElement("span");
    warn.className = "warn-badge";
    warn.textContent = "⚠";
    warn.title = t("dead_path_title");
    row.appendChild(warn);
  } else if (f.local) {
    row.appendChild(localBadge());
  }

  // Verlinkung auf eine andere Datei umstellen (wie „ändern…" bei den festen Feldern)
  const acts = rowActions(row);
  const pick = document.createElement("button");
  pick.className = "btn-sm";
  pick.textContent = t("change");
  pick.addEventListener("click", () => guard("#detail-error", async () => {
    pick.disabled = true;
    try {
      const res = await nativeDialog({ kind: "file", filter: "any", initial: f.path });
      if (!res.path) return;
      await api(`/files/${f.id}`, { method: "PATCH", body: JSON.stringify({ path: res.path }) });
      await refreshMolecule(molId);
    } finally {
      pick.disabled = false;
    }
  }));
  acts.appendChild(pick);

  const del = document.createElement("button");
  del.className = "icon-btn";
  del.textContent = "✕";
  del.title = t("unlink");
  del.addEventListener("click", () => guard("#detail-error", async () => {
    await api(`/files/${f.id}`, { method: "DELETE" });
    await refreshMolecule(molId);
  }));
  acts.appendChild(del);
  return row;
}

// ---------- Formatierte Notizen ----------
// Notizen sind contenteditable-Felder mit fett/kursiv/hoch-/tiefgestellt.
// Gespeichert wird bereinigtes HTML (nur b, i, sup, sub, br); der Server
// leitet daraus den Klartext für Export & Co. ab. Alte Notizen ohne HTML
// werden aus ihrem Text aufgebaut.
const NOTE_TAGS = { B: "b", STRONG: "b", I: "i", EM: "i", SUP: "sup", SUB: "sub", BR: "br" };
const NOTE_FORMATS = [
  ["<b>B</b>", "bold", "fmt_bold"],
  ["<i>I</i>", "italic", "fmt_italic"],
  ["x<sup>2</sup>", "superscript", "fmt_sup"],
  ["x<sub>2</sub>", "subscript", "fmt_sub"],
];
// Tastenkürzel im Notizfeld (Strg + Taste); ev.code als layoutunabhängige Rückfallebene
const NOTE_KEYS = { b: "bold", i: "italic", ".": "superscript", ",": "subscript" };
const NOTE_CODES = { KeyB: "bold", KeyI: "italic", Period: "superscript", Comma: "subscript" };

// Rundungsknopf im Notizfeld: bei ¹³C die Verschiebungen auf eine
// Nachkommastelle, beim IR-Spektrum die Wellenzahlen auf ganze Zahlen.
const ROUND_BUTTONS = {
  nmr_13c: { digits: 1, label: "≈0.0", key: "fmt_round1", unit: /^\s*ppm\b/ },
  ir: { digits: 0, label: "≈0", key: "fmt_round0", unit: /^\s*cm\b/ },
};
// Zusätzliche Kerne bringen ihre üblichen Nachkommastellen aus dem Katalog mit
// (¹⁹F zwei, ³¹P eine, ¹⁹⁵Pt ganze Zahlen) — siehe nuclei.py.
const SHIFT_ROUND = {
  0: { label: "≈0", key: "fmt_round_int" },
  1: { label: "≈0.0", key: "fmt_round1" },
  2: { label: "≈0.00", key: "fmt_round2" },
};

// Welcher Rundungsknopf gehört an dieses Notizfeld? Bei einem zusätzlichen
// Kern die Nachkommastellen aus dem Katalog, sonst die feste Zuordnung oben.
function roundSpec(e) {
  const nucleus = nucleusOf(e);
  const shift = nucleus && SHIFT_ROUND[nucleus.digits];
  return shift ? { ...shift, digits: nucleus.digits, unit: /^\s*ppm\b/ }
               : ROUND_BUTTONS[e.type_code];
}

// Kopfzeile eines NMR-Datensatzes („13C{1H} NMR (126 MHz…") — wie
// chem_text.NMR_HEAD. Steht sie schon in der Notiz, wird der Knopf zum
// Einsetzen nicht angeboten.
const NMR_HEAD_RE = /^\s*\d{1,3}\s*[A-Z][a-z]?(\s*\{\s*\d{1,3}\s*[A-Z][a-z]?\s*\})?\s*-?\s*NMR\b/;
// Einträge, deren Notiz mit so einer Kopfzeile beginnt: ¹H, ¹³C und die
// zusätzlichen Kerne (2D-NMR hat im Dokument keine Textzeile).
const hasHeadLine = (e) => ["nmr_1h", "nmr_13c"].includes(e.type_code) || e.is_nmr;

// Rundet die Ziffernfolge selbst, nicht die Gleitkommazahl: „128.45" wird
// verlässlich zu „128.5" (Number(128.45).toFixed(1) ergibt „128.4", weil
// 128.45 binär etwas kleiner liegt). Fehlende Stellen werden aufgefüllt,
// damit eine Reihe von Verschiebungen gleich viele Nachkommastellen hat.
function roundDecimal(num, digits) {
  const [whole, frac = ""] = num.split(".");
  if (frac.length <= digits) {
    return digits ? `${whole}.${frac.padEnd(digits, "0")}` : whole;
  }
  let kept = whole + frac.slice(0, digits);
  if (frac[digits] >= "5") kept = String(BigInt(kept) + 1n).padStart(kept.length, "0");
  const point = kept.length - digits;
  return digits ? `${kept.slice(0, point)}.${kept.slice(point)}` : kept;
}

// Welche Zahlen sind Messwerte? Angefasst wird nur, was für sich steht:
// nicht Teil einer Formel oder Probennummer („CDCl3", „cm-1", „JA294") und
// ohne Einheit oder Integral dahinter — „126 MHz", „298 K", „7.5 Hz" und
// „2H" bleiben also, wie sie sind.
function roundEdits(text, from, digits, unit) {
  const re = /\d+(?:\.\d+)?/g;
  re.lastIndex = from;
  const edits = [];
  let m;
  while ((m = re.exec(text))) {
    const num = m[0];
    const prev = text[m.index - 1] || "";
    const prev2 = text[m.index - 2] || "";
    const rest = text.slice(re.lastIndex);
    if (/[\w.]/.test(prev)) continue;                        // CDCl3, 12.34.5
    if (/[-−–]/.test(prev) && /\w/.test(prev2)) continue;     // cm-1, -d6
    // Die eigene Einheit („128.4 ppm", „1730 cm-1") gehört zum Messwert;
    // jede andere weist die Zahl als etwas anderes aus.
    if (!unit.test(rest) && /^\s*[A-Za-zµ°]/.test(rest)) continue;  // 126 MHz, 2H
    const value = roundDecimal(num, digits);
    if (value !== num) edits.push({ start: m.index, end: re.lastIndex, value });
  }
  return edits;
}

// Rundet die Messwerte einer Notiz und lässt Formatierung und Wortlaut
// unangetastet: geschrieben wird nur in die Textknoten, hoch- und
// tiefgestellte Teile (Indizes, „cm⁻¹") bleiben außen vor. Steht in der
// Notiz ein „=", wird erst dahinter gerundet — der Kopf mit Frequenz,
// Lösungsmittel und Temperatur ist kein Messwert.
function roundNoteValues(root, digits, unit) {
  const nodes = [];
  const walk = (node) => {
    for (const child of node.childNodes) {
      if (child.nodeType === Node.TEXT_NODE) nodes.push(child);
      else if (child.nodeType === Node.ELEMENT_NODE && !/^(SUP|SUB)$/.test(child.tagName)) walk(child);
    }
  };
  walk(root);

  const text = nodes.map((n) => n.nodeValue).join("");
  const edits = roundEdits(text, text.indexOf("=") + 1, digits, unit);
  if (!edits.length) return false;

  // Von hinten nach vorn zurückschreiben, damit die Positionen gültig
  // bleiben. Eine Zahl, die über mehrere Knoten verteilt ist (teilweise
  // formatiert), landet komplett im ersten davon.
  let pos = 0;
  const spans = nodes.map((n) => [pos, (pos += n.nodeValue.length)]);
  for (let i = nodes.length - 1; i >= 0; i--) {
    const [start, end] = spans[i];
    let value = nodes[i].nodeValue;
    for (let k = edits.length - 1; k >= 0; k--) {
      const edit = edits[k];
      if (edit.end <= start || edit.start >= end) continue;
      value = value.slice(0, Math.max(edit.start, start) - start)
        + (edit.start >= start ? edit.value : "")
        + value.slice(Math.min(edit.end, end) - start);
    }
    if (value !== nodes[i].nodeValue) nodes[i].nodeValue = value;
  }
  return true;
}

function textToHtml(text) {
  return esc(text || "").replace(/\r?\n/g, "<br>");
}

// Reduziert das vom Browser erzeugte Markup auf die erlaubten Tags;
// Blockelemente (Enter in manchen Browsern) werden zu Zeilenumbrüchen
function cleanNoteHtml(root) {
  const out = [];
  const walk = (node) => {
    for (const child of node.childNodes) {
      if (child.nodeType === Node.TEXT_NODE) { out.push(esc(child.nodeValue)); continue; }
      if (child.nodeType !== Node.ELEMENT_NODE) continue;
      const tag = NOTE_TAGS[child.tagName];
      if (tag === "br") { out.push("<br>"); continue; }
      if (/^(DIV|P|LI)$/.test(child.tagName) && out.length && out[out.length - 1] !== "<br>") {
        out.push("<br>");
      }
      if (tag) out.push(`<${tag}>`);
      walk(child);
      if (tag) out.push(`</${tag}>`);
    }
  };
  walk(root);
  let html = out.join("");
  while (html.endsWith("<br>")) html = html.slice(0, -4);
  return html;
}

// ---------- Formatiertes Einfügen ----------
// Eingefügter Text behält fett, kursiv, hoch- und tiefgestellt. Gelesen wird
// das HTML der Zwischenablage (Word, Browser, MestReNova, Google Docs …),
// ersatzweise RTF, sonst der reine Text — alles wird auf Textstücke mit
// diesen vier Merkmalen reduziert. Die formatierbaren Felder (Notizen,
// Molekülname, Zitat, Probenvermerk) bekommen daraus bereinigtes HTML. Die
// einfachen Eingabefelder kennen kein Kursiv/Fett; dort wird Hoch-/
// Tiefgestelltes zu Unicode-Zeichen (CDCl₃, ¹⁹F) wie im Klartext der Notizen.

// Words Symbol-Schrift: dort steht „d" für δ, „m" für μ und 0xB0 für °. Ohne
// Übersetzung kämen lateinische Buchstaben an. Word legt eingefügte Symbole
// auch als Privatbereich-Zeichen U+F020–U+F0FF ab — dieselben Codes.
const SYMBOL_FONT = new Map();
{
  // Großbuchstaben auf A–Z; Kleinbuchstaben 0x20 höher, bis auf die
  // Varianten auf J (ϑ/ϕ) und V (ς/ϖ)
  const greek = [0x391, 0x392, 0x3A7, 0x394, 0x395, 0x3A6, 0x393, 0x397, 0x399, 0x3D1, 0x39A, 0x39B, 0x39C,
                 0x39D, 0x39F, 0x3A0, 0x398, 0x3A1, 0x3A3, 0x3A4, 0x3A5, 0x3C2, 0x3A9, 0x39E, 0x3A8, 0x396];
  greek.forEach((upper, k) => {
    SYMBOL_FONT.set(0x41 + k, String.fromCharCode(upper));
    SYMBOL_FONT.set(0x61 + k, String.fromCharCode(k === 9 ? 0x3D5 : k === 21 ? 0x3D6 : upper + 0x20));
  });
  const rows = [
    [0x22, [0x2200]], [0x24, [0x2203]], [0x27, [0x220B]], [0x2A, [0x2217]], [0x2D, [0x2212]],
    [0x40, [0x2245]], [0x5C, [0x2234]], [0x5E, [0x22A5]], [0x60, [0x203E]], [0x7E, [0x223C]],
    // 0xA0 bleibt das geschützte Leerzeichen (Word setzt es auch in Symbol-Spannen)
    [0xA1, [0x3D2, 0x2032, 0x2264, 0x2044, 0x221E, 0x192, 0x2663, 0x2666, 0x2665, 0x2660,
            0x2194, 0x2190, 0x2191, 0x2192, 0x2193, 0xB0, 0xB1, 0x2033, 0x2265, 0xD7, 0x221D, 0x2202,
            0x2022, 0xF7, 0x2260, 0x2261, 0x2248, 0x2026, 0x23D0, 0x23AF, 0x21B5]],
    [0xC0, [0x2135, 0x2111, 0x211C, 0x2118, 0x2297, 0x2295, 0x2205, 0x2229, 0x222A, 0x2283, 0x2287,
            0x2284, 0x2282, 0x2286, 0x2208, 0x2209, 0x2220, 0x2207, 0xAE, 0xA9, 0x2122, 0x220F, 0x221A,
            0x22C5, 0xAC, 0x2227, 0x2228, 0x21D4, 0x21D0, 0x21D1, 0x21D2, 0x21D3, 0x25CA, 0x2329, 0xAE,
            0xA9, 0x2122, 0x2211]],
    [0xF1, [0x232A, 0x222B]],
  ];
  for (const [from, codes] of rows) codes.forEach((c, k) => SYMBOL_FONT.set(from + k, String.fromCharCode(c)));
}

function symbolChar(ch) {
  let code = ch.charCodeAt(0);
  if (code >= 0xF020 && code <= 0xF0FF) code -= 0xF000;
  return SYMBOL_FONT.get(code) || (code < 0x100 ? String.fromCharCode(code) : ch);
}

// Wie richtext.py SUPERSCRIPT/SUBSCRIPT — was Unicode nicht hergibt, bleibt
const scriptTable = (from, to) => new Map([...from].map((c, k) => [c, [...to][k]]));
const SUP_CHARS = scriptTable("0123456789+-−–=()n", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁻⁻⁼⁽⁾ⁿ");
const SUB_CHARS = scriptTable("0123456789+-−–=()aeoxhklmnpst", "₀₁₂₃₄₅₆₇₈₉₊₋₋₋₌₍₎ₐₑₒₓₕₖₗₘₙₚₛₜ");

const PASTE_FORMAT = { b: false, i: false, sup: false, sub: false, symbol: false, dingbats: false, pre: false };
const PASTE_SKIP = new Set(["HEAD", "STYLE", "SCRIPT", "TITLE", "META", "LINK", "TEMPLATE", "NOSCRIPT",
                            "IMG", "SVG", "OBJECT", "IFRAME", "BUTTON", "SELECT", "INPUT", "TEXTAREA"]);
const PASTE_BLOCK = new Set(["P", "DIV", "LI", "TR", "H1", "H2", "H3", "H4", "H5", "H6", "BLOCKQUOTE",
                             "PRE", "TABLE", "UL", "OL", "DL", "DT", "DD", "SECTION", "ARTICLE",
                             "HEADER", "FOOTER", "ADDRESS", "CAPTION", "FIGCAPTION"]);

// Textstück anhängen; gleich formatierte Nachbarn werden eins. `sym`: hier
// wurde ein Symbol-Schrift-Zeichen übersetzt.
function pushPiece(pieces, text, fmt, sym = false) {
  const last = pieces[pieces.length - 1];
  if (last && !last.br && last.b === !!fmt.b && last.i === !!fmt.i
      && last.sup === !!fmt.sup && last.sub === !!fmt.sub) {
    last.text += text;
    last.sym = last.sym || sym;
  } else {
    pieces.push({ text, b: !!fmt.b, i: !!fmt.i, sup: !!fmt.sup, sub: !!fmt.sub, sym });
  }
}

// Leerraum am Ende der letzten Zeile entfernen
function trimLineEnd(pieces) {
  while (pieces.length && !pieces[pieces.length - 1].br) {
    const last = pieces[pieces.length - 1];
    last.text = last.text.replace(/[  ]+$/, "");
    if (last.text) break;
    pieces.pop();
  }
}

// Leerzeilen und Leerraum am Anfang und Ende weg
function finishPieces(pieces) {
  for (;;) {
    trimLineEnd(pieces);
    if (!pieces.length || !pieces[pieces.length - 1].br) break;
    pieces.pop();
  }
  while (pieces.length && pieces[0].br) pieces.shift();
  return pieces;
}

function fontFace(f, value) {
  const family = value.split(",")[0].trim().replace(/^["']|["']$/g, "").toLowerCase();
  f.symbol = family === "symbol";
  f.dingbats = /^(wingdings|webdings)/.test(family);  // eigene Belegung: unverändert lassen
}

// Klassenregeln aus <style> (Word: Zeichenformatvorlagen wie „Hervorhebung")
function cssClassStyles(doc) {
  const rules = new Map();
  for (const style of doc.querySelectorAll("style")) {
    const css = style.textContent.replace(/\/\*[\s\S]*?\*\//g, "");
    for (const [, selectors, body] of css.matchAll(/([^{}]+)\{([^{}]*)\}/g)) {
      for (const sel of selectors.split(",")) {
        const m = sel.trim().match(/^[a-z0-9]*\.([\w-]+)$/i);
        if (m) rules.set(m[1].toLowerCase(), `${rules.get(m[1].toLowerCase()) || ""};${body}`);
      }
    }
  }
  return rules;
}

// Auszeichnung eines Elements: Tag, dann Klassenregeln, dann style-Attribut
// (Google Docs etwa hüllt alles in <b style="font-weight:normal">)
function elementFormat(el, tag, parent, classes) {
  const f = { ...parent, hidden: false };
  if (tag === "B" || tag === "STRONG") f.b = true;
  else if (["I", "EM", "CITE", "VAR", "DFN"].includes(tag)) f.i = true;
  else if (tag === "SUP") { f.sup = true; f.sub = false; }
  else if (tag === "SUB") { f.sub = true; f.sup = false; }
  else if (tag === "PRE") f.pre = true;
  else if (tag === "FONT" && el.hasAttribute("face")) fontFace(f, el.getAttribute("face"));
  let css = "";
  for (const name of (el.getAttribute("class") || "").split(/\s+/)) {
    if (name) css += classes.get(name.toLowerCase()) || "";
  }
  css += `;${el.getAttribute("style") || ""}`;
  for (const decl of css.split(";")) {
    const colon = decl.indexOf(":");
    if (colon < 0) continue;
    const prop = decl.slice(0, colon).trim().toLowerCase();
    const value = decl.slice(colon + 1).replace(/!important/i, "").trim().toLowerCase();
    if (prop === "font-weight") f.b = value === "bold" || value === "bolder" || Number(value) >= 600;
    else if (prop === "font-style") f.i = value.startsWith("italic") || value.startsWith("oblique");
    else if (prop === "vertical-align" && ["super", "sub", "baseline"].includes(value)) {
      f.sup = value === "super";
      f.sub = value === "sub";
    } else if (prop === "font-family" || prop === "mso-symbol-font-family") fontFace(f, value);
    else if (prop === "font") {
      // Kurzform „italic bold 11pt "Times New Roman"": Schrift steht hinter der Größe
      if (/\bbold\b|\b[6-9]00\b/.test(value)) f.b = true;
      if (/\bitalic\b/.test(value)) f.i = true;
      const family = value.match(/[\d.]+(?:pt|px|em|rem|%)(?:\/\S+)?\s+(.+)$/);
      if (family) fontFace(f, family[1]);
    } else if (prop === "white-space") f.pre = value.startsWith("pre") || value === "break-spaces";
    else if ((prop === "display" && value === "none") || (prop === "mso-hide" && value === "all")) f.hidden = true;
  }
  return f;
}

function htmlPieces(html) {
  const doc = new DOMParser().parseFromString(html, "text/html");
  const classes = cssClassStyles(doc);
  const pieces = [];
  // Browser legen Kontext-Markup um die Auswahl und markieren das
  // eigentlich Kopierte mit <!--StartFragment-->…<!--EndFragment-->
  let active = !/<!--\s*StartFragment\s*-->/i.test(html);
  let lineHasText = false;
  let pendingBreak = false;  // Blockgrenze: Umbruch erst vor dem nächsten Text
  let afterSpace = true;     // Zeilenanfang zählt wie Leerraum
  const lineBreak = () => {
    trimLineEnd(pieces);
    pieces.push({ br: true });
    lineHasText = pendingBreak = false;
    afterSpace = true;
  };
  const addText = (raw, fmt) => {
    if (!active) return;
    const value = fmt.pre ? raw.replace(/\r\n?/g, "\n") : raw.replace(/[ \t\r\n\f]+/g, " ");
    if (pendingBreak && /\S/.test(value)) lineBreak();
    value.split("\n").forEach((part, k) => {
      if (k) lineBreak();
      if (!fmt.pre && afterSpace) part = part.replace(/^ /, "");
      if (!part) return;
      let sym = false;
      if (!fmt.dingbats) {
        const mapped = fmt.symbol ? [...part].map(symbolChar).join("")
                                  : part.replace(/[-]/g, symbolChar);
        sym = mapped !== part;
        part = mapped;
      }
      pushPiece(pieces, part, fmt, sym);
      lineHasText = true;
      afterSpace = part.endsWith(" ");
    });
  };
  const walk = (node, fmt) => {
    for (const child of node.childNodes) {
      if (child.nodeType === Node.COMMENT_NODE) {
        if (/^\s*StartFragment\s*$/i.test(child.data)) active = true;
        else if (/^\s*EndFragment\s*$/i.test(child.data)) active = false;
      } else if (child.nodeType === Node.TEXT_NODE) {
        addText(child.data, fmt);
      } else if (child.nodeType === Node.ELEMENT_NODE) {
        const tag = child.tagName.toUpperCase();
        if (PASTE_SKIP.has(tag)) continue;
        if (tag === "BR") {
          if (!active) continue;
          if (pendingBreak) lineBreak();  // <div><br></div> ist eine Leerzeile
          lineBreak();
          continue;
        }
        const f = elementFormat(child, tag, fmt, classes);
        if (f.hidden) continue;
        const block = PASTE_BLOCK.has(tag);
        if (block && lineHasText) pendingBreak = true;
        if ((tag === "TD" || tag === "TH") && active && lineHasText && !pendingBreak) {
          pushPiece(pieces, "\t", f);  // Tabellenzellen wie beim Kopieren als Text
          afterSpace = true;
        }
        walk(child, f);
        if (block && lineHasText) pendingBreak = true;
      }
    }
  };
  walk(doc.body, PASTE_FORMAT);
  return finishPieces(pieces);
}

// RTF — liefern Programme ohne HTML in der Zwischenablage. Gelesen werden nur
// Text, fett/kursiv/hoch/tief, Umbrüche und die Symbol-Schrift; Kopfbereiche
// (Schriften-, Farbtabellen, Bilder, Feldbefehle) werden übersprungen.
const RTF_SKIP = new Set(["colortbl", "stylesheet", "info", "pict", "object", "header", "headerl", "headerr",
  "headerf", "footer", "footerl", "footerr", "footerf", "footnote", "listtable", "listoverridetable",
  "rsidtbl", "generator", "xmlnstbl", "themedata", "colorschememapping", "latentstyles", "datastore",
  "fldinst", "shp", "shpinst", "nonshppict", "revtbl", "filetbl", "pgdsctbl", "bkmkstart", "bkmkend",
  "xe", "tc", "txe"]);
const RTF_CHARS = { emdash: "—", endash: "–", bullet: "•", lquote: "‘", rquote: "’",
  ldblquote: "“", rdblquote: "”", emspace: " ", enspace: " ", qmspace: " ",
  tab: "\t", cell: "\t" };
const RTF_CONTROL = /\\([a-zA-Z]{1,32})(-?\d{1,10})? ?/y;

function rtfPieces(rtf) {
  const pieces = [];
  if (!/^\s*\{\\rtf/.test(rtf)) return pieces;
  const cp1252 = new TextDecoder("windows-1252");
  const symbolFonts = new Set();
  const stack = [];
  let st = { ...PASTE_FORMAT, skip: false, fonttbl: false, uc: 1 };
  let font = null;     // Eintrag der Schrifttabelle, der gerade gelesen wird
  let skipChars = 0;   // Ersatzzeichen hinter \uN
  const finishFont = () => {
    if (font && font.name.trim().toLowerCase() === "symbol") symbolFonts.add(font.num);
    font = null;
  };
  const emit = (ch) => {
    if (skipChars > 0) { skipChars--; return; }
    if (st.skip) return;
    if (st.fonttbl) {
      if (ch === ";") finishFont();
      else if (font) font.name += ch;
      return;
    }
    const mapped = st.symbol || (ch >= "" && ch <= "") ? symbolChar(ch) : ch;
    pushPiece(pieces, mapped, st, mapped !== ch);
  };
  const lineBreak = () => {
    if (st.skip || st.fonttbl) return;
    trimLineEnd(pieces);
    pieces.push({ br: true });
  };
  const control = (word, param) => {
    const on = param !== 0;
    switch (word) {
      case "fonttbl": st.fonttbl = true; break;
      case "f":
        if (st.fonttbl) font = { num: param, name: "" };
        else st.symbol = symbolFonts.has(param);
        break;
      case "b": st.b = on; break;
      case "i": st.i = on; break;
      case "super": st.sup = true; st.sub = false; break;
      case "sub": st.sub = true; st.sup = false; break;
      case "nosupersub": st.sup = st.sub = false; break;
      case "up": st.sup = on; st.sub = false; break;
      case "dn": st.sub = on; st.sup = false; break;
      case "plain": st.b = st.i = st.sup = st.sub = st.symbol = false; break;
      case "par": case "line": case "row": case "sect": case "page": lineBreak(); break;
      case "uc": st.uc = param ?? 1; break;
      case "u":
        if (param !== null) {
          emit(String.fromCharCode(param < 0 ? param + 65536 : param));
          skipChars = st.uc;
        }
        break;
      default:
        if (RTF_CHARS[word]) emit(RTF_CHARS[word]);
        else if (RTF_SKIP.has(word)) st.skip = true;
    }
  };
  let pos = 0;
  while (pos < rtf.length) {
    const ch = rtf[pos];
    if (ch === "{" || ch === "}") {
      if (ch === "{") {
        stack.push(st);
        st = { ...st };
      } else {
        if (st.fonttbl) finishFont();
        st = stack.pop() || st;
      }
      skipChars = 0;
      pos++;
    } else if (ch === "\r" || ch === "\n") {
      pos++;
    } else if (ch !== "\\") {
      emit(ch);
      pos++;
    } else if (/[a-z]/i.test(rtf[pos + 1] || "")) {
      RTF_CONTROL.lastIndex = pos;
      const m = RTF_CONTROL.exec(rtf);
      pos = RTF_CONTROL.lastIndex;
      control(m[1], m[2] === undefined ? null : Number(m[2]));
    } else {
      const next = rtf[pos + 1];
      pos += 2;
      if (next === "'") {
        const byte = parseInt(rtf.substr(pos, 2), 16);
        pos += 2;
        if (!Number.isNaN(byte)) {
          emit(st.symbol ? String.fromCharCode(byte) : cp1252.decode(new Uint8Array([byte])));
        }
      } else if (next === "*") st.skip = true;
      else if (next === "~") emit(" ");
      else if (next === "_") emit("‑");
      else if (next === "\\" || next === "{" || next === "}") emit(next);
      else if (next === "\r" || next === "\n") lineBreak();
      // \- (bedingter Trennstrich) und Unbekanntes: nichts
    }
  }
  return finishPieces(pieces);
}

function plainPieces(text) {
  const pieces = [];
  (text || "").replace(/\r\n?/g, "\n").split("\n").forEach((line, k) => {
    if (k) pieces.push({ br: true });
    const mapped = line.replace(/[-]/g, symbolChar);
    if (mapped) pushPiece(pieces, mapped, PASTE_FORMAT, mapped !== line);
  });
  return finishPieces(pieces);
}

// Inhalt der Zwischenablage als Textstücke — bestes verfügbares Format zuerst
function clipboardPieces(dt) {
  if (!dt) return [];
  const hasText = (pieces) => pieces.some((p) => !p.br);
  const html = dt.getData("text/html");
  if (html) {
    const pieces = htmlPieces(html);
    if (hasText(pieces)) return pieces;
  }
  const rtf = dt.getData("text/rtf");
  if (rtf) {
    const pieces = rtfPieces(rtf);
    if (hasText(pieces)) return pieces;
  }
  return plainPieces(dt.getData("text/plain"));
}

function piecesToHtml(pieces, singleLine = false) {
  return pieces.map((p) => {
    if (p.br) return singleLine ? " " : "<br>";
    let h = esc(singleLine ? p.text.replace(/\t/g, " ") : p.text);
    if (p.sup) h = `<sup>${h}</sup>`;
    else if (p.sub) h = `<sub>${h}</sub>`;
    if (p.i) h = `<i>${h}</i>`;
    if (p.b) h = `<b>${h}</b>`;
    return h;
  }).join("");
}

function piecesToText(pieces) {
  return pieces.map((p) => {
    if (p.br) return "\n";
    const table = p.sup ? SUP_CHARS : p.sub ? SUB_CHARS : null;
    return table ? [...p.text].map((c) => table.get(c) || c).join("") : p.text;
  }).join("");
}

// Einfügen in ein formatierbares Feld (contenteditable)
function pasteFormatted(ev, singleLine = false) {
  const pieces = clipboardPieces(ev.clipboardData);
  if (!pieces.length) return;  // kein Text (etwa nur ein Bild): der Bild-Handler übernimmt
  ev.preventDefault();
  ev.stopPropagation();
  // wie getippt: das Text-Undo des Felds greift
  document.execCommand("insertHTML", false, piecesToHtml(pieces, singleLine));
}

// Einfache Eingabefelder: nur eingreifen, wenn es etwas zu übersetzen gibt
// (Hoch-/Tiefgestelltes, Symbol-Schrift) — sonst fügt der Browser selbst ein.
// SMILES und DOI (data-no-symbols) bleiben unangetastet.
document.addEventListener("paste", (ev) => {
  const el = ev.target;
  if (!symbolField(el) || el.isContentEditable) return;
  const pieces = clipboardPieces(ev.clipboardData);
  if (!pieces.some((p) => p.sup || p.sub || p.sym)) return;
  ev.preventDefault();
  ev.stopPropagation();
  document.execCommand("insertText", false, piecesToText(pieces));
}, true);

// Formatierbare Einzelfelder (Molekülname, Zitat, Probenvermerk): dieselbe
// Auszeichnung und dieselben Tastenkürzel wie die Notizen, ohne Werkzeugleiste
function setupRichField(el, { singleLine = false, onEnter = () => el.blur() } = {}) {
  el.addEventListener("keydown", (ev) => {
    if (ev.key === "Enter") {
      ev.preventDefault();
      if (singleLine) onEnter();
      else document.execCommand("insertLineBreak");
      return;
    }
    const cmd = ev.ctrlKey && !ev.altKey && !ev.shiftKey
      && (NOTE_KEYS[ev.key.toLowerCase()] || NOTE_CODES[ev.code]);
    if (cmd) {
      ev.preventDefault();
      document.execCommand(cmd, false, null);
    }
  });
  el.addEventListener("paste", (ev) => pasteFormatted(ev, singleLine));
  // Leer geräumt bleibt oft ein <br> stehen — dann fehlte der Platzhalter
  el.addEventListener("input", () => { if (!el.textContent) el.innerHTML = ""; });
}

// Bereinigtes HTML eines formatierbaren Felds (einzeilig: Umbrüche -> Leerzeichen)
function richValue(el, singleLine = false) {
  const html = cleanNoteHtml(el);
  return (singleLine ? html.replace(/<br>/g, " ") : html).trim();
}

// So stünde der Serverstand im Feld — zum Vergleich, ob sich etwas geändert hat
function richShown(html, text, singleLine = false) {
  const tmp = document.createElement("div");
  tmp.innerHTML = html || textToHtml(text);
  return richValue(tmp, singleLine);
}

// Wie setValue: das Feld, in dem gerade geschrieben wird, bleibt unberührt
function setRich(el, html, text) {
  if (el !== document.activeElement) el.innerHTML = html || textToHtml(text);
}

// Häkchen „ins Word-Dokument" — nur bei eigenen Einträgen. Beim Anlegen ist
// es für NMR-Messungen vorbelegt (siehe api.add_other_entry).
function inDocumentRow(e) {
  const molId = detailMolId;
  const row = document.createElement("div");
  row.className = "field-row";
  const label = document.createElement("span");
  label.className = "field-label";
  row.appendChild(label);

  const box = document.createElement("label");
  box.title = t("in_document_title");
  const input = document.createElement("input");
  input.type = "checkbox";
  input.checked = e.in_document;
  input.addEventListener("change", () => guard("#detail-error", async () => {
    await api(`/entries/${e.id}`, {
      method: "PATCH",
      body: JSON.stringify({ in_document: input.checked }),
    });
    await refreshMolecule(molId);
  }));
  box.appendChild(input);
  box.appendChild(document.createTextNode(" " + t("in_document")));
  row.appendChild(box);
  return row;
}

// Einzelne Notiz: Werkzeugleiste unter der Beschriftung, speichern beim
// Verlassen, löschen per ✕
function noteRow(n, e) {
  // Ein Datentyp kann sein Notizfeld umbenennen und dauerhaft einblenden
  // (Versuchsvorschrift -> „Durchführung"); n.id === null ist so ein noch
  // leeres Feld, das erst beim ersten Schreiben angelegt wird.
  const spec = (datatypes.find((d) => d.code === e.type_code) || {}).note || {};
  const molId = detailMolId;
  const row = document.createElement("div");
  row.className = "field-row note-row";
  const label = document.createElement("span");
  label.className = "field-label note-label";
  const caption = document.createElement("span");
  caption.textContent = spec.label ? spec.label[lang] : t("note_label");
  label.appendChild(caption);

  const ed = document.createElement("div");
  ed.className = "note-edit";
  ed.contentEditable = "true";
  if (n.id !== null) ed.dataset.noteId = n.id;
  ed.dataset.fkey = n.id !== null ? `note:${n.id}` : `note-new:${e.id}`;
  ed.dataset.placeholder = spec.placeholder ? spec.placeholder[lang] : t("text_ph");
  ed.innerHTML = n.html || textToHtml(n.text);
  let saved = cleanNoteHtml(ed);

  // Sichert den Stand, sobald er sich geändert hat — beim Verlassen des
  // Felds und direkt nach dem Runden.
  const save = () => {
    const html = cleanNoteHtml(ed);
    if (html === saved) return;
    saved = html;
    guard("#detail-error", async () => {
      if (n.id === null) {
        // Dauerhaft eingeblendetes, noch leeres Feld: erst jetzt anlegen
        if (!html) return;
        await api(`/entries/${e.id}/notes`, {
          method: "POST",
          body: JSON.stringify({ html }),
        });
      } else {
        await api(`/notes/${n.id}`, { method: "PATCH", body: JSON.stringify({ html }) });
      }
      await refreshMolecule(molId);
    });
  };

  const bar = document.createElement("div");
  bar.className = "note-toolbar";
  const buttons = [];
  const updateBar = () => {
    for (const [btn, cmd] of buttons) btn.classList.toggle("on", document.queryCommandState(cmd));
  };
  const exec = (cmd) => {
    ed.focus();
    document.execCommand(cmd, false, null);
    updateBar();
  };
  for (const [html, cmd, key] of NOTE_FORMATS) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.innerHTML = html;
    btn.title = t(key);
    btn.addEventListener("mousedown", (ev) => ev.preventDefault()); // Auswahl im Feld behalten
    btn.addEventListener("click", () => exec(cmd));
    bar.appendChild(btn);
    buttons.push([btn, cmd]);
  }
  // Sonderzeichen (−, °C, µ, Griechisch …) — dieselbe Palette wie an den
  // einfachen Eingabefeldern, siehe „Sonderzeichen“
  const symBtn = document.createElement("button");
  symBtn.type = "button";
  symBtn.textContent = "Ω";
  symBtn.title = t("sym_title");
  symBtn.addEventListener("mousedown", (ev) => ev.preventDefault()); // Auswahl im Feld behalten
  symBtn.addEventListener("click", () => toggleSymbols(ed, symBtn));
  bar.appendChild(symBtn);
  // Kopfzeile einsetzen — bei NMR-Einträgen, deren Notiz noch keine hat. Der
  // Vorschlag kommt vom Server (api.entry_head): Frequenz aus dem
  // Kernverhältnis, Lösungsmittel und Temperatur wörtlich von den schon
  // erfassten Kernen dieses Moleküls. Geschrieben wird nur auf Knopfdruck.
  if (hasHeadLine(e) && !NMR_HEAD_RE.test(ed.textContent)) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = "δ";
    btn.title = t("fmt_head_title");
    btn.addEventListener("mousedown", (ev) => ev.preventDefault()); // Auswahl im Feld behalten
    btn.addEventListener("click", () => guard("#detail-error", async () => {
      const { text } = await api(`/entries/${e.id}/head`);
      ed.focus();
      // an den Anfang der Notiz, egal wo der Cursor stand
      const range = document.createRange();
      range.setStart(ed, 0);
      range.collapse(true);
      const sel = window.getSelection();
      sel.removeAllRanges();
      sel.addRange(range);
      document.execCommand("insertText", false, text);
      // Die Kopfzeile steht jetzt drin — der Knopf hat seinen Zweck erfüllt
      // (die Zeile bleibt nach dem Speichern stehen und würde ihn sonst behalten)
      btn.remove();
      save();
    }));
    bar.appendChild(btn);
  }
  // Messwerte auf einen Schlag runden: bei NMR die Verschiebungen mit den
  // üblichen Nachkommastellen des Kerns, beim IR die Wellenzahlen
  const round = roundSpec(e);
  if (round) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = round.label;
    btn.title = t(round.key);
    btn.addEventListener("mousedown", (ev) => ev.preventDefault()); // Auswahl im Feld behalten
    btn.addEventListener("click", () => {
      ed.focus();
      if (roundNoteValues(ed, round.digits, round.unit)) save();
    });
    bar.appendChild(btn);
  }
  label.appendChild(bar);
  row.appendChild(label);

  ed.addEventListener("keydown", (ev) => {
    if (ev.key === "Enter" && !ev.shiftKey) {
      ev.preventDefault();  // Zeilenumbruch statt neuem Block
      document.execCommand("insertLineBreak");
      return;
    }
    const cmd = ev.ctrlKey && !ev.altKey && !ev.shiftKey
      && (NOTE_KEYS[ev.key.toLowerCase()] || NOTE_CODES[ev.code]);
    if (cmd) {
      ev.preventDefault();
      exec(cmd);
    }
  });
  ed.addEventListener("keyup", updateBar);
  ed.addEventListener("mouseup", updateBar);
  ed.addEventListener("focus", updateBar);
  // Einfügen mit Auszeichnung und Sonderzeichen, aber ohne Fremd-Markup aus
  // Word & Co. — siehe „Formatiertes Einfügen“
  ed.addEventListener("paste", (ev) => pasteFormatted(ev));
  ed.addEventListener("blur", save);
  row.appendChild(ed);

  const acts = rowActions(row);
  if (n.id !== null) {
    const del = document.createElement("button");
    del.className = "icon-btn";
    del.textContent = "✕";
    del.title = t("del_note");
    del.addEventListener("click", () => guard("#detail-error", async () => {
      await api(`/notes/${n.id}`, { method: "DELETE" });
      await refreshMolecule(molId);
    }));
    acts.appendChild(del);
  }
  return row;
}

// "+ Datei" / "+ Notiz" pro Eintrag
function addButtonsRow(e) {
  const molId = detailMolId;
  const row = document.createElement("div");
  row.className = "field-row";
  const spacer = document.createElement("span");
  spacer.className = "field-label";
  row.appendChild(spacer);

  const addFile = document.createElement("button");
  addFile.className = "btn-sm btn-ghost";
  addFile.textContent = t("add_file");
  addFile.addEventListener("click", () => guard("#detail-error", async () => {
    addFile.disabled = true;
    try {
      const res = await nativeDialog({ kind: "file", filter: "any" });
      if (!res.path) return;
      const created = await api(`/entries/${e.id}/files`, {
        method: "POST",
        body: JSON.stringify({ path: res.path }),
      });
      await refreshMolecule(molId);
      // direkt benennen können
      const inp = document.querySelector(`input[data-file-id="${created.id}"]`);
      if (inp) inp.focus();
    } finally {
      addFile.disabled = false;
    }
  }));
  row.appendChild(addFile);

  const addNote = document.createElement("button");
  addNote.className = "btn-sm btn-ghost";
  addNote.textContent = t("add_note");
  addNote.addEventListener("click", () => guard("#detail-error", async () => {
    const created = await api(`/entries/${e.id}/notes`, {
      method: "POST",
      body: JSON.stringify({}),
    });
    await refreshMolecule(molId);
    const ed = document.querySelector(`.note-edit[data-note-id="${created.id}"]`);
    if (ed) ed.focus();
  }));
  row.appendChild(addNote);
  return row;
}

function fieldRow(e, field) {
  const molId = detailMolId;
  const row = document.createElement("div");
  row.className = "field-row";

  // Zahlenwert (Schmelzpunkt): feste Beschriftung
  if (field.key === "value") {
    const label = document.createElement("span");
    label.className = "field-label";
    label.textContent = field.label[lang];
    row.appendChild(label);
    const inp = document.createElement("input");
    inp.type = "number";
    inp.step = "0.1";
    inp.className = "mp-input";
    inp.value = e.mp_value ?? "";
    inp.placeholder = t("mp_ph");
    inp.dataset.fkey = `mp:${e.id}`;
    inp.addEventListener("change", () => guard("#detail-error", async () => {
      const val = inp.value === "" ? null : Number(inp.value);
      const updated = await api(`/entries/${e.id}`, { method: "PATCH", body: JSON.stringify({ mp_value: val }) });
      if (val !== null && field.suggest) await maybeSuggestPresent(updated);
      await refreshMolecule(molId);
    }));
    row.appendChild(inp);
    const unit = document.createElement("span");
    unit.className = "unit";
    unit.textContent = "°C";
    row.appendChild(unit);
    return row;
  }

  // Ordner / Datei / SVG — Feldschlüssel benennt die Spalten (folder_path, file_path, svg_path …)
  const isFolder = field.key === "folder";
  const pathField = `${field.key}_path`;
  const current = e[pathField];
  const exists = e[`${field.key}_exists`];

  // Beschriftung frei umbenennbar; leeren stellt das Standard-Label wieder her
  const labelField = `${field.key}_label`;
  const defaultLabel = field.label[lang];
  const effectiveLabel = e[labelField] || defaultLabel;
  const label = document.createElement("input");
  label.className = "field-label file-label-input";
  label.value = effectiveLabel;
  label.placeholder = defaultLabel;
  label.dataset.fkey = `flabel:${e.id}:${field.key}`;
  label.addEventListener("blur", () => {
    const val = label.value.trim();
    if (val === effectiveLabel) return;
    guard("#detail-error", async () => {
      // Standard-Label oder leer -> Überschreibung entfernen
      await api(`/entries/${e.id}`, {
        method: "PATCH",
        body: JSON.stringify({ [labelField]: val === defaultLabel ? "" : val }),
      });
      await refreshMolecule(molId);
    });
  });
  label.addEventListener("keydown", (ev) => { if (ev.key === "Enter") label.blur(); });
  row.appendChild(label);

  const path = pathEl(current, { folder: isFolder, dead: exists === false });
  if (current) {
    path.addEventListener("dblclick", () => guard("#detail-error", async () => {
      await api("/open", { method: "POST", body: JSON.stringify({ path: current, reveal: true }) });
    }));
  }
  row.appendChild(path);

  if (current && exists === false) {
    const warn = document.createElement("span");
    warn.className = "warn-badge";
    warn.textContent = "⚠";
    warn.title = t("dead_path_title");
    row.appendChild(warn);
  } else if (current && e[`${field.key}_local`]) {
    row.appendChild(localBadge());
  }

  const acts = rowActions(row);
  const pick = document.createElement("button");
  pick.className = "btn-sm";
  pick.textContent = current ? t("change") : t("pick");
  pick.addEventListener("click", () => guard("#detail-error", async () => {
    pick.disabled = true;
    try {
      const res = await nativeDialog({
        kind: isFolder ? "folder" : "file",
        filter: field.filter || "any",
        initial: current || "",
      });
      if (!res.path) return;
      const body = { [pathField]: res.path };
      const updated = await api(`/entries/${e.id}`, { method: "PATCH", body: JSON.stringify(body) });
      if (field.suggest) await maybeSuggestPresent(updated);
      await refreshMolecule(molId);
    } finally {
      pick.disabled = false;
    }
  }));
  acts.appendChild(pick);

  if (current) {
    const clear = document.createElement("button");
    clear.className = "icon-btn";
    clear.textContent = "✕";
    clear.title = t("unlink");
    clear.addEventListener("click", () => guard("#detail-error", async () => {
      await api(`/entries/${e.id}`, { method: "PATCH", body: JSON.stringify({ [pathField]: "" }) });
      await refreshMolecule(molId);
    }));
    acts.appendChild(clear);
  }
  return row;
}

async function maybeSuggestPresent(updated) {
  // Manuell + Vorschlag: nur nachfragen, nie automatisch umstellen
  if (updated.required && updated.status === "missing" &&
      confirm(t("suggest")(entryLabel(updated)))) {
    await api(`/entries/${updated.id}`, { method: "PATCH", body: JSON.stringify({ status: "present" }) });
  }
}

async function setEntryState(molId, entryId, state) {
  const patch = state === "na"
    ? { required: false }
    : { required: true, status: state };
  await api(`/entries/${entryId}`, { method: "PATCH", body: JSON.stringify(patch) });
  await refreshMolecule(molId);
}

// Status sofort anzeigen, noch bevor der Server geantwortet hat — der
// Neuaufbau nach der Antwort zeigt dann den gespeicherten Stand
function showEntryState(seg, state) {
  for (const btn of seg.querySelectorAll("button[data-state]")) {
    const s = btn.dataset.state;
    btn.classList.toggle(`on-${s}`, s === state);
  }
  const head = seg.closest(".entry-head");
  const dot = head && head.querySelector(".status-dot");
  if (dot) dot.className = `status-dot ${state}`;
  const entry = seg.closest(".entry");
  if (entry) entry.classList.toggle("na", state === "na");
}

// ---------- Undo ----------
async function doUndo() {
  if ($("#btn-undo").disabled || quitting) return;
  try {
    await api("/undo", { method: "POST" });
    await refresh();
    if ($("#dlg-backup").open) await renderBackupList();
  } catch (e) {
    alert(e.message);
  }
}

// ---------- Backups ----------
function backupStamp(b) {
  return b.created
    ? new Date(b.created).toLocaleString(t("locale"), { dateStyle: "medium", timeStyle: "medium" })
    : b.name;
}

async function renderBackupList() {
  const list = await api("/backups");
  const box = $("#backup-list");
  box.innerHTML = "";
  if (!list.length) {
    box.innerHTML = `<div class="hint">${t("no_backups")}</div>`;
    return;
  }
  for (const b of list) {
    const row = document.createElement("div");
    row.className = "backup-row";
    const label = document.createElement("span");
    label.className = "backup-when";
    label.textContent = backupStamp(b);
    if (b.pre_import) {
      // Sicherung von unmittelbar vor einem Transfer-Import — der Rückweg
      const tag = document.createElement("span");
      tag.className = "backup-tag";
      tag.textContent = t("backup_import_tag");
      label.appendChild(tag);
    }
    const size = document.createElement("span");
    size.className = "backup-size";
    size.textContent = `${Math.max(1, Math.round(b.size / 1024))} KB`;
    const btn = document.createElement("button");
    btn.className = "btn-sm";
    btn.textContent = t("restore");
    btn.addEventListener("click", async () => {
      if (!confirm(t("confirm_restore")(backupStamp(b)))) return;
      const msg = $("#backup-msg");
      msg.className = "";
      msg.textContent = "";
      try {
        await api(`/backups/${encodeURIComponent(b.name)}/restore`, { method: "POST" });
        msg.className = "msg-ok";
        msg.textContent = t("restore_done");
        await refresh();
      } catch (e) {
        msg.className = "error";
        msg.textContent = e.message;
      }
    });
    row.append(label, size, btn);
    box.appendChild(row);
  }
}

// ---------- Dialog-Hilfen ----------
function openDialog(dlg, errorSel) {
  $(errorSel).textContent = "";
  dlg.showModal();
}

async function guard(errorSel, fn) {
  const el = $(errorSel);
  el.textContent = "";
  try { await fn(); } catch (e) { el.textContent = e.message; }
}

// ---------- Events ----------
let newMolProjectId = null;

document.addEventListener("click", async (ev) => {
  const t2 = ev.target;

  if (t2.dataset.close !== undefined) t2.closest("dialog").close();

  if (t2.dataset.addMol) {
    newMolProjectId = Number(t2.dataset.addMol);
    $("#mol-name").innerHTML = "";
    $("#mol-smiles").value = "";
    openDialog($("#dlg-molecule"), "#mol-error");
    $("#mol-name").focus();
  }

  if (t2.dataset.delProj) {
    const p = projects.find((p) => p.id === Number(t2.dataset.delProj));
    if (confirm(t("confirm_del_project")(p.name, p.molecules.length))) {
      await api(`/projects/${p.id}`, { method: "DELETE" });
      refresh();
    }
  }

  if (t2.dataset.exportProj) {
    exportProject(Number(t2.dataset.exportProj), t2);
  }

  const toggle = t2.closest("[data-toggle-proj]");
  if (toggle) {
    toggleCollapsed(Number(toggle.dataset.toggleProj));
    return;
  }

  const card = t2.closest(".mol-card");
  if (card && dragMolId === null) {
    detailMolId = Number(card.dataset.molId);
    // Strg+V zielt auf den ersten leeren Slot (Struktur vor Schema vor Gleichung)
    const mol = findMol(detailMolId);
    pasteSlot = (mol && IMG_SLOTS.find((s) => !slotOf(mol, s).path)) || "image";
    // fehlgeschlagene ChemDraw-Aktualisierungen beim Neuöffnen erneut versuchen
    for (const slot of IMG_SLOTS) cdxFailed.delete(`${detailMolId}:${slot}`);
    renderDetail();
    $("#dlg-detail").showModal();
    $("#detail-error").textContent = "";
    $("#export-result").innerHTML = "";
  }

  const seg = t2.closest(".seg");
  if (seg && t2.dataset.state && detailMolId !== null) {
    const molId = detailMolId;
    const entryId = Number(seg.dataset.entry);
    showEntryState(seg, t2.dataset.state);
    guard("#detail-error", async () => {
      try {
        await setEntryState(molId, entryId, t2.dataset.state);
      } catch (err) {
        // Nicht gespeichert: vorab gezeigten Status zurücknehmen
        detailNodes.delete(`head:${entryId}`);
        if (detailMolId === molId) renderDetail();
        throw err;
      }
    });
  }

  if (t2.dataset.delEntry && detailMolId !== null) {
    const molId = detailMolId;
    guard("#detail-error", async () => {
      await api(`/entries/${t2.dataset.delEntry}`, { method: "DELETE" });
      await refreshMolecule(molId);
    });
  }
});

$("#btn-new-project").addEventListener("click", () => {
  $("#project-name").value = "";
  openDialog($("#dlg-project"), "#project-error");
  $("#project-name").focus();
});

$("#project-save").addEventListener("click", () =>
  guard("#project-error", async () => {
    await api("/projects", {
      method: "POST",
      body: JSON.stringify({ name: $("#project-name").value }),
    });
    $("#dlg-project").close();
    refresh();
  })
);

$("#mol-save").addEventListener("click", () =>
  guard("#mol-error", async () => {
    await api("/molecules", {
      method: "POST",
      body: JSON.stringify({
        project_id: newMolProjectId,
        name_html: richValue($("#mol-name"), true),
        smiles: $("#mol-smiles").value || null,
      }),
    });
    $("#dlg-molecule").close();
    refresh();
  })
);

setupRichField($("#mol-name"), { singleLine: true, onEnter: () => $("#mol-save").click() });

// Markiert den Block, in den Strg+V gerade einfügt
function updatePasteTarget() {
  for (const slot of IMG_SLOTS) {
    const active = slot === pasteSlot;
    $(`#img-block-${slot}`).classList.toggle("paste-target", active);
    $(`#paste-badge-${slot}`).style.display = active ? "" : "none";
  }
}

// Rohe Bilddaten hochladen (der api()-Helper sendet JSON, hier brauchen wir Binärdaten)
async function uploadImageBlob(blob, slot, molId = detailMolId) {
  trackBusy(1);
  try {
    const resp = await fetch(`/api/molecules/${molId}/${slot}`, {
      method: "POST",
      headers: { "X-Lang": lang, "Content-Type": blob.type || "image/png" },
      body: blob,
    });
    if (!resp.ok) {
      let msg = httpError(resp.status);
      try { msg = (await resp.json()).detail || msg; } catch {}
      throw new Error(msg);
    }
    return await resp.json();
  } finally {
    trackBusy(-1);
  }
}

// Bild aus einem DataTransfer (Paste oder Drop) fischen. Kopierte Dateien
// (Strg+C im Explorer) liegen in `files`, teils ohne MIME-Typ — dann zählt
// die Endung; die Magic-Byte-Prüfung des Servers greift ohnehin.
const IMAGE_EXT = /\.(png|jpe?g|gif|bmp|webp)$/i;

function transferImageFile(dt) {
  if (!dt) return null;
  const item = [...(dt.items || [])].find((it) => it.type && it.type.startsWith("image/"));
  if (item) {
    const f = item.getAsFile();
    if (f) return f;
  }
  return [...(dt.files || [])].find(
    (f) => (f.type && f.type.startsWith("image/")) || IMAGE_EXT.test(f.name)
  ) || null;
}

// Serverseitiges Einfügen: der Server liest die Windows-Zwischenablage direkt
// und sieht damit auch Formate, die der Browser nicht durchreicht
// (z. B. ChemDraws „Copy as PNG").
async function pasteFromServerClipboard(slot) {
  const molId = detailMolId;
  await api(`/molecules/${molId}/${slot}/clipboard`, { method: "POST" });
  await refreshMolecule(molId);
}

// Strg+V im Detail-Dialog: Bild aus der Zwischenablage in den markierten Slot
document.addEventListener("paste", (ev) => {
  if (detailMolId === null) return;  // nur bei geöffnetem Molekül-Detail
  const file = transferImageFile(ev.clipboardData);
  if (file) {
    ev.preventDefault();
    const molId = detailMolId;
    guard("#detail-error", async () => {
      await uploadImageBlob(file, pasteSlot, molId);
      await refreshMolecule(molId);
    });
    return;
  }
  // Browser sieht kein Bild: In Textfeldern normal weiter-einfügen lassen,
  // sonst die Zwischenablage serverseitig lesen (ChemDraw & Co.)
  if (isTextField(document.activeElement)) return;
  ev.preventDefault();
  guard("#detail-error", () => pasteFromServerClipboard(pasteSlot));
});

for (const slot of IMG_SLOTS) {
  // Klick auf den Block: Strg+V zielt ab jetzt hierhin
  $(`#img-block-${slot}`).addEventListener("click", () => {
    if (pasteSlot === slot) return;
    pasteSlot = slot;
    updatePasteTarget();
  });

  // Bilddatei über den nativen Dialog wählen
  $(`#img-pick-${slot}`).addEventListener("click", () =>
    guard("#detail-error", async () => {
      const molId = detailMolId;
      const s = slotOf(findMol(molId), slot);
      const res = await nativeDialog({ kind: "file", filter: "image", initial: s.path || "" });
      if (!res.path) return;
      await api(`/molecules/${molId}`, {
        method: "PATCH",
        body: JSON.stringify({ [s.field]: res.path }),
      });
      await refreshMolecule(molId);
    })
  );

  // Button „Einfügen": serverseitig lesen — sieht alles, was Windows hat
  // (ChemDraw-„PNG", Bitmaps, kopierte Dateien), ohne Browser-Grenzen
  $(`#img-paste-${slot}`).addEventListener("click", () =>
    guard("#detail-error", () => pasteFromServerClipboard(slot))
  );

  $(`#img-clear-${slot}`).addEventListener("click", () =>
    guard("#detail-error", async () => {
      const molId = detailMolId;
      await api(`/molecules/${molId}`, {
        method: "PATCH",
        body: JSON.stringify({ [slotOf(findMol(molId), slot).field]: "" }),
      });
      await refreshMolecule(molId);
    })
  );

  // Beim Einfügen aus ChemDraw mitgespeicherte .cdx in ChemDraw öffnen
  $(`#img-cdx-${slot}`).addEventListener("click", () =>
    guard("#detail-error", async () => {
      const s = slotOf(findMol(detailMolId), slot);
      if (!s.cdx) return;
      await api("/open", { method: "POST", body: JSON.stringify({ path: s.cdx }) });
    })
  );

  // ChemDraw-Zeichnung in die Zwischenablage — der Server schreibt sie, weil
  // der Browser ChemDraw-/OLE-Formate nicht ablegen kann
  const copyBtn = $(`#img-copy-${slot}`);
  copyBtn.addEventListener("click", () =>
    guard("#detail-error", async () => {
      await api(`/molecules/${detailMolId}/${slot}/copy`, { method: "POST" });
      copyBtn.textContent = t("copy_cdx_done");
      clearTimeout(copyBtn.doneTimer);
      copyBtn.doneTimer = setTimeout(() => { copyBtn.textContent = t("copy_cdx"); }, 1500);
    })
  );

  // Klick aufs Bild: Großansicht (Datei öffnen geht von dort aus)
  $(`#img-view-${slot}`).addEventListener("click", () => openZoom(slot));

  // Bilddatei direkt auf den Slot ziehen (umgeht alle Zwischenablage-Grenzen)
  const block = $(`#img-block-${slot}`);
  block.addEventListener("dragover", (ev) => {
    if (detailMolId === null || ![...ev.dataTransfer.types].includes("Files")) return;
    ev.preventDefault();
    ev.dataTransfer.dropEffect = "copy";
    block.classList.add("drop-hover");
  });
  block.addEventListener("dragleave", (ev) => {
    if (!block.contains(ev.relatedTarget)) block.classList.remove("drop-hover");
  });
  block.addEventListener("drop", (ev) => {
    ev.preventDefault();
    block.classList.remove("drop-hover");
    const file = transferImageFile(ev.dataTransfer);
    const molId = detailMolId;
    guard("#detail-error", async () => {
      if (!file) throw new Error(t("not_an_image"));
      pasteSlot = slot;  // der Drop wählt den Slot auch als Strg+V-Ziel
      await uploadImageBlob(file, slot, molId);
      await refreshMolecule(molId);
    });
  });
}

// Daneben gegangene Drops dürfen nicht die Seite durch die Datei ersetzen
document.addEventListener("dragover", (ev) => {
  if (detailMolId !== null) ev.preventDefault();
});
document.addEventListener("drop", (ev) => {
  if (detailMolId !== null) ev.preventDefault();
});

// ---------- Großansicht (Lightbox) ----------
let zoomPath = null;  // Pfad des gerade vergrößerten Bilds

function openZoom(slot) {
  const mol = findMol(detailMolId);
  const s = mol && slotOf(mol, slot);
  if (!s || !s.path || s.exists === false) return;
  zoomPath = s.path;
  $("#zoom-img").src = $(`#img-view-${slot}`).src;
  $("#zoom-title").textContent = t(`slot_${slot}`);
  $("#dlg-zoom").showModal();
}

$("#zoom-open").addEventListener("click", () =>
  guard("#detail-error", async () => {
    if (!zoomPath) return;
    await api("/open", { method: "POST", body: JSON.stringify({ path: zoomPath }) });
  })
);

// Klick aufs große Bild oder daneben schließt die Großansicht
$("#zoom-img").addEventListener("click", () => $("#dlg-zoom").close());
$("#dlg-zoom").addEventListener("mousedown", (ev) => {
  if (ev.target === $("#dlg-zoom")) $("#dlg-zoom").close();
});

$("#phys-state").addEventListener("change", () =>
  guard("#detail-error", async () => {
    const molId = detailMolId;
    await api(`/molecules/${molId}`, {
      method: "PATCH",
      body: JSON.stringify({ physical_state: $("#phys-state").value }),
    });
    await refreshMolecule(molId);  // blendet den Schmelzpunkt bei „Öl" ein/aus
  })
);

for (const id of ["#phys-color", "#phys-consistency"]) {
  const field = id === "#phys-color" ? "color" : "consistency";
  $(id).addEventListener("blur", () =>
    guard("#detail-error", async () => {
      const molId = detailMolId;
      const mol = findMol(molId);
      if (!mol || $(id).value === (mol[field] || "")) return;
      await api(`/molecules/${molId}`, {
        method: "PATCH",
        body: JSON.stringify({ [field]: $(id).value }),
      });
      await refreshMolecule(molId);
    })
  );
  $(id).addEventListener("keydown", (ev) => { if (ev.key === "Enter") ev.target.blur(); });
}

$("#lit-known").addEventListener("change", () =>
  guard("#detail-error", async () => {
    const molId = detailMolId;
    await api(`/molecules/${molId}`, {
      method: "PATCH",
      body: JSON.stringify({ literature_known: $("#lit-known").checked }),
    });
    await refreshMolecule(molId);
  })
);

$("#lit-doi").addEventListener("blur", () =>
  guard("#detail-error", async () => {
    const molId = detailMolId;
    const mol = findMol(molId);
    if (!mol || $("#lit-doi").value === (mol.doi || "")) return;
    await api(`/molecules/${molId}`, {
      method: "PATCH",
      body: JSON.stringify({ doi: $("#lit-doi").value }),
    });
    await refreshMolecule(molId);
  })
);
$("#lit-doi").addEventListener("keydown", (ev) => { if (ev.key === "Enter") ev.target.blur(); });

// Doppelklick auf die DOI öffnet das Paper im Browser
$("#lit-doi").addEventListener("dblclick", () => {
  const doi = $("#lit-doi").value.trim();
  if (!doi) return;
  const url = /^https?:\/\//i.test(doi) ? doi : `https://doi.org/${doi}`;
  window.open(url, "_blank");
});

// Substanz übrig: Haken schaltet Probennummer + Vermerk frei; unvollständige
// Moleküle werden dann gelb statt rot markiert
$("#sample-available").addEventListener("change", () =>
  guard("#detail-error", async () => {
    const molId = detailMolId;
    await api(`/molecules/${molId}`, {
      method: "PATCH",
      body: JSON.stringify({ sample_available: $("#sample-available").checked }),
    });
    await refreshMolecule(molId);
  })
);

$("#sample-number").addEventListener("blur", () =>
  guard("#detail-error", async () => {
    const molId = detailMolId;
    const mol = findMol(molId);
    if (!mol || $("#sample-number").value === (mol.sample_number || "")) return;
    await api(`/molecules/${molId}`, {
      method: "PATCH",
      body: JSON.stringify({ sample_number: $("#sample-number").value }),
    });
    await refreshMolecule(molId);
  })
);
$("#sample-number").addEventListener("keydown", (ev) => { if (ev.key === "Enter") ev.target.blur(); });

// Zitat und Probenvermerk sind formatierbar (Zeitschrift kursiv, Jahrgang fett …)
for (const [sel, field] of [["#lit-citation", "citation"], ["#sample-comment", "sample_comment"]]) {
  setupRichField($(sel));
  $(sel).addEventListener("blur", () =>
    guard("#detail-error", async () => {
      const molId = detailMolId;
      const mol = findMol(molId);
      const html = richValue($(sel));
      if (!mol || html === richShown(mol[`${field}_html`], mol[field])) return;
      await api(`/molecules/${molId}`, {
        method: "PATCH",
        body: JSON.stringify({ [`${field}_html`]: html }),
      });
      await refreshMolecule(molId);
    })
  );
}

// Molekülname direkt im Titel umbenennen (auch kursiv/tiefgestellt):
// speichern beim Verlassen, Enter übernimmt; leer oder fehlgeschlagen ->
// alter Name kehrt zurück
setupRichField($("#detail-title"), { singleLine: true });
$("#detail-title").addEventListener("blur", async () => {
  const molId = detailMolId;
  const mol = findMol(molId);
  if (!mol) return;
  const inp = $("#detail-title");
  const restore = () => { inp.innerHTML = mol.name_html || esc(mol.name); };
  const html = richValue(inp, true);
  if (!inp.textContent.trim() || html === richShown(mol.name_html, mol.name, true)) {
    restore();
    return;
  }
  const el = $("#detail-error");
  el.textContent = "";
  try {
    await api(`/molecules/${molId}`, {
      method: "PATCH",
      body: JSON.stringify({ name_html: html }),
    });
    await refreshMolecule(molId);
  } catch (e) {
    el.textContent = e.message;
    restore();
  }
});

$("#detail-smiles-save").addEventListener("click", () =>
  guard("#detail-error", async () => {
    const molId = detailMolId;
    await api(`/molecules/${molId}`, {
      method: "PATCH",
      body: JSON.stringify({ smiles: $("#detail-smiles").value }),
    });
    await refreshMolecule(molId);
  })
);

// Auswahlliste der NMR-Kerne: „¹⁹F NMR — Fluor". Gewählt wird der Kern, die
// Bezeichnung („19F NMR") baut die App daraus — daran hängen Word-Häkchen,
// Satz im Dokument und die NMR-Felder des Eintrags.
function renderNucleusPicker() {
  const sel = $("#nucleus-pick");
  if (!sel) return;
  const keep = sel.value;
  sel.innerHTML = "";
  const none = document.createElement("option");
  none.value = "";
  none.textContent = t("nucleus_pick");
  sel.appendChild(none);
  for (const n of nuclei) {
    const opt = document.createElement("option");
    opt.value = n.code;
    opt.textContent = `${supLabel(n.code)} — ${n.name[lang]}`;
    sel.appendChild(opt);
  }
  sel.value = keep;
  $("#nucleus-add").title = t("nucleus_add");
  const dec = $("#nucleus-decoupled");
  dec.parentElement.title = t("nucleus_decoupled_title");
  dec.nextElementSibling.textContent = t("nucleus_decoupled");
  syncDecoupled();
}

// Massenzahlen hochstellen — wie chem_text.typeset auf der Serverseite
const SUPERSCRIPT = { 0: "⁰", 1: "¹", 2: "²", 3: "³", 4: "⁴", 5: "⁵", 6: "⁶", 7: "⁷", 8: "⁸", 9: "⁹" };
const supLabel = (code) =>
  code.replace(/\d+(?=[A-Z])/g, (d) => [...d].map((c) => SUPERSCRIPT[c]).join(""));

// „{¹H}" ist je Kern vorbelegt: ³¹P und ²⁹Si werden üblicherweise entkoppelt
// gemessen, ¹⁹F nicht.
function syncDecoupled() {
  const n = nuclei.find((x) => x.code === $("#nucleus-pick").value);
  $("#nucleus-decoupled").checked = !!(n && n.decoupled);
  $("#nucleus-decoupled").disabled = !n;
}

$("#nucleus-pick").addEventListener("change", syncDecoupled);

$("#nucleus-add").addEventListener("click", () =>
  guard("#detail-error", async () => {
    const n = nuclei.find((x) => x.code === $("#nucleus-pick").value);
    if (!n) return;
    const label = $("#nucleus-decoupled").checked
      ? `${n.mass}${n.symbol}{1H} NMR` : n.code;
    const molId = detailMolId;
    const mol = findMol(molId);
    if (mol && mol.entries.some((e) => e.custom_label === label)) {
      throw new Error(t("nucleus_exists")(supLabel(label)));
    }
    await api(`/molecules/${molId}/entries`, {
      method: "POST",
      body: JSON.stringify({ custom_label: label }),
    });
    $("#nucleus-pick").value = "";
    syncDecoupled();
    await refreshMolecule(molId);
  })
);

$("#other-add").addEventListener("click", () =>
  guard("#detail-error", async () => {
    const label = $("#other-label").value.trim();
    if (!label) return;
    const molId = detailMolId;
    await api(`/molecules/${molId}/entries`, {
      method: "POST",
      body: JSON.stringify({ custom_label: label }),
    });
    $("#other-label").value = "";
    await refreshMolecule(molId);
  })
);

$("#detail-export").addEventListener("click", () =>
  guard("#detail-error", async () => {
    const btn = $("#detail-export");
    btn.disabled = true;
    try {
      const res = await nativeDialog({ kind: "folder" });
      if (!res.path) return;
      const result = await api(`/molecules/${detailMolId}/export`, {
        method: "POST",
        body: JSON.stringify({ target_dir: res.path }),
      });
      $("#export-result").innerHTML = `
        <div class="msg-ok">${t("export_ok")(result.exported.length)}<br><code>${esc(result.target)}</code></div>
        ${result.warnings.length ? `
          <div class="msg-warn">${t("export_warn")}
            <ul>${result.warnings.map((w) => `<li>${esc(w)}</li>`).join("")}</ul>
          </div>` : ""}`;
    } finally {
      btn.disabled = false;
    }
  })
);

// Word-Dokument der Versuchsvorschrift (Zielordner wählen). Dauert spürbar
// länger als der Export — daher eine eigene Laufmeldung.
$("#detail-word").addEventListener("click", () =>
  guard("#detail-error", async () => {
    const btn = $("#detail-word");
    const molId = detailMolId;
    btn.disabled = true;
    try {
      const res = await nativeDialog({ kind: "folder" });
      if (!res.path) return;
      $("#export-result").innerHTML = `<div class="msg-ok">${t("word_running")}</div>`;
      const result = await api(`/molecules/${molId}/word`, {
        method: "POST",
        body: JSON.stringify({ target_dir: res.path }),
      });
      // Das Dokument wird beim Eintrag „Versuchsvorschrift“ verlinkt —
      // die Ansicht muss das mitbekommen (#export-result bleibt dabei stehen).
      await refreshMolecule(molId);
      $("#export-result").innerHTML = `
        <div class="msg-ok">${t("word_ok")(result.spectra)}<br><code>${esc(result.file)}</code>
          ${result.linked === "entry" || result.linked === "extra"
            ? `<br>${t("word_linked")}` : ""}</div>
        ${result.warnings.length ? `
          <div class="msg-warn">${t("word_warn")}
            <ul>${result.warnings.map((w) => `<li>${esc(w)}</li>`).join("")}</ul>
          </div>` : ""}`;
    } finally {
      btn.disabled = false;
    }
  })
);

$("#detail-delete").addEventListener("click", async () => {
  const mol = findMol(detailMolId);
  if (!confirm(t("confirm_del_mol")(mol.name))) return;
  await api(`/molecules/${detailMolId}`, { method: "DELETE" });
  detailMolId = null;
  $("#dlg-detail").close();
  refresh();
});

$("#btn-undo").addEventListener("click", doUndo);

$("#btn-backup").addEventListener("click", async () => {
  const msg = $("#backup-msg");
  msg.className = "";
  msg.textContent = "";
  $("#dlg-backup").showModal();
  await renderBackupList();
});

$("#backup-now").addEventListener("click", async () => {
  const msg = $("#backup-msg");
  msg.className = "";
  msg.textContent = "";
  try {
    await api("/backups", { method: "POST" });
    msg.className = "msg-ok";
    msg.textContent = t("backup_created");
    await renderBackupList();
  } catch (e) {
    msg.className = "error";
    msg.textContent = e.message;
  }
});

// ---------- Datenordner & Lesemodus (mehrere PCs) ----------

let appStatus = null;  // letzte Antwort von /status

function localBadge() {
  // Pfad auf einem lokalen Laufwerk — von anderen PCs aus nicht erreichbar
  const b = document.createElement("span");
  b.className = "local-badge";
  b.textContent = "💻";
  b.title = t("local_path_title");
  return b;
}

function renderStatus(s) {
  appStatus = s;
  const banner = $("#ro-banner");
  banner.hidden = !s.read_only;
  if (s.read_only) {
    const who = (s.lock && s.lock.computer) || "?";
    const since = s.lock && s.lock.since
      ? new Date(s.lock.since).toLocaleString(t("locale"), { dateStyle: "short", timeStyle: "short" })
      : "";
    $("#ro-text").textContent = t("ro_text")(who, since);
  }
  $("#datadir-path").textContent = s.data_dir || "";
}

async function loadStatus() {
  if (quitting) return;  // Server fährt herunter bzw. ist beendet
  try {
    const before = appStatus && appStatus.read_only;
    renderStatus(await api("/status"));
    // Vom Lesemodus zurück ins Schreiben (anderer PC hat beendet) -> Daten neu laden
    if (before && !appStatus.read_only) await refresh();
  } catch {}
}

$("#ro-takeover").addEventListener("click", async () => {
  const who = (appStatus && appStatus.lock && appStatus.lock.computer) || "?";
  if (!confirm(t("ro_confirm_takeover")(who))) return;
  try {
    renderStatus(await api("/lock/takeover", { method: "POST" }));
    await refresh();
  } catch (e) {
    alert(e.message);
  }
});

$("#datadir-change").addEventListener("click", async () => {
  const msg = $("#datadir-msg");
  const btn = $("#datadir-change");
  msg.className = "";
  msg.textContent = "";
  btn.disabled = true;
  try {
    const res = await nativeDialog({ kind: "folder", initial: (appStatus && appStatus.data_dir) || "" });
    if (!res.path) return;
    if (appStatus && appStatus.data_dir &&
        appStatus.data_dir.toLowerCase() === res.path.toLowerCase()) return;
    // Ob der Ordner schon einen Datensatz enthält (-> öffnen) oder leer ist
    // (-> aktuellen hineinkopieren), entscheidet der Server.
    if (!confirm(t("datadir_confirm")(res.path))) return;
    const result = await api("/settings/data-dir", {
      method: "POST",
      body: JSON.stringify({ path: res.path }),
    });
    renderStatus(result);
    msg.className = "msg-ok";
    msg.textContent = t("datadir_switched")(result.data_dir, result.copied);
    await refresh();
    if ($("#dlg-backup").open) await renderBackupList();
  } catch (e) {
    msg.className = "error";
    msg.textContent = e.message;
  } finally {
    btn.disabled = false;
  }
});

// Regelmäßig nachsehen: ist der andere PC fertig (Lesemodus endet) — oder hat
// ein anderer PC die Sperre übernommen (Lesemodus beginnt)?
setInterval(loadStatus, 30000);

// ---------- Weitergabe an einen anderen PC ----------

$("#transfer-export").addEventListener("click", async () => {
  const msg = $("#transfer-msg");
  const btn = $("#transfer-export");
  msg.className = "";
  msg.textContent = "";
  btn.disabled = true;
  try {
    const res = await nativeDialog({ kind: "folder" });
    if (!res.path) return;
    // Optionale Bezeichnung (leer = nur Datum) und optionales Passwort
    // (leer = unverschlüsselt); Abbrechen beendet den Export
    const name = prompt(t("transfer_name_prompt"), "");
    if (name === null) return;
    const pw = prompt(t("transfer_pw_prompt"), "");
    if (pw === null) return;
    msg.textContent = t("transfer_running");
    const result = await api("/transfer/export", {
      method: "POST",
      body: JSON.stringify({ target_dir: res.path, password: pw || null, name: name.trim() || null }),
    });
    msg.className = "msg-ok";
    msg.textContent = t("transfer_exported")(result.file, result.encrypted);
  } catch (e) {
    msg.className = "error";
    msg.textContent = e.message;
  } finally {
    btn.disabled = false;
  }
});

$("#transfer-import").addEventListener("click", async () => {
  const msg = $("#transfer-msg");
  const btn = $("#transfer-import");
  msg.className = "";
  msg.textContent = "";
  btn.disabled = true;
  try {
    const res = await nativeDialog({ kind: "file", filter: "zip" });
    if (!res.path) return;
    const name = res.path.split(/[\\/]/).pop();
    if (!confirm(t("confirm_import")(name))) return;
    msg.textContent = t("transfer_running");
    // Passwortgeschützte Datei: Server antwortet mit 401 (Meldung = Prompt-Text),
    // solange nachfragen, bis das Passwort stimmt oder abgebrochen wird
    let password = null;
    let result;
    for (;;) {
      try {
        result = await api("/transfer/import", {
          method: "POST",
          body: JSON.stringify({ path: res.path, password }),
        });
        break;
      } catch (e) {
        if (e.status !== 401) throw e;
        password = prompt(e.message);
        if (password === null) {
          msg.textContent = "";
          return;
        }
      }
    }
    msg.className = "msg-ok";
    const when = result.created
      ? new Date(result.created).toLocaleString(t("locale"), { dateStyle: "short", timeStyle: "short" })
      : null;
    msg.textContent = t("transfer_imported")(result, when);
    await refresh();
    await renderBackupList();
  } catch (e) {
    msg.className = "error";
    msg.textContent = e.message;
  } finally {
    btn.disabled = false;
  }
});

// ---------- Beenden ----------
// Sauber beenden statt das schwarze Fenster zu schließen: der Server sichert
// (nur falls nötig), gibt die Sperre frei und fährt herunter — das Fenster
// schließt sich dann von selbst. Das Schließen des Fensters beendet den
// Prozess dagegen sofort: kein Beenden-Backup, und ein anderer PC bleibt bis
// zu fünf Minuten im Lesemodus.
let quitting = false;  // ab dem Klick auf „Beenden“: nichts mehr nachladen oder ändern

function showQuitDialog(heading, text, hint = "") {
  $("#dlg-quit h3").textContent = heading;
  $("#quit-text").textContent = text;
  $("#quit-hint").textContent = hint;
}

$("#btn-quit").addEventListener("click", () => {
  showQuitDialog(t("quit_heading"), t("quit_text"));
  $("#quit-error").textContent = "";
  $("#quit-actions").hidden = false;
  $("#dlg-quit").showModal();
});

$("#quit-confirm").addEventListener("click", async () => {
  quitting = true;
  $("#quit-actions").hidden = true;
  $("#quit-error").textContent = "";
  showQuitDialog(t("quit_heading"), t("quit_running"));
  try {
    const result = await api("/shutdown", { method: "POST" });
    showQuitDialog(t("quit_done_heading"), t("quit_done")(result), t("quit_done_hint"));
  } catch (e) {
    quitting = false;
    showQuitDialog(t("quit_heading"), t("quit_text"));
    $("#quit-error").textContent = e.message;
    $("#quit-actions").hidden = false;
  }
});

// Während und nach dem Beenden bleibt der Dialog stehen (Esc schließt ihn nicht)
$("#dlg-quit").addEventListener("cancel", (ev) => {
  if (quitting) ev.preventDefault();
});

// ---------- Sonderzeichen ----------
// Eine Zeichenpalette für alle Textfelder: in den formatierbaren Notizen
// (auch „Durchführung“) über den Ω-Knopf der Werkzeugleiste, in einfachen
// Eingabefeldern über ein kleines Ω am rechten Rand, solange das Feld den
// Fokus hat. Eingefügt wird per insertText, also wie getippt — Text-Undo im
// Feld und die input-/change-/blur-Speicherlogik der Felder bleiben, wie sie
// sind. Palette und Ω sind Popover (Top Layer, über den modalen Dialogen)
// und nehmen dem Feld nie den Fokus (mousedown -> preventDefault).
const symItem = (ch, de, en = de) => ({ ch, de, en });

const GREEK_LOWER = [..."αβγδεζηθικλμνξπρστυφχψω"];
const GREEK_NAMES = {
  de: "Alpha Beta Gamma Delta Epsilon Zeta Eta Theta Iota Kappa Lambda My Ny Xi Pi Rho Sigma Tau Ypsilon Phi Chi Psi Omega".split(" "),
  en: "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi pi rho sigma tau upsilon phi chi psi omega".split(" "),
};
function greekItem(ch) {
  const i = GREEK_LOWER.indexOf(ch.toLowerCase());
  return ch === GREEK_LOWER[i]
    ? symItem(ch, GREEK_NAMES.de[i], GREEK_NAMES.en[i])
    : symItem(ch, `${GREEK_NAMES.de[i]} (groß)`, `capital ${GREEK_NAMES.en[i]}`);
}

const SCRIPT_DIGITS = [..."0123456789+−"];
const scriptItems = (chars, de, en) =>
  [...chars].map((ch, i) => symItem(ch, `${de} ${SCRIPT_DIGITS[i]}`, `${en} ${SCRIPT_DIGITS[i]}`));

// Reiter -> Gruppen -> Zeichen. µ steht als Mikrozeichen (U+00B5, wie AltGr+M)
// unter den Einheiten, das griechische My (U+03BC) unter „Griechisch“.
const SYMBOL_TABS = [
  { key: "sym_tab_common", groups: [
    { key: "sym_signs", items: [
      symItem("−", "Minuszeichen, z. B. −78 °C", "Minus sign, e.g. −78 °C"),
      symItem("±", "Plus-minus"),
      symItem("×", "Malzeichen, z. B. 3 × 20 mL", "Multiplication sign, e.g. 3 × 20 mL"),
      symItem("·", "Mittelpunkt, z. B. CuSO₄·5H₂O", "Middle dot, e.g. CuSO₄·5H₂O"),
      symItem("•", "Punkt, z. B. Kation • Anion", "Bullet, e.g. cation • anion"),
      symItem("≈", "ungefähr", "approximately"),
      symItem("≤", "kleiner oder gleich", "less than or equal to"),
      symItem("≥", "größer oder gleich", "greater than or equal to"),
      symItem("°", "Grad", "Degree"),
      symItem("′", "Strich, z. B. H-2′", "Prime, e.g. H-2′"),
      symItem("″", "Doppelstrich, z. B. H-2″", "Double prime, e.g. H-2″"),
      symItem("‡", "Doppelkreuz (Übergangszustand)", "Double dagger (transition state)"),
    ] },
    { key: "sym_arrows", items: [
      symItem("→", "Reaktionspfeil", "Reaction arrow"),
      symItem("←", "Pfeil nach links", "Left arrow"),
      symItem("⇌", "Gleichgewichtspfeil", "Equilibrium arrow"),
      symItem("↔", "Mesomeriepfeil", "Resonance arrow"),
      symItem("↑", "Gas entweicht", "Gas evolution"),
      symItem("↓", "Niederschlag", "Precipitate"),
    ] },
    { key: "sym_units", items: [
      symItem("°C", "Grad Celsius", "Degrees Celsius"),
      symItem("µ", "Mikro (10⁻⁶)", "Micro (10⁻⁶)"),
      symItem("µL", "Mikroliter", "Microliter"),
      symItem("µmol", "Mikromol", "Micromole"),
      symItem("µg", "Mikrogramm", "Microgram"),
      symItem("µM", "mikromolar", "Micromolar"),
      symItem("µm", "Mikrometer", "Micrometer"),
      symItem("Å", "Ångström"),
      symItem("cm⁻¹", "Wellenzahl", "Wavenumber"),
    ] },
  ] },
  { key: "sym_tab_greek", groups: [
    { key: "sym_greek_lower", items: GREEK_LOWER.map(greekItem) },
    { key: "sym_greek_upper", items: [..."ΓΔΘΛΞΠΣΦΨΩ"].map(greekItem) },
  ] },
  { key: "sym_tab_scripts", groups: [
    { key: "sym_superscript",
      items: scriptItems("⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻", "hochgestellt", "superscript") },
    { key: "sym_subscript",
      items: scriptItems("₀₁₂₃₄₅₆₇₈₉₊₋", "tiefgestellt", "subscript") },
  ] },
  { key: "sym_tab_text", groups: [
    { key: "sym_punctuation", items: [
      symItem("–", "Halbgeviertstrich, z. B. 10–20 min", "En dash, e.g. 10–20 min"),
      symItem("—", "Geviertstrich", "Em dash"),
      symItem("…", "Auslassungspunkte", "Ellipsis"),
      symItem("„", "Anführungszeichen unten", "Low double quotation mark"),
      symItem("“", "Anführungszeichen oben links", "Left double quotation mark"),
      symItem("”", "Anführungszeichen oben rechts", "Right double quotation mark"),
      symItem("‘", "Einfaches Anführungszeichen links", "Left single quotation mark"),
      symItem("’", "Einfaches Anführungszeichen rechts", "Right single quotation mark"),
      symItem("†", "Kreuz (Fußnote)", "Dagger (footnote)"),
      symItem("§", "Paragraf", "Section sign"),
    ] },
    { key: "sym_letters", items: [..."äöüÄÖÜßéèáàçñøå"].map((ch) => symItem(ch, "")) },
  ] },
];
const SYMBOL_BY_CHAR = new Map(
  SYMBOL_TABS.flatMap((tab) => tab.groups.flatMap((g) => g.items)).map((item) => [item.ch, item]),
);

const RECENT_SYMBOLS_KEY = "recentSymbols";
const RECENT_SYMBOLS_MAX = 12;
let symPanel = null;      // Palette (Popover)
let symTarget = null;     // Feld, in das die Palette einfügt
let symTrigger = null;    // Knopf, der sie geöffnet hat (Toolbar-Ω oder Feld-Ω)
let symTab = 0;           // zuletzt gewählter Reiter, gilt für die Sitzung
let symChip = null;       // Ω am fokussierten Eingabefeld (Popover)
let symChipField = null;  // Feld, an dem es gerade steht
// Wachsende Notiz, von Hand gezogener Textbereich, neu gerendertes Detail:
// Palette und Ω wandern mit bzw. verschwinden
const symResize = new ResizeObserver(() => positionSymbolUi());

function recentSymbols() {
  try {
    const list = JSON.parse(localStorage.getItem(RECENT_SYMBOLS_KEY) || "[]");
    return Array.isArray(list) ? list.filter((ch) => typeof ch === "string" && ch) : [];
  } catch {
    return [];
  }
}

function rememberSymbol(ch) {
  const list = [ch, ...recentSymbols().filter((c) => c !== ch)].slice(0, RECENT_SYMBOLS_MAX);
  try { localStorage.setItem(RECENT_SYMBOLS_KEY, JSON.stringify(list)); } catch {}
}

// Felder mit Ω: Text- und Suchfelder, Textbereiche und die formatierbaren
// Einzelfelder (Name, Zitat, Probenvermerk). Die Notizen haben den Knopf in
// ihrer Werkzeugleiste; SMILES und DOI sind maschinenlesbar und bleiben
// außen vor (data-no-symbols).
function symbolField(el) {
  if (!el || el.readOnly || el.disabled || el.closest("[data-no-symbols]")) return false;
  return el.tagName === "TEXTAREA" || el.classList.contains("rich-field")
    || (el.tagName === "INPUT" && (el.type === "text" || el.type === "search"));
}

// Popover im offenen modalen Dialog des Felds anlegen — außerhalb davon wäre
// es inert und nicht anklickbar
function showSymbolPopover(el, field) {
  const parent = field.closest("dialog[open]") || document.body;
  if (el.parentElement !== parent) {
    if (el.matches(":popover-open")) el.hidePopover();
    parent.appendChild(el);
  }
  if (!el.matches(":popover-open")) el.showPopover();
}

function renderSymbolPanel() {
  const tabs = document.createElement("div");
  tabs.className = "sym-tabs";
  const body = document.createElement("div");
  body.className = "sym-body";
  const info = document.createElement("div");
  info.className = "sym-info";

  const idle = () => { info.textContent = t("sym_hint"); };
  const describe = (item) => {
    const ch = document.createElement("b");
    ch.textContent = item.ch;
    info.replaceChildren(ch, item[lang] || "");
    if ([...item.ch].length === 1) {
      const code = document.createElement("span");
      code.className = "sym-code";
      code.textContent = `U+${item.ch.codePointAt(0).toString(16).toUpperCase().padStart(4, "0")}`;
      info.appendChild(code);
    }
  };
  const group = (key, items) => {
    const label = document.createElement("div");
    label.className = "sym-group";
    label.textContent = t(key);
    const grid = document.createElement("div");
    grid.className = "sym-grid";
    for (const item of items) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.tabIndex = -1;
      btn.textContent = item.ch;
      btn.setAttribute("aria-label", item[lang] || item.ch);
      btn.addEventListener("mouseenter", () => describe(item));
      btn.addEventListener("mouseleave", idle);
      btn.addEventListener("click", () => insertSymbol(item.ch));
      grid.appendChild(btn);
    }
    body.append(label, grid);
  };
  const show = (index) => {
    symTab = index;
    [...tabs.children].forEach((b, i) => b.classList.toggle("on", i === index));
    body.replaceChildren();
    // Zuletzt verwendete Zeichen stehen vorn — aktualisiert beim nächsten
    // Öffnen, damit beim Einfügen nichts unter dem Mauszeiger verrutscht
    const recent = index === 0 ? recentSymbols() : [];
    if (recent.length) group("sym_recent", recent.map((ch) => SYMBOL_BY_CHAR.get(ch) || symItem(ch, "")));
    for (const g of SYMBOL_TABS[index].groups) group(g.key, g.items);
    idle();
    positionSymbolUi();
  };
  SYMBOL_TABS.forEach((tab, i) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.tabIndex = -1;
    btn.textContent = t(tab.key);
    btn.addEventListener("click", () => show(i));
    tabs.appendChild(btn);
  });
  symPanel.replaceChildren(tabs, body, info);
  show(symTab);
}

function insertSymbol(ch) {
  const field = symTarget;
  if (!field || !field.isConnected) {
    closeSymbols();
    return;
  }
  if (document.activeElement !== field) field.focus();
  document.execCommand("insertText", false, ch);
  rememberSymbol(ch);
}

function openSymbols(field, trigger) {
  closeSymbols();
  if (!symPanel) {
    symPanel = document.createElement("div");
    symPanel.className = "sym-panel";
    symPanel.popover = "manual";
    symPanel.addEventListener("mousedown", (ev) => ev.preventDefault()); // Fokus bleibt im Feld
  }
  if (document.activeElement !== field) {
    field.focus();
    // Notiz ohne Cursor: am Ende weiterschreiben statt am Anfang
    if (field.isContentEditable) {
      const sel = getSelection();
      sel.selectAllChildren(field);
      sel.collapseToEnd();
    }
  }
  symTarget = field;
  symTrigger = trigger;
  trigger.classList.add("on");
  showSymbolPopover(symPanel, field);
  symResize.observe(field);
  renderSymbolPanel();
}

function closeSymbols() {
  if (symPanel && symPanel.matches(":popover-open")) symPanel.hidePopover();
  if (symTrigger) symTrigger.classList.remove("on");
  if (symTarget && symTarget !== symChipField) symResize.unobserve(symTarget);
  symTarget = null;
  symTrigger = null;
}

function toggleSymbols(field, trigger) {
  if (symTarget === field) closeSymbols();
  else openSymbols(field, trigger);
}

function showSymbolChip(field) {
  if (!symChip) {
    symChip = document.createElement("button");
    symChip.type = "button";
    symChip.className = "sym-chip";
    symChip.popover = "manual";
    symChip.tabIndex = -1;
    symChip.textContent = "Ω";
    symChip.addEventListener("mousedown", (ev) => ev.preventDefault()); // Fokus bleibt im Feld
    symChip.addEventListener("click", () => { if (symChipField) toggleSymbols(symChipField, symChip); });
  }
  symChip.title = t("sym_title");
  symChipField = field;
  field.classList.add("sym-pad");
  showSymbolPopover(symChip, field);
  symResize.observe(field);
  positionSymbolUi();
}

function hideSymbolChip() {
  if (symChip && symChip.matches(":popover-open")) symChip.hidePopover();
  if (symChipField) {
    symChipField.classList.remove("sym-pad");
    if (symChipField !== symTarget) symResize.unobserve(symChipField);
  }
  symChipField = null;
}

// Ω innen am rechten Rand des Felds (bei Textbereichen oben rechts), die
// Palette unter dem Feld — passt sie dort nicht hin, darüber. Ausgerichtet
// wird zur Seite, auf der der auslösende Knopf sitzt.
function positionSymbolUi() {
  const MARGIN = 8;
  if (symChipField) {
    if (!symChipField.isConnected) {
      hideSymbolChip();
    } else {
      const r = symChipField.getBoundingClientRect();
      const size = symChip.offsetHeight;
      const multiline = symChipField.tagName === "TEXTAREA" || symChipField.hasAttribute("data-multiline");
      const top = multiline ? r.top + 4 : r.top + (r.height - size) / 2;
      symChip.style.left = `${r.right - size - 4}px`;
      symChip.style.top = `${top}px`;
      // aus dem sichtbaren Bereich des Dialogs gescrollt -> ausblenden
      const clip = symChipField.closest("dialog");
      const c = clip ? clip.getBoundingClientRect() : { top: 0, bottom: innerHeight };
      symChip.style.visibility = r.bottom > c.top && r.top < c.bottom ? "" : "hidden";
    }
  }
  if (symTarget) {
    if (!symTarget.isConnected) {
      closeSymbols();
      return;
    }
    const r = symTarget.getBoundingClientRect();
    const tr = symTrigger.getBoundingClientRect();
    const w = symPanel.offsetWidth;
    const h = symPanel.offsetHeight;
    const alignLeft = tr.left + tr.width / 2 < r.left + r.width / 2;
    const left = Math.min(Math.max(alignLeft ? r.left : r.right - w, MARGIN), innerWidth - w - MARGIN);
    let top = r.bottom + 6;
    if (top + h > innerHeight - MARGIN) {
      top = r.top - 6 - h >= MARGIN ? r.top - 6 - h : innerHeight - MARGIN - h;
    }
    symPanel.style.left = `${left}px`;
    symPanel.style.top = `${Math.max(top, MARGIN)}px`;
  }
}

document.addEventListener("focusin", (ev) => {
  if (symbolField(ev.target)) showSymbolChip(ev.target);
});
document.addEventListener("focusout", (ev) => {
  if (ev.target === symChipField) hideSymbolChip();
  if (ev.target === symTarget) closeSymbols();
});
// Dialog geschlossen, während darin ein Feld den Fokus hatte
document.addEventListener("close", (ev) => {
  if (ev.target.contains(symTarget)) closeSymbols();
  if (ev.target.contains(symChipField)) hideSymbolChip();
}, true);
document.addEventListener("scroll", positionSymbolUi, true);
window.addEventListener("resize", positionSymbolUi);
// Esc schließt nur die Palette, nicht den Dialog dahinter
document.addEventListener("keydown", (ev) => {
  if (ev.key !== "Escape" || !symTarget) return;
  ev.preventDefault();
  ev.stopPropagation();
  closeSymbols();
}, true);

// Eingabefelder inkl. der formatierbaren Notizen (contenteditable)
function isTextField(el) {
  return Boolean(el && (el.tagName === "INPUT" || el.tagName === "TEXTAREA" || el.isContentEditable));
}

// Strg+Z: globales Undo — außer in Eingabefeldern, dort gilt das native Text-Undo
document.addEventListener("keydown", (ev) => {
  if (!ev.ctrlKey || ev.shiftKey || ev.altKey || ev.key.toLowerCase() !== "z") return;
  if (isTextField(document.activeElement)) return;
  ev.preventDefault();
  doUndo();
});

// Klick außerhalb des Dialogs (auf den Backdrop) schließt ihn.
// Der Inhalt liegt komplett in .dlg-body — trifft ein Klick den Dialog
// selbst, ist es zwangsläufig der Backdrop.
for (const dlg of [$("#dlg-detail"), $("#dlg-backup")]) {
  dlg.addEventListener("mousedown", (ev) => {
    if (ev.target === dlg) dlg.close();
  });
}

$("#dlg-detail").addEventListener("close", () => {
  detailMolId = null;
  detailNodesMol = null;  // beim nächsten Öffnen alles frisch aufbauen
});
$("#search").addEventListener("input", renderProjects);
$("#filter").addEventListener("change", renderProjects);

$("#lang").addEventListener("change", () => {
  lang = $("#lang").value === "en" ? "en" : "de";
  localStorage.setItem("lang", lang);
  applyStaticTexts();
  renderDashboard(lastDashboard || { total_molecules: 0, complete_molecules: 0, by_type: {} });
  renderProjects();
  if (detailMolId !== null) renderDetail();
});

// Enter-Taste in den Anlege-Dialogen
$("#project-name").addEventListener("keydown", (e) => { if (e.key === "Enter") $("#project-save").click(); });
$("#mol-smiles").addEventListener("keydown", (e) => { if (e.key === "Enter") $("#mol-save").click(); });

// ---------- Theme (hell/dunkel) ----------
// Ohne gespeicherte Wahl folgt die App der Windows-Einstellung;
// der Umschalter legt die Wahl fest (localStorage, wie die Sprache).
function isDarkNow() {
  const explicit = document.documentElement.dataset.theme;
  if (explicit) return explicit === "dark";
  return matchMedia("(prefers-color-scheme: dark)").matches;
}

function updateThemeButton() {
  $("#btn-theme").textContent = isDarkNow() ? "☀" : "🌙";
}

$("#btn-theme").addEventListener("click", () => {
  const next = isDarkNow() ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  localStorage.setItem("theme", next);
  updateThemeButton();
});

// Folgt der Systemeinstellung, solange keine eigene Wahl getroffen wurde
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", updateThemeButton);

// Versionsstempel der Weitergabe-Kopie anzeigen (im Entwicklungsordner leer)
async function showVersion() {
  try {
    const { version } = await api("/version");
    if (version) {
      const el = $("#app-version");
      el.textContent = version;
      el.hidden = false;
    }
  } catch {}
}

// ---------- Start ----------
(async () => {
  $("#lang").value = lang;
  applyStaticTexts();
  updateThemeButton();
  showVersion();
  loadStatus();
  datatypes = await api("/datatypes");
  typeFields = Object.fromEntries(datatypes.map((dt) => [dt.code, dt.fields]));
  // Zusätzliche NMR-Kerne: Katalog für die Auswahlliste, Felder wie ¹H/¹³C
  const nmr = await api("/nuclei");
  nuclei = nmr.nuclei;
  typeFields.other_nmr = nmr.fields;
  renderNucleusPicker();
  await refresh();
})();
