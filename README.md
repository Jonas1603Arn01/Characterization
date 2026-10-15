# Characterization

A local web app for organizing characterization data in synthetic organic
chemistry. You track your compounds as **Projects → Molecules → Data types**
and see at a glance which analytics are still missing before a compound is
fully characterized.

Everything runs on your own PC — no account, no cloud, nothing leaves your
machine.

## What the app does for you

- **Dashboard** — how many molecules you have, how many are complete, and a
  per-method statistic (¹H NMR, ¹³C NMR, MS, IR, …).
- **Three states per data type** — every molecule starts with the standard
  set (procedure, ¹H/¹³C/2D NMR, MS, IR, melting point), each either
  *present*, *missing*, or *n/a* (not needed for this molecule; doesn't
  count toward completeness). Custom entries (e.g. elemental analysis) can
  be added freely. A molecule marked as an **oil** automatically drops the
  melting point.
- **Structure image, reaction scheme & reaction equation** — three image
  slots per molecule: paste directly from ChemDraw with **Ctrl+V**, drag an
  image file onto the slot, or pick a file. Click an
  image to enlarge it. When pasting from ChemDraw, the native ChemDraw file
  (.cdx) is saved alongside the picture — the "ChemDraw ⬈" button reopens
  the structure in ChemDraw for further editing, "Copy" puts the drawing on
  the clipboard (pastes editable into ChemDraw and as a ChemDraw object into
  Word/PowerPoint), and exports include the
  .cdx file. After editing and saving in ChemDraw, the picture in the app
  updates automatically (ChemDraw re-renders it in the background).
  If the molecule's SMILES field is still empty, pasting the
  structure also fills it in from the clipboard (formula and exact mass are
  computed automatically).
- **SMILES → formula & exact mass** — enter a SMILES and the molecular
  formula and exact mass are calculated automatically.
- **Link your data files** — measurement folders, MNova files, Word
  documents, PDFs… Every NMR tab has three fixed slots: the measurement
  folder, the MNova file and the SVG of the spectrum (the one the Word
  document embeds). Files are only *referenced* by path, never copied, so
  nothing is duplicated. Double-click a linked path to open its folder in
  Explorer (linked folders open themselves); "change…" points a link to a
  different file. Renaming a linked file or folder in Explorer does **not**
  break the link: the app remembers the file's file-system id and finds the
  renamed file in its folder, then stores the new name. Links that are really
  gone (file deleted or moved elsewhere) are flagged with ⚠.
- **Notes** — any number of notes per data type (shifts, remarks,
  HRMS values, …) with **bold**, *italic*, super- and subscript
  (toolbar under the "Note" label, or Ctrl+B / Ctrl+I / Ctrl+. / Ctrl+,).
  Exports keep the formatting as plain text with Unicode super-/subscripts
  (e.g. ¹³C, CDCl₃).
- **Pasting keeps formatting** — text pasted from Word, MestReNova, a web
  page etc. keeps its bold, italic, super- and subscript in the notes, the
  molecule name (also in the Word title, e.g. *N*-, *tert*-), the citation
  and the sample remark; these accept the same shortcuts as notes. All other
  text fields have no italics, so super-/subscripts arrive there as Unicode
  characters (CDCl₃). Characters in Word's Symbol font (δ, μ, °, ±) are
  converted to real Unicode characters everywhere.
- **Physical properties & literature** — physical state, color,
  consistency, "known compound" flag with DOI (double-click the DOI to open
  the paper), a free-text citation and a link to the paper's supporting information (PDF or Word
  file; double-click to open its folder, exported as `SI - <file>` next to
  `Info.txt`).
- **Search & filter** — by name, formula, or SMILES; filter for complete /
  incomplete molecules. Drag a molecule card onto another project to move it.
- **Export** — one molecule or a whole project. Creates a clean folder tree
  `<target>/<project>/<molecule>/<method>/…` with all linked files copied
  in, plus an `Info.txt` summary (formula, mass, properties, DOI, all notes)
  per molecule.
- **Word document** — "Word document…" in a molecule's detail dialog writes
  the procedure as a ready-made `.docx`: compound name and number, the
  reaction equation as an embedded ChemDraw object (double-click it in Word
  to keep editing the structure), the **Procedure** text field, the analytics
  from your notes, and every linked `.svg` spectrum on its own page with a
  numbered caption. The finished document is linked back under "Procedure".
  Everything is typeset the way it appears in a thesis — ¹H NMR bold with a
  raised mass number, CDCl₃ subscripted, the coupling *J* italic, and the
  observed nucleus italic in every assignment (the *H* for ¹H, the *C* for
  ¹³C). In the procedure text, formulas get their subscripts and every value
  is glued to its unit with a non-breaking space, so justified lines never
  break between "1.52" and "g". Nothing is invented: anything the app has no
  data for is left as a red `[insert]` marker.
