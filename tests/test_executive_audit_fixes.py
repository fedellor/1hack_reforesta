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
