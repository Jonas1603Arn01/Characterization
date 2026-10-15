"""Tests für die Restsubstanz-Markierung (Substanz übrig + Probennummer + Vermerk)."""
import pytest
from fastapi.testclient import TestClient

from app import db
from app.main import app


@pytest.fixture()
def client(tmp_path):
    db.init_db(tmp_path / "test.db")
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def mol(client):
    pid = client.post("/api/projects", json={"name": "P"}).json()["id"]
    return client.post("/api/molecules", json={"project_id": pid, "name": "M-1"}).json()


def test_defaults(mol):
    assert mol["sample_available"] is False
    assert mol["sample_number"] is None
    assert mol["sample_comment"] is None


def test_set_sample_fields(client, mol):
    r = client.patch(f"/api/molecules/{mol['id']}", json={
        "sample_available": True,
        "sample_number": "JA-042-F2",
        "sample_comment": "nicht sauber genug",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["sample_available"] is True
    assert data["sample_number"] == "JA-042-F2"
    assert data["sample_comment"] == "nicht sauber genug"


def test_empty_string_clears_fields(client, mol):
    client.patch(f"/api/molecules/{mol['id']}", json={
        "sample_available": True, "sample_number": "X", "sample_comment": "Y",
    })
    data = client.patch(f"/api/molecules/{mol['id']}", json={
        "sample_number": "", "sample_comment": "  ",
    }).json()
    assert data["sample_number"] is None
    assert data["sample_comment"] is None
    # Haken bleibt unangetastet, wenn er nicht im Patch steht
    assert data["sample_available"] is True


def test_unrelated_patch_keeps_sample_fields(client, mol):
    client.patch(f"/api/molecules/{mol['id']}", json={
        "sample_available": True, "sample_number": "JA-1",
    })
    data = client.patch(f"/api/molecules/{mol['id']}", json={"color": "gelb"}).json()
    assert data["sample_available"] is True
    assert data["sample_number"] == "JA-1"


def test_export_info_mentions_sample(client, mol, tmp_path):
    client.patch(f"/api/molecules/{mol['id']}", json={
        "sample_available": True,
        "sample_number": "JA-042-F2",
        "sample_comment": "nicht sauber genug",
    })
    target = tmp_path / "export"
    target.mkdir()
    r = client.post(f"/api/molecules/{mol['id']}/export",
                    json={"target_dir": str(target)})
    assert r.status_code == 200
    info = (target / "P" / "M-1" / "Info.txt").read_text(encoding="utf-8")
    assert "JA-042-F2" in info
    assert "nicht sauber genug" in info
