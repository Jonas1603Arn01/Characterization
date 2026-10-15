"""Formatierbare Molekülfelder (Name, Zitat, Probenvermerk): das Frontend
schickt HTML — etwa aus Word eingefügt —, der Server bereinigt es wie bei
den Notizen und leitet den Klartext ab. Der Klartext bleibt maßgeblich für
Ordnernamen, Info.txt, Suche und die Namensgleichheit im Projekt.
"""
import pytest
from fastapi.testclient import TestClient

from app import db, richtext
from app.main import app


# ---------- richtext.field ----------

def test_field_liefert_klartext_und_html():
    assert richtext.field("CDCl<sub>3</sub> in Zeile 1<br>Zeile 2") == (
        "CDCl₃ in Zeile 1\nZeile 2", "CDCl<sub>3</sub> in Zeile 1<br>Zeile 2")
    assert richtext.field("nur Text") == ("nur Text", None)
    assert richtext.field("<b> </b><br>") == (None, None)
    assert richtext.field(None) == (None, None)


def test_field_einzeilig_macht_umbrueche_zu_leerzeichen():
    assert richtext.field("<i>N</i>-Methyl<br>anilin", single_line=True) == (
        "N-Methyl anilin", "<i>N</i>-Methyl anilin")


def test_minuszeichen_und_halbgeviertstrich_werden_hochgestellt():
    assert richtext.to_text("cm<sup>−1</sup>, cm<sup>–1</sup>") == "cm⁻¹, cm⁻¹"
    assert richtext.to_text("X<sub>−1</sub>") == "X₋₁"


# ---------- API ----------

@pytest.fixture()
def client(tmp_path):
    db.init_db(tmp_path / "test.db")
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def project(client):
    return client.post("/api/projects", json={"name": "P"}).json()


def _create(client, project, **fields):
    return client.post("/api/molecules", json={"project_id": project["id"], **fields})


def test_anlegen_mit_formatiertem_namen(client, project):
    r = _create(client, project, name_html="<i>N</i>-Boc-Ph<sub>3</sub>P<script>x</script>")
    assert r.status_code == 201, r.text
    mol = r.json()
    assert mol["name_html"] == "<i>N</i>-Boc-Ph<sub>3</sub>P"
    assert mol["name"] == "N-Boc-Ph₃P"
    # auch in der Projektliste (Karten)
    listed = client.get("/api/projects").json()[0]["molecules"][0]
    assert listed["name_html"] == "<i>N</i>-Boc-Ph<sub>3</sub>P"


def test_ungeformter_name_bleibt_reiner_text(client, project):
    assert _create(client, project, name_html="M-1").json()["name_html"] is None
    mol = _create(client, project, name="M-2").json()  # alter Aufruf ohne HTML
    assert mol["name"] == "M-2" and mol["name_html"] is None


def test_formatierung_allein_macht_keinen_neuen_namen(client, project):
    assert _create(client, project, name="N-Boc").status_code == 201
    assert _create(client, project, name_html="<i>N</i>-Boc").status_code == 409


def test_leerer_formatierter_name_wird_abgewiesen(client, project):
    assert _create(client, project, name_html="<b> </b><br>").status_code == 422


def test_umbenennen_mit_formatierung_und_zurueck(client, project):
    mol = _create(client, project, name="M-1").json()
    r = client.patch(f"/api/molecules/{mol['id']}",
                     json={"name_html": "<i>tert</i>-Butyl<br>ester"}).json()
    assert r["name"] == "tert-Butyl ester"
    assert r["name_html"] == "<i>tert</i>-Butyl ester"

    # nur die Formatierung ändern ist kein Namenskonflikt mit sich selbst
    r = client.patch(f"/api/molecules/{mol['id']}", json={"name_html": "tert-Butyl ester"})
    assert r.status_code == 200, r.text
    assert r.json()["name_html"] is None

    client.patch(f"/api/molecules/{mol['id']}", json={"name_html": "<b>X</b>"})
    r = client.patch(f"/api/molecules/{mol['id']}", json={"name": "Y"}).json()
    assert r["name"] == "Y" and r["name_html"] is None


def test_zitat_und_probenvermerk_formatiert(client, project):
    mol = _create(client, project, name="M-1").json()
    r = client.patch(f"/api/molecules/{mol['id']}", json={
        "citation_html": "<i>J. Am. Chem. Soc.</i> <b>2020</b>, <i>142</i>, 1.",
        "sample_comment_html": "in CH<sub>2</sub>Cl<sub>2</sub><br>bei −20 °C",
    }).json()
    assert r["citation"] == "J. Am. Chem. Soc. 2020, 142, 1."
    assert r["citation_html"] == "<i>J. Am. Chem. Soc.</i> <b>2020</b>, <i>142</i>, 1."
    assert r["sample_comment"] == "in CH₂Cl₂\nbei −20 °C"
    assert r["sample_comment_html"] == "in CH<sub>2</sub>Cl<sub>2</sub><br>bei −20 °C"

    # leer entfernt beides; reiner Text setzt die Formatierung zurück
    r = client.patch(f"/api/molecules/{mol['id']}",
                     json={"citation_html": "", "sample_comment": "nur Text"}).json()
    assert r["citation"] is None and r["citation_html"] is None
    assert r["sample_comment"] == "nur Text" and r["sample_comment_html"] is None


def test_export_nutzt_den_klartext(client, project, tmp_path):
    mol = _create(client, project, name_html="Ph<sub>3</sub>P").json()
    client.patch(f"/api/molecules/{mol['id']}",
                 json={"literature_known": True, "citation_html": "<i>Org. Lett.</i> 2021"})
    target = tmp_path / "export"
    target.mkdir()
    r = client.post(f"/api/molecules/{mol['id']}/export", json={"target_dir": str(target)})
    assert r.status_code == 200, r.text
    info = (target / "P" / "Ph₃P" / "Info.txt").read_text(encoding="utf-8")
    assert "Ph₃P" in info and "Org. Lett. 2021" in info
    assert "<i>" not in info and "<sub>" not in info
