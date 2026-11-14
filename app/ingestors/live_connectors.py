"""Live Async Connectors for Official Public & Private Sources: BDNS, PLACSP Atom, BOE, EU SEDIA, 19 CCAA Web/RSS & Private Foundations."""
import asyncio
from datetime import date, timedelta
import json
import logging
import ssl
from typing import Any
import xml.etree.ElementTree as ET
import httpx
from app.ingestors.web_monitors import (
    PRIVATE_FOUNDATION_SOURCES,
    enrich_candidate_from_linked_pdf,
    poll_web_source,
)
from app.pipeline.layer1_regex import evaluate_layer1
from app.pipeline.orchestrator import RawCandidate

logger = logging.getLogger(__name__)


def _is_specific_document_url(url: str | None) -> bool:
    """Return True only if URL links to a specific document/PDF/call rather than a generic homepage."""
    if not url or not url.strip().startswith(("http://", "https://")):
        return False
    low = url.strip().lower()
    if any(
        tok in low
        for tok in (
            ".pdf",
            "iddocumento=",
            "documentid=",
            "verobj",
            "descargararchivo",
            "referencia=",
            "txt.php?id=",
            "/eli/",
            "topic-details/",
            "/convocatoria/",
            "/api/v1/fuentes/",
        )
    ):
        return True
    from urllib.parse import urlparse

    parsed = urlparse(low)
    path = parsed.path.strip("/")
    return bool(path and path.count("/") >= 2 and not path.endswith(("convocatorias", "index.html", "index.htm", "boja", "portada", "bor-portada")))


def _extract_bdns_specific_pdf_url(det: dict[str, Any]) -> str | None:
    """Select the most relevant official downloadable PDF from BDNS `documentos` array."""
    docs = det.get("documentos") or []
    if not isinstance(docs, list) or not docs:
        return None
    ranked: list[tuple[int, int]] = []
    for doc in docs:
        if not isinstance(doc, dict):
            continue
        doc_id = doc.get("id")
        if doc_id is None:
            continue
        try:
            doc_id_int = int(doc_id)
        except (TypeError, ValueError):
            continue
        name = f"{doc.get('nombreFic') or ''} {doc.get('descripcion') or ''}".lower()
        score = 0
        if ".pdf" in name:
            score += 40
        if any(k in name for k in ("convocatoria", "resolucion", "resolución", "extracto", "bases", "orden", "decreto")):
            score += 30
        if any(k in name for k in ("cast", "_es.", " castellano")):
            score += 10
        if any(k in name for k in ("certificado", "nominativ", "anexo")):
            score -= 5
        ranked.append((score, doc_id_int))
    if not ranked:
        return None
    ranked.sort(key=lambda pair: pair[0], reverse=True)
    return f"https://www.infosubvenciones.es/bdnstrans/api/convocatorias/documentos?idDocumento={ranked[0][1]}"


def _build_ssl_context() -> ssl.SSLContext | bool:
    """Use native OS certificate store via truststore when available (fixes Windows/corporate CAs cleanly)."""
    try:
        import truststore  # type: ignore

        return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    except Exception:
        return True


_SSL_VERIFY = _build_ssl_context()


def _make_async_client(timeout: float, headers: dict[str, str] | None = None) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=timeout,
        headers=headers,
        verify=_SSL_VERIFY,
        follow_redirects=True,
    )

BDNS_SEARCH_URL = "https://www.pap.hacienda.gob.es/bdnstrans/api/convocatorias/busqueda"
BOE_SUMARIO_URL = "https://www.boe.es/datosabiertos/api/boe/sumario/{ymd}"
EU_SEDIA_SEARCH_URL = "https://api.tech.ec.europa.eu/search-api/prod/rest/search"
PLACSP_ATOM_STATE_URL = "https://contrataciondelestado.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3.atom"
PLACSP_ATOM_LOCAL_URL = "https://contrataciondelestado.es/sindicacion/sindicacion_1044/PlataformasAgregadasSinMenores.atom"

CCAA_RSS_FEEDS: list[dict[str, str]] = [
    {"id": "rss-dog", "ccaa": "ES-GA", "nombre": "DOG Galicia", "url": "https://www.xunta.gal/diario-oficial-galicia/rss/UltimosDogs_gl.rss"},
    {"id": "rss-boja", "ccaa": "ES-AN", "nombre": "BOJA Andalucía", "url": "https://www.juntadeandalucia.es/boja/distribucion/boja.xml"},
    {"id": "rss-dogc", "ccaa": "ES-CT", "nombre": "DOGC Catalunya", "url": "https://dogc.gencat.cat/es/el-dogc/rss/"},
    {"id": "rss-bocyl", "ccaa": "ES-CL", "nombre": "BOCYL Castilla y León", "url": "https://bocyl.jcyl.es/rss/ultimoboletin.xml"},
    {"id": "rss-bopa", "ccaa": "ES-AS", "nombre": "BOPA Asturias", "url": "https://sede.asturias.es/bopa-rss"},
    {"id": "web-bocm", "ccaa": "ES-MD", "nombre": "BOCM Madrid", "url": "https://www.bocm.es/"},
    {"id": "web-boa", "ccaa": "ES-AR", "nombre": "BOA Aragón", "url": "https://www.boa.aragon.es/"},
    {"id": "web-dogv", "ccaa": "ES-VC", "nombre": "DOGV Comunitat Valenciana", "url": "https://dogv.gva.es/"},
    {"id": "web-bopv", "ccaa": "ES-PV", "nombre": "BOPV País Vasco", "url": "https://www.euskadi.eus/bopv/"},
    {"id": "web-bon", "ccaa": "ES-NC", "nombre": "BON Navarra", "url": "https://bon.navarra.es/"},
    {"id": "web-borm", "ccaa": "ES-MC", "nombre": "BORM Región de Murcia", "url": "https://www.borm.es/"},
    {"id": "web-doe", "ccaa": "ES-EX", "nombre": "DOE Extremadura", "url": "https://doe.juntaex.es/"},
    {"id": "web-docm", "ccaa": "ES-CM", "nombre": "DOCM Castilla-La Mancha", "url": "https://docm.jccm.es/"},
    {"id": "web-boib", "ccaa": "ES-IB", "nombre": "BOIB Illes Balears", "url": "https://www.caib.es/eboibfront/"},
    {"id": "web-boc-cb", "ccaa": "ES-CB", "nombre": "BOC Cantabria", "url": "https://boc.cantabria.es/"},
    {"id": "web-boc-cn", "ccaa": "ES-CN", "nombre": "BOC Canarias", "url": "https://www.gobiernodecanarias.org/boc/"},
    {"id": "web-bor", "ccaa": "ES-RI", "nombre": "BOR La Rioja", "url": "https://web.larioja.org/bor-portada"},
    {"id": "web-bocce", "ccaa": "ES-CE", "nombre": "BOCCE Ceuta", "url": "https://www.ceuta.es/ceuta/bocce"},
    {"id": "web-bome", "ccaa": "ES-ML", "nombre": "BOME Melilla", "url": "https://bomemelilla.es/"},
]


