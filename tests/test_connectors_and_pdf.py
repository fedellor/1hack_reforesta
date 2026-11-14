"""Tests for Live Async Connectors (Mocked HTTP: BDNS, BOE, PLACSP CODICE, EU SEDIA, CCAA RSS) & PyMuPDF Parsing."""
import json
from datetime import date
import httpx
import pymupdf as fitz
import pytest
from fastapi.testclient import TestClient
from app.ingestors import live_connectors
from app.ingestors.fuentes_local import pdf_doc_to_candidate
from app.main import app
from app.pipeline.layer1_regex import evaluate_layer1
from app.pipeline.pdf_extractor import extract_pdf_from_bytes


@pytest.mark.asyncio
async def test_live_connectors_concurrent_parsing_and_codice_cpv(monkeypatch):
    """Mock httpx.AsyncClient to test BDNS, BOE, PLACSP State+Local CODICE XML, EU SEDIA & CCAA RSS parsers."""

    async def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)

        if "bdnstrans/api/convocatorias/busqueda" in url:
            return httpx.Response(
                200,
                json={
                    "content": [
                        {
                            "numeroConvocatoria": "940111",
                            "descripcion": "Ayudas para repoblación forestal y cortafuegos en Montes Vecinales",
                            "nivel1": "GALICIA",
                            "nivel2": "CONSELLERÍA DO MEDIO RURAL",
                            "presupuestoTotal": 3500000.0,
                            "fechaRegistro": "2026-11-10",
                            "fechaFinSolicitud": "2026-12-10",
                            "mrr": True,
                        }
                    ]
                },
            )

        if "boe.es/datosabiertos/api/boe/sumario" in url:
            return httpx.Response(
                200,
                json={
                    "data": {
                        "sumario": {
                            "diario": {
                                "seccion": [
                                    {
                                        "departamento": [
                                            {
                                                "nombre": "MINISTERIO PARA LA TRANSICIÓN ECOLÓGICA",
                                                "epigrafe": [
                                                    {
                                                        "item": [
                                                            {
                                                                "identificador": "BOE-A-2026-99001",
                                                                "titulo": "Extracto de Resolución para restauración de zonas incendiadas",
                                                                "url_pdf": {"texto": "/boe/dias/2026/11/10/pdfs/BOE-A-2026-99001.pdf"},
                                                                "url_html": "/diario_boe/txt.php?id=BOE-A-2026-99001",
                                                            }
                                                        ]
                                                    }
                                                ],
                                            }
                                        ]
                                    }
                                ]
                            }
                        }
                    }
                },
            )

        if "sindicacion_643" in url or "sindicacion_1044" in url:
            atom_xml = """<?xml version="1.0" encoding="UTF-8"?>
            <feed xmlns="http://www.w3.org/2005/Atom"
                  xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
                  xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
              <entry>
                <id>https://contrataciondelestado.es/sindicacion/licitaciones/EXP-2026-FOREST</id>
                <title>Servicio de trabajos silvícolas preventivos y fajas auxiliares</title>
                <summary>Actuaciones en monte público municipal.</summary>
                <updated>2026-11-11T10:00:00Z</updated>
                <link href="https://contrataciondelestado.es/wps/poc?EXP-2026-FOREST"/>
                <cac:ContractFolderStatus>
                  <cac:ContractingParty>
                    <cac:Party><cac:PartyName><cbc:Name>Concello de Pontevedra</cbc:Name></cac:PartyName></cac:Party>
                  </cac:ContractingParty>
                  <cac:ProcurementProject>
                    <cac:BudgetAmount><cbc:EstimatedOverallContractAmount>245000.50</cbc:EstimatedOverallContractAmount></cac:BudgetAmount>
                    <cac:RequiredCommodityClassification>
                      <cbc:ItemClassificationCode>77231600</cbc:ItemClassificationCode>
                    </cac:RequiredCommodityClassification>
                  </cac:ProcurementProject>
                  <cac:TenderingProcess>
                    <cac:TenderSubmissionDeadlinePeriod><cbc:EndDate>2026-12-05</cbc:EndDate></cac:TenderSubmissionDeadlinePeriod>
                  </cac:TenderingProcess>
                </cac:ContractFolderStatus>
              </entry>
            </feed>"""
            return httpx.Response(200, text=atom_xml)

        if "api.tech.ec.europa.eu" in url:
            return httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "metadata": {
                                "identifier": ["LIFE-2026-NAT-ES-FOREST"],
                                "title": ["Forest restoration and wildfire resilience in Iberian mountains"],
                                "descriptionByte": ["Grants for native reforestation"],
                                "startDate": ["2026-09-01T00:00:00"],
                                "deadlineDate": ["2026-12-20T17:00:00"],
                            }
                        }
                    ]
                },
            )

        if "UltimosDogs_gl.rss" in url:
            rss_xml = """<?xml version="1.0" encoding="UTF-8"?>
            <rss version="2.0"><channel><title>DOG</title>
              <item>
                <title>ORDE do 10 de novembro de 2026 de axudas para repoboación forestal con frondosas</title>
                <link>https://www.xunta.gal/dog/Publicados/2026/20261110/Anuncio1.html</link>
                <description>Subvencións para montes veciñais en man común en Galicia.</description>
              </item>
            </channel></rss>"""
            return httpx.Response(200, text=rss_xml)

        return httpx.Response(503)  # Simulate transient outage on other feeds (must be resilient!)

    transport = httpx.MockTransport(handler)
    real_client_cls = httpx.AsyncClient

    def mock_client_factory(*args, **kwargs):
        kwargs["transport"] = transport
        return real_client_cls(*args, **kwargs)

    monkeypatch.setattr(live_connectors.httpx, "AsyncClient", mock_client_factory)

    bdns = await live_connectors.fetch_live_bdns_candidates(keywords=["reforestacion", "forestal"])
    assert len(bdns) == 1  # Deduplicated across 2 queries!
    assert bdns[0].codigo_oficial == "BDNS-940111"
    assert bdns[0].cofinanciado_ue is True
    assert bdns[0].presupuesto_total == 3500000.0

    boe = await live_connectors.fetch_live_boe_candidates(days_back=2)
    assert len(boe) >= 1
    assert boe[0].codigo_oficial == "BOE-A-2026-99001"
    assert boe[0].url_bases_reguladoras == "https://www.boe.es/boe/dias/2026/11/10/pdfs/BOE-A-2026-99001.pdf"

    placsp = await live_connectors.fetch_live_placsp_candidates()
    assert len(placsp) == 1
    assert placsp[0].organo_convocante == "Concello de Pontevedra"
    assert "77231600" in placsp[0].cpv_codes
    assert placsp[0].presupuesto_total == 245000.50
    assert placsp[0].fecha_fin_solicitud == "2026-12-05"

    eu = await live_connectors.fetch_live_eu_sedia_candidates()
    assert len(eu) == 1
    assert eu[0].fondo_ue == "LIFE"
    assert eu[0].fecha_fin_solicitud == "2026-12-20"

    rss = await live_connectors.fetch_live_ccaa_rss_candidates()
    assert len(rss) == 1  # Survived 503 on the other 4 RSS feeds without raising!
    assert "frondosas" in rss[0].titulo.lower()


