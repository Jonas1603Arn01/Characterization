"""Builds the packaged program for the system it runs on.

    python tools/build.py [--version 1.2.0] [--test]

Result in dist/:
    Windows  Characterization/ (Characterization.exe) + Characterization-<v>-windows.zip
    macOS    Characterization.app + Characterization-<v>-macos-arm64.zip

Uses its own environment (.venv-build) so the everyday .venv stays as it is.
The build contains only program files: static/, app/ and the Python
packages, plus the helper files from release/<system>/. data/, backups/,
config.json and the Git history never go in; a check at the end aborts if
any of them turns up anyway.
"""
import argparse
import datetime
import os
import platform
import shutil
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENV = ROOT / ".venv-build"
DIST = ROOT / "dist"

SYSTEM = {"win32": "windows", "darwin": "macos"}.get(sys.platform, "")
MACHINE = {"amd64": "x86_64", "x86_64": "x86_64", "arm64": "arm64",
           "aarch64": "arm64"}.get(platform.machine().lower(), platform.machine().lower())

LEAK_NAMES = {"app.db", "config.json", "in-use.lock", ".git", ".claude", ".venv"}
LEAK_SUFFIXES = {".db", ".cdx"}
DATA_DIRS = {"data", "backups", "undo", "images"}
# Folders where PyInstaller puts the bundled files (data dirs must not appear there)
BUNDLE_ROOTS = {"Characterization", "_internal", "Resources", "Frameworks"}


def run(*cmd: object, **kw) -> None:
    print("+", " ".join(str(c) for c in cmd), flush=True)
    subprocess.run([str(c) for c in cmd], check=True, cwd=ROOT, **kw)


def venv_python() -> Path:
    return VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def check_no_leaks(folder: Path) -> None:
    """Abort if any dataset, settings or developer file made it into the build."""
    leaks = []
    for p in folder.rglob("*"):
        if p.name in LEAK_NAMES or (p.is_file() and p.suffix.lower() in LEAK_SUFFIXES):
            leaks.append(p)
        elif p.is_dir() and p.name in DATA_DIRS and p.parent.name in BUNDLE_ROOTS:
            leaks.append(p)
    if leaks:
        for p in leaks:
            print("  ", p)
        sys.exit("Build contains data or developer files - aborted")


def package(version: str) -> Path:
    """Put the helper files next to the program and pack the download."""
    stem = f"Characterization-{version}-{SYSTEM}" + ("" if SYSTEM == "windows" else f"-{MACHINE}")
    helpers = ROOT / "release" / SYSTEM
    if SYSTEM == "macos":
        # ZIP holds a folder with the .app and the guide (ditto keeps the
        # symlinks and signature inside the bundle intact)
        stage = DIST / "package" / "Characterization"
        if stage.parent.exists():
            shutil.rmtree(stage.parent)
        stage.mkdir(parents=True)
        shutil.copytree(DIST / "Characterization.app", stage / "Characterization.app", symlinks=True)
        for f in helpers.iterdir():
            shutil.copy2(f, stage)
        check_no_leaks(stage)
        archive = DIST / f"{stem}.zip"
        archive.unlink(missing_ok=True)
        run("ditto", "-c", "-k", "--sequesterRsrc", "--keepParent", stage, archive)
        return archive

    folder = DIST / "Characterization"
    for f in helpers.iterdir():
        shutil.copy2(f, folder)
    check_no_leaks(folder)
    archive = DIST / f"{stem}.zip"
    archive.unlink(missing_ok=True)
    shutil.make_archive(str(DIST / stem), "zip", DIST, "Characterization")
    return archive


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--version", default="")
    ap.add_argument("--test", action="store_true", help="run the test suite first")
    args = ap.parse_args()
    version = args.version.lstrip("v") or "dev-" + datetime.date.today().isoformat()
    version = version.replace("/", "-")  # test runs on branch ci/…
    if not SYSTEM:
        sys.exit("The program is built for Windows and macOS only")

    py = venv_python()
    if not py.exists():
        print("Creating build environment (.venv-build) ...", flush=True)
        venv.create(VENV, with_pip=True)
    env = dict(os.environ, PIP_CONFIG_FILE=str(ROOT / "pip.ini"))
    run(py, "-m", "pip", "install", "--disable-pip-version-check", "-q",
        "-r", "requirements.txt", "-r", "requirements-build.txt", env=env)

    if args.test:
        run(py, "-m", "pytest", "tests", "-q")

    (ROOT / "build").mkdir(exist_ok=True)
    (ROOT / "build" / "VERSION").write_text(version + "\n", encoding="utf-8")
    run(py, "-m", "PyInstaller", "--noconfirm", "--clean", "Characterization.spec")

    archive = package(version)
    print(f"\nDone: {archive.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
