"""Comprehensive Tests for High-Impact Improvements 1-5:
1A. Extract -> Linked Full PDF Enricher
1B. Automatic Amendment Detection & Application (Ampliación de plazo & Corrección de errores)
2.  Scanned PDF Image-Only OCR Fallback (custom/pytesseract/Vision hook)
3.  Cross-Portal Semantic Fuzzy/Trigram Deduplication (with distinct-ID guards)
4.  Persistent SQLite/PostgreSQL Layer 2 LLM Verdict Cache (`llm_verdict_cache`)
5.  Private Foundation HTML Monitors + Dual RSS/Atom/HTML CCAA Bulletin Scraper
"""
from datetime import date, timedelta
from pathlib import Path
import httpx
import pymupdf as fitz
import pytest
from sqlmodel import Session, SQLModel, create_engine, select
from app.config import settings
from app.ingestors import live_connectors
from app.ingestors.fuentes_local import pdf_doc_to_candidate
from app.ingestors.live_connectors import (
    enrich_candidates_with_linked_pdfs,
    fetch_live_ccaa_rss_candidates,
    fetch_live_private_foundation_candidates,
)
from app.models import LLMVerdictCache, Opportunity
from app.pipeline import layer2_judge
from app.pipeline.layer1_regex import evaluate_layer1
from app.pipeline.layer2_judge import evaluate_layer2
from app.pipeline.orchestrator import RawCandidate, process_candidate
from app.pipeline.pdf_extractor import extract_pdf_from_bytes


def _isolated_session(tmp_path: Path) -> Session:
    db_file = tmp_path / "isolated_test.db"
    test_engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(test_engine)
    return Session(test_engine)


def _build_pdf_bytes(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), text, fontsize=10)
    data = doc.tobytes()
    doc.close()
    return data


def _build_scanned_image_only_pdf_bytes(visible_text: str) -> bytes:
    """Create a PDF whose page has ZERO selectable text — only an embedded PNG image."""
    src = fitz.open()
    src_page = src.new_page()
    src_page.insert_text((50, 72), visible_text, fontsize=12)
    png_bytes = src_page.get_pixmap(dpi=120).tobytes("png")
    src.close()

    img_doc = fitz.open()
    page = img_doc.new_page()
    page.insert_image(page.rect, stream=png_bytes)
    out_bytes = img_doc.tobytes()
    img_doc.close()
    return out_bytes


