"""End-to-End Tests for Layer 2 Judge, Prioritizer, Deduplication, Live Sync & Full REST API Contracts."""
from datetime import date, timedelta
import httpx
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from app.config import settings
from app.database import engine, query_cache
from app.ingestors import runner
from app.ingestors.runner import refresh_live_database_states
from app.main import app
from app.models import Opportunity
from app.pipeline import layer2_judge
from app.pipeline.layer1_regex import evaluate_layer1
from app.pipeline.layer2_judge import _extract_json_object, evaluate_layer2
from app.pipeline.orchestrator import RawCandidate, process_candidate
from app.pipeline.prioritizer import calculate_priority


def test_layer2_json_fence_parser_and_deterministic_extractors(monkeypatch):
    # 1. Markdown-wrapped JSON extraction from LLM providers
    fenced = 'Aquí tienes:\n```json\n{"es_relevante": true, "relevancia_tipo": "DIRECTA"}\n```'
    parsed = _extract_json_object(fenced)
    assert parsed["es_relevante"] is True

    # 2. Deterministic fallback parses budget, % and deadline when hints omitted
    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "groq_api_key", "")
    monkeypatch.setattr(settings, "openrouter_api_key", "")
    monkeypatch.setattr(settings, "enable_public_llm_fallback", False)

    titulo = "Subvenciones para reforestación autóctona y restauración de bosques quemados"
    organo = "Xunta de Galicia"
    texto = (
        "Convocatoria dotada con 950.000,00 euros destinada a entidades sin ánimo de lucro "
        "con financiación hasta el 95%. Plazo de solicitud: 20 días hábiles."
    )
    l1 = evaluate_layer1(titulo=titulo, organo=organo, texto=texto)
    verdict = evaluate_layer2(titulo=titulo, organo=organo, texto=texto, layer1_result=l1)
    assert verdict.es_relevante is True
    assert verdict.presupuesto_total_detectado == 950000.0
    assert verdict.porcentaje_max_financiacion_detectado == 95.0
    assert "20 días hábiles" in (verdict.plazo_solicitud_detectado or "")
    assert "ONG_FUNDACIONES" in verdict.beneficiarios_tipos

    # 3. Verify hash cache hit on second identical call
    verdict_cached = evaluate_layer2(titulo=titulo, organo=organo, texto=texto, layer1_result=l1)
    assert verdict_cached.titulo_limpio_es == verdict.titulo_limpio_es


def test_layer2_fallback_on_cloud_error(monkeypatch):
    """If an OpenAI-compatible key fails with HTTP 500, Judge MUST gracefully fall back to Deterministic Expert."""
    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "groq_api_key", "fake-groq-key")

    class FailingClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def post(self, *args, **kwargs):
            return httpx.Response(500, json={"error": "rate_limit"})

    monkeypatch.setattr(layer2_judge.httpx, "Client", FailingClient)

    l1 = evaluate_layer1("Ayudas prevención incendios forestales", organo="MITECO")
    verdict = evaluate_layer2(
        titulo="Ayudas prevención incendios forestales (test fallback)",
        organo="MITECO",
        texto="Silvicultura preventiva para asociaciones y ayuntamientos.",
        layer1_result=l1,
    )
    assert verdict.es_relevante is True
    assert verdict.metodo_evaluacion == "HYBRID_HEURISTIC"


def test_prioritizer_tiers_and_closed_cap():
    # Ideal ONG grant: DIRECTA 95 + ONG + 100% funded + 500k + 12 days remaining -> CRITICA (>=88)
    crit = calculate_priority(
        estado="ACTIVA",
        dias_restantes=12,
        relevancia_tipo="DIRECTA",
        relevancia_score=95,
        beneficiarios_tipos=["ONG_FUNDACIONES"],
        porcentaje_financiacion=100.0,
        presupuesto_total=500000.0,
        importe_max_proyecto=120000.0,
        nivel_territorial="CCAA",
    )
    assert crit.prioridad_score >= 90
    assert crit.prioridad_nivel == "CRITICA"
    assert crit.urgencia_label == "VENTANA_OPTIMA"

    # Closed grant MUST be HISTORICO and capped <= 50
    hist = calculate_priority(
        estado="CERRADA",
        dias_restantes=0,
        relevancia_tipo="DIRECTA",
        relevancia_score=98,
        beneficiarios_tipos=["ONG_FUNDACIONES"],
        porcentaje_financiacion=100.0,
        presupuesto_total=1000000.0,
        importe_max_proyecto=200000.0,
        nivel_territorial="ESTADO",
    )
    assert hist.prioridad_nivel == "HISTORICO"
    assert hist.prioridad_score <= 50


