"""Smoke test of a built program (dist/), on the system it was built for.

    python tools/smoke_test.py [--window]

Starts the packaged program with throwaway data on a test port and checks
what only the frozen build can get wrong: it starts at all, serves the UI,
RDKit computes a formula, and "Quit" ends it cleanly (backup written, data
folder released). With --window the real program window is opened too and
must load the UI (on Linux run it under xvfb-run). Never touches a real
dataset: CHARACTERIZATION_HOME points into a temporary folder.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORT = 8790
BASE = f"http://127.0.0.1:{PORT}/api"


def program() -> Path:
    dist = ROOT / "dist"
    if sys.platform == "darwin":
        return dist / "Characterization.app" / "Contents" / "MacOS" / "Characterization"
    return dist / "Characterization" / ("Characterization.exe" if os.name == "nt" else "Characterization")


def call(method: str, path: str, body: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read() or b"null")


def wait_for(check, seconds: float, what: str) -> None:
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        try:
            if check():
                return
        except OSError:
            pass
        time.sleep(0.5)
    raise AssertionError(f"timed out waiting for {what}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", action="store_true", help="open the program window too")
    args = ap.parse_args()

    exe = program()
    assert exe.is_file(), f"no program at {exe}"
    home = Path(tempfile.mkdtemp(prefix="characterization-smoke-"))
    env = dict(os.environ, CHARACTERIZATION_HOME=str(home), CHARACTERIZATION_PORT=str(PORT))
    cmd = [str(exe)] if args.window else [str(exe), "--server-only"]
    print("starting", " ".join(cmd), flush=True)
    proc = subprocess.Popen(cmd, env=env)
    log = home / "app.log"
    try:
        wait_for(lambda: call("GET", "/version") is not None, 180, "the server")
        print("version:", call("GET", "/version")["version"])

        if args.window:
            wait_for(lambda: "app.js" in log.read_text(encoding="utf-8", errors="replace"),
                     120, "the window to load the UI")
            text = log.read_text(encoding="utf-8", errors="replace")
            assert "No program window" not in text, "window fell back to the browser"
            print("window loaded the UI")

        project = call("POST", "/projects", {"name": "Smoke test"})
        mol = call("POST", "/molecules", {"project_id": project["id"], "name": "Aspirin",
                                          "smiles": "CC(=O)Oc1ccccc1C(=O)O"})
        assert mol["formula"] == "C9H8O4", mol
        print("RDKit:", mol["formula"], mol["exact_mass"])

        call("POST", "/shutdown")
        proc.wait(timeout=60)
        assert not (home / "data" / "in-use.lock").exists(), "data folder still locked"
        backups = list((home / "backups").glob("*.zip"))
        assert backups, "no backup written on quit"
        print("quit cleanly, backup:", backups[0].name)
        print("SMOKE TEST PASSED")
    except BaseException:
        if log.exists():
            print("----- app.log -----")
            print(log.read_text(encoding="utf-8", errors="replace"))
        raise
    finally:
        if proc.poll() is None:
            proc.kill()


if __name__ == "__main__":
    main()