# ---------------------------------------------------------------------------
# Mejora 1A: Seguimiento automático Extracto -> PDF completo
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_linked_pdf_enrichment_and_guards(monkeypatch, tmp_path):
    full_pdf_bytes = _build_pdf_bytes(
        "Orden 2245/2026 de la Consejería de Medio Ambiente.\n"
        "Objeto: Subvenciones para reforestación autóctona y restauración de bosques de ribera.\n"
        "Beneficiarios: entidades sin ánimo de lucro.\n"
        "Dotación total de 1.250.000,00 euros y financiación hasta el 90%.\n"
        "CPV 77231600-4.\n"
        "Plazo de presentación de solicitudes: 20 días hábiles."
    )

    async def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url.endswith("orden-2245-2026.pdf"):
            return httpx.Response(200, content=full_pdf_bytes, headers={"content-type": "application/pdf"})
        if url.endswith("software-erp.pdf"):
            return httpx.Response(200, content=full_pdf_bytes, headers={"content-type": "application/pdf"})
        if url.endswith("broken-html.pdf"):
            return httpx.Response(200, text="<html><body>Not a PDF</body></html>", headers={"content-type": "text/html"})
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    real_cls = httpx.AsyncClient
    monkeypatch.setattr(live_connectors.httpx, "AsyncClient", lambda *a, **kw: real_cls(*a, **{**kw, "transport": transport}))

    short_extract = RawCandidate(
        id="boe-extracto-2245",
        codigo_oficial="BOE-B-2026-2245",
        fuente="BOE",
        tipo_oportunidad="SUBVENCION",
        titulo="Extracto de Orden 2245/2026 sobre ayudas forestales",
        organo_convocante="Comunidad de Madrid",
        texto="Extracto breve sin importes.",
        fecha_publicacion=date.today(),
        url_ficha_oficial="https://www.boe.es/diario_boe/txt.php?id=BOE-B-2026-2245",
        url_bases_reguladoras="https://www.boe.es/boe/dias/2026/11/10/pdfs/orden-2245-2026.pdf",
    )
    unrelated_extract = RawCandidate(
        id="placsp-erp-short",
        codigo_oficial="EXP-ERP",
        fuente="PLACSP",
        tipo_oportunidad="LICITACION",
        titulo="Adquisición de mobiliario de oficina y papelería",
        texto="Suministro estándar.",
        url_bases_reguladoras="https://example.org/software-erp.pdf",
    )
    html_disguised = RawCandidate(
        id="fake-pdf-link",
        codigo_oficial="RSS-99",
        fuente="BOLETIN_CCAA",
        tipo_oportunidad="SUBVENCION",
        titulo="Ayudas para restauración forestal en cuenca fluvial",
        texto="Texto corto.",
        url_bases_reguladoras="https://example.org/broken-html.pdf",
    )

    enriched_count = await enrich_candidates_with_linked_pdfs([short_extract, unrelated_extract, html_disguised])
    assert enriched_count == 1
    assert "[TEXTO COMPLETO PDF ENLAZADO" in short_extract.texto
    assert short_extract.presupuesto_total == 1250000.0
    assert short_extract.porcentaje_financiacion == 90.0
    assert "77231600" in short_extract.cpv_codes
    assert "20 días hábiles" in (short_extract.plazo_texto_original or "").lower()
    # Unrelated furniture PDF must not be fetched; disguised HTML must be ignored
    assert "[TEXTO COMPLETO PDF" not in unrelated_extract.texto
    assert "[TEXTO COMPLETO PDF" not in html_disguised.texto

    with _isolated_session(tmp_path) as session:
        res = process_candidate(short_extract, session=session, persist=True)
        assert res.accepted_layer2 is True
        assert res.opportunity is not None
        assert res.opportunity.presupuesto_total == 1250000.0
        assert res.opportunity.ccaa_codigo == "ES-MD"


# ---------------------------------------------------------------------------
# Mejora 1B: Detección de Ampliación de plazo y Corrección de errores
# ---------------------------------------------------------------------------