def test_cross_source_deduplication_and_state_refresh(monkeypatch):
    """Verify BDNS & BOCM records sharing 'Orden 1689/2026' merge cleanly without duplicates."""
    with TestClient(app):
        with Session(engine) as session:
            before_count = len(session.exec(select(Opportunity)).all())
            dup_cand = RawCandidate(
                id="bdns-dup-test-1689",
                codigo_oficial="BDNS-998877",
                fuente="BDNS",
                tipo_oportunidad="SUBVENCION",
                titulo="Extracto de la Orden 1689/2026 de subvenciones a entidades sin ánimo de lucro",
                organo_convocante="Comunidad de Madrid",
                texto="Red Natura 2000 y conservación ambiental en la Comunidad de Madrid.",
                anio_convocatoria=2026,
                url_ficha_oficial="https://www.infosubvenciones.es/",
            )
            res = process_candidate(dup_cand, session=session, persist=True)
            assert res.accepted_layer2 is True

            after_count = len(session.exec(select(Opportunity)).all())
            assert after_count == before_count  # Merged into existing bocm-orden-1689-2026!

            # Verify refresh_live_database_states advances expired call to CERRADA
            test_opp = session.get(Opportunity, "eu-life-2026-sap-nat-forest")
            assert test_opp is not None
            orig_estado = test_opp.estado
            monkeypatch.setattr(settings, "reference_date", date(2028, 1, 1))
            updated_rows = refresh_live_database_states(session)
            assert updated_rows >= 1
            session.refresh(test_opp)
            assert test_opp.estado == "CERRADA"
            assert test_opp.prioridad_nivel == "HISTORICO"

            # Restore today's date cleanly
            monkeypatch.setattr(settings, "reference_date", None)
            refresh_live_database_states(session)
            session.refresh(test_opp)
            assert test_opp.estado == orig_estado


def test_api_all_filters_sorting_pagination_and_errors():
    with TestClient(app) as client:
        # 1. Health & Cache check
        health = client.get("/api/v1/health").json()
        assert health["status"] == "ok"
        assert health["golden_benchmark"]["passed"] is True

        # 2. All sort options on /api/v1/opportunities
        for sort_opt in ("prioridad_score", "relevancia_score", "dias_restantes", "presupuesto_total", "fecha_publicacion"):
            r = client.get(f"/api/v1/opportunities?estado=TODAS&sort_by={sort_opt}&page=1&limit=10")
            assert r.status_code == 200
            body = r.json()
            assert body["limit"] == 10
            assert len(body["items"]) <= 10

        # 3. Payment modality & anticipo_sin_aval filter (must catch Madrid Orden 1689/2026)
        anticipo_resp = client.get("/api/v1/opportunities?solo_anticipo_sin_aval=true").json()
        assert anticipo_resp["total"] >= 1
        assert any(i["id"] == "bocm-orden-1689-2026" for i in anticipo_resp["items"])

        # 4. Text search + EU co-financed filter
        search_resp = client.get("/api/v1/opportunities?q=Natura&cofinanciado_ue=true").json()
        assert search_resp["total"] >= 1

        # 5. Lookup by codigo_oficial + 404 on unknown
        by_code = client.get("/api/v1/opportunities/BDNS-923290")
        assert by_code.status_code == 200
        assert by_code.json()["id"] == "bdns-923290"
        assert client.get("/api/v1/opportunities/NO-EXISTE-999").status_code == 404

        # 6. PATCH state validation: 400 invalid state, 404 missing ID, restore valid state
        bad_state = client.patch("/api/convocatorias/bdns-923290/estado", json={"estadoInterno": "inventado"})
        assert bad_state.status_code == 400
        missing_id = client.patch("/api/convocatorias/no-existe/estado", json={"estadoInterno": "priorizada"})
        assert missing_id.status_code == 404
        ok_state = client.patch("/api/convocatorias/bocm-orden-1689-2026/estado", json={"estadoInterno": "priorizada"})
        assert ok_state.status_code == 200

        # 7. Predictive calendar CCAA filter & CSV CCAA export
        cal_md = client.get("/api/v1/opportunities/predictive-calendar?ccaa=ES-MD").json()
        prog_ids = {p["programa_id"] for p in cal_md["programas_recurrentes"]}
        assert "REC-CAM-ORDEN-ESAL" in prog_ids
        assert "REC-XUNTA-MONTES-INCENDIOS" not in prog_ids

        csv_md = client.get("/api/v1/export/csv?ccaa=ES-MD&incluir_nacionales_ue=false")
        assert csv_md.status_code == 200
        assert "ORDEN 1689/2026" in csv_md.content.decode("utf-8")

        assert client.get("/api/v1/export/markdown/NO-EXISTE").status_code == 404
        assert query_cache.version >= 1