# Official & Private Source Registry across all 6 levels (95+ sources)
SOURCES_REGISTRY: list[dict[str, Any]] = [
    # 1. EUROPEAN UNION
    {"id": "eu-sedia-portal", "nivel": "UE", "nombre": "Funding & Tenders Portal de la UE (SEDIA API)", "tipo": "API_REST", "url": "https://funding-and-tenders-portal.ec.europa.eu/", "idiomas": ["en", "es"]},
    {"id": "eu-cinea-life", "nivel": "UE", "nombre": "Programa LIFE - Comisión Europea (CINEA: Nature & Biodiversity / Climate)", "tipo": "API_REST", "url": "https://cinea.ec.europa.eu/life_en", "idiomas": ["en", "es"]},
    {"id": "eu-horizon-cl6", "nivel": "UE", "nombre": "Horizon Europe - Cluster 6 (Biodiversidad, Bosques y Misión Suelos)", "tipo": "API_REST", "url": "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/programmes/horizon", "idiomas": ["en"]},
    {"id": "eu-interreg-poctep", "nivel": "UE", "nombre": "Interreg VI-A España-Portugal (POCTEP)", "tipo": "PORTAL_UE", "url": "https://www.poctep.eu/", "idiomas": ["es", "en"]},
    {"id": "eu-interreg-sudoe", "nivel": "UE", "nombre": "Interreg SUDOE (Sudoeste Europeo - Prevención de Incendios y Montes)", "tipo": "PORTAL_UE", "url": "https://interreg-sudoe.eu/", "idiomas": ["es", "en"]},
    {"id": "eu-interreg-poctefa", "nivel": "UE", "nombre": "Interreg POCTEFA (Pirineos España-Francia-Andorra)", "tipo": "PORTAL_UE", "url": "https://www.poctefa.eu/", "idiomas": ["es", "ca", "eu", "en"]},
    # 2. STATE (ESPAÑA)
    {"id": "es-bdns-infosubvenciones", "nivel": "ESTADO", "nombre": "Base de Datos Nacional de Subvenciones (BDNS / SNPSAP - infosubvenciones.es)", "tipo": "API_REST", "url": "https://www.infosubvenciones.es/", "idiomas": ["es", "ca", "gl", "eu"]},
    {"id": "es-bdns-pap", "nivel": "ESTADO", "nombre": "Portal de Administración Presupuestaria BDNS API (pap.hacienda.gob.es)", "tipo": "API_REST", "url": "https://www.pap.hacienda.gob.es/bdnstrans/ge/es/convocatorias", "idiomas": ["es", "ca", "gl", "eu"]},
    {"id": "es-boe-api", "nivel": "ESTADO", "nombre": "BOE - Boletín Oficial del Estado (Buscador y API Datos Abiertos)", "tipo": "API_REST_XML_JSON", "url": "https://www.boe.es/", "idiomas": ["es"]},
    {"id": "es-miteco", "nivel": "ESTADO", "nombre": "MITECO - Ministerio para la Transición Ecológica y el Reto Demográfico", "tipo": "MINISTERIO", "url": "https://www.miteco.gob.es/", "idiomas": ["es"]},
    {"id": "es-fundacion-biodiversidad", "nivel": "ESTADO", "nombre": "Fundación Biodiversidad F.S.P. (MITECO)", "tipo": "FUNDACION_SECTOR_PUBLICO", "url": "https://www.fundacion-biodiversidad.es/", "idiomas": ["es"]},
    {"id": "es-placsp", "nivel": "ESTADO", "nombre": "PLACSP - Plataforma de Contratación del Sector Público (Licitaciones CPV Forestal/Incendios Estatal + Agregadas Locales)", "tipo": "ATOM_CODICE", "url": "https://contrataciondelestado.es/", "idiomas": ["es", "ca", "gl", "eu"]},
    # 3. 19 CCAA / CIUDADES AUTÓNOMAS
    {"id": "ccaa-boja", "nivel": "CCAA", "ccaa": "ES-AN", "nombre": "BOJA - Boletín Oficial de la Junta de Andalucía", "tipo": "BOLETIN_OFICIAL_RSS", "url": "https://www.juntadeandalucia.es/eboja.html", "idiomas": ["es"]},
    {"id": "ccaa-boa", "nivel": "CCAA", "ccaa": "ES-AR", "nombre": "BOA - Boletín Oficial de Aragón", "tipo": "BOLETIN_OFICIAL", "url": "https://www.boa.aragon.es/", "idiomas": ["es"]},
    {"id": "ccaa-bopa", "nivel": "CCAA", "ccaa": "ES-AS", "nombre": "BOPA - Boletín Oficial del Principado de Asturias", "tipo": "BOLETIN_OFICIAL_RSS", "url": "https://sede.asturias.es/bopa", "idiomas": ["es"]},
    {"id": "ccaa-boc-cantabria", "nivel": "CCAA", "ccaa": "ES-CB", "nombre": "BOC - Boletín Oficial de Cantabria", "tipo": "BOLETIN_OFICIAL", "url": "https://boc.cantabria.es/", "idiomas": ["es"]},
    {"id": "ccaa-bocce", "nivel": "CCAA", "ccaa": "ES-CE", "nombre": "BOCCE - Boletín Oficial de la Ciudad de Ceuta", "tipo": "BOLETIN_OFICIAL", "url": "https://www.ceuta.es/ceuta/bocce", "idiomas": ["es"]},
    {"id": "ccaa-bocyl", "nivel": "CCAA", "ccaa": "ES-CL", "nombre": "BOCYL - Boletín Oficial de Castilla y León", "tipo": "BOLETIN_OFICIAL_RSS", "url": "https://bocyl.jcyl.es/", "idiomas": ["es"]},
    {"id": "ccaa-docm", "nivel": "CCAA", "ccaa": "ES-CM", "nombre": "DOCM - Diario Oficial de Castilla-La Mancha", "tipo": "BOLETIN_OFICIAL", "url": "https://docm.jccm.es/", "idiomas": ["es"]},
    {"id": "ccaa-boc-canarias", "nivel": "CCAA", "ccaa": "ES-CN", "nombre": "BOC - Boletín Oficial de Canarias", "tipo": "BOLETIN_OFICIAL", "url": "https://www.gobiernodecanarias.org/boc/", "idiomas": ["es"]},
    {"id": "ccaa-dogc", "nivel": "CCAA", "ccaa": "ES-CT", "nombre": "DOGC - Diari Oficial de la Generalitat de Catalunya", "tipo": "BOLETIN_OFICIAL_RSS", "url": "https://dogc.gencat.cat/", "idiomas": ["ca", "es"]},
    {"id": "ccaa-doe", "nivel": "CCAA", "ccaa": "ES-EX", "nombre": "DOE - Diario Oficial de Extremadura", "tipo": "BOLETIN_OFICIAL", "url": "https://doe.juntaex.es/", "idiomas": ["es"]},
    {"id": "ccaa-dog", "nivel": "CCAA", "ccaa": "ES-GA", "nombre": "DOG - Diario Oficial de Galicia (Xunta de Galicia)", "tipo": "BOLETIN_OFICIAL_RSS", "url": "https://www.xunta.gal/diario-oficial-galicia", "idiomas": ["gl", "es"]},
    {"id": "ccaa-boib", "nivel": "CCAA", "ccaa": "ES-IB", "nombre": "BOIB - Butlletí Oficial de les Illes Balears", "tipo": "BOLETIN_OFICIAL", "url": "https://www.caib.es/eboibfront/", "idiomas": ["ca", "es"]},
    {"id": "ccaa-borm", "nivel": "CCAA", "ccaa": "ES-MC", "nombre": "BORM - Boletín Oficial de la Región de Murcia", "tipo": "BOLETIN_OFICIAL", "url": "https://www.borm.es/", "idiomas": ["es"]},
    {"id": "ccaa-bocm", "nivel": "CCAA", "ccaa": "ES-MD", "nombre": "BOCM - Boletín Oficial de la Comunidad de Madrid", "tipo": "BOLETIN_OFICIAL", "url": "https://www.bocm.es/", "idiomas": ["es"]},
    {"id": "ccaa-bome", "nivel": "CCAA", "ccaa": "ES-ML", "nombre": "BOME - Boletín Oficial de la Ciudad de Melilla", "tipo": "BOLETIN_OFICIAL", "url": "https://bomemelilla.es/", "idiomas": ["es"]},
    {"id": "ccaa-bon", "nivel": "CCAA", "ccaa": "ES-NC", "nombre": "BON - Boletín Oficial de Navarra", "tipo": "BOLETIN_OFICIAL", "url": "https://bon.navarra.es/", "idiomas": ["es", "eu"]},
    {"id": "ccaa-bopv", "nivel": "CCAA", "ccaa": "ES-PV", "nombre": "BOPV / EHAA - Boletín Oficial del País Vasco", "tipo": "BOLETIN_OFICIAL", "url": "https://www.euskadi.eus/bopv/", "idiomas": ["eu", "es"]},
    {"id": "ccaa-bor", "nivel": "CCAA", "ccaa": "ES-RI", "nombre": "BOR - Boletín Oficial de La Rioja", "tipo": "BOLETIN_OFICIAL", "url": "https://web.larioja.org/bor-portada", "idiomas": ["es"]},
    {"id": "ccaa-dogv", "nivel": "CCAA", "ccaa": "ES-VC", "nombre": "DOGV - Diari Oficial de la Generalitat Valenciana", "tipo": "BOLETIN_OFICIAL", "url": "https://dogv.gva.es/", "idiomas": ["ca", "es"]},
    # 4. PROVINCIAS (50 DIPUTACIONES, CABILDOS, CONSELLS & BOPs)
    {"id": "prov-bops-50", "nivel": "PROVINCIA", "nombre": "Red de los 50 Boletines Oficiales de la Provincia (BOPs), Diputaciones Forales, Cabildos y Consells Insulares", "tipo": "AGREGADOR_BDNS_BOP", "url": "https://www.infosubvenciones.es/", "idiomas": ["es", "ca", "gl", "eu"]},
    # 5. MUNICIPIOS (8.131 AYUNTAMIENTOS, CONCELLOS, AJUNTAMENTS, UDALAK)
    {"id": "muni-concellos-aytos", "nivel": "MUNICIPIO", "nombre": "Red Municipal de España (8.131 Ayuntamientos, Concellos, Ajuntaments, Udalak, Mancomunidades y Juntas Vecinales)", "tipo": "AGREGADOR_BDNS_PLACSP", "url": "https://www.infosubvenciones.es/", "idiomas": ["es", "ca", "gl", "eu"]},
    # 6. FUNDACIONES PRIVADAS Y PROGRAMAS DE RSC CON CONVOCATORIA PÚBLICA
    {"id": "priv-lacaixa", "nivel": "PRIVADA", "nombre": "Fundación ”la Caixa” - Convocatoria de Medio Ambiente y Acción Ambiental", "tipo": "FUNDACION_RSC", "url": "https://fundacionlacaixa.org/es/convocatorias-medioambiente", "idiomas": ["es", "ca"]},
    {"id": "priv-santander", "nivel": "PRIVADA", "nombre": "Fundación Banco Santander - Santander for the Seas & Recuperación de Patrimonio Natural", "tipo": "FUNDACION_RSC", "url": "https://www.fundacionbancosantander.com/es/accion-sostenible", "idiomas": ["es"]},
    {"id": "priv-bbva", "nivel": "PRIVADA", "nombre": "Fundación BBVA - Ayudas a Proyectos de Investigación en Ecología y Biología de la Conservación", "tipo": "FUNDACION_RSC", "url": "https://www.fbbva.es/ayudas/", "idiomas": ["es"]},
    {"id": "priv-motorverde-repsol", "nivel": "PRIVADA", "nombre": "Fundación Repsol & Grupo Sylvestris - Motor Verde (RSC e Inversión en Reforestación y Carbono)", "tipo": "PROGRAMA_RSC", "url": "https://www.fundacionrepsol.com/es/motor-verde/", "idiomas": ["es"]},
    {"id": "priv-iberdrola", "nivel": "PRIVADA", "nombre": "Fundación Iberdrola España - Programa de Biodiversidad y Plan Bosque Defensa", "tipo": "FUNDACION_RSC", "url": "https://www.fundacioniberdrolaespana.org/", "idiomas": ["es"]},
    {"id": "priv-endesa", "nivel": "PRIVADA", "nombre": "Fundación Endesa - Convocatorias de Biodiversidad, Renaturalización y Premios a la Ecoeficiencia", "tipo": "FUNDACION_RSC", "url": "https://www.fundacionendesa.org/es/biodiversidad", "idiomas": ["es"]},
    {"id": "priv-naturgy", "nivel": "PRIVADA", "nombre": "Fundación Naturgy - Premios y Ayudas a Iniciativas Sociales y Ambientales", "tipo": "FUNDACION_RSC", "url": "https://www.fundacionnaturgy.org/", "idiomas": ["es"]},
    {"id": "priv-abanca-afundacion", "nivel": "PRIVADA", "nombre": "Obra Social ABANCA / Afundación - Programas PlanctON y Rebrote de Reforestación Autóctona", "tipo": "FUNDACION_RSC", "url": "https://www.afundacion.org/", "idiomas": ["es", "gl"]},
    {"id": "priv-cajacanarias", "nivel": "PRIVADA", "nombre": "Fundación CajaCanarias - Convocatoria de Ayudas a Proyectos Medioambientales", "tipo": "FUNDACION_RSC", "url": "https://www.cajacanarias.com/", "idiomas": ["es"]},
    {"id": "priv-cajaburgos", "nivel": "PRIVADA", "nombre": "Fundación Caja de Burgos & Fundación Gutiérrez Manrique - Ayudas de Medio Ambiente y Montes", "tipo": "FUNDACION_RSC", "url": "https://www.cajadeburgos.com/", "idiomas": ["es"]},
    {"id": "priv-tatiana", "nivel": "PRIVADA", "nombre": "Fundación Tatiana Pérez de Guzmán el Bueno - Ayudas a Proyectos de Medio Ambiente y Custodia", "tipo": "FUNDACION_RSC", "url": "https://fundaciontatianapgb.org/", "idiomas": ["es"]},
    {"id": "priv-eoca", "nivel": "PRIVADA", "nombre": "EOCA (European Outdoor Conservation Association) - Conservation & Reforestation Grants", "tipo": "PROGRAMA_RSC_INT", "url": "https://www.outdoorconservation.eu/", "idiomas": ["en"]},
    {"id": "priv-onetreeplanted", "nivel": "PRIVADA", "nombre": "One Tree Planted & 1% for the Planet - Corporate RSC Reforestation Partners in Spain", "tipo": "PROGRAMA_RSC_INT", "url": "https://onetreeplanted.org/", "idiomas": ["en", "es"]},
    {"id": "priv-bosques-sostenibles-retree", "nivel": "PRIVADA", "nombre": "Bosques Sostenibles & ReTree - Programas Corporativos de RSC para Reforestación y Huella de Carbono", "tipo": "PROGRAMA_RSC", "url": "https://www.bosquessostenibles.com/", "idiomas": ["es"]},
]


