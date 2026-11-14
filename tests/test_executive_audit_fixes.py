"""Tests covering the three executive audit fixes: strict Reforesta eligibility, concrete foundation scraping & sitemaps, and 2016-2027+ dynamic history/recurrence."""
from datetime import date, datetime, timezone
import httpx
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.config import settings
from app.domain.reforesta_profile import assess_reforesta_eligibility
from app.ingestors.web_monitors import parse_rss_or_atom_xml, poll_web_source
from app.main import app
from app.models import Opportunity
from app.pipeline.date_resolver import compute_dates_and_status
from app.pipeline.layer1_regex import evaluate_layer1
from app.pipeline.orchestrator import RawCandidate, process_candidate
from app.pipeline.predictive_and_export import build_predictive_calendar


def test_strict_eligibility_reforesta_exclusions_and_valid_esal():
    """Verify Reforesta eligibility rejects company/tender/municipal/MVMC/domicile/exclusion calls and keeps valid ESALs."""
    # 1. PYME / empresa-only subsidy -> EXCLUIDA
    pyme = assess_reforesta_eligibility(
        titulo="Ayudas a la repoblación forestal y trabajos silvícolas",
        organo="Consejería de Medio Ambiente",
        texto="Subvenciones destinadas a empresas del sector forestal.",
        beneficiarios_hint="PYME Y PERSONAS FÍSICAS QUE DESARROLLAN ACTIVIDAD ECONÓMICA",
        tipo_oportunidad="SUBVENCION",
    )
    assert pyme.elegible is False
    assert any("empresas" in db.lower() or "pyme" in db.lower() for db in pyme.dealbreakers)

    # 2. Public tender LICITACION -> EXCLUIDA (even if mentioning forest planting)
    lic = assess_reforesta_eligibility(
        titulo="Contrato de servicio para la reforestación de montes incendiados",
        organo="TRAGSA / MITECO",
        texto="Licitación de obras mediante procedimiento abierto simplificado LCSP.",
        tipo_oportunidad="LICITACION",
    )
    assert lic.elegible is False
    assert any("licitación" in db.lower() for db in lic.dealbreakers)

    # 3. Fundación Biodiversidad grant EXCLUSIVELY for Ayuntamientos -> MUST NOT match 'Fundación' in organo!
    fb_muni = assess_reforesta_eligibility(
        titulo="Subvenciones a ayuntamientos para renaturalización urbana y bosques periurbanos",
        organo="Fundación Biodiversidad F.S.P.",
        texto="Convocatoria dirigida a municipios y entidades locales de más de 20.000 habitantes.",
        beneficiarios_hint="ENTIDADES LOCALES, MUNICIPIOS",
        tipo_oportunidad="SUBVENCION",
    )
    assert fb_muni.elegible is False
    assert "NGO" not in fb_muni.beneficiarios_tipos
    assert "ONG_FUNDACIONES" not in fb_muni.beneficiarios_tipos

    # 4. MVMC Galician forestry community -> EXCLUIDA
    mvmc = assess_reforesta_eligibility(
        titulo="Axudas para prevención de incendios en montes veciñais en man común",
        organo="Xunta de Galicia",
        texto="Beneficiarias: comunidades de montes veciñais en man común.",
        ccaa_codigo="ES-GA",
    )
    assert mvmc.elegible is False

    # 5. Universities / OPIs only -> EXCLUIDA
    uni = assess_reforesta_eligibility(
        titulo="Proyectos de investigación forestal y cambio climático en ecosistemas ibéricos",
        organo="Agencia Estatal de Investigación",
        texto="Beneficiarios: universidades públicas, CSIC y organismos públicos de investigación (OPIs).",
    )
    assert uni.elegible is False

    # 6. Domicile outside Madrid -> EXCLUIDA even if associations can apply
    dom_and = assess_reforesta_eligibility(
        titulo="Subvenciones a asociaciones ecologistas para restauración forestal en Andalucía",
        organo="Junta de Andalucía",
        texto="Podrán solicitar entidades sin ánimo de lucro con domicilio social en Andalucía inscritas en su registro.",
        ccaa_codigo="ES-AN",
        ccaa_nombre="Andalucía",
        nivel_territorial="CCAA",
    )
    assert dom_and.elegible is False
    assert any("domicilio" in db.lower() for db in dom_and.dealbreakers)

    # 7. Explicit negative exclusion clause -> MUST strip exclusion clause first and reject!
    neg_clause = assess_reforesta_eligibility(
        titulo="Ayudas forestales para terrenos agrícolas",
        organo="Consejería de Agricultura",
        texto="Beneficiarios: titulares privados. Quedan excluidas expresamente las asociaciones y entidades sin ánimo de lucro.",
    )
    assert neg_clause.elegible is False

    # 8. Unannotated subsidy without NGO evidence -> EXCLUIDA (never blindly 'Apta')
    unknown = assess_reforesta_eligibility(
        titulo="Ayudas al sector forestal 2021",
        organo="Gobierno Regional",
        texto="Extracto breve de convocatoria sin detalle de beneficiarios.",
    )
    assert unknown.elegible is False

    # 9. Valid ESAL calls MUST be eligible: MITECO Línea A (even with BDNS 'Personas físicas' quirk), Madrid 1689/2026, Endesa ESAL, EU LIFE
    miteco = assess_reforesta_eligibility(
        titulo="AYUDAS CONCURRENCIA COMPETITIVA LÍNEA A DESARROLLO ACTIVIDADES INTERÉS GENERAL CONSIDERADAS INTERÉS SOCIAL EN PROTECCIÓN MEDIO AMBIENTE",
        organo="MITECO",
        texto="Orden TED/898/2023 convocatoria anual.",
        beneficiarios_hint="PERSONAS FÍSICAS QUE NO DESARROLLAN ACTIVIDAD ECONÓMICA",
        codigo_oficial="BDNS-923290",
    )
    assert miteco.elegible is True
    assert "ONG_FUNDACIONES" in miteco.beneficiarios_tipos

    endesa = assess_reforesta_eligibility(
        titulo="II Convocatoria de Ayudas a Proyectos de Emprendimiento Verde",
        organo="Fundación Endesa",
        texto="Dirigida a entidades privadas sin ánimo de lucro, pymes y empresas de economía social para conservación y reforestación.",
        tipo_oportunidad="CONVOCATORIA_PRIVADA",
        nivel_territorial="PRIVADA",
    )
    assert endesa.elegible is True

    eu_life = assess_reforesta_eligibility(
        titulo="Nature and Biodiversity — Standard Action Projects (LIFE-2026-SAP-NAT)",
        organo="European Commission (CINEA)",
        texto="Open to public bodies and non-profit legal entities established in the EU.",
        tipo_oportunidad="PROGRAMA_UE",
        nivel_territorial="UE",
        ccaa_codigo="EU",
    )
    assert eu_life.elegible is True


