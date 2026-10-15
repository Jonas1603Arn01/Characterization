# Characterization

A desktop program (Windows and macOS) for organizing characterization data
in synthetic organic chemistry. You track your compounds as **Projects → Molecules → Data types**
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

## Getting started

Download the file for your system from the [Releases](../../releases) page,
under **Assets** — **not** "Source code (zip)", which contains no program:

| System | File |
| --- | --- |
| Windows 10/11 | `Characterization-<version>-windows.zip` |
| macOS (Apple silicon, M1 or newer) | `Characterization-<version>-macos-arm64.zip` |

**Windows:** extract the ZIP to a permanent location (e.g. Documents — not
too deep in sub-folders, Windows limits path lengths) and double-click
**`Create desktop shortcut.bat`** in it; the desktop icon then starts
`Characterization.exe`. The program is not code-signed, so SmartScreen may
warn on the first start (*More info* → *Run anyway*). The window needs the
Microsoft Edge WebView2 runtime, which Windows 11 and current Windows 10
already have; without it the app opens in your browser instead.

**macOS:** drag `Characterization.app` into Applications. The app is not
notarized by Apple, so macOS blocks the first start; run once in Terminal
`xattr -dr com.apple.quarantine /Applications/Characterization.app`
(or open it, then *System Settings → Privacy & Security → Open Anyway*).

The app opens in its own window — no Python, no browser, no server window.
To close it, close the window or click **Quit** (top right): both take the
exit backup and release the data folder for other PCs. `GETTING-STARTED.txt`
next to the program is the short version of this README for each system.

**ChemDraw on macOS:** pasting from ChemDraw (Cmd+V) keeps the ChemDraw
drawing (.cdx) as on Windows, "ChemDraw ⬈" opens it in ChemDraw, and "Copy"
puts it back on the clipboard. Two things need Windows, where the app can
remote-control ChemDraw: after you edit a .cdx, the picture is not
re-rendered automatically — copy the drawing in ChemDraw and paste it again —
and the reaction equation in the Word document is still an editable ChemDraw
object, but with a picture preview instead of vector graphics. On macOS the
app recognizes ChemDraw's drawing by its content and notes in `app.log` under
which clipboard type ChemDraw delivered it.

## Updates (no data loss)

Your data is kept separately from the program, so an update never touches
it (`data`, `backups`, `config.json`):

| System | Data folder |
| --- | --- |
| Windows | `%LOCALAPPDATA%\Characterization` |
| macOS | `~/Library/Application Support/Characterization` |

**Automatic (from version 1.4.0 on):** shortly after start the app asks
GitHub once whether a newer version exists. If so, a bar at the top offers
it — nothing happens until you click **"Install update and restart"**. The
app then downloads the file for your system, checks it against the
release's checksum list, takes a backup and quits like with **Quit**, swaps
itself for the new version and starts again. If anything goes wrong, the old
version stays and keeps running. The check only contacts github.com (no
data of yours is sent); to switch it off, put `"update_check": false` into
`config.json` in the data folder. Progress and problems are written to
`update.log` there. On macOS the app has to be in Applications (not started
from Downloads) to update itself.

**By hand** (or for versions before 1.4.0):

1. Close the app.
2. Download the new file from the [Releases](../../releases) page.
3. Replace the old program with the new one (Windows: delete the old folder
   and extract the new ZIP — if it is now somewhere else, run
   `Create desktop shortcut.bat` again; macOS: replace the app in
   Applications and repeat the `xattr` command).

The installed version is shown in the window title and in the app header.

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

The choice is remembered per PC in `config.json` in the program's data folder
(see the table above; never touched by updates). Backups then live in `backups\`
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

Everything below is relative to the program's data folder (table under
"Updates").

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
  folder choice itself stays in `config.json`.

## Troubleshooting

- **Windows says the program is unknown** — *More info* → *Run anyway*
  (the program is not code-signed).
- **The window stays blank or does not open** — the Microsoft Edge WebView2
  runtime is missing; the app then opens in your browser instead. Install
  WebView2 from microsoft.com to get the window back.
- **The ZIP cannot be extracted / files are missing** — extract it to a
  shorter path (e.g. directly into Documents).
- **macOS: "Characterization is damaged and can't be opened"** — run the
  `xattr` command from "Getting started"; the app is not notarized.
- **Anything else** — error details are in `app.log` in the program's data
  folder (rewritten on every start).

## For developers

**Install from the repository** (requirements: Git, Python 3.12+):

```powershell
git config --global core.autocrlf true   # once, for correct line endings
git clone https://github.com/Jonas1603Arn01/Characterization.git
cd Characterization
.\tools\setup.ps1  # or tools\setup.bat; on macOS: python3 -m venv .venv && pip install -r requirements.txt
python run.py      # development server, opens the browser at 127.0.0.1:8710
```

From the source folder the app keeps `config.json`, `data\` and `backups\`
in the folder itself; only the packaged program uses the per-system data
folder.

**Run the tests:**

```
.venv\Scripts\python.exe -m pytest tests
```

**Build the program** for the system you are on (own window via pywebview:
WebView2 on Windows, WebKit on macOS; packaged with
PyInstaller — recipe in `Characterization.spec`, launcher in `desktop.py`):

```
python tools/build.py --version 1.0.0 --test
python tools/smoke_test.py --window
```

`build.py` creates the program in `dist/` (plus the helper files from
`release/<system>/`) and the download archive next to it, using its own
`.venv-build`. `smoke_test.py` starts the build with throwaway data and
checks start-up, the UI in the window, RDKit and a clean quit;
`update_test.py` lets a copy posing as version 0.0.1 update itself to the
newest GitHub release (`app/updater.py`). To try a
build by hand without touching your real dataset, set `CHARACTERIZATION_HOME`
to a scratch folder (and `CHARACTERIZATION_PORT`, e.g. 8790, if the real app
is running).

Releases are built by GitHub Actions (`.github/workflows/release.yml`) for
Windows and macOS when a version tag is pushed (`git tag v1.0.0`,
`git push origin v1.0.0`); every build is smoke-tested and only then
released, so a download never contains anything from a developer PC.
"Run workflow" in the Actions tab builds and tests without releasing.

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