def _build_pdf_bytes(text_body: str) -> bytes:
    """Create a real in-memory PDF with PyMuPDF for end-to-end parser & upload testing."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_textbox(fitz.Rect(50, 50, 545, 780), text_body, fontsize=10)
    data = doc.tobytes()
    doc.close()
    return data


def test_pdf_extractor_multilingual_orders_and_tenders():
    # 1. Galician Bulletin Resolution with credit limit & 1-month deadline
    gl_pdf = _build_pdf_bytes(
        "Orde do 15 de maio de 2026 da Consellería do Medio Rural da Xunta de Galicia pola que se convocan "
        "axudas para repoboación forestal con frondosas autóctonas e prevención de lumes forestais en comunidades "
        "de montes veciñais en man común.\n"
        "Crédito presupuestario: 1.450.000,00 euros.\n"
        "Máximo por beneficiario: 45.000 euros.\n"
        "Intensidad máxima del 80%.\n"
        "Plazo de presentación de solicitudes: un mes.\n"
        "Publicación: 15/05/2026\n"
    )
    doc_gl = extract_pdf_from_bytes(gl_pdf, filename="dog-frondosas-2026.pdf")
    assert doc_gl.presupuesto_total == 1450000.0
    assert doc_gl.importe_max_entidad == 45000.0
    assert doc_gl.porcentaje_financiacion == 80.0
    assert "un mes" in (doc_gl.plazo_solicitud_texto or "").lower()

    cand_gl = pdf_doc_to_candidate(doc_gl)
    assert not cand_gl.id.startswith("bocm-")  # Non-Madrid orders must not get bocm- prefix!
    l1_gl = evaluate_layer1(cand_gl.titulo, cand_gl.texto, cand_gl.organo_convocante, cand_gl.cpv_codes)
    assert l1_gl.passed is True
    assert l1_gl.detected_language == "gl"

    # 2. Municipal Tender PDF detected ONLY via CPV code (75251120)
    tender_pdf = _build_pdf_bytes(
        "Expediente: LIC-2026-VIC-99\n"
        "Ajuntament de Vic\n"
        "Contrato de servicio de desbroce forestal i franges de protecció.\n"
        "Código CPV: 75251120-7.\n"
        "Valor estimado del contrato: 180.000 euros.\n"
        "En el plazo de 20 dies hàbils desde publicación.\n"
    )
    doc_tender = extract_pdf_from_bytes(tender_pdf, filename="pliego-vic.pdf")
    assert "75251120" in doc_tender.cpv_codes
    assert doc_tender.presupuesto_total == 180000.0
    cand_tender = pdf_doc_to_candidate(doc_tender)
    l1_t = evaluate_layer1(cand_tender.titulo, cand_tender.texto, cand_tender.organo_convocante, cand_tender.cpv_codes)
    assert l1_t.passed is True
    assert "prevencion_incendios" in l1_t.matched_categories


def test_upload_noise_pdf_rejected_cleanly():
    noise_pdf = _build_pdf_bytes(
        "Resolución para contratación de suministro de extintores portátiles y detección de incendios en edificio hospitalario.\n"
        "Presupuesto: 25.000 euros."
    )
    with TestClient(app) as client:
        resp = client.post(
            "/api/v1/analyze/pdf?guardar_en_bd=false",
            files={"file": ("hospital-extintores.pdf", noise_pdf, "application/pdf")},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["passed_layer1"] is False
        assert body["accepted_layer2"] is False
        assert body["opportunity"] is None