- **More NMR nuclei** — ¹H, ¹³C and 2D NMR are there from the start (2D NMR
  has two spectrum slots, HSQC and HMBC, instead of one); every
  further nucleus is picked from a list at the bottom of the molecule detail
  (¹⁹F, ³¹P, ¹¹B, ²⁹Si, ¹⁵N, ⁷Li, ²H, ²⁷Al, ⁷⁷Se, ¹¹⁹Sn, …). The `{¹H}` box
  next to it is pre-ticked for the nuclei that are usually measured
  ¹H-decoupled. The entry arrives fully set up: the name typeset (`¹⁹F NMR`),
  the same three slots as ¹H and ¹³C (data folder, MNova file, SVG spectrum),
  the "into Word document" box already ticked, and a rounding button with the
  decimals that are usual for that nucleus. Its note field offers a **δ**
  button that inserts the header line for you —
  `19F NMR (471 MHz, CDCl3, 298 K) δ [ppm] = `: the frequency follows from the
  nucleus and the spectrometer, solvent and temperature are taken word for
  word from the nuclei you have already recorded for that molecule. Nothing is
  written on its own; the button has to be pressed.
- **Custom entries in the document** — every custom entry has an "into Word
  document" checkbox. Typing an NMR name yourself works just as well (`19F NMR`,
  `31P{1H} NMR`, `1H,15N HMBC`) — the box is then ticked for you: the entry
  goes in by exactly the same rules as ¹H and ¹³C — its own line right after
  the ¹³C, its spectra with the same kind of caption, and its measurement
  conditions read from its own note. Tick the box on anything else (elemental
  analysis, X-ray, …) and it gets its line at the end of the analytics block,
  with the entry name as the bold label. Unticked entries stay out entirely.
- **Transfer to another PC** — create a transfer file (database + images)
  from the Backups dialog and import it on another PC running this app, e.g.
  to give your supervisor a quick overview of the status and storage location
  of all data.
- **Undo & backups** — every change can be undone with **Ctrl+Z** (last 20
  actions, including deletions and restores). The database is backed up
  automatically on every start and exit (last 10 kept); older states can be
  restored from the Backups dialog.
- **Language & theme** — EN/DE toggle and light/dark theme in the header;
  both are remembered.

## Getting started with the program (download from GitHub)

1. Download `Characterization-<version>-windows.zip` from the
   [Releases](../../releases) page and extract it anywhere (e.g. Documents).
2. Double-click **`Characterization.exe`** inside the extracted folder. The app
   opens in its own window — no Python, no browser, no black server window.
   Closing the window (or **Quit**) takes the exit backup and releases the
   data folder.
3. Optional: right-click `Characterization.exe` → *Send to* → *Desktop
   (create shortcut)*.

