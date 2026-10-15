"""Update-Logik (app/updater.py) ohne Netz: GitHub-Antworten werden
nachgestellt. Den echten Ablauf (Download, Austausch, Neustart) prüft
tools/update_test.py am gebauten Programm."""
import hashlib
import io
import shutil
import subprocess
import sys
import urllib.error
import zipfile

import pytest

from app import config, updater


@pytest.fixture(autouse=True)
def fresh_state(monkeypatch, tmp_path):
    monkeypatch.setattr(updater, "_state", {"status": "idle"})
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "config.json")
    monkeypatch.delenv("CHARACTERIZATION_FAKE_VERSION", raising=False)


class FakeResponse(io.BytesIO):
    def __init__(self, url: str, body: bytes = b""):
        super().__init__(body)
        self.url = url
        self.headers = {"Content-Length": str(len(body))}

    def geturl(self):
        return self.url

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def fake_github(monkeypatch, latest_tag: str, missing: tuple = ()):
    calls = []

    def _open(url, method="GET"):
        calls.append((method, url))
        if any(m in url for m in missing):
            raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
        if url.endswith("/releases/latest"):
            return FakeResponse(f"{updater.SITE}/releases/tag/{latest_tag}")
        return FakeResponse(url)

    monkeypatch.setattr(updater, "_open", _open)
    return calls


@pytest.fixture()
def packaged(monkeypatch, tmp_path):
    """So tun, als liefe das gepackte Programm in Version 1.2.0."""
    monkeypatch.setattr(updater, "install_target", lambda: tmp_path / "Characterization")
    monkeypatch.setenv("CHARACTERIZATION_FAKE_VERSION", "1.2.0")


def test_parse():
    assert updater.parse("1.10.2") == (1, 10, 2)
    assert updater.parse("v2.0.0") == (2, 0, 0)
    assert updater.parse("0.0.0-local") is None
    assert updater.parse("dev-2026-10-15") is None
    assert updater.parse("1.10.0") > updater.parse("1.9.9")


def test_not_offered_when_running_from_source():
    st = updater.check()
    assert st["status"] == "none" and st["supported"] is False


def test_newer_release_is_offered_once(monkeypatch, packaged):
    calls = fake_github(monkeypatch, "v1.4.0")
    st = updater.check()
    assert st["status"] == "available"
    assert st["latest"] == "1.4.0" and st["current"] == "1.2.0"
    assert st["url"].endswith(f"/releases/download/v1.4.0/{updater.asset_name('1.4.0')}")
    assert ("HEAD", st["url"]) in calls
    updater.check()                     # zweiter Aufruf: kein neuer Netzzugriff
    assert len(calls) == 2


def test_same_or_older_release_is_not_offered(monkeypatch, packaged):
    fake_github(monkeypatch, "v1.2.0")
    assert updater.check()["status"] == "none"


def test_release_without_download_for_this_system(monkeypatch, packaged):
    fake_github(monkeypatch, "v1.4.0", missing=(updater.asset_name("1.4.0"),))
    assert updater.check()["status"] == "none"


def test_switched_off_in_config(monkeypatch, packaged):
    config.save({"update_check": False})
    calls = fake_github(monkeypatch, "v9.0.0")
    assert updater.check()["status"] == "none"
    assert calls == []


def test_offline_means_no_update(monkeypatch, packaged):
    def offline(url, method="GET"):
        raise urllib.error.URLError("no network")

    monkeypatch.setattr(updater, "_open", offline)
    assert updater.check()["status"] == "none"