async def fetch_live_bdns_candidates(
    keywords: list[str] | None = None,
    max_per_keyword: int = 20,
    timeout: float = 6.0,
) -> list[RawCandidate]:
    """
    Query the official BDNS / SNPSAP API concurrently across 16 forestry/biodiversity terms
    spanning State, CCAA, Diputaciones, Concellos, Ayuntamientos and Ajuntaments.
    """
    search_terms = keywords or [
        "reforestación",
        "repoblación",
        "silvícola",
        "silvicultura",
        "forestal",
        "incendios forestales",
        "montes",
        "restauración forestal",
        "biodiversidad",
        "natura 2000",
        "arbolado",
        "custodia del territorio",
    ]
    candidates: list[RawCandidate] = []
    seen_codes: set[str] = set()
    # Gentle concurrency (<=3) avoids HTTP 429 rate-limits on infosubvenciones.es during batch detail enrichment
    sem = asyncio.Semaphore(3)
    recent_desde = (date.today() - timedelta(days=240)).strftime("%d/%m/%Y")

    headers = {
        "Accept": "application/json",
        "User-Agent": "1hack_reforesta/2.0 (Radar Vivo de Oportunidades Forestales)",
    }

    async def _get_json_with_retry(
        client: httpx.AsyncClient,
        url: str,
        params: dict[str, str],
        attempts: int = 3,
    ) -> Any:
        for attempt in range(attempts):
            async with sem:
                try:
                    await asyncio.sleep(0.08 * (attempt + 1))
                    resp = await client.get(url, params=params)
                    if resp.status_code == 200:
                        return resp.json()
                    if resp.status_code not in (429, 500, 502, 503, 504):
                        return None
                except Exception as exc:
                    if attempt == attempts - 1:
                        logger.debug("BDNS GET failed after %d attempts (%s): %s", attempts, url, exc)
                        return None
            await asyncio.sleep(0.75 * (attempt + 1))
        return None

    async def _query_term(client: httpx.AsyncClient, term: str, only_open: bool = False) -> list[dict[str, Any]]:
        try:
            params = {
                "vpd": "GE",
                "descripcion": term,
                "descripcionTipoBusqueda": "1",
                "page": "0",
                "pageSize": str(max_per_keyword),
            }
            if only_open:
                params["abierto"] = "true"
            else:
                params["fechaDesde"] = recent_desde
            data = await _get_json_with_retry(client, BDNS_SEARCH_URL, params=params, attempts=3)
            if not data:
                return []
            return (
                data.get("content")
                or data.get("datos")
                or (data if isinstance(data, list) else [])
            )
        except Exception as exc:
            logger.debug("BDNS live query for '%s' skipped: %s", term, exc)
            return []

    async def _enrich_bdns_detail(client: httpx.AsyncClient, cand: RawCandidate, num_conv: str) -> None:
        if cand.presupuesto_total is not None and cand.fecha_fin_solicitud is not None and cand.url_bases_reguladoras:
            return
        try:
            det = await _get_json_with_retry(
                client,
                "https://www.infosubvenciones.es/bdnstrans/api/convocatorias",
                params={"numConv": num_conv, "vpd": "GE"},
                attempts=3,
            )
            if not isinstance(det, dict):
                return
            if cand.presupuesto_total is None and det.get("presupuestoTotal") is not None:
                try:
                    cand.presupuesto_total = float(det["presupuestoTotal"])
                except (TypeError, ValueError):
                    pass
            if not cand.fecha_inicio_solicitud and det.get("fechaInicioSolicitud"):
                cand.fecha_inicio_solicitud = str(det["fechaInicioSolicitud"])[:10]
            if not cand.fecha_fin_solicitud and det.get("fechaFinSolicitud"):
                cand.fecha_fin_solicitud = str(det["fechaFinSolicitud"])[:10]
            raw_text_fin = str(det.get("textFin") or "").strip()
            if raw_text_fin and raw_text_fin not in (".", "None"):
                import re as _re

                if not cand.fecha_fin_solicitud:
                    m_dmy = _re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", raw_text_fin)
                    if m_dmy:
                        cand.fecha_fin_solicitud = f"{m_dmy.group(3)}-{m_dmy.group(2)}-{m_dmy.group(1)}"
                if not cand.plazo_texto_original:
                    norm_fin = (
                        _re.sub(r"\b0?(\d+)\s+Mesos\b", r"\1 mes", raw_text_fin, flags=_re.IGNORECASE)
                        if "mesos" in raw_text_fin.lower()
                        else raw_text_fin
                    )
                    cand.plazo_texto_original = norm_fin[:240]

            regiones = det.get("regiones") or []
            if isinstance(regiones, list) and regiones:
                reg_desc = " | ".join(
                    str(r.get("descripcion") or "") for r in regiones if isinstance(r, dict)
                ).strip()
                if reg_desc:
                    cand.region_hint = f"{reg_desc} - {cand.region_hint}".strip(" -")
                    for r in regiones:
                        desc_r = str(r.get("descripcion") or "") if isinstance(r, dict) else ""
                        if desc_r.startswith("ES") and len(desc_r) >= 4 and desc_r[2:4].isdigit():
                            cand.nuts_code = desc_r[:4]
                            break

            benefs = det.get("tiposBeneficiarios") or []
            if isinstance(benefs, list) and benefs and not cand.beneficiarios_hint:
                cand.beneficiarios_hint = ", ".join(
                    str(b.get("descripcion") or "") for b in benefs if isinstance(b, dict)
                )
            fondos = det.get("fondos") or []
            if isinstance(fondos, list) and fondos:
                cand.cofinanciado_ue = True
                if not cand.fondo_ue:
                    cand.fondo_ue = ", ".join(
                        str(f.get("descripcion") or "") for f in fondos if isinstance(f, dict)
                    )[:120]

            # Prioritize direct downloadable BDNS call PDF (`idDocumento`), then specific official bases URL
            specific_pdf_url = _extract_bdns_specific_pdf_url(det)
            raw_bases_url = str(det.get("urlBasesReguladoras") or "").strip()
            if specific_pdf_url:
                cand.url_bases_reguladoras = specific_pdf_url
                if _is_specific_document_url(raw_bases_url) and not cand.url_boletin_extracto:
                    cand.url_boletin_extracto = raw_bases_url
            elif _is_specific_document_url(raw_bases_url):
                cand.url_bases_reguladoras = raw_bases_url

            for anuncio in det.get("anuncios") or []:
                if isinstance(anuncio, dict):
                    an_url = str(anuncio.get("url") or "").strip()
                    if _is_specific_document_url(an_url) and not cand.url_boletin_extracto:
                        cand.url_boletin_extracto = an_url
                        break

            if not cand.url_tramitacion and det.get("sedeElectronica"):
                cand.url_tramitacion = str(det["sedeElectronica"])
            extra_txt_parts = [
                str(det.get("descripcionFinalidad") or ""),
                str(det.get("descripcionBasesReguladoras") or ""),
                str(det.get("textFin") or ""),
            ]
            extra_txt = ". ".join(p.strip() for p in extra_txt_parts if p.strip())
            if extra_txt:
                cand.texto = f"{cand.texto} {extra_txt}".strip()
        except Exception as exc:
            logger.debug("BDNS detail enrichment for '%s' skipped: %s", num_conv, exc)

    async with _make_async_client(timeout=timeout, headers=headers) as client:
        queries = [_query_term(client, t, only_open=False) for t in search_terms] + [
            _query_term(client, t, only_open=True) for t in search_terms[:6]
        ]
        results_lists = await asyncio.gather(*queries)

        to_enrich: list[tuple[RawCandidate, str]] = []
        for items in results_lists:
            for item in items:
                num_conv = str(
                    item.get("numeroConvocatoria")
                    or item.get("codigoBDNS")
                    or item.get("codBdns")
                    or item.get("id")
                    or ""
                ).strip()
                if not num_conv or num_conv in seen_codes:
                    continue
                seen_codes.add(num_conv)

                titulo = str(item.get("descripcion") or item.get("titulo") or "").strip()
                organo_obj = item.get("organo") if isinstance(item.get("organo"), dict) else {}
                organo = " - ".join(
                    filter(
                        None,
                        [
                            item.get("nivel1") or organo_obj.get("nivel1"),
                            item.get("nivel2") or organo_obj.get("nivel2"),
                            item.get("nivel3") or organo_obj.get("nivel3"),
                        ],
                    )
                )
                region_str = " - ".join(
                    filter(
                        None,
                        [
                            str(item.get("nivel2") or ""),
                            str(item.get("nivel3") or ""),
                            str(item.get("nivel1") or item.get("region") or ""),
                        ],
                    )
                )
                f_rec = item.get("fechaRecepcion") or item.get("fechaRegistro")
                presupuesto = item.get("presupuestoTotal") or item.get("importeTotal") or item.get("importe")
                try:
                    pres_float = float(presupuesto) if presupuesto is not None else None
                except (TypeError, ValueError):
                    pres_float = None

                mrr_flag = bool(item.get("mrr"))
                cand = RawCandidate(
                    id=f"bdns-{num_conv}",
                    codigo_oficial=f"BDNS-{num_conv}",
                    fuente="BDNS",
                    tipo_oportunidad="SUBVENCION",
                    titulo=titulo,
                    organo_convocante=organo or "Administración Pública (BDNS)",
                    texto=f"{titulo}. Órgano: {organo}.",
                    region_hint=region_str,
                    presupuesto_total=pres_float,
                    cofinanciado_ue=mrr_flag,
                    fondo_ue="NextGenerationEU / PRTR" if mrr_flag else None,
                    fecha_publicacion=f_rec,
                    fecha_inicio_solicitud=item.get("fechaInicioSolicitud"),
                    fecha_fin_solicitud=item.get("fechaFinSolicitud"),
                    url_ficha_oficial=f"https://www.infosubvenciones.es/bdnstrans/GE/es/convocatoria/{num_conv}",
                )
                candidates.append(cand)
                l1_pre = evaluate_layer1(titulo=titulo, texto=cand.texto, organo=organo)
                if l1_pre.passed:
                    to_enrich.append((cand, num_conv))

        if to_enrich:
            # Sort newest BDNS IDs first so 2026 active calls always get priority detail & PDF enrichment
            to_enrich.sort(
                key=lambda pair: int(pair[1]) if pair[1].isdigit() else 0,
                reverse=True,
            )
            await asyncio.gather(*[_enrich_bdns_detail(client, c, n) for c, n in to_enrich[:120]])

    return candidates


