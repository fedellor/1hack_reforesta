"""Automated Test Suite: Golden Benchmark (fuentes/), Multilingual Hybrid Filter, Map API & Historical Archive."""
from pathlib import Path
from fastapi.testclient import TestClient
from app.config import FUENTES_DIR
from app.main import app
from app.pipeline.layer1_regex import evaluate_layer1


def test_golden_benchmark_fuentes_detected():
    """
    GOLDEN BENCHMARK: Verify that both reference PDFs in ./fuentes/
    (miteco-convocatoria-923290.pdf and comunidad-madrid-orden-1689-2026.pdf)
    are automatically ingested, pass Layer 1 & Layer 2, and have accurate structured data.
    """
    with TestClient(app) as client:
        resp = client.get("/api/v1/benchmark/verify")
        assert resp.status_code == 200
        data = resp.json()
        assert data["benchmark_passed"] is True

        miteco, madrid = data["fuentes_detectadas"]

        # 1. Verify MITECO BDNS 923290
        assert miteco is not None
        assert miteco["id"] == "bdns-923290"
        assert miteco["codigo_oficial"] == "BDNS-923290"
        assert miteco["estado"] == "ACTIVA"
        assert miteco["ambito_geografico"]["ccaa_codigo"] == "ES"
        assert miteco["economia"]["presupuesto_total"] == 17389322.52
        assert "miteco.gob.es" in (miteco["enlaces"]["url_tramitacion"] or "")
        assert "BOE-A-2023-17623" in (miteco["enlaces"]["url_bases_reguladoras"] or "")
        assert (
            "15 días hábiles tras publicación extracto BOE"
            in (miteco["fechas"]["plazo_texto_original"] or "")
        )

        # 2. Verify Comunidad de Madrid Orden 1689/2026
        assert madrid is not None
        assert madrid["id"] == "bocm-orden-1689-2026"
        assert madrid["codigo_oficial"] == "ORDEN 1689/2026"
        assert madrid["estado"] == "ACTIVA"
        assert madrid["ambito_geografico"]["ccaa_codigo"] == "ES-MD"
        assert madrid["economia"]["presupuesto_total"] == 500000.0
        assert madrid["economia"]["importe_max_beneficiario"] == 60000.0
        assert madrid["economia"]["importe_max_proyecto"] == 30000.0
        assert madrid["economia"]["porcentaje_max_financiacion"] == 100.0
        assert len(madrid["beneficiarios"]["criterios_valoracion"]) == 4
        assert "extracto" in (madrid["fechas"]["plazo_texto_original"] or "").lower()


def test_multilingual_layer1_and_anti_noise():
    """Verify Layer 1 accepts ES/CA/GL/EU/EN forestry & wildfire calls and rejects administrative noise."""
    # English EU LIFE call
    en_res = evaluate_layer1(
        titulo="Call for proposals: Forest restoration and wildfire prevention in Natura 2000",
        organo="European Commission - CINEA",
    )
    assert en_res.passed is True
    assert en_res.detected_language == "en"
    assert "reforestacion" in en_res.matched_categories
    assert "prevencion_incendios" in en_res.matched_categories

    # Galician call
    gl_res = evaluate_layer1(
        titulo="Orde pola que se convocan subvencións para a repoboación forestal e prevención de lumes forestais en montes veciñais",
        organo="Xunta de Galicia",
    )
    assert gl_res.passed is True
    assert gl_res.detected_language == "gl"

    # Catalan call
    ca_res = evaluate_layer1(
        titulo="Subvencions per a la gestió forestal sostenible i prevenció d'incendis forestals a Catalunya",
        organo="Generalitat de Catalunya",
    )
    assert ca_res.passed is True
    assert ca_res.detected_language == "ca"

    # Basque call
    eu_res = evaluate_layer1(
        titulo="Diru-laguntzak baso-berritze eta baso-suteen prebentziorako",
        organo="Bizkaiko Foru Aldundia",
    )
    assert eu_res.passed is True
    assert eu_res.detected_language == "eu"

    # Noise 1: Hospital fire extinguishers -> MUST REJECT
    noise_hosp = evaluate_layer1(
        titulo="Suministro de extintores portátiles y detección de incendios en edificio de hospital",
        organo="Consejería de Sanidad",
    )
    assert noise_hosp.passed is False
    assert noise_hosp.decision == "REJECT"

    # Noise 2: Condominium extinction -> MUST REJECT
    noise_cond = evaluate_layer1(
        titulo="Subasta por extinción de condominio y Monte de Piedad",
        organo="Juzgado de Primera Instancia",
    )
    assert noise_cond.passed is False


def test_map_summary_and_historical_2020_2026():
    """Verify that /map/summary covers all 19 territories and /stats/historical covers 2020-2026."""
    with TestClient(app) as client:
        # Map endpoint
        map_resp = client.get("/api/v1/map/summary?estado=ACTIVA&incluir_nacionales_ue=true")
        assert map_resp.status_code == 200
        map_data = map_resp.json()
        assert len(map_data["ccaa"]) == 19
        assert map_data["resumen_estatal_es"]["oportunidades"] >= 3
        assert map_data["resumen_europeo_eu"]["oportunidades"] >= 3

        # Check every CCAA has at least 1 territorial active call + global applicable calls
        for region in map_data["ccaa"]:
            assert region["oportunidades_territoriales"] >= 1
            assert region["oportunidades_totales_aplicables"] > region["oportunidades_territoriales"]

        # Historical stats endpoint (2020-2026)
        hist_resp = client.get("/api/v1/stats/historical")
        assert hist_resp.status_code == 200
        hist_data = hist_resp.json()
        years_present = {item["anio"] for item in hist_data["serie_anual"] if item["total"] > 0}
        assert {2020, 2021, 2022, 2023, 2024, 2025, 2026}.issubset(years_present)
        assert hist_data["auditoria_ultimo_filtrado"]["ruido_descartado"] >= 3