def test_amendments_extend_deadline_and_update_budget_in_place(tmp_path):
    with _isolated_session(tmp_path) as session:
        original = RawCandidate(
            id="orig-orden-445-2026",
            codigo_oficial="Orden 445/2026",
            fuente="BOLETIN_CCAA",
            tipo_oportunidad="SUBVENCION",
            titulo="Orden 445/2026 de subvenciones para repoblación forestal y prevención de incendios",
            organo_convocante="Comunidad de Madrid",
            texto="Ayudas a asociaciones sin ánimo de lucro para restauración de bosques.",
            presupuesto_total=500000.0,
            porcentaje_financiacion=100.0,
            fecha_publicacion=date(2026, 2, 1),
            fecha_fin_solicitud=date(2026, 3, 15),
            anio_convocatoria=2026,
            url_ficha_oficial="https://bocm.es/orden-445-2026",
        )
        res_orig = process_candidate(original, session=session, persist=True)
        assert res_orig.opportunity is not None
        assert res_orig.opportunity.estado == "CERRADA"

        # 1. Terse Ampliación de plazo notice (without repeating forestry words!)
        new_close = date.today() + timedelta(days=25)
        ampliacion = RawCandidate(
            id="bocm-ampliacion-445",
            codigo_oficial="BOCM-2026-AMP-445",
            fuente="BOLETIN_CCAA",
            tipo_oportunidad="SUBVENCION",
            titulo="Orden de ampliación del plazo de presentación de solicitudes de la Orden 445/2026",
            organo_convocante="Comunidad de Madrid",
            texto=f"Se amplía el plazo de presentación de solicitudes hasta el {new_close.isoformat()}.",
            fecha_publicacion=date.today(),
            url_ficha_oficial="https://bocm.es/ampliacion-445-2026",
        )
        res_amp = process_candidate(ampliacion, session=session, persist=True)
        assert res_amp.amendment_applied == "AMPLIACION_PLAZO"
        assert res_amp.opportunity is not None
        assert res_amp.opportunity.id == "orig-orden-445-2026"
        assert res_amp.opportunity.fecha_fin_solicitud == new_close
        assert res_amp.opportunity.estado == "ACTIVA"
        assert any("AMPLIACION_PLAZO" in c for c in res_amp.opportunity.citas_bases)

        # 2. Corrección de errores updating budget without creating a second row
        correccion = RawCandidate(
            id="bocm-errata-445",
            codigo_oficial="BOCM-2026-ERR-445",
            fuente="BOLETIN_CCAA",
            tipo_oportunidad="SUBVENCION",
            titulo="Corrección de errores de la Orden 445/2026",
            organo_convocante="Comunidad de Madrid",
            texto="Se corrige el crédito presupuestario total asignado a la convocatoria.",
            presupuesto_total=850000.0,
            fecha_publicacion=date.today(),
        )
        res_corr = process_candidate(correccion, session=session, persist=True)
        assert res_corr.amendment_applied == "CORRECCION_ERRORES"
        all_rows = session.exec(select(Opportunity)).all()
        assert len(all_rows) == 1
        assert all_rows[0].presupuesto_total == 850000.0

        # 3. Negative guard: amendment on noise (subasta judicial) must still be rejected!
        noise_amp = RawCandidate(
            id="noise-errata",
            codigo_oficial="ERR-SUBASTA",
            fuente="BOE",
            tipo_oportunidad="SUBVENCION",
            titulo="Corrección de errores de subasta judicial por extinción de condominio",
            texto="Orden 445/2026 no relacionada.",
        )
        res_noise = process_candidate(noise_amp, session=session, persist=True)
        assert res_noise.passed_layer1 is False
        assert len(session.exec(select(Opportunity)).all()) == 1


def test_amendment_extension_in_business_days(tmp_path):
    """Verify 'se amplía en 10 días hábiles' adds business days onto existing closing date."""
    with _isolated_session(tmp_path) as session:
        base_close = date(2026, 11, 20)
        base = RawCandidate(
            id="bdns-880011",
            codigo_oficial="BDNS-880011",
            fuente="BDNS",
            tipo_oportunidad="SUBVENCION",
            titulo="Ayudas para cortafuegos y prevención de incendios forestales en Andalucía",
            organo_convocante="Junta de Andalucía",
            texto="Subvenciones para entidades sin ánimo de lucro.",
            fecha_publicacion=date(2026, 11, 1),
            fecha_fin_solicitud=base_close,
            anio_convocatoria=2026,
        )
        process_candidate(base, session=session, persist=True)

        ext = RawCandidate(
            id="boja-amp-10d",
            codigo_oficial="BOJA-AMP-880011",
            fuente="BOLETIN_CCAA",
            tipo_oportunidad="SUBVENCION",
            titulo="Resolución por la que se amplía el plazo de la convocatoria BDNS 880011",
            organo_convocante="Junta de Andalucía",
            texto="Se amplía el plazo de presentación en 10 días hábiles desde la finalización del plazo inicial.",
            fecha_publicacion=date(2026, 11, 13),
        )
        res = process_candidate(ext, session=session, persist=True)
        assert res.amendment_applied == "AMPLIACION_PLAZO"
        assert res.opportunity is not None
        assert res.opportunity.fecha_fin_solicitud is not None
        assert res.opportunity.fecha_fin_solicitud > base_close
        assert res.opportunity.estado == "ACTIVA"


# ---------------------------------------------------------------------------
# Mejora 2: OCR de respaldo para PDFs escaneados (imagen sin texto seleccionable)
# ---------------------------------------------------------------------------