async def fetch_live_boe_candidates(
    days_back: int = 7,
    timeout: float = 6.0,
) -> list[RawCandidate]:
    """Query the official BOE Open Data API (datosabiertos) concurrently across recent daily summaries."""
    candidates: list[RawCandidate] = []
    seen_ids: set[str] = set()
    headers = {"Accept": "application/json", "User-Agent": "1hack_reforesta/2.0"}
    today = date.today()
    sem = asyncio.Semaphore(5)

    def _abs_boe_url(raw_url: str) -> str:
        u = raw_url.strip()
        if u.startswith("/"):
            return f"https://www.boe.es{u}"
        return u

    async def _fetch_day(client: httpx.AsyncClient, target_date: date) -> list[RawCandidate]:
        if target_date.weekday() == 6:
            return []
        ymd = target_date.strftime("%Y%m%d")
        day_items: list[RawCandidate] = []
        async with sem:
            try:
                resp = await client.get(BOE_SUMARIO_URL.format(ymd=ymd))
                if resp.status_code != 200:
                    return []
                payload = resp.json()
                sumario = payload.get("data", {}).get("sumario", {})
                diario_list = sumario.get("diario", [])
                if isinstance(diario_list, dict):
                    diario_list = [diario_list]

                for diario in diario_list:
                    secciones = diario.get("seccion", [])
                    if isinstance(secciones, dict):
                        secciones = [secciones]
                    for sec in secciones:
                        dept_list = sec.get("departamento", [])
                        if isinstance(dept_list, dict):
                            dept_list = [dept_list]
                        for dept in dept_list:
                            dept_name = dept.get("nombre", "")
                            epigrafes = dept.get("epigrafe", [])
                            if isinstance(epigrafes, dict):
                                epigrafes = [epigrafes]
                            items = list(epigrafes)
                            if "item" in dept:
                                items.append({"item": dept["item"]})
                            for ep in items:
                                sub_items = ep.get("item", [])
                                if isinstance(sub_items, dict):
                                    sub_items = [sub_items]
                                for it in sub_items:
                                    ident = str(it.get("identificador", "")).strip()
                                    titulo = str(it.get("titulo", "")).strip()
                                    if not ident or not titulo:
                                        continue
                                    url_pdf_obj = it.get("url_pdf", {})
                                    url_pdf_raw = (
                                        url_pdf_obj.get("texto", "")
                                        if isinstance(url_pdf_obj, dict)
                                        else str(url_pdf_obj or "")
                                    )
                                    url_html_raw = str(it.get("url_html", "") or "")
                                    day_items.append(
                                        RawCandidate(
                                            id=f"boe-{ident.lower()}",
                                            codigo_oficial=ident,
                                            fuente="BOE",
                                            tipo_oportunidad="SUBVENCION",
                                            titulo=titulo,
                                            organo_convocante=dept_name,
                                            texto=f"{titulo} ({dept_name})",
                                            fecha_publicacion=target_date,
                                            anio_convocatoria=target_date.year,
                                            url_ficha_oficial=_abs_boe_url(url_html_raw) or f"https://www.boe.es/diario_boe/txt.php?id={ident}",
                                            url_bases_reguladoras=_abs_boe_url(url_pdf_raw) if url_pdf_raw else None,
                                        )
                                    )
            except Exception as exc:
                logger.debug("BOE live summary for %s skipped: %s", ymd, exc)
        return day_items

    async with _make_async_client(timeout=timeout, headers=headers) as client:
        batches = await asyncio.gather(
            *[_fetch_day(client, today - timedelta(days=offset)) for offset in range(days_back)]
        )

    for batch in batches:
        for cand in batch:
            if cand.id not in seen_ids:
                seen_ids.add(cand.id)
                candidates.append(cand)

    return candidates