def test_orchestrator_sets_low_priority_and_dealbreakers_on_excluded_calls():
    """Verify full pipeline propagates elegible=False, dealbreakers and capped priority to frontend JSON."""
    cand = RawCandidate(
        id="test-pyme-excl-2026",
        codigo_oficial="BDNS-999001",
        fuente="BDNS",
        tipo_oportunidad="SUBVENCION",
        titulo="Ayudas 2026 a pymes forestales para plantación de frondosas y mejora de cortafuegos",
        organo_convocante="Junta de Castilla y León",
        texto="Convocatoria dotada con 400.000 euros para pymes y empresas forestales de trabajos silvícolas.",
        beneficiarios_hint="PYME Y PERSONAS FÍSICAS QUE DESARROLLAN ACTIVIDAD ECONÓMICA",
        fecha_publicacion="2026-11-10",
        fecha_fin_solicitud="2027-02-15",
    )
    res = process_candidate(cand, session=None, persist=False)
    assert res.accepted_layer2 is True
    assert res.opportunity is not None
    assert "ONG_FUNDACIONES" not in (res.opportunity.beneficiarios_tipos or [])
    assert res.opportunity.prioridad_score <= 38
    assert res.opportunity.prioridad_nivel == "BAJA"
    assert res.opportunity.fecha_fin_solicitud == date(2027, 2, 15)

    front = res.opportunity.to_frontend_convocatoria()
    assert front["elegible"] is False
    assert front["fechaCierre"] == "2027-02-15"
    assert any("empresas" in d.lower() or "pyme" in d.lower() for d in front["dealbreakers"])


