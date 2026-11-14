"""Live Async Connectors for Official Public & Private Sources: BDNS, PLACSP Atom, BOE, EU SEDIA & Foundations."""
import logging
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from typing import Any
import httpx
from app.pipeline.orchestrator import RawCandidate

logger = logging.getLogger(__name__)

BDNS_SEARCH_URL = "https://www.pap.hacienda.gob.es/bdnstrans/api/convocatorias/busqueda"
BOE_SUMARIO_URL = "https://www.boe.es/datosabiertos/api/boe/sumario/{ymd}"
EU_SEDIA_SEARCH_URL = "https://api.tech.ec.europa.eu/search-api/prod/rest/search"
PLACSP_ATOM_URL = "https://contrataciondelestado.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3.atom"


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
    {"id": "es-placsp", "nivel": "ESTADO", "nombre": "PLACSP - Plataforma de Contratación del Sector Público (Licitaciones CPV Forestal/Incendios)", "tipo": "ATOM_CODICE", "url": "https://contrataciondelestado.es/", "idiomas": ["es", "ca", "gl", "eu"]},
    # 3. 19 CCAA / CIUDADES AUTÓNOMAS
    {"id": "ccaa-boja", "nivel": "CCAA", "ccaa": "ES-AN", "nombre": "BOJA - Boletín Oficial de la Junta de Andalucía", "tipo": "BOLETIN_OFICIAL", "url": "https://www.juntadeandalucia.es/eboja.html", "idiomas": ["es"]},
    {"id": "ccaa-boa", "nivel": "CCAA", "ccaa": "ES-AR", "nombre": "BOA - Boletín Oficial de Aragón", "tipo": "BOLETIN_OFICIAL", "url": "https://www.boa.aragon.es/", "idiomas": ["es"]},
    {"id": "ccaa-bopa", "nivel": "CCAA", "ccaa": "ES-AS", "nombre": "BOPA - Boletín Oficial del Principado de Asturias", "tipo": "BOLETIN_OFICIAL", "url": "https://sede.asturias.es/bopa", "idiomas": ["es"]},
    {"id": "ccaa-boc-cantabria", "nivel": "CCAA", "ccaa": "ES-CB", "nombre": "BOC - Boletín Oficial de Cantabria", "tipo": "BOLETIN_OFICIAL", "url": "https://boc.cantabria.es/", "idiomas": ["es"]},
    {"id": "ccaa-bocce", "nivel": "CCAA", "ccaa": "ES-CE", "nombre": "BOCCE - Boletín Oficial de la Ciudad de Ceuta", "tipo": "BOLETIN_OFICIAL", "url": "https://www.ceuta.es/ceuta/bocce", "idiomas": ["es"]},
    {"id": "ccaa-bocyl", "nivel": "CCAA", "ccaa": "ES-CL", "nombre": "BOCYL - Boletín Oficial de Castilla y León", "tipo": "BOLETIN_OFICIAL", "url": "https://bocyl.jcyl.es/", "idiomas": ["es"]},
    {"id": "ccaa-docm", "nivel": "CCAA", "ccaa": "ES-CM", "nombre": "DOCM - Diario Oficial de Castilla-La Mancha", "tipo": "BOLETIN_OFICIAL", "url": "https://docm.jccm.es/", "idiomas": ["es"]},
    {"id": "ccaa-boc-canarias", "nivel": "CCAA", "ccaa": "ES-CN", "nombre": "BOC - Boletín Oficial de Canarias", "tipo": "BOLETIN_OFICIAL", "url": "https://www.gobiernodecanarias.org/boc/", "idiomas": ["es"]},
    {"id": "ccaa-dogc", "nivel": "CCAA", "ccaa": "ES-CT", "nombre": "DOGC - Diari Oficial de la Generalitat de Catalunya", "tipo": "BOLETIN_OFICIAL", "url": "https://dogc.gencat.cat/", "idiomas": ["ca", "es"]},
    {"id": "ccaa-doe", "nivel": "CCAA", "ccaa": "ES-EX", "nombre": "DOE - Diario Oficial de Extremadura", "tipo": "BOLETIN_OFICIAL", "url": "https://doe.juntaex.es/", "idiomas": ["es"]},
    {"id": "ccaa-dog", "nivel": "CCAA", "ccaa": "ES-GA", "nombre": "DOG - Diario Oficial de Galicia (Xunta de Galicia)", "tipo": "BOLETIN_OFICIAL", "url": "https://www.xunta.gal/diario-oficial-galicia", "idiomas": ["gl", "es"]},
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
    Query the official BDNS / SNPSAP API across State, CCAA, Diputaciones,
    Concellos, Ayuntamientos and Ajuntaments.
    """
    search_terms = keywords or [
        "reforestacion",
        "repoblacion forestal",
        "incendios forestales",
        "silvicultura",
        "montes vecinales",
        "prevencion de incendios",
        "restauracion ambiental",
    ]
    candidates: list[RawCandidate] = []
    seen_codes: set[str] = set()

    headers = {
        "Accept": "application/json",
        "User-Agent": "1hack_reforesta/2.0 (Radar Vivo de Oportunidades Forestales)",
    }

    async with httpx.AsyncClient(timeout=timeout, headers=headers, follow_redirects=True) as client:
        for term in search_terms:
            try:
                params = {
                    "vpd": "GE",
                    "descripcion": term,
                    "descripcionTipoBusqueda": "1",
                    "page": "0",
                    "pageSize": str(max_per_keyword),
                }
                resp = await client.get(BDNS_SEARCH_URL, params=params)
                if resp.status_code != 200:
                    continue
                data = resp.json()
                items: list[dict[str, Any]] = (
                    data.get("content")
                    or data.get("datos")
                    or (data if isinstance(data, list) else [])
                )
                for item in items:
                    num_conv = str(
                        item.get("numeroConvocatoria")
                        or item.get("codigoBDNS")
                        or item.get("id")
                        or ""
                    ).strip()
                    if not num_conv or num_conv in seen_codes:
                        continue
                    seen_codes.add(num_conv)

                    titulo = str(item.get("descripcion") or item.get("titulo") or "").strip()
                    organo = " - ".join(
                        filter(
                            None,
                            [
                                item.get("nivel1"),
                                item.get("nivel2"),
                                item.get("nivel3"),
                            ],
                        )
                    )
                    f_rec = item.get("fechaRecepcion") or item.get("fechaRegistro")
                    presupuesto = item.get("presupuestoTotal") or item.get("importe")
                    try:
                        pres_float = float(presupuesto) if presupuesto is not None else None
                    except (TypeError, ValueError):
                        pres_float = None

                    candidates.append(
                        RawCandidate(
                            id=f"bdns-{num_conv}",
                            codigo_oficial=f"BDNS-{num_conv}",
                            fuente="BDNS",
                            tipo_oportunidad="SUBVENCION",
                            titulo=titulo,
                            organo_convocante=organo or "Administración Pública (BDNS)",
                            texto=f"{titulo}. Órgano: {organo}.",
                            region_hint=str(item.get("nivel1") or item.get("region") or ""),
                            presupuesto_total=pres_float,
                            fecha_publicacion=f_rec,
                            fecha_inicio_solicitud=item.get("fechaInicioSolicitud"),
                            fecha_fin_solicitud=item.get("fechaFinSolicitud"),
                            url_ficha_oficial=f"https://www.pap.hacienda.gob.es/bdnstrans/ge/es/convocatorias/{num_conv}",
                        )
                    )
            except Exception as exc:
                logger.debug("BDNS live query for '%s' skipped: %s", term, exc)

    return candidates


async def fetch_live_boe_candidates(
    days_back: int = 3,
    timeout: float = 6.0,
) -> list[RawCandidate]:
    """Query the official BOE Open Data API (datosabiertos) for recent daily summaries."""
    candidates: list[RawCandidate] = []
    headers = {"Accept": "application/json", "User-Agent": "1hack_reforesta/2.0"}
    today = date.today()

    async with httpx.AsyncClient(timeout=timeout, headers=headers, follow_redirects=True) as client:
        for offset in range(days_back):
            target_date = today - timedelta(days=offset)
            if target_date.weekday() == 6:
                continue
            ymd = target_date.strftime("%Y%m%d")
            try:
                resp = await client.get(BOE_SUMARIO_URL.format(ymd=ymd))
                if resp.status_code != 200:
                    continue
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
                                raw_items = dept["item"]
                                items.append({"item": raw_items})
                            for ep in items:
                                sub_items = ep.get("item", [])
                                if isinstance(sub_items, dict):
                                    sub_items = [sub_items]
                                for it in sub_items:
                                    ident = it.get("identificador", "")
                                    titulo = it.get("titulo", "")
                                    url_pdf_obj = it.get("url_pdf", {})
                                    url_pdf = (
                                        url_pdf_obj.get("texto")
                                        if isinstance(url_pdf_obj, dict)
                                        else str(url_pdf_obj or "")
                                    )
                                    url_html = it.get("url_html", "")
                                    if not ident or not titulo:
                                        continue
                                    candidates.append(
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
                                            url_ficha_oficial=url_html or f"https://www.boe.es/diario_boe/txt.php?id={ident}",
                                            url_bases_reguladoras=url_pdf or None,
                                        )
                                    )
            except Exception as exc:
                logger.debug("BOE live summary for %s skipped: %s", ymd, exc)

    return candidates


async def fetch_live_eu_sedia_candidates(
    timeout: float = 6.0,
) -> list[RawCandidate]:
    """Query the European Commission Funding & Tenders Portal (SEDIA API) for LIFE, Horizon & Interreg calls."""
    candidates: list[RawCandidate] = []
    queries = [
        "reforestation wildfire forest restoration LIFE",
        "biodiversity forest fire Horizon Europe",
        "silviculture afforestation carbon farming",
    ]

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        for q in queries:
            try:
                params = {
                    "apiKey": "SEDIA",
                    "text": q,
                    "pageSize": "15",
                    "pageNumber": "1",
                }
                resp = await client.get(EU_SEDIA_SEARCH_URL, params=params)
                if resp.status_code != 200:
                    continue
                data = resp.json()
                results = data.get("results", [])
                for r in results:
                    meta = r.get("metadata", {})
                    ident_list = meta.get("identifier", []) or [r.get("reference", "")]
                    ident = str(ident_list[0]).strip() if ident_list else ""
                    title_list = meta.get("title", []) or [r.get("summary", "")]
                    title = str(title_list[0]).strip() if title_list else ""
                    desc_list = meta.get("descriptionByte", []) or meta.get("callTitle", []) or []
                    desc = " ".join(str(x) for x in desc_list)
                    deadline_list = meta.get("deadlineDate", [])
                    deadline_raw = str(deadline_list[0])[:10] if deadline_list else None
                    start_list = meta.get("startDate", [])
                    start_raw = str(start_list[0])[:10] if start_list else None

                    if not ident or not title:
                        continue
                    candidates.append(
                        RawCandidate(
                            id=f"eu-{ident.lower().replace('_', '-')}",
                            codigo_oficial=ident,
                            fuente="EU_SEDIA",
                            tipo_oportunidad="PROGRAMA_UE",
                            titulo=title,
                            organo_convocante="European Commission - CINEA / REA (EU Funding & Tenders)",
                            texto=f"{title}. {desc}",
                            region_hint="Unión Europea (Aplicable en España)",
                            nuts_code="EU",
                            cofinanciado_ue=True,
                            fondo_ue="LIFE" if "LIFE" in ident.upper() else "Horizon Europe",
                            fecha_publicacion=start_raw,
                            fecha_inicio_solicitud=start_raw,
                            fecha_fin_solicitud=deadline_raw,
                            url_ficha_oficial=f"https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/{ident}",
                        )
                    )
            except Exception as exc:
                logger.debug("EU SEDIA live query for '%s' skipped: %s", q, exc)

    return candidates


async def fetch_live_placsp_candidates(timeout: float = 6.0) -> list[RawCandidate]:
    """Query the official PLACSP (Contratación del Sector Público) Atom Syndication Feed."""
    candidates: list[RawCandidate] = []
    headers = {"User-Agent": "1hack_reforesta/2.0"}
    async with httpx.AsyncClient(timeout=timeout, headers=headers, follow_redirects=True) as client:
        try:
            resp = await client.get(PLACSP_ATOM_URL)
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
                short_id = entry_id.split("/")[-1] if "/" in entry_id else str(abs(hash(title)) % 1000000)
                candidates.append(
                    RawCandidate(
                        id=f"placsp-{short_id.lower()}",
                        codigo_oficial=f"PLACSP-{short_id}",
                        fuente="PLACSP",
                        tipo_oportunidad="LICITACION",
                        titulo=title,
                        organo_convocante="Contratación del Sector Público (PLACSP)",
                        texto=f"{title}. {summary}",
                        fecha_publicacion=updated or date.today(),
                        url_ficha_oficial=href,
                    )
                )
        except Exception as exc:
            logger.debug("PLACSP Atom live feed skipped: %s", exc)
    return candidates
