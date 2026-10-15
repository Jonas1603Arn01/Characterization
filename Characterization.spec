# PyInstaller recipe for the packaged program — build with tools/build.py.
# Windows: one folder with the executable (not one file: starts faster and
# trips fewer virus scanners). macOS: Characterization.app.
import os
import sys

from PyInstaller.utils.hooks import collect_all, collect_submodules

datas = [("static", "static"), ("app/wordskel", "app/wordskel")]
binaries = []
hiddenimports = collect_submodules("uvicorn") + ["app.dialog_worker"]
# pywebview picks its window backend at runtime; name it so it is bundled
if sys.platform == "darwin":
    hiddenimports += ["webview.platforms.cocoa", "app.clipboard_mac"]
else:
    hiddenimports += ["webview.platforms.winforms", "webview.platforms.edgechromium"]

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

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="Characterization.app",
        icon="static/icon.ico",  # converted to .icns by PyInstaller (Pillow)
        bundle_identifier="io.github.jonas1603arn01.characterization",
        version=open("build/VERSION").read().strip() if os.path.isfile("build/VERSION") else "0",
        info_plist={"NSHighResolutionCapable": True},
    )