@pytest.mark.asyncio
async def test_foundation_xml_sitemap_and_concrete_direct_call_extractor():
    """Verify XML <urlset> sitemap filters relevant ecology links and direct_call extracts clean PDF + main body."""
    sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>https://www.fbbva.es/ayudas/ecologia-biologia-la-conservacion-2016/</loc><lastmod>2016-06-01</lastmod></url>
      <url><loc>https://www.fbbva.es/ayudas/ecologia-biologia-la-conservacion-2025/</loc><lastmod>2025-05-10</lastmod></url>
      <url><loc>https://www.fbbva.es/ayudas/premios-fronteras-del-conocimiento-informatica/</loc><lastmod>2025-04-01</lastmod></url>
    </urlset>"""
    sitemap_cfg = {
        "id": "priv-web-bbva-sitemap",
        "kind": "sitemap",
        "fuente": "FUNDACION_PRIVADA",
        "tipo_oportunidad": "CONVOCATORIA_PRIVADA",
        "nombre": "Fundación BBVA",
        "url": "https://www.fbbva.es/ayudas-sitemap.xml",
    }
    parsed = parse_rss_or_atom_xml(sitemap_xml, sitemap_cfg)
    assert len(parsed) == 2
    urls = {c.url_ficha_oficial for c in parsed}
    assert "https://www.fbbva.es/ayudas/premios-fronteras-del-conocimiento-informatica/" not in urls
    assert any("2016" in str(c.fecha_publicacion) for c in parsed)

    call_html = """<!doctype html><html><head><title>Emprendimiento Verde | Fundación Endesa</title></head><body>
    <nav>Menu Quiénes somos Actualidad Cookies</nav>
    <main>
      <h1>II Convocatoria de Ayudas a Proyectos de Emprendimiento Verde</h1>
      <p>Dotación de 90.000 euros para entidades sin ánimo de lucro en conservación y reforestación hasta el 18 de diciembre de 2026.</p>
      <a href="/wp-content/uploads/Bases II Convocatoria Emprendimiento Verde 2026_Vf.pdf">Descargar bases oficiales</a>
    </main></body></html>"""
    soft404_html = "<html><head><title>Error 404 - Página no encontrada</title></head><body><h1>Error 404</h1></body></html>"

    def _handler(request: httpx.Request) -> httpx.Response:
        if "emprendimiento-verde-broken" in str(request.url):
            return httpx.Response(200, text=soft404_html)
        return httpx.Response(200, text=call_html)

    transport = httpx.MockTransport(_handler)
    direct_cfg = {
        "id": "priv-web-endesa-verde",
        "kind": "direct_call",
        "fuente": "FUNDACION_PRIVADA",
        "tipo_oportunidad": "CONVOCATORIA_PRIVADA",
        "nombre": "Fundación Endesa",
        "url": "https://www.fundacionendesa.org/es/formacion-empleo/ii-convocatoria-emprendimiento-verde",
    }
    soft_cfg = {**direct_cfg, "id": "priv-web-broken", "url": "https://www.fundacionendesa.org/es/emprendimiento-verde-broken"}
    async with httpx.AsyncClient(transport=transport) as client:
        cands = await poll_web_source(client, direct_cfg)
        broken = await poll_web_source(client, soft_cfg)

    assert broken == []
    assert len(cands) == 1
    assert cands[0].titulo.startswith("II Convocatoria de Ayudas")
    assert "Menu Quiénes somos" not in cands[0].texto
    assert cands[0].url_bases_reguladoras == (
        "https://www.fundacionendesa.org/wp-content/uploads/Bases%20II%20Convocatoria%20Emprendimiento%20Verde%202026_Vf.pdf"
    )


def test_2016_horizon_2027_deadlines_and_empirical_recurrence_mining():
    """Verify 2016+ dates & 2027 deadlines work without 2026 clamping and recurrence mines multi-year families."""
    d_2016 = compute_dates_and_status(
        fecha_publicacion=date(2016, 4, 10),
        fecha_fin_solicitud=date(2016, 5, 25),
        today=date(2026, 11, 14),
    )
    assert d_2016.anio_convocatoria == 2016
    assert d_2016.estado == "CERRADA"

    d_2027 = compute_dates_and_status(
        fecha_publicacion=date(2026, 11, 10),
        fecha_fin_solicitud=date(2027, 2, 20),
        today=date(2026, 11, 14),
    )
    assert d_2027.estado == "ACTIVA"
    assert d_2027.fecha_fin_solicitud == date(2027, 2, 20)

    # Create 7 historical editions (2016, 2017, 2018, 2019, 2021, 2023, 2026) of a recurring nongrant/ESAL family
    synthetic_opps = []
    for yr in (2016, 2017, 2018, 2019, 2021, 2023, 2026):
        synthetic_opps.append(
            Opportunity(
                id=f"test-rec-custodia-{yr}",
                codigo_oficial=f"BDNS-CUST-{yr}",
                fuente="BDNS",
                tipo_oportunidad="SUBVENCION",
                estado="ACTIVA" if yr == 2026 else "CERRADA",
                dias_restantes=40 if yr == 2026 else 0,
                prioridad_score=85 if yr == 2026 else 40,
                prioridad_nivel="ALTA" if yr == 2026 else "HISTORICO",
                relevancia_tipo="DIRECTA",
                relevancia_score=88,
                categorias=["reforestacion", "biodiversidad"],
                justificacion_juez="Apta para entidades de custodia y asociaciones sin ánimo de lucro.",
                titulo_limpio=f"Ayudas estatales {yr} a entidades de custodia del territorio y bosques autóctonos",
                titulo_original=f"Subvenciones {yr} para entidades de custodia del territorio y restauración forestal",
                resumen="Programa anual abierto a asociaciones sin ánimo de lucro.",
                nivel_territorial="ESTADO",
                ccaa_codigo="ES",
                ccaa_nombre="Estatal",
                organo_convocante="Organismo Autónomo Parques Nacionales (OAPN)",
                presupuesto_total=1200000.0,
                beneficiarios_tipos=["ONG_FUNDACIONES"],
                anio_convocatoria=yr,
                fecha_publicacion=date(yr, 5, 12),
                fecha_fin_solicitud=date(2027, 1, 20) if yr == 2026 else date(yr, 6, 20),
                url_ficha_oficial=f"https://www.infosubvenciones.es/bdnstrans/GE/es/convocatoria/{yr}",
                fecha_ingesta=datetime.now(timezone.utc),
            )
        )

    cal = build_predictive_calendar(synthetic_opps, today=date(2026, 11, 14))
    mined = [p for p in cal["programas_recurrentes"] if p["programa_id"].startswith("MINED-")]
    assert len(mined) >= 1
    oapn_prog = next(p for p in mined if "custodia" in p["nombre_programa"].lower())
    # Must NOT truncate historical editions to [:5]
    assert len(oapn_prog["historico_ediciones_detectadas"]) == 7
    assert 2016 in oapn_prog["patron_empirico"]["anios_detectados"]
    assert oapn_prog["mes_apertura_habitual"] == 5
    assert oapn_prog["elegible_reforesta"] is True


def test_title_exclusive_recipient_and_foundation_classification():
    """Verify title-addressed municipal grants are excluded and regional foundations map to privada_rsc."""
    aragon_local = assess_reforesta_eligibility(
        titulo="Subvenciones dirigidas a las entidades locales aragonesas para prevención de incendios forestales",
        organo="Gobierno de Aragón",
        beneficiarios_hint="PERSONAS JURÍDICAS QUE NO DESARROLLAN ACTIVIDAD ECONÓMICA",
        texto="Proyectos de interés social y forestal en montes públicos gestionados por municipios.",
        nivel_territorial="CCAA",
        ccaa_codigo="ES-AR",
    )
    assert aragon_local.elegible is False
    assert "ONG_FUNDACIONES" not in aragon_local.beneficiarios_tipos

    ibercaja_l1 = evaluate_layer1(
        titulo="Convocatoria 2026 Sostenibilidad y Protección del Medioambiente",
        organo="Fundación Ibercaja",
        texto=(
            "Ayudas para entidades sin ánimo de lucro en reforestación, restauración de ecosistemas y biodiversidad. "
            "La aportación se formalizará mediante un convenio de colaboración. Ver proyectos ganadores anteriores."
        ),
    )
    assert ibercaja_l1.passed is True

    bilateral_l1 = evaluate_layer1(
        titulo="Convenio de colaboración con el Ayuntamiento para repoblación urbana",
        organo="Diputación Provincial",
        texto="Convenio nominativo directo.",
    )
    assert bilateral_l1.passed is False

    cand = RawCandidate(
        id="test-fundacion-moeve-md",
        codigo_oficial="PRIV-MOEVE-2026",
        fuente="FUNDACION_PRIVADA",
        tipo_oportunidad="CONVOCATORIA_PRIVADA",
        titulo="Convocatoria Fundación Moeve para restauración forestal y biodiversidad en España",
        organo_convocante="Fundación Moeve (Premios al Valor Social)",
        texto="Abierta a asociaciones y entidades sin ánimo de lucro para proyectos de reforestación y biodiversidad en Madrid y toda España hasta 2027-02-15.",
        region_hint="ES-MD - Comunidad de Madrid (Privada / RSC)",
        url_ficha_oficial="https://fundacion.moeveglobal.com/es/premios-al-valor-social",
    )
    res = process_candidate(cand, persist=False)
    assert res.accepted_layer2 is True
    assert res.opportunity is not None
    assert res.opportunity.nivel_territorial == "PRIVADA"
    fe = res.opportunity.to_frontend_convocatoria()
    assert fe["tipoFuente"] == "privada_rsc"
    assert fe["elegible"] is True


def test_budget_realism_noise_exclusions_and_closed_year_resolution():
    """Verify no fake 100k budget fallback, EU consortium grant cap, noise exclusions, and past 'Cerrada YYYY' resolution."""
    # 1. Missing budget must serialize as 0 (never phantom 100.000 EUR)
    cand_no_budget = RawCandidate(
        id="test-no-budget-2026",
        codigo_oficial="PRIV-NOBUDGET-2026",
        fuente="FUNDACION_PRIVADA",
        tipo_oportunidad="CONVOCATORIA_PRIVADA",
        titulo="Convocatoria de ayudas para reforestación y conservación forestal 2026",
        organo_convocante="Fundación Ejemplo",
        texto="Abierta a asociaciones y entidades sin ánimo de lucro para proyectos de reforestación en España.",
        region_hint="ES-MD - Comunidad de Madrid (Privada / RSC)",
        url_ficha_oficial="https://fundacion-ejemplo.org/convocatoria-2026",
    )
    res_nb = process_candidate(cand_no_budget, persist=False)
    assert res_nb.accepted_layer2 is True
    assert res_nb.opportunity is not None
    fe_nb = res_nb.opportunity.to_frontend_convocatoria()
    assert fe_nb["cuantiaMaximaProyecto"] == 0
    assert fe_nb["presupuestoTotal"] == 0

    # 2. Multi-partner EU Horizon consortium grant caps per-NGO tranche <= 350k while preserving full EU budget
    cand_eu = RawCandidate(
        id="eu-horizon-nature-test-2027",
        codigo_oficial="HORIZON-CL6-2027-TEST",
        fuente="UE_SEDIA",
        tipo_oportunidad="PROGRAMA_UE",
        titulo="Laboratorios vivientes para restauración forestal y biodiversidad europea",
        organo_convocante="Comisión Europea (Horizon Europe)",
        texto=(
            "Open to non-profit legal entities and NGOs for forest ecosystem restoration and biodiversity. "
            "Funding budget 12000000 EUR."
        ),
        presupuesto_total=12_000_000.0,
        fecha_publicacion="2026-10-15",
        fecha_fin_solicitud="2027-04-20",
        url_ficha_oficial="https://ec.europa.eu/info/funding-tenders/opportunities/portal/test",
    )
    res_eu = process_candidate(cand_eu, persist=False)
    assert res_eu.accepted_layer2 is True
    assert res_eu.opportunity is not None
    fe_eu = res_eu.opportunity.to_frontend_convocatoria()
    assert 0 < fe_eu["cuantiaMaximaProyecto"] <= 350_000
    assert fe_eu["presupuestoTotal"] == 12_000_000

    # 3. Hard noise title exclusions (footwear recycling, organic crop breeding, national awards)
    for noise_title in (
        "Innovative circular solutions for end-of-life footwear through collection, sorting and recycling",
        "Enhancing the competitiveness of organic crop breeding: focus on intercropping adapted varieties",
        "Premios Nacionales de Medioambiente y de Energía 2026",
    ):
        l1 = evaluate_layer1(
            titulo=noise_title,
            organo="European Commission / MITECO",
            texto="Biodiversity climate action grant.",
        )
        assert l1.passed is False, f"Expected Layer-1 rejection for: {noise_title}"

    # 4. Past 'Cerrada ... 2025' title resolves to CERRADA instead of lingering ACTIVA
    cand_closed = RawCandidate(
        id="priv-closed-2025-test",
        codigo_oficial="PRIV-CLOSED-2025",
        fuente="FUNDACION_PRIVADA",
        tipo_oportunidad="CONVOCATORIA_PRIVADA",
        titulo="Cerrada Ayudas a Proyectos de Investigación Ambiental 2025 Convocatoria 2025",
        organo_convocante="Fundación CajaCanarias",
        texto="Proyectos de investigación y conservación forestal para asociaciones sin ánimo de lucro.",
        region_hint="ES-CN - Canarias (Privada / RSC)",
        url_ficha_oficial="https://www.cajacanarias.com/ayudas-investigacion-2025",
    )
    res_closed = process_candidate(cand_closed, persist=False)
    assert res_closed.accepted_layer2 is True
    assert res_closed.opportunity is not None
    assert res_closed.opportunity.estado == "CERRADA"
    assert res_closed.opportunity.fecha_fin_solicitud == date(2025, 12, 31)


def test_lcsp_service_tender_eligibility_ted_connector_and_range_closure(monkeypatch):
    """
    Verify:
    1. LCSP Art. 65 environmental service tenders are APTAS (with realistic <=220k tranche & 0 rejection dealbreakers)
       while heavy obras/machinery tenders remain EXCLUIDAS.
    2. Spanish date ranges 'Del X al DD de mes de YYYY' resolve closing dates properly (June 2026 -> CERRADA).
    3. Nominative Dir 22.2.c / Convenios / anniversary news articles are rejected by Layer-1.
    4. fetch_live_ted_candidates cleanly maps TED Search API v3 Spanish notices (NUTS, PLACSP link, TED PDF).
    """
    from app.ingestors.live_connectors import fetch_live_ted_candidates
    from app.search_utils import score_convocatoria_dict

    service_cand = RawCandidate(
        id="ted-test-service-2026",
        codigo_oficial="TED 650001-2026",
        fuente="PLACSP",
        tipo_oportunidad="LICITACION",
        titulo="Servicio de reforestación con especies autóctonas y educación ambiental en montes de Cuenca",
        organo_convocante="Junta de Comunidades de Castilla-La Mancha",
        texto=(
            "Contrato de servicios públicos (LCSP Art. 65) para plantación forestal, restauración ecológica "
            "y talleres de educación ambiental en la Serranía de Cuenca."
        ),
        cpv_codes=["77200000", "80540000"],
        nuts_code="ES423",
        presupuesto_total=800_000.0,
        importe_max_proyecto=800_000.0,
        fecha_publicacion="2026-10-20",
        fecha_fin_solicitud="2026-12-20",
        url_ficha_oficial="https://contrataciondelestado.es/wps/poc?uri=deeplink:detalle_licitacion&idEvl=test123",
        url_bases_reguladoras="https://ted.europa.eu/es/notice/650001-2026/pdf",
    )
    res_srv = process_candidate(service_cand, persist=False)
    assert res_srv.accepted_layer2 is True
    assert res_srv.opportunity is not None
    fe_srv = res_srv.opportunity.to_frontend_convocatoria()
    assert fe_srv["elegible"] is True
    assert not any(
        any(tok in db.lower() for tok in ("no acredita elegibilidad", "orientada a contratistas", "no es elegible"))
        for db in fe_srv["dealbreakers"]
    )
    assert fe_srv["ccaaCodigo"] == "ES-CM"
    assert fe_srv["presupuestoTotal"] == 800_000
    assert 0 < fe_srv["cuantiaMaximaProyecto"] <= 220_000
    assert score_convocatoria_dict(fe_srv, "licitaciones") > 0

    works_elig = assess_reforesta_eligibility(
        titulo="Contrato de obras de prevención de incendios y ahoyado mecanizado con autobombas",
        organo="Consejería de Medio Ambiente",
        texto="Licitación de obras de infraestructura viaria y suministro de maquinaria pesada LCSP.",
        tipo_oportunidad="LICITACION",
    )
    assert works_elig.elegible is False
    assert any("licitación" in db.lower() for db in works_elig.dealbreakers)

    # Date range closure: "Del 02 de junio al 30 de junio de 2026" -> 2026-06-30 -> CERRADA in Nov 2026
    cand_range = RawCandidate(
        id="priv-range-jun2026-test",
        codigo_oficial="PRIV-IBER-2026",
        fuente="FUNDACION_PRIVADA",
        tipo_oportunidad="CONVOCATORIA_PRIVADA",
        titulo="Del 02 de junio al 30 de junio de 2026 Convocatoria 2026 de Medio Ambiente",
        organo_convocante="Fundación Ibercaja",
        texto="Ayudas a asociaciones sin ánimo de lucro para restauración ecológica y reforestación.",
        region_hint="ES-AR - Aragón (Privada / RSC)",
        url_ficha_oficial="https://www.fundacionibercaja.es/convocatorias/medio-ambiente-2026/",
    )
    monkeypatch.setattr(settings, "reference_date", date(2026, 11, 14))
    res_range = process_candidate(cand_range, persist=False)
    assert res_range.accepted_layer2 is True
    assert res_range.opportunity is not None
    assert res_range.opportunity.fecha_fin_solicitud == date(2026, 6, 30)
    assert res_range.opportunity.estado == "CERRADA"

    # Nominative / news exclusions rejected cleanly
    for bad in (
        "202604306014_Dir 22.2.c_Subvención destinada a fundación privada",
        "Convenio con Ecodes para sensibilización climática en Navarra",
        "Celebramos diez años de BBK Basoa recuperando nuestros bosques autóctonos",
    ):
        assert evaluate_layer1(titulo=bad, organo="Organismo Público", texto="Reforestación y bosques.").passed is False

    # TED v3 live parser (mocked HTTP transport)
    mock_ted_payload = {
        "notices": [
            {
                "ND": "777001-2026",
                "title-proc": {"spa": "Servicio de restauración forestal y silvicultura preventiva en Guadalajara"},
                "description-proc": {"spa": "Trabajos de repoblación forestal y mejora de hábitats en el Alto Tajo."},
                "buyer-name": {"spa": ["Consejería de Desarrollo Sostenible"]},
                "place-of-performance-city-proc": {"spa": ["Guadalajara"]},
                "place-of-performance-subdiv-proc": ["ES424"],
                "classification-cpv": ["77200000"],
                "estimated-value-glo": 185000.0,
                "contract-nature-main-proc": "services",
                "publication-date": "2026-11-01+01:00",
                "deadline-receipt-request": ["2026-12-18+01:00"],
                "document-url-lot": ["https://contrataciondelestado.es/wps/poc?uri=deeplink:detalle&idEvl=abc"],
                "links": {
                    "pdf": {"SPA": "https://ted.europa.eu/es/notice/777001-2026/pdf"},
                    "html": {"SPA": "https://ted.europa.eu/es/notice/-/detail/777001-2026"},
                },
            }
        ]
    }

    class _FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, json=None):
            return httpx.Response(200, json=mock_ted_payload, request=httpx.Request("POST", url))

    monkeypatch.setattr("app.ingestors.live_connectors._make_async_client", lambda **kw: _FakeAsyncClient())
    import asyncio

    ted_items = asyncio.run(fetch_live_ted_candidates())
    assert len(ted_items) == 1
    t0 = ted_items[0]
    assert t0.id == "ted-777001-2026"
    assert t0.tipo_oportunidad == "LICITACION"
    assert t0.nuts_code == "ES424"
    assert t0.presupuesto_total == 185000.0
    assert t0.fecha_fin_solicitud == date(2026, 12, 18)
    assert "contrataciondelestado.es" in (t0.url_ficha_oficial or "")
    assert t0.url_bases_reguladoras == "https://ted.europa.eu/es/notice/777001-2026/pdf"