async def fetch_live_eu_sedia_candidates(
    timeout: float = 6.0,
) -> list[RawCandidate]:
    """
    Query the European Commission Funding & Tenders Portal (SEDIA Search POST API) concurrently
    for open and forthcoming EU calls (LIFE, Horizon Europe, Interreg, EMFAF) in ES/EN.
    """
    candidates_by_id: dict[str, RawCandidate] = {}
    queries = [
        "reforestation OR afforestation OR tree planting OR forest restoration",
        "wildfire OR forest fire OR post-fire restoration OR silviculture",
        "LIFE Nature OR habitat restoration OR riparian restoration OR urban greening",
        "agroforestry OR carbon sink OR carbon farming OR Natura 2000",
        "Interreg OR Iberian OR dehesa OR forest management",
    ]
    sem = asyncio.Semaphore(5)
    query_blob = json.dumps(
        {
            "bool": {
                "must": [
                    {"terms": {"type": ["1", "2"]}},
                    {"terms": {"status": ["31094501", "31094502"]}},
                ]
            }
        }
    )
    languages_blob = json.dumps(["en", "es"])

    def _parse_sedia_budget_overview(
        meta: dict[str, Any],
        ident: str,
    ) -> tuple[float | None, float | None, str | None, str | None, str]:
        """Extract topic budget, max contribution per grant, dates and action type from SEDIA budgetOverview JSON."""
        raw_list = meta.get("budgetOverview") or []
        if not raw_list or not isinstance(raw_list, list):
            return None, None, None, None, ""
        try:
            b_obj = json.loads(str(raw_list[0]))
            topic_map = b_obj.get("budgetTopicActionMap") or {}
            chosen_entry: dict[str, Any] | None = None
            id_up = ident.upper()
            for entries in topic_map.values():
                if not isinstance(entries, list):
                    continue
                for entry in entries:
                    if not isinstance(entry, dict):
                        continue
                    act_str = str(entry.get("action") or "").upper()
                    if id_up in act_str:
                        chosen_entry = entry
                        break
                if chosen_entry:
                    break
            if not chosen_entry:
                return None, None, None, None, ""

            year_map = chosen_entry.get("budgetYearMap") or {}
            total_b = sum(float(v) for v in year_map.values() if str(v).replace(".", "").isdigit())
            pres_total = total_b if total_b > 0 else None
            max_contrib = chosen_entry.get("maxContribution")
            max_proy = float(max_contrib) if max_contrib and float(max_contrib) > 0 else None
            open_d = str(chosen_entry.get("plannedOpeningDate") or "")[:10] or None
            d_dates = chosen_entry.get("deadlineDates") or []
            end_d = str(d_dates[0])[:10] if d_dates else None
            act_type = str(chosen_entry.get("action") or "")
            return pres_total, max_proy, open_d, end_d, act_type
        except Exception:
            return None, None, None, None, ""

    async def _query_sedia(client: httpx.AsyncClient, q: str) -> list[RawCandidate]:
        batch: list[RawCandidate] = []
        async with sem:
            try:
                params = {
                    "apiKey": "SEDIA",
                    "text": q,
                    "pageSize": "15",
                    "pageNumber": "1",
                }
                files = {
                    "query": ("blob", query_blob, "application/json"),
                    "languages": ("blob", languages_blob, "application/json"),
                }
                resp = await client.post(EU_SEDIA_SEARCH_URL, params=params, files=files)
                if resp.status_code != 200:
                    return []
                data = resp.json()
                for r in data.get("results", []):
                    meta = r.get("metadata", {})
                    status_vals = {str(s) for s in (meta.get("status") or [])}
                    if status_vals == {"31094503"}:  # Closed topic
                        continue
                    langs = [str(l).lower() for l in (meta.get("language") or [])]
                    if langs and "en" not in langs and "es" not in langs:
                        continue
                    ident_list = (
                        meta.get("identifier")
                        or meta.get("callIdentifier")
                        or ([r.get("reference")] if r.get("reference") else [])
                    )
                    ident = str(ident_list[0]).strip() if ident_list else ""
                    title_list = meta.get("title") or ([r.get("summary")] if r.get("summary") else [])
                    title = str(title_list[0]).strip() if title_list else ""
                    if not ident or not title:
                        continue
                    desc_list = meta.get("descriptionByte") or meta.get("callTitle") or []
                    desc = " ".join(str(x) for x in desc_list)
                    deadline_list = meta.get("deadlineDate", [])
                    deadline_raw = str(deadline_list[0])[:10] if deadline_list else None
                    start_list = meta.get("startDate", [])
                    start_raw = str(start_list[0])[:10] if start_list else None

                    pres_b, max_proy_b, open_b, end_b, act_type = _parse_sedia_budget_overview(meta, ident)
                    resolved_deadline = end_b or deadline_raw
                    if resolved_deadline and resolved_deadline < date.today().isoformat():
                        continue
                    types_of_action = " ".join(str(x) for x in (meta.get("typesOfAction") or []))
                    action_info = f"{act_type} {types_of_action}".strip()

                    id_up = ident.upper()
                    if "LIFE" in id_up:
                        fondo = "LIFE"
                    elif "INTERREG" in id_up:
                        fondo = "Interreg / FEDER"
                    elif "EMFAF" in id_up:
                        fondo = "EMFAF"
                    else:
                        fondo = "Horizon Europe"

                    topic_url = f"https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/{ident}"
                    batch.append(
                        RawCandidate(
                            id=f"eu-{ident.lower().replace('_', '-')}",
                            codigo_oficial=ident,
                            fuente="EU_SEDIA",
                            tipo_oportunidad="PROGRAMA_UE",
                            titulo=title,
                            organo_convocante="European Commission - CINEA / REA (EU Funding & Tenders)",
                            texto=f"{title}. {desc}. {action_info}".strip(),
                            region_hint="Unión Europea (Aplicable en España)",
                            nuts_code="EU",
                            presupuesto_total=pres_b,
                            importe_max_proyecto=max_proy_b,
                            cofinanciado_ue=True,
                            fondo_ue=fondo,
                            fecha_publicacion=open_b or start_raw,
                            fecha_inicio_solicitud=open_b or start_raw,
                            fecha_fin_solicitud=resolved_deadline,
                            url_ficha_oficial=topic_url,
                            url_bases_reguladoras=topic_url,
                        )
                    )
            except Exception as exc:
                logger.debug("EU SEDIA live query for '%s' skipped: %s", q, exc)
        return batch

    async with _make_async_client(timeout=timeout, headers={"User-Agent": "1hack_reforesta/2.0"}) as client:
        batches = await asyncio.gather(*[_query_sedia(client, q) for q in queries])

    for batch in batches:
        for cand in batch:
            prev = candidates_by_id.get(cand.id)
            if prev is None or len(cand.texto) > len(prev.texto):
                candidates_by_id[cand.id] = cand

    return list(candidates_by_id.values())


