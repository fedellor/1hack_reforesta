"""Tests for Daily 07:00 AM Schedule, Specific PDF Links, Anti-Noise & Reforesta Statutory Profile."""
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi.testclient import TestClient
from app.domain.reforesta_profile import get_reforesta_profile, match_statute_alignment
from app.ingestors.live_connectors import _extract_bdns_specific_pdf_url, _is_specific_document_url
from app.ingestors.runner import seconds_until_next_daily_sync
from app.main import app
from app.pipeline.layer1_regex import evaluate_layer1


def test_daily_07_00_am_scheduler_calculation():
    """Verify automatic sync scheduler targets exactly 07:00 AM Europe/Madrid."""
    tz = ZoneInfo("Europe/Madrid")
    # Before 07:00 -> triggers same day at 07:00
    before = datetime(2026, 11, 14, 6, 30, 0, tzinfo=tz)
    wait_s, nxt = seconds_until_next_daily_sync(now=before, hour=7, minute=0, tz_name="Europe/Madrid")
    assert nxt.hour == 7 and nxt.minute == 0 and nxt.day == 14
    assert int(wait_s) == 1800

    # After 07:00 -> triggers tomorrow at 07:00
    after = datetime(2026, 11, 14, 8, 15, 0, tzinfo=tz)
    wait_s2, nxt2 = seconds_until_next_daily_sync(now=after, hour=7, minute=0, tz_name="Europe/Madrid")
    assert nxt2.hour == 7 and nxt2.minute == 0 and nxt2.day == 15
    assert int(wait_s2) == (22 * 3600 + 45 * 60)


def test_bdns_specific_document_pdf_extraction_and_generic_url_rejection():
    """Ensure BDNS PDF documents (`idDocumento`) are preferred and generic portals are rejected."""
    assert _is_specific_document_url("http://www.navarra.es") is False
    assert _is_specific_document_url("https://doe.juntaex.es/") is False
    assert _is_specific_document_url("https://fundacion-biodiversidad.es/") is False
    assert _is_specific_document_url("https://www.boe.es/boe/dias/2026/11/07/pdfs/BOE-A-2026-23372.pdf") is True
    assert _is_specific_document_url("https://www.infosubvenciones.es/bdnstrans/api/convocatorias/documentos?idDocumento=1519060") is True

    det = {
        "documentos": [
            {"id": 1521001, "nombreFic": "anexo_solicitud.docx", "descripcion": "Anexo Word"},
            {"id": 1521002, "nombreFic": "Convocatoria_Reforestacion_2026.pdf", "descripcion": "Resolución convocatoria"},
        ]
    }
    pdf_url = _extract_bdns_specific_pdf_url(det)
    assert pdf_url == "https://www.infosubvenciones.es/bdnstrans/api/convocatorias/documentos?idDocumento=1521002"


def test_reforesta_statutory_profile_endpoint_and_local_pdf_serving():
    """Verify /api/v1/reforesta/profile, /api/v1/fuentes/*.pdf, and statute citations in /api/convocatorias."""
    profile = get_reforesta_profile()
    assert profile["nif"] == "G80428204"
    assert profile["utilidad_publica"] is True
    assert len(profile["fines_estatutarios"]) == 11

    align = match_statute_alignment(
        titulo="Ayudas para reforestación contra la desertificación",
        texto="Actuaciones de educación ambiental en Madrid",
        ccaa_codigo="ES-MD",
    )
    assert any("Fin 2" in f for f in align["fines_alineados"])
    assert "Madrid" in (align["presencia_territorial_previa"] or "")

    with TestClient(app) as client:
        p_resp = client.get("/api/v1/reforesta/profile")
        assert p_resp.status_code == 200
        assert p_resp.json()["nif"] == "G80428204"

        pdf_resp = client.get("/api/v1/fuentes/comunidad-madrid-orden-1689-2026.pdf")
        assert pdf_resp.status_code == 200
        assert "application/pdf" in pdf_resp.headers["content-type"]
        assert pdf_resp.content.startswith(b"%PDF")

        health = client.get("/api/v1/health").json()
        assert health["daily_sync_schedule"] == "07:00 Europe/Madrid"
        assert "next_daily_sync_at" in health

        conv_resp = client.get("/api/convocatorias").json()
        madrid_call = next(c for c in conv_resp["convocatorias"] if c["id"] == "bocm-orden-1689-2026")
        assert "/api/v1/fuentes/comunidad-madrid-orden-1689-2026.pdf" in madrid_call["urlBasesPdf"]
        assert any("[Estatutos Reforesta]" in cit for cit in madrid_call["citasBasesJustificacion"])


def test_strict_noise_and_livestock_exclusion():
    """Reject livestock repopulation, cultural art/sports grants, and direct nominative awards."""
    for bad_title in (
        "Ayudas 2026 a la repoblación en explotaciones de ganado bovino, ovino y caprino",
        "EL PRADO EN LAS CALLES en la Región de Murcia",
        "La Fundación Iberdrola abre convocatoria para deportistas con discapacidad",
        "2026-Subv.nom.Agrupació Defensa Forestal El Pinyó",
    ):
        res = evaluate_layer1(titulo=bad_title, texto=bad_title, organo="Organismo")
        assert res.passed is False, f"Expected false positive rejected: {bad_title}"


def test_production_mode_excludes_synthetic_catalog_templates(tmp_path, monkeypatch):
    """Verify ensure_initial_seed loads zero synthetic catalog calls when include_catalog_templates=False."""
    from sqlmodel import Session, SQLModel, create_engine, select
    from app.config import settings
    from app.ingestors.runner import ensure_initial_seed
    from app.models import Opportunity

    db_file = tmp_path / "prod_only_test.db"
    test_engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(test_engine)

    monkeypatch.setattr(settings, "include_catalog_templates", False)
    with Session(test_engine) as session:
        ensure_initial_seed(session)
        rows = session.exec(select(Opportunity)).all()
        ids = {r.id for r in rows}
        assert ids == {"bdns-923290", "bocm-orden-1689-2026"}

