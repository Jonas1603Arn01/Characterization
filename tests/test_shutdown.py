"""Beenden-Knopf: sichert, gibt die Sperre frei und fährt die App herunter —
anders als das Schließen des schwarzen Fensters, das den Prozess sofort
beendet (ohne Beenden-Backup, fremde PCs bleiben bis zu fünf Minuten im
Lesemodus)."""
import json
import signal
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app import api, db
from app.main import app


@pytest.fixture()
def heruntergefahren(monkeypatch):
    """Tests fahren nie den Testprozess herunter — nur mitschreiben."""
    aufrufe = []
    monkeypatch.setattr(api, "request_shutdown", lambda: aufrufe.append(True))
    return aufrufe


@pytest.fixture()
def client(tmp_path):
    db.init_db(tmp_path / "test.db")
    with TestClient(app) as c:
        yield c


def test_beenden_sichert_und_faehrt_danach_herunter(client, heruntergefahren):
    client.post("/api/projects", json={"name": "P"})
    r = client.post("/api/shutdown")
    assert r.status_code == 200
    assert r.json()["backup"] in [b["name"] for b in db.list_backups()]
    assert heruntergefahren == [True]
    # Das Beenden-Backup im Lifespan hat danach nichts mehr zu tun
    assert db.create_backup(only_if_changed=True) is None


def test_beenden_ohne_aenderung_legt_kein_weiteres_backup_an(client, heruntergefahren):
    client.post("/api/projects", json={"name": "P"})
    client.post("/api/shutdown")
    anzahl = len(db.list_backups())

    r = client.post("/api/shutdown")
    assert r.json() == {"backup": None, "read_only": False}
    assert len(db.list_backups()) == anzahl


def test_beenden_geht_auch_im_lesemodus(tmp_path, heruntergefahren):
    db.init_db(tmp_path / "test.db")
    db.close_db()
    jetzt = datetime.now().isoformat(timespec="seconds")
    (tmp_path / db.LOCK_FILE).write_text(json.dumps(
        {"computer": "ANDERER-PC", "user": "y", "pid": 1, "since": jetzt, "heartbeat": jetzt}))
    db.init_db(tmp_path / "test.db")
    assert db.is_read_only()

    with TestClient(app) as c:
        r = c.post("/api/shutdown")
    assert r.status_code == 200  # nicht 423 — Beenden ändert den Datenordner nicht
    assert r.json() == {"backup": None, "read_only": True}
    assert heruntergefahren == [True]
    assert (tmp_path / db.LOCK_FILE).exists()  # die fremde Sperre bleibt stehen


def test_herunterfahren_nutzt_sigterm_des_servers(monkeypatch):
    gesendet = []
    monkeypatch.setattr(signal, "getsignal", lambda sig: (lambda *args: None))
    monkeypatch.setattr(signal, "raise_signal", gesendet.append)
    api.request_shutdown()
    assert gesendet == [signal.SIGTERM]