def _parse_codice_entry_metadata(entry: ET.Element) -> tuple[list[str], str | None, float | None, str | None]:
    """
    Namespace-agnostic extraction of CODICE fields embedded inside a PLACSP Atom <entry>:
    - CPV codes (<cbc:ItemClassificationCode>)
    - Contracting party name (<cac:ContractingParty>...<cbc:Name>)
    - Estimated contract amount (<cbc:EstimatedOverallContractAmount> / <cbc:TaxExclusiveAmount>)
    - Tender submission deadline (<cac:TenderSubmissionDeadlinePeriod>/<cbc:EndDate>)
    """
    cpvs: list[str] = []
    organo: str | None = None
    budget: float | None = None
    deadline: str | None = None

    def _local(tag: str) -> str:
        return tag.split("}", 1)[-1] if "}" in tag else tag

    for elem in entry.iter():
        lname = _local(elem.tag)
        txt = (elem.text or "").strip()
        if lname == "ItemClassificationCode" and txt:
            cpvs.append(txt)
        elif lname in ("EstimatedOverallContractAmount", "TotalAmount", "TaxExclusiveAmount") and txt and budget is None:
            try:
                val = float(txt)
                if val > 0:
                    budget = val
            except ValueError:
                pass
        elif lname == "ContractingParty" and organo is None:
            for sub in elem.iter():
                if _local(sub.tag) == "Name" and (sub.text or "").strip():
                    organo = sub.text.strip()
                    break
        elif lname == "TenderSubmissionDeadlinePeriod" and deadline is None:
            for sub in elem.iter():
                if _local(sub.tag) == "EndDate" and (sub.text or "").strip():
                    deadline = sub.text.strip()[:10]
                    break

    return sorted(set(cpvs)), organo, budget, deadline