def test_checksum(monkeypatch, tmp_path):
    archive = tmp_path / "Characterization-1.4.0-windows.zip"
    archive.write_bytes(b"program")
    good = hashlib.sha256(b"program").hexdigest()

    def sums(text):
        monkeypatch.setattr(updater, "_open",
                            lambda url, method="GET": FakeResponse(url, text.encode()))

    sums(f"{good}  {archive.name}\n")
    updater._verify("v1.4.0", archive)  # passt
    sums(f"{'0' * 64}  {archive.name}\n")
    with pytest.raises(OSError, match="checksum"):
        updater._verify("v1.4.0", archive)
    fake_github(monkeypatch, "v1.4.0", missing=("SHA256SUMS.txt",))
    updater._verify("v1.4.0", archive)  # ältere Releases ohne Liste: kein Fehler


@pytest.mark.skipif(updater.asset_name("1.0.0") is None
                    or not updater.asset_name("1.0.0").endswith("windows.zip"),
                    reason="Windows-Archiv")
def test_unpack_puts_new_version_next_to_old(tmp_path):
    target = tmp_path / "Characterization"
    target.mkdir()
    archive = tmp_path / "update.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("Characterization/Characterization.exe", b"exe")
        zf.writestr("Characterization/_internal/VERSION", b"1.4.0\n")
        zf.writestr("Characterization/../evil.txt", b"no")
    new = updater._unpack(archive, target)
    assert new == tmp_path / "Characterization.new"
    assert (new / "Characterization.exe").read_bytes() == b"exe"
    assert (new / "_internal" / "VERSION").read_text() == "1.4.0\n"
    assert not (tmp_path / "evil.txt").exists()


def dead_pid() -> int:
    """PID eines schon beendeten Prozesses — die App ist „schon zu"."""
    proc = subprocess.Popen([sys.executable, "-c", "pass"])
    proc.wait()
    return proc.pid


def old_and_new(tmp_path, target_name, new_rel):
    target = tmp_path / target_name
    target.mkdir()
    (target / "marker").write_text("old")
    new = tmp_path / new_rel
    new.mkdir(parents=True)
    (new / "marker").write_text("new")
    return target, new


@pytest.mark.skipif(sys.platform == "win32", reason="Shell-Skript (macOS)")
@pytest.mark.parametrize("args", [[], ["--server-only"]])
def test_mac_helper_swaps_the_app(tmp_path, args, monkeypatch):
    target, new = old_and_new(tmp_path, "Characterization.app",
                              ".Characterization-update/Characterization/Characterization.app")
    log = tmp_path / "update.log"
    script = tmp_path / "update.sh"
    script.write_text(updater._sh_script(dead_pid(), target, new, log, args), encoding="utf-8")
    assert subprocess.run(["sh", "-n", str(script)]).returncode == 0  # Syntax
    # "open" würde eine echte App starten wollen — hier ein harmloser Ersatz
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    (fake_bin / "open").write_text("#!/bin/sh\nexit 0\n")
    (fake_bin / "open").chmod(0o755)
    monkeypatch.setenv("PATH", f"{fake_bin}:{__import__('os').environ['PATH']}")
    subprocess.run(["sh", str(script)], check=True, timeout=60)
    assert (target / "marker").read_text() == "new"
    assert not (tmp_path / "Characterization.app.old").exists()
    assert not (tmp_path / ".Characterization-update").exists()
    assert "updated" in log.read_text()


@pytest.mark.skipif(sys.platform != "win32", reason="PowerShell-Skript (Windows)")
def test_windows_helper_swaps_the_folder(tmp_path):
    target, new = old_and_new(tmp_path, "Characterization", "Characterization.new")
    log = tmp_path / "update.log"
    script = tmp_path / "update.ps1"
    script.write_text(updater._ps_script(dead_pid(), target, new, log, ["--server-only"]),
                      encoding="utf-8-sig")
    # Ohne Characterization.exe im Ordner scheitert nur der Neustart am Ende
    subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                    "-File", str(script)], timeout=120, capture_output=True)
    assert (target / "marker").read_text() == "new"
    assert not (tmp_path / "Characterization.old").exists()
    assert not new.exists()
    assert "updated" in log.read_text(encoding="utf-8")
