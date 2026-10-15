"""End-to-end test of the self-update, on the system it runs on.

    python tools/update_test.py

Copies the built program (dist/) to a temporary install location, starts it
with throwaway data and a faked old version (0.0.1), and lets it update
itself to the newest release on GitHub — the real download, checksum,
swap and restart. Passes when the program that answers after the restart is
that release, the install location holds it, and the data survived.
Never touches a real dataset or the real installation.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import ci_report

ROOT = Path(__file__).resolve().parent.parent
PORT = 8791
BASE = f"http://127.0.0.1:{PORT}/api"


def call(method: str, path: str, body: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read() or b"null")


def wait_for(check, seconds: float, what: str):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        try:
            result = check()
            if result:
                return result
        except OSError:
            pass
        time.sleep(0.5)
    raise AssertionError(f"timed out waiting for {what}")


def install_copy(tmp: Path) -> tuple[Path, Path]:
    """Copy of the build at a scratch install location: (target, executable)."""
    dist = ROOT / "dist"
    if sys.platform == "darwin":
        target = tmp / "Applications" / "Characterization.app"
        target.parent.mkdir()
        subprocess.run(["ditto", str(dist / "Characterization.app"), str(target)], check=True)
        return target, target / "Contents" / "MacOS" / "Characterization"
    target = tmp / "Programs" / "Characterization"
    shutil.copytree(dist / "Characterization", target)
    return target, target / "Characterization.exe"


def installed_version(target: Path) -> str:
    rels = (["Contents/Resources/VERSION", "Contents/Frameworks/VERSION"]
            if sys.platform == "darwin" else ["_internal/VERSION"])
    for rel in rels:
        if (target / rel).is_file():
            return (target / rel).read_text(encoding="utf-8").strip()
    raise AssertionError(f"no VERSION in {target}")


def main() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="characterization-update-"))
    home = tmp / "home"
    target, exe = install_copy(tmp)
    env = dict(os.environ, CHARACTERIZATION_HOME=str(home), CHARACTERIZATION_PORT=str(PORT),
               CHARACTERIZATION_FAKE_VERSION="0.0.1")
    proc = subprocess.Popen([str(exe), "--server-only"], env=env)
    try:
        wait_for(lambda: call("GET", "/version"), 180, "the old version to start")
        project = call("POST", "/projects", {"name": "Survives the update"})

        state = call("GET", "/update")
        print("update check:", state)
        assert state["status"] == "available", state
        latest = state["latest"]

        call("POST", "/update/install")
        last = None
        while proc.poll() is None:
            try:
                st = call("GET", "/update")
                if st["status"] != last:
                    print("  ", st["status"], st.get("progress", ""), st.get("error") or "")
                    last = st["status"]
                assert st["status"] != "error", st
            except OSError:
                pass
            time.sleep(0.5)
        print("old version quit")

        # the helper swaps and starts the new version (same --server-only)
        version = wait_for(lambda: call("GET", "/version")["version"], 300,
                           "the new version to answer")
        print("running after restart:", version)
        assert version == latest, (version, latest)
        assert installed_version(target) == latest
        names = [p["name"] for p in call("GET", "/projects")]
        assert project["name"] in names, names
        call("POST", "/shutdown")
        time.sleep(3)
        print((home / "update.log").read_text(encoding="utf-8"))
        print("UPDATE TEST PASSED")
    except BaseException:
        logs = {}
        for log in (home / "app.log", home / "update.log", home / "update" / "update.sh"):
            if log.exists():
                logs[log.name] = log.read_text(encoding="utf-8", errors="replace")
                print(f"----- {log.name} -----")
                print(logs[log.name])
        logs["install location"] = "\n".join(
            str(p.relative_to(tmp)) for p in sorted(tmp.glob("*/*")))
        ci_report.report("Self-update test failed", logs)
        raise
    finally:
        if proc.poll() is None:
            proc.kill()


if __name__ == "__main__":
    main()