async def fetch_live_placsp_candidates(timeout: float = 6.0) -> list[RawCandidate]:
    """
    Query BOTH official PLACSP Atom Syndication Feeds concurrently:
    1. State Sector (`sindicacion_643`)
    2. Regional, Provincial, Diputaciones & Municipal Agregadas (`sindicacion_1044`)
    Extracts embedded CODICE CPV codes, budgets, contracting authority & submission deadlines.
    """
    candidates: list[RawCandidate] = []
    seen_ids: set[str] = set()
    headers = {"User-Agent": "1hack_reforesta/2.0"}

    async def _fetch_feed(client: httpx.AsyncClient, url: str) -> list[RawCandidate]:
        items: list[RawCandidate] = []
        try:
            resp = await client.get(url)
            if resp.status_code != 200:
                return []
            root = ET.fromstring(resp.text)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            for entry in root.findall("atom:entry", ns)[:80]:
                entry_id = entry.findtext("atom:id", default="", namespaces=ns).strip()
                title = entry.findtext("atom:title", default="", namespaces=ns).strip()
                summary = entry.findtext("atom:summary", default="", namespaces=ns).strip()
                updated = entry.findtext("atom:updated", default="", namespaces=ns)[:10]
                link_el = entry.find("atom:link", ns)
                href = link_el.attrib.get("href", "") if link_el is not None else entry_id
                if not title:
                    continue

                cpvs, organo_codice, budget_codice, deadline_codice = _parse_codice_entry_metadata(entry)
                short_id = entry_id.split("/")[-1] if "/" in entry_id else str(abs(hash(title)) % 1000000)
                items.append(
                    RawCandidate(
                        id=f"placsp-{short_id.lower()}",
                        codigo_oficial=f"PLACSP-{short_id}",
                        fuente="PLACSP",
                        tipo_oportunidad="LICITACION",
                        titulo=title,
                        organo_convocante=organo_codice or "Contratación del Sector Público (PLACSP)",
                        texto=f"{title}. {summary}",
                        cpv_codes=cpvs,
                        presupuesto_total=budget_codice,
                        fecha_publicacion=updated or date.today(),
                        fecha_fin_solicitud=deadline_codice,
                        url_ficha_oficial=href,
                    )
                )
        except Exception as exc:
            logger.debug("PLACSP Atom live feed '%s' skipped: %s", url, exc)
        return items

    async with _make_async_client(timeout=timeout, headers=headers) as client:
        batches = await asyncio.gather(
            _fetch_feed(client, PLACSP_ATOM_STATE_URL),
            _fetch_feed(client, PLACSP_ATOM_LOCAL_URL),
        )

    for batch in batches:
        for cand in batch:
            if cand.id not in seen_ids:
                seen_ids.add(cand.id)
                candidates.append(cand)

    return candidates