def test_trigger_ingestion_endpoint_with_mocked_live_apis(monkeypatch):
    """End-to-end verification of POST /api/v1/ingest/trigger persisting a mocked live BDNS call."""
    async def fake_bdns(**kwargs):
        return [
            RawCandidate(
                id="bdns-999123-live-test",
                codigo_oficial="BDNS-999123",
                fuente="BDNS",
                tipo_oportunidad="SUBVENCION",
                titulo="Subvención urgente en vivo para reforestación post-incendio en León",
                organo_convocante="Diputación Provincial de León",
                texto="Restauración de montes quemados con especies autóctonas para asociaciones y juntas vecinales.",
                presupuesto_total=450000.0,
                porcentaje_financiacion=100.0,
                fecha_publicacion=date.today(),
                fecha_fin_solicitud=date.today() + timedelta(days=18),
                url_ficha_oficial="https://www.infosubvenciones.es/",
            )
        ]

    async def empty_async(*args, **kwargs):
        return []

    async def zero_enrich(*args, **kwargs):
        return 0

    monkeypatch.setattr(runner, "fetch_live_bdns_candidates", fake_bdns)
    monkeypatch.setattr(runner, "fetch_live_placsp_candidates", empty_async)
    monkeypatch.setattr(runner, "fetch_live_boe_candidates", empty_async)
    monkeypatch.setattr(runner, "fetch_live_eu_sedia_candidates", empty_async)
    monkeypatch.setattr(runner, "fetch_live_ccaa_rss_candidates", empty_async)
    monkeypatch.setattr(runner, "fetch_live_private_foundation_candidates", empty_async)
    monkeypatch.setattr(runner, "enrich_candidates_with_linked_pdfs", zero_enrich)

    with TestClient(app) as client:
        resp = client.post("/api/v1/ingest/trigger?include_live_apis=true")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "COMPLETED"
        assert body["details"]["live_api_fetched"]["bdns_live"] == 1

        # Verify mocked live record landed cleanly in DB and resolved ES-LE / ES-CL
        live_rec = client.get("/api/v1/opportunities/bdns-999123-live-test")
        assert live_rec.status_code == 200
        data = live_rec.json()
        assert data["ambito_geografico"]["ccaa_codigo"] == "ES-CL"
        assert data["ambito_geografico"]["provincia_codigo"] == "ES-LE"
        assert data["estado"] == "ACTIVA"

        # Clean up test row so production seed DB remains clean
        with Session(engine) as session:
            row = session.get(Opportunity, "bdns-999123-live-test")
            if row:
                session.delete(row)
                session.commit()
