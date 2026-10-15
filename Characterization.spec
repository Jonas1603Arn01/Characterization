# PyInstaller recipe for Characterization.exe — build with tools\build_exe.ps1.
# One folder (not one file): starts faster and trips fewer virus scanners.
import os

from PyInstaller.utils.hooks import collect_all, collect_submodules

datas = [("static", "static"), ("app/wordskel", "app/wordskel")]
binaries = []
hiddenimports = collect_submodules("uvicorn") + ["app.dialog_worker"]

# Version stamp written by the build script (shown in the header and title)
if os.path.isfile("build/VERSION"):
    datas.append(("build/VERSION", "."))

for package in ("rdkit",):
    d, b, h = collect_all(package)
    datas += d
    binaries += b
    hiddenimports += h

a = Analysis(
    ["desktop.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["pytest", "_pytest", "httpx"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Characterization",
    icon="static/icon.ico",
    console=False,
    upx=False,
)
coll = COLLECT(exe, a.binaries, a.datas, name="Characterization", upx=False)