async def _gather_web_monitors(
    sources: list[dict[str, str]],
    timeout: float,
    user_agent: str,
    max_concurrency: int = 8,
) -> list[RawCandidate]:
    """Shared concurrent runner for RSS/Atom/HTML bulletin and foundation monitors."""
    candidates: list[RawCandidate] = []
    seen_ids: set[str] = set()
    sem = asyncio.Semaphore(max_concurrency)
    headers = {"User-Agent": user_agent}

    async def _run_one(client: httpx.AsyncClient, cfg: dict[str, str]) -> list[RawCandidate]:
        async with sem:
            batch = await poll_web_source(client, cfg)
            for item in batch:
                if item.fecha_publicacion is None:
                    item.fecha_publicacion = date.today()
            return batch

    async with _make_async_client(timeout=timeout, headers=headers) as client:
        batches = await asyncio.gather(*[_run_one(client, s) for s in sources])

    for batch in batches:
        for cand in batch:
            if cand.id not in seen_ids:
                seen_ids.add(cand.id)
                candidates.append(cand)
    return candidates


async def fetch_live_ccaa_rss_candidates(timeout: float = 4.0) -> list[RawCandidate]:
    """
    Poll all 19 Spanish CCAA & Autonomous City official bulletins (RSS, Atom, or HTML portals
    with automatic <link rel='alternate' type='application/rss+xml'> discovery).
    """
    return await _gather_web_monitors(
        sources=CCAA_RSS_FEEDS,
        timeout=timeout,
        user_agent="1hack_reforesta/2.0 (CCAA Bulletin Monitor)",
        max_concurrency=8,
    )


async def fetch_live_private_foundation_candidates(timeout: float = 5.0) -> list[RawCandidate]:
    """
    Poll official web portals of private foundations and RSC conservation programs without APIs
    (Fundación la Caixa, Motor Verde Repsol, Santander, BBVA, Biodiversidad, Iberdrola, EOCA, etc.).
    """
    return await _gather_web_monitors(
        sources=PRIVATE_FOUNDATION_SOURCES,
        timeout=timeout,
        user_agent="1hack_reforesta/2.0 (Private RSC Monitor)",
        max_concurrency=6,
    )


async def enrich_candidates_with_linked_pdfs(
    candidates: list[RawCandidate],
    timeout: float = 5.0,
    max_downloads: int = 15,
    api_key_override: str | None = None,
) -> int:
    """
    Follow linked PDFs for sparse extract candidates (< 900 chars) concurrently, extract full
    text + CPVs + budgets + deadlines (with OCR fallback), and return the count of enriched records.
    """
    targets: list[RawCandidate] = []
    for cand in candidates:
        if len(targets) >= max_downloads:
            break
        if cand.fuente != "FUENTES_PDF" and len(cand.texto or "") < 900 and (
            cand.url_bases_reguladoras
            or cand.url_boletin_extracto
            or (cand.url_ficha_oficial and ".pdf" in cand.url_ficha_oficial.lower())
        ):
            targets.append(cand)

    if not targets:
        return 0

    sem = asyncio.Semaphore(5)
    headers = {"User-Agent": "1hack_reforesta/2.0 (PDF Extract Enricher)"}

    async def _enrich_one(client: httpx.AsyncClient, cand: RawCandidate) -> bool:
        async with sem:
            return await enrich_candidate_from_linked_pdf(
                client,
                cand,
                api_key_override=api_key_override,
            )

    async with _make_async_client(timeout=timeout, headers=headers) as client:
        results = await asyncio.gather(*[_enrich_one(client, c) for c in targets])

    return sum(1 for r in results if r)