def test_scanned_pdf_ocr_fallback_and_empty_graceful_handling():
    scanned_bytes = _build_scanned_image_only_pdf_bytes("Documento escaneado municipal")

    # Verify the raw PDF indeed has ZERO selectable text before OCR
    raw_doc_check = fitz.open(stream=scanned_bytes, filetype="pdf")
    assert raw_doc_check[0].get_text("text").strip() == ""
    raw_doc_check.close()

    seen_png_pages: list[int] = []

    def fake_ocr(png_pages: list[bytes]) -> str:
        seen_png_pages.append(len(png_pages))
        assert png_pages[0].startswith(b"\x89PNG")
        return (
            "BOP de Pontevedra - Extracto Orden 333/2026\n"
            "Concello de Pontevedra convoca subvenciones para repoblación forestal "
            "con frondosas autóctonas y prevención de incendios forestales.\n"
            "Presupuesto: 320.000,00 euros. CPV 77231600-4.\n"
            "Plazo de solicitud: 15 días hábiles."
        )

    extracted = extract_pdf_from_bytes(scanned_bytes, filename="bop-escaneado.pdf", ocr_handler=fake_ocr)
    assert seen_png_pages == [1]
    assert extracted.used_ocr is True
    assert extracted.ocr_engine == "CUSTOM_OCR"
    assert extracted.codigo_orden == "Orden 333/2026"
    assert extracted.presupuesto_total == 320000.0
    assert "77231600" in extracted.cpv_codes

    cand = pdf_doc_to_candidate(extracted)
    res = process_candidate(cand, persist=False)
    assert res.passed_layer1 is True
    assert res.accepted_layer2 is True
    assert res.opportunity is not None
    assert res.opportunity.ccaa_codigo == "ES-GA"
    assert res.opportunity.provincia_codigo == "ES-PO"

    # When no OCR engine and no API key are configured, scanned PDF returns cleanly without crashing
    no_ocr = extract_pdf_from_bytes(scanned_bytes, filename="bop-vacio.pdf")
    assert no_ocr.used_ocr is False
    assert no_ocr.full_text == ""


# ---------------------------------------------------------------------------
# Mejora 3: Deduplicación semántica (fuzzy + trigramas) con guardias de precisión
# ---------------------------------------------------------------------------

def test_semantic_deduplication_merges_without_shared_id_but_preserves_distinct_codes(tmp_path):
    with _isolated_session(tmp_path) as session:
        c1 = RawCandidate(
            id="xunta-portal-frondosas",
            codigo_oficial="PORTAL-GAL-2026",
            fuente="BOLETIN_CCAA",
            tipo_oportunidad="SUBVENCION",
            titulo="Ayudas para la prevención de incendios forestales y fajas auxiliares en montes vecinales de Galicia",
            organo_convocante="Xunta de Galicia",
            texto="Subvenciones para comunidades de montes y asociaciones.",
            presupuesto_total=1800000.0,
            fecha_publicacion=date(2026, 11, 1),
            fecha_fin_solicitud=date(2026, 12, 10),
        )
        process_candidate(c1, session=session, persist=True)

        # Semantically equivalent entry from another portal without matching code or Orden ID
        c2 = RawCandidate(
            id="nota-prensa-frondosas",
            codigo_oficial="PRENSA-GA-88",
            fuente="BOE",
            tipo_oportunidad="SUBVENCION",
            titulo="Extracto de subvenciones prevención de incendios forestales y fajas en montes vecinales Galicia",
            organo_convocante="Consellería do Medio Rural - Xunta de Galicia",
            texto="Subvenciones para comunidades de montes.",
            fecha_publicacion=date(2026, 11, 1),
            fecha_fin_solicitud=date(2026, 12, 12),  # within 7-day compatibility window
            url_tramitacion="https://sede.xunta.gal/procedimiento-forestal",
        )
        res2 = process_candidate(c2, session=session, persist=True)
        assert res2.accepted_layer2 is True
        rows = session.exec(select(Opportunity)).all()
        assert len(rows) == 1
        assert rows[0].presupuesto_total == 1800000.0
        assert rows[0].url_tramitacion == "https://sede.xunta.gal/procedimiento-forestal"

        # Distinct explicit BDNS codes with almost identical wording MUST NOT merge!
        distinct_bdns = RawCandidate(
            id="bdns-771002",
            codigo_oficial="BDNS-771002",
            fuente="BDNS",
            tipo_oportunidad="SUBVENCION",
            titulo="Ayudas para la prevención de incendios forestales y fajas auxiliares en montes vecinales de Galicia (Línea B)",
            organo_convocante="Xunta de Galicia",
            texto="Segunda línea diferenciada con presupuesto independiente.",
            fecha_publicacion=date(2026, 11, 1),
            fecha_fin_solicitud=date(2026, 12, 10),
        )
        process_candidate(distinct_bdns, session=session, persist=True)
        c_first_bdns = RawCandidate(
            id="bdns-771001",
            codigo_oficial="BDNS-771001",
            fuente="BDNS",
            tipo_oportunidad="SUBVENCION",
            titulo="Ayudas para la prevención de incendios forestales y fajas auxiliares en montes vecinales de Galicia (Línea A)",
            organo_convocante="Xunta de Galicia",
            texto="Primera línea diferenciada.",
            fecha_publicacion=date(2026, 11, 1),
            fecha_fin_solicitud=date(2026, 12, 10),
        )
        process_candidate(c_first_bdns, session=session, persist=True)
        assert session.get(Opportunity, "bdns-771002") is not None
        assert session.get(Opportunity, "bdns-771001") is not None