Your data is kept separately from the program, in
`%LOCALAPPDATA%\Characterization` (`data\`, `backups\`, `config.json`). To
update, delete the old program folder and extract the new ZIP — your data is
not touched. The program is not code-signed, so Windows SmartScreen may warn
on the first start (*More info* → *Run anyway*). The window needs the
Microsoft Edge WebView2 runtime, which Windows 11 and current Windows 10
already have; without it the app opens in your browser instead.

Already using the `start.bat` version? Point the program at your existing
data via **Backups → Data folder → "Change data folder…"** and pick the
`data` folder of your old installation.

## Getting started (received the app as a folder or ZIP?)

You only need **Python 3.12** (from [python.org](https://www.python.org/downloads/) —
tick *"Add python.exe to PATH"* during setup).

1. If you got a ZIP, **extract it first**, then move the folder to a
   permanent location (e.g. Documents).
2. Double-click **`start.bat`**. The first launch sets everything up
   automatically (takes a few minutes), then your browser opens at
   `http://127.0.0.1:8710`.
3. Recommended: double-click **`Help and tools\Create desktop shortcut.bat`**
   to get a "Characterization" icon on your desktop.

The black server window must stay open while you use the app. To close the
app, click **Quit** (top right): it takes a backup, releases the data folder
for other PCs, and the black window then closes by itself. Closing the black
window directly ends the app immediately — without the exit backup, and other
PCs stay read-only for about five minutes. The **`Help and tools`** folder contains
everything you need besides `start.bat`: the quick guide
(`GETTING-STARTED.txt`), the update installer, and the shortcut creator.

## Installing an update (no data loss)

When you receive a new version as a ZIP
(`Characterization-App_YYYY-MM-DD.zip`):

1. Put the ZIP in your **Downloads** or **Desktop** folder.
2. **Close the app** (**Quit** button, top right).
3. Double-click **`Help and tools\Install update.bat`**.

The script finds the newest ZIP automatically, saves an extra safety copy of
your database to `backups\`, and replaces **only the program files** — your
projects, images, notes, and backups (`data\`, `backups\`) are never touched.
Changed Python packages are installed automatically.

The installed version is shown in the app header next to the title (and in
the `VERSION` file).

> Updating from an old version that still had German file names? The update
> also recognizes `Charakterisierung-App*.zip` and cleans up the old German
> helper files (`ANLEITUNG.txt`, `Update einspielen.bat`, …) on the next run.

## Sharing the app with someone else (without your data)

1. Double-click **`Distribute.bat`**.
2. Choose whether the copy includes the **Distribute feature** itself
   (`y`: the recipient can pass the app on in the same way; default `n`).
3. This creates a clean copy `Characterization-App` on your desktop plus a
   dated ZIP `Characterization-App_YYYY-MM-DD.zip`.

The copy contains only the program — **not** your `data\`, `backups\`,
`.venv`, or the Git history. A safety check aborts if any database or
developer files would leak into the copy. The copy is stamped with a version
(file `VERSION`, shown in the app header).

- **First-time handover:** send the ZIP (or copy the folder to a USB drive).
  The recipient needs Python 3.12 and starts with `start.bat`.
- **Updates later:** run `Distribute.bat` again and send only the new ZIP —
  the recipient double-clicks `Help and tools\Install update.bat` and keeps
  all their data. The update also follows your choice for the Distribute
  feature: an update without it removes it from the recipient's copy.
- **Passed on by a recipient:** such a copy keeps its original version stamp,
  so your next real release is still recognized as newer.

## Transferring your data to another PC

To show your current data on another PC that already runs this app (e.g. your
supervisor's):

1. Open **Backups → Transfer to another PC → "Create transfer file…"** and
   pick a target folder (USB drive, network share, …). This creates
   `characterization-transfer-<date>.zip` with your database and all images.
   You can optionally give the file a **name** (e.g. "July status") — it
   becomes part of the file name and is shown again when importing — and set
   a **password**, in which case the file is AES-encrypted and can only be
   imported with that password.
2. On the other PC, open the same dialog and click **"Import transfer
   file…"** (the password, if set, is asked for). The current data there is
   replaced — a backup of it is created automatically first, so nothing is
   lost. These pre-import backups are marked **"before import"** in the
   backup list and rotate separately from the automatic start/exit backups
   (last 20 kept), so the way back to the previous dataset stays available.

Linked measurement/document files do **not** travel along: their paths are
kept as references, so the recipient sees the status of every molecule and
where each file is stored (paths on shared network drives open directly).

## Working from several PCs with the same dataset

Put the data folder on a network drive and point every PC at it:

1. On the PC that has your data: **Backups → Data folder → "Change data
   folder…"** and pick an (empty) folder on a network drive, e.g.
   `H:\Uni\Promotion\Characterization-Data`. The current dataset (database +
   images) is copied there and the app switches to it immediately.
2. On every other PC (the app installed there as usual): same dialog, pick
   the **same** folder. It already contains a dataset, so it is simply
   opened — the local data on that PC stays untouched.

The choice is remembered per PC in `config.json` next to `start.bat` (never
touched by updates, never distributed). Backups then live in `backups\`
inside the data folder, so they are the same from every PC.

**One PC edits at a time.** SQLite on a network share cannot safely be
written by two computers at once, so the first app to open the folder marks
it as in use (`in-use.lock`). A second PC opens the dataset **read-only**: a
banner says which PC is working and since when, and everything becomes
editable automatically (within about half a minute) once the app is closed
there. After a crash the lock goes stale after five minutes and is taken
over silently; "Take over anyway" does the same on demand.

**Paths stay valid on every PC.** Images pasted from ChemDraw are stored by
file name only, relative to the data folder. Linked files and folders on
network drives are stored in UNC form (`\\server\share\…`) — the drive
letter may differ from PC to PC, the UNC path does not — and are shown with
your local drive letter where the share is mapped. Existing datasets are
converted on the next start. Links to local drives (`C:\…`) cannot be
translated; they are marked with 💻 as "only on this PC".

## Where your data lives

- SQLite database: `data\app.db`; pasted images and ChemDraw (.cdx) files:
  `data\images\`. Image files that are no longer referenced anywhere (neither
  by the database nor by an undo snapshot) are cleaned up automatically
  before each backup, so backups and transfer files stay small.
- Backups: `backups\` (automatic on start/exit + "Create backup now" button,
  rotating, last 10 kept; backups taken right before a transfer import carry
  `-import` in the file name and rotate separately, last 20 kept).
- Undo snapshots: `data\undo\` (last 20).
- Linked measurement/document files stay where they are — only their paths
  are stored (the export is the only thing that copies files).
- With a custom data folder (see above) all of this lives in that folder
  instead (`app.db`, `images\`, `undo\`, `backups\`, `in-use.lock`); the
  folder choice itself is in `config.json` next to `start.bat`.

## Troubleshooting

- **"No Python found"** — install Python 3.12 and tick *Add python.exe to
  PATH*, then run `start.bat` again.
- **App doesn't start after moving to another PC** — just run `start.bat`;
  the environment is rebuilt automatically.
- **Browser shows nothing** — open `http://127.0.0.1:8710` manually; make
  sure the server window is open.
- **Update failed / app broken after update** — delete the `.venv` folder
  and run `start.bat`; the environment is rebuilt from scratch. Your data is
  in `data\` and is not affected.

## For developers

**Install from the repository** (requirements: Git, Python 3.12+):

```powershell
git config --global core.autocrlf true   # once, for correct line endings
git clone <repo-url>
cd Charackterisierung
.\tools\setup.ps1  # or tools\setup.bat; on macOS/Linux: python3 -m venv .venv && pip install -r requirements.txt
python run.py
```

**Run the tests:**

```
.venv\Scripts\python.exe -m pytest tests
```

**Build the program** (`Characterization.exe`, own window via pywebview,
packaged with PyInstaller — recipe in `Characterization.spec`, launcher in
`desktop.py`):

```powershell
powershell -ExecutionPolicy Bypass -File tools\build_exe.ps1 -Version 1.0.0 -Test
```

This creates `dist\Characterization\` and a ZIP next to it, using its own
`.venv-build`. To try a build without touching your real dataset, set
`CHARACTERIZATION_HOME` to a scratch folder before starting the exe.
Releases are built by GitHub Actions (`.github/workflows/release.yml`) when a
version tag is pushed (`git tag v1.0.0`, `git push origin v1.0.0`), so a
download never contains anything from a developer PC.

**Architecture:** FastAPI + SQLite (SQLAlchemy) backend in `app/`, vanilla
HTML/CSS/JS frontend in `static/`, served at `127.0.0.1:8710`. All UI texts
and API error messages are bilingual (EN default, DE via the header toggle /
`X-Lang` header). Native file dialogs run in a tkinter subprocess; the
Windows clipboard is read server-side so ChemDraw's "Copy as PNG" works and
the native "ChemDraw Interchange Format" (CDX) is captured alongside. When a
saved .cdx becomes newer than its picture (edited via "ChemDraw ⬈"), the app
re-renders the picture through ChemDraw's COM automation (invisible to the
user; see `app/chemdraw_render.py`). "Copy" writes the clipboard server-side
as well: CDX, an embedded ChemDraw OLE object ("Embed Source" + "Object
Descriptor", same container as the Word export) and the picture as DIB only
(`clipboard_win.write_clipboard`) — with an additional "PNG" format, Word's
Ctrl+V would paste the picture instead of the ChemDraw object.

**Word export** (`app/word_export.py`) is modelled on one hand-written
document and reproduces its layout. It is written without python-docx,
because the three things that matter here are all beyond it: an SVG with a
raster fallback, an embedded ChemDraw object, and the `SEQ` field behind the
figure numbering. The pieces:

| Module | Does |
| --- | --- |
| `docx_write.py` | Writes the `.docx` package. The parts that never change (styles, theme, fonts, settings) ship as files in `app/wordskel/` and come from the original document, so generated files look exactly like a hand-written one. |
| `chem_text.py` | Turns the plain text of a note into typeset runs (bold head with raised mass number, subscripted formulas, italic *J* and observed nucleus). A note that carries its own formatting is passed through untouched. |
| `olecf.py` | Writes the OLE container ([MS-CFB]) that holds the ChemDraw drawing, so the equation stays editable in Word. |
| `svg_raster.py` | Rasterizes the SVG spectra with Inkscape — Word stores every SVG together with a raster fallback. Set `inkscape_path` in `config.json` if Inkscape lives somewhere unusual. |

The export needs ChemDraw (vector output of the equation) and Inkscape
(fallback images) on the PC; without either it still produces a document and
says in its warnings what is missing.