def test_opportunities_filters_and_live_analyze():
    """Test filtering by CCAA, historical year ranges, and live PDF/text evaluation endpoints."""
    with TestClient(app) as client:
        # 1. Filter by Madrid only vs Madrid + State + EU
        md_only = client.get("/api/v1/opportunities?ccaa=ES-MD&incluir_nacionales_ue=false").json()
        md_plus_global = client.get("/api/v1/opportunities?ccaa=ES-MD&incluir_nacionales_ue=true").json()
        assert md_only["total"] >= 2  # Active Orden 1689/2026 + Historical Orden 2429/2024
        assert md_plus_global["total"] > md_only["total"]

        # 2. Filter historical closed calls (2020-2024)
        hist_2020_2024 = client.get(
            "/api/v1/opportunities?estado=CERRADA&anio_desde=2020&anio_hasta=2024"
        ).json()
        assert hist_2020_2024["total"] >= 7
        for item in hist_2020_2024["items"]:
            assert item["estado"] == "CERRADA"
            assert 2020 <= item["fechas"]["anio_convocatoria"] <= 2024

        # 3. Live text analyze endpoint (Positive case)
        pos_eval = client.post(
            "/api/v1/analyze/text",
            json={
                "titulo": "Subvenciones del Ayuntamiento de Cuenca para repoblación forestal y fajas cortafuegos",
                "organo_convocante": "Ayuntamiento de Cuenca",
                "texto": "Ayudas para plantación de especies autóctonas y prevención de incendios forestales en montes municipales.",
                "presupuesto_total": 120000.0,
                "guardar_en_bd": False,
            },
        )
        assert pos_eval.status_code == 200
        pos_data = pos_eval.json()
        assert pos_data["passed_layer1"] is True
        assert pos_data["accepted_layer2"] is True
        assert pos_data["opportunity"]["ambito_geografico"]["ccaa_codigo"] == "ES-CM"
        assert pos_data["opportunity"]["ambito_geografico"]["nivel"] == "MUNICIPIO"

        # 4. Live PDF upload endpoint using real PDF from ./fuentes/
        pdf_file: Path = FUENTES_DIR / "miteco-convocatoria-923290.pdf"
        with pdf_file.open("rb") as f:
            pdf_resp = client.post(
                "/api/v1/analyze/pdf?guardar_en_bd=false",
                files={"file": ("miteco-convocatoria-923290.pdf", f, "application/pdf")},
            )
        assert pdf_resp.status_code == 200
        pdf_data = pdf_resp.json()
        assert pdf_data["accepted_layer2"] is True
        assert pdf_data["opportunity"]["codigo_oficial"] == "BDNS-923290"


def test_all_6_levels_concellos_provinces_and_private_foundations():
    """Verify 100% coverage across UE, ESTADO, CCAA, PROVINCIA, MUNICIPIO (Concellos/Ayuntamientos) and PRIVADA."""
    with TestClient(app) as client:
        reg_resp = client.get("/api/v1/sources/registry")
        assert reg_resp.status_code == 200
        reg_data = reg_resp.json()
        assert reg_data["total_fuentes_monitorizadas"] >= 30

        by_level = reg_data["oportunidades_por_nivel"]
        for expected_lvl in ("UE", "ESTADO", "CCAA", "PROVINCIA", "MUNICIPIO", "PRIVADA"):
            assert by_level.get(expected_lvl, 0) >= 2, f"Missing level {expected_lvl}"

        # Filter specifically for Private Foundations (PRIVADA)
        priv_resp = client.get("/api/v1/opportunities?nivel=PRIVADA").json()
        assert priv_resp["total"] >= 5
        priv_titles = " ".join(i["titulo_limpio"] for i in priv_resp["items"]).lower()
        assert "caixa" in priv_titles
        assert "motor verde" in priv_titles

        # Filter specifically for Concellos / Ayuntamientos (MUNICIPIO)
        muni_resp = client.get("/api/v1/opportunities?nivel=MUNICIPIO").json()
        assert muni_resp["total"] >= 5

        # Verify Prioritization Engine ('Encontrar y Priorizar')
        prio_resp = client.get("/api/v1/opportunities/prioritized?perfil_beneficiario=ONG_FUNDACIONES")
        assert prio_resp.status_code == 200
        prio_data = prio_resp.json()
        assert prio_data["total_activas_analizadas"] >= 10
        assert len(prio_data["top_10_priorizadas"]) >= 5
        top_first = prio_data["top_10_priorizadas"][0]
        assert top_first["priorizacion"]["score"] >= 80
        assert top_first["priorizacion"]["nivel"] in ("CRITICA", "ALTA")