# ---------------------------------------------------------------------------
# Mejora 4: Caché persistente de Capa 2 en SQLite/PostgreSQL
# ---------------------------------------------------------------------------

def test_persistent_layer2_cache_survives_ram_reset(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "groq_api_key", "")
    monkeypatch.setattr(settings, "openrouter_api_key", "")
    monkeypatch.setattr(settings, "enable_public_llm_fallback", False)

    layer2_judge._VERDICT_CACHE.clear()
    with _isolated_session(tmp_path) as session:
        titulo = "Subvención piloto para restauración de alcornoques y encinares"
        organo = "Junta de Extremadura"
        texto = "Financiación del 100% para entidades sin ánimo de lucro en dehesas extremenas."
        l1 = evaluate_layer1(titulo=titulo, organo=organo, texto=texto)

        # Cold run: computes verdict and writes row to llm_verdict_cache
        v1 = evaluate_layer2(titulo=titulo, organo=organo, texto=texto, layer1_result=l1, session=session)
        assert v1.es_relevante is True
        cached_rows = session.exec(select(LLMVerdictCache)).all()
        assert len(cached_rows) == 1
        assert cached_rows[0].hit_count == 1

        # Simulate server restart by wiping RAM OrderedDict AND tracking whether deterministic judge runs again
        layer2_judge._VERDICT_CACHE.clear()
        calls = {"expert_runs": 0}
        orig_expert = layer2_judge._deterministic_expert_judge

        def spy_expert(*args, **kwargs):
            calls["expert_runs"] += 1
            return orig_expert(*args, **kwargs)

        monkeypatch.setattr(layer2_judge, "_deterministic_expert_judge", spy_expert)

        # Warm hit from SQLite persistent table: must NOT re-run _deterministic_expert_judge!
        v2 = evaluate_layer2(titulo=titulo, organo=organo, texto=texto, layer1_result=l1, session=session)
        assert calls["expert_runs"] == 0
        assert v2.titulo_limpio_es == v1.titulo_limpio_es

        session.refresh(cached_rows[0])
        assert cached_rows[0].hit_count == 2

        # Cloud override guard: passing api_key_override bypasses cached HYBRID_HEURISTIC verdict
        gemini_attempted = {"called": False}

        def spy_gemini(api_key: str, user_prompt: str):
            gemini_attempted["called"] = True
            return None

        monkeypatch.setattr(layer2_judge, "_try_gemini_judge", spy_gemini)
        layer2_judge._VERDICT_CACHE.clear()
        evaluate_layer2(
            titulo=titulo,
            organo=organo,
            texto=texto,
            layer1_result=l1,
            api_key_override="user-test-gemini-key",
            session=session,
        )
        assert gemini_attempted["called"] is True


# ---------------------------------------------------------------------------
# Mejora 5: Scrapers HTML Fundaciones Privadas + Dual RSS/Atom/HTML CCAA
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_private_foundation_html_monitors_and_multiformat_ccaa(monkeypatch):
    async def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)

        if "fundacionlacaixa.org" in url:
            html = """
            <html><body>
              <nav><a href="/aviso-legal">Aviso Legal y Cookies</a></nav>
              <article>
                <h3>Convocatoria Medio Ambiente 2026</h3>
                <p>Ayudas para restauración ecológica, bosques y prevención de incendios forestales en España.</p>
                <a href="/documents/bases-medioambiente-2026.pdf">Descargar bases de la convocatoria medioambiental 2026</a>
              </article>
            </body></html>
            """
            return httpx.Response(200, text=html, headers={"content-type": "text/html"})

        if "fundacionrepsol.com" in url:
            html = """
            <html><body>
              <section>
                <h2>Motor Verde Reforestación España</h2>
                <a href="/es/motor-verde/convocatoria-reforestacion-montes">Convocatoria abierta para proyectos de reforestación de grandes superficies quemadas y absorción de carbono</a>
              </section>
            </body></html>
            """
            return httpx.Response(200, text=html, headers={"content-type": "text/html"})

        if "bocm.es" in url and "rss.xml" not in url:
            html = """
            <html>
              <head><link rel="alternate" type="application/rss+xml" href="/rss.xml" /></head>
              <body>
                <ul>
                  <li><a href="/boletin/CM_Orden_1695_2026.pdf">Orden 1695/2026 de ayudas para repoblación forestal y cortafuegos en la Sierra Norte</a></li>
                </ul>
              </body>
            </html>
            """
            return httpx.Response(200, text=html, headers={"content-type": "text/html"})

        if "bocm.es/rss.xml" in url:
            atom = """<?xml version="1.0" encoding="UTF-8"?>
            <feed xmlns="http://www.w3.org/2005/Atom">
              <entry>
                <title>Resolución 99/2026 sobre biodiversidad forestal Red Natura 2000</title>
                <link href="https://www.bocm.es/boletin/Res_99_2026.html" />
                <summary>Subvenciones para entidades sin ánimo de lucro en Madrid.</summary>
              </entry>
            </feed>"""
            return httpx.Response(200, text=atom)

        return httpx.Response(503)

    transport = httpx.MockTransport(handler)
    real_cls = httpx.AsyncClient
    monkeypatch.setattr(live_connectors.httpx, "AsyncClient", lambda *a, **kw: real_cls(*a, **{**kw, "transport": transport}))

    priv_cands = await fetch_live_private_foundation_candidates()
    assert len(priv_cands) == 2
    caixa = next(c for c in priv_cands if "la Caixa" in c.organo_convocante)
    assert caixa.url_ficha_oficial == "https://fundacionlacaixa.org/documents/bases-medioambiente-2026.pdf"
    assert caixa.url_bases_reguladoras == caixa.url_ficha_oficial
    assert "cookies" not in " ".join(c.titulo.lower() for c in priv_cands)

    res_caixa = process_candidate(caixa, persist=False)
    assert res_caixa.accepted_layer2 is True
    assert res_caixa.opportunity is not None
    assert res_caixa.opportunity.nivel_territorial == "PRIVADA"
    assert res_caixa.opportunity.tipo_oportunidad == "CONVOCATORIA_PRIVADA"

    ccaa_cands = await fetch_live_ccaa_rss_candidates()
    titles = " | ".join(c.titulo for c in ccaa_cands)
    assert "Orden 1695/2026" in titles
    assert "Resolución 99/2026" in titles
