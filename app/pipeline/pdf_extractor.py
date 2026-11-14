"""PDF Text & Structured Metadata Extractor using PyMuPDF (fitz)."""
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import pymupdf as fitz  # PyMuPDF


@dataclass
class ExtractedPDFDocument:
    filename: str
    num_pages: int
    full_text: str
    codigo_bdns: str | None = None
    codigo_orden: str | None = None
    titulo_detectado: str = ""
    organo_detectado: str = ""
    unidad_detectada: str | None = None
    region_detectada: str = ""
    sector_economico_raw: str | None = None
    beneficiarios_raw: str = ""
    presupuesto_total: float | None = None
    importe_max_entidad: float | None = None
    importe_max_proyecto: float | None = None
    porcentaje_financiacion: float | None = None
    fecha_registro_o_firma: str | None = None
    plazo_solicitud_texto: str | None = None
    url_tramitacion: str | None = None
    url_bases_reguladoras: str | None = None
    cofinanciado_ue: bool = False
    criterios_valoracion: list[dict[str, Any]] = field(default_factory=list)


def _parse_euro_amount(raw: str) -> float | None:
    """Convert Spanish number string like '17.389.322,52' or '500.000' to float."""
    if not raw:
        return None
    cleaned = raw.strip().replace("€", "").replace("euros", "").strip()
    cleaned = cleaned.replace(".", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _clean_watermark_noise(text: str) -> str:
    """Remove repetitive lateral verification watermarks from official bulletins."""
    text = re.sub(
        r"La autenticidad de este documento se puede comprobar en\s+https?://\S+\s+mediante el siguiente código seguro de verificación:\s*\d*",
        "",
        text,
        flags=re.IGNORECASE,
    )
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def extract_pdf_from_path(pdf_path: str | Path) -> ExtractedPDFDocument:
    """Extract text and structured administrative metadata from a local PDF file."""
    path = Path(pdf_path)
    doc = fitz.open(str(path))
    pages_text: list[str] = []
    for page in doc:
        pages_text.append(page.get_text("text"))
    num_pages = len(doc)
    doc.close()

    raw_full = "\n".join(pages_text)
    full_text = _clean_watermark_noise(raw_full)
    return _parse_document_fields(path.name, num_pages, full_text)


def extract_pdf_from_bytes(pdf_bytes: bytes, filename: str = "uploaded.pdf") -> ExtractedPDFDocument:
    """Extract text and structured administrative metadata from PDF bytes."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages_text: list[str] = []
    for page in doc:
        pages_text.append(page.get_text("text"))
    num_pages = len(doc)
    doc.close()

    raw_full = "\n".join(pages_text)
    full_text = _clean_watermark_noise(raw_full)
    return _parse_document_fields(filename, num_pages, full_text)


def _parse_document_fields(filename: str, num_pages: int, full_text: str) -> ExtractedPDFDocument:
    result = ExtractedPDFDocument(
        filename=filename,
        num_pages=num_pages,
        full_text=full_text,
    )

    # Case A: BDNS "Detalle de la convocatoria" sheet (e.g. miteco-convocatoria-923290.pdf)
    if "Detalle de la convocatoria" in full_text and "Código BDNS" in full_text:
        _parse_bdns_sheet(full_text, result)
        return result

    # Case B: Official Bulletin Order / Bases / Convocatoria (e.g. comunidad-madrid-orden-1689-2026.pdf)
    _parse_bulletin_order(full_text, result)
    return result


def _parse_bdns_sheet(text: str, res: ExtractedPDFDocument) -> None:
    # BDNS Code
    m_bdns = re.search(r"\b(\d{6,7})\s*\n\s*Código BDNS", text) or re.search(
        r"Código BDNS\s*\n\s*(\d{6,7})", text
    )
    if m_bdns:
        res.codigo_bdns = m_bdns.group(1).strip()

    # Title
    m_title = re.search(
        r"(AYUDAS[^\n]+(?:\n[A-ZÁÉÍÓÚÑ0-9\s,.\-]+)*?)\s*\n\s*Título de las bases reguladoras",
        text,
    )
    if m_title:
        res.titulo_detectado = re.sub(r"\s+", " ", m_title.group(1)).strip()
    else:
        m_t2 = re.search(r"Título de la convocatoria en español\s*\n+([^\n]+)", text)
        if m_t2:
            res.titulo_detectado = m_t2.group(1).strip()

    # Issuing body
    if "MINISTERIO PARA LA TRANSICIÓN" in text:
        res.organo_detectado = "MINISTERIO PARA LA TRANSICIÓN ECOLÓGICA Y EL RETO DEMOGRÁFICO (MITECO)"
        if "DIRECCIÓN GENERAL DE SERVICIOS" in text:
            res.unidad_detectada = "DIRECCIÓN GENERAL DE SERVICIOS"
    else:
        m_org = re.search(r"Órgano convocante\s*\n+([^\n]+(?:\n[^\n]+)?)", text)
        if m_org:
            res.organo_detectado = re.sub(r"\s+", " ", m_org.group(1)).strip()

    # Region
    if "ES - ESPAÑA" in text:
        res.region_detectada = "ES - ESPAÑA"

    # Sector & Beneficiaries
    if "ACTIVIDADES INMOBILIARIAS" in text:
        res.sector_economico_raw = "ACTIVIDADES INMOBILIARIAS"
    if "PERSONAS FÍSICAS QUE NO DESARROLLAN ACTIVIDAD ECONÓMICA" in text:
        res.beneficiarios_raw = "PERSONAS FÍSICAS QUE NO DESARROLLAN ACTIVIDAD ECONÓMICA / ENTIDADES INTERÉS SOCIAL"

    # Budget
    m_budget = re.search(r"([\d.]+,\d{2})\s*€\s*\n\s*Presupuesto total", text) or re.search(
        r"Presupuesto total de la convocatoria\s*\n\s*([\d.]+,\d{2})\s*€", text
    )
    if m_budget:
        res.presupuesto_total = _parse_euro_amount(m_budget.group(1))

    # Registration date
    m_date = re.search(r"(\d{2}/\d{2}/20\d{2})\s*\n\s*Fecha de registro", text) or re.search(
        r"Fecha de registro\s*\n\s*(\d{2}/\d{2}/20\d{2})", text
    )
    if m_date:
        res.fecha_registro_o_firma = m_date.group(1)

    # Deadline text
    m_plazo = re.search(
        r"Fecha de finalización del periodo de solicitud\s*\n\s*([^\n]+)", text
    )
    if m_plazo:
        res.plazo_solicitud_texto = m_plazo.group(1).strip()

    # URLs
    urls = re.findall(r"https?://[^\s\n]+", text)
    for u in urls:
        if "sede." in u and not res.url_tramitacion:
            res.url_tramitacion = u
        elif "boe.es" in u and not res.url_bases_reguladoras:
            res.url_bases_reguladoras = u


def _parse_bulletin_order(text: str, res: ExtractedPDFDocument) -> None:
    # Order code (e.g., Orden 1689/2026)
    m_orden = re.search(r"\b(Orden\s+\d+/\d{4})\b", text, re.IGNORECASE)
    if m_orden:
        res.codigo_orden = m_orden.group(1)

    # Title (full paragraph starting with Orden ...)
    m_title = re.search(
        r"(Orden\s+\d+/\d{4},[^\n]+(?:\n[^\n]+){0,5}?\.)",
        text,
    )
    if m_title:
        res.titulo_detectado = re.sub(r"\s+", " ", m_title.group(1)).strip()
    else:
        first_lines = [ln.strip() for ln in text.splitlines() if len(ln.strip()) > 20][:3]
        res.titulo_detectado = " ".join(first_lines)[:300]

    # Issuing body & Region
    if "Comunidad de Madrid" in text:
        res.region_detectada = "Comunidad de Madrid"
        if "Consejería de Medio Ambiente, Agricultura e Interior" in text:
            res.organo_detectado = "Comunidad de Madrid - Consejería de Medio Ambiente, Agricultura e Interior"
            res.unidad_detectada = "Dirección General de Biodiversidad y Gestión Forestal"
        else:
            res.organo_detectado = "Comunidad de Madrid"
    else:
        m_cons = re.search(r"(Consejería de [^\n,.;]+|Ministerio de [^\n,.;]+|Diputación de [^\n,.;]+|Ayuntamiento de [^\n,.;]+)", text)
        if m_cons:
            res.organo_detectado = m_cons.group(1).strip()

    # Beneficiaries
    if "entidades sin ánimo de lucro" in text.lower():
        res.beneficiarios_raw = "Entidades sin ánimo de lucro (Asociaciones, Fundaciones, ONGs ambientales)"

    # Total budget ("dotación de la convocatoria es de 500.000 euros")
    m_dot = re.search(
        r"(?:dotación|presupuesto|importe\s+total)[^.\n]{0,60}?es\s+de\s+([\d.]+(?:,\d{1,2})?)\s*(?:euros|€)",
        text,
        re.IGNORECASE,
    )
    if m_dot:
        res.presupuesto_total = _parse_euro_amount(m_dot.group(1))

    # Max per entity ("60.000 euros por entidad beneficiaria")
    m_ent = re.search(
        r"([\d.]+(?:,\d{1,2})?)\s*(?:euros|€)\s*por\s+entidad\s+beneficiaria",
        text,
        re.IGNORECASE,
    )
    if m_ent:
        res.importe_max_entidad = _parse_euro_amount(m_ent.group(1))

    # Max per project ("30.000 euros por proyecto")
    m_proj = re.search(
        r"([\d.]+(?:,\d{1,2})?)\s*(?:euros|€)\s*por\s+proyecto",
        text,
        re.IGNORECASE,
    )
    if m_proj:
        res.importe_max_proyecto = _parse_euro_amount(m_proj.group(1))

    # Co-financing % ("alcanzar el 100 %")
    m_pct = re.search(r"alcanzar\s+el\s+(\d{1,3})\s*%", text, re.IGNORECASE)
    if m_pct:
        res.porcentaje_financiacion = float(m_pct.group(1))

    # Deadline clause ("en el plazo de 10 días hábiles a contar desde el día siguiente...")
    m_plazo = re.search(
        r"en\s+el\s+plazo\s+de\s+([^.]+?d[ií]as\s+(?:h[aá]biles|naturales)[^.]+)",
        text,
        re.IGNORECASE,
    )
    if m_plazo:
        res.plazo_solicitud_texto = re.sub(r"\s+", " ", m_plazo.group(1)).strip()

    # Digital signature date ("Fecha: 2026.05.07")
    m_sig = re.search(r"Fecha:\s*(20\d{2}[./-]\d{2}[./-]\d{2})", text)
    if m_sig:
        res.fecha_registro_o_firma = m_sig.group(1)

    # Tramitacion URL
    if "sede.comunidad.madrid" in text:
        res.url_tramitacion = "https://sede.comunidad.madrid"

    # Valuation criteria extraction if present
    if "DIMENSIÓN AMBIENTAL" in text:
        res.criterios_valoracion = [
            {"dimension": "Dimensión Técnica", "puntos_max": 5.0, "detalle": "Coherencia técnica, experiencia previa, innovación, continuidad y cofinanciación propia (>25%)."},
            {"dimension": "Dimensión Ambiental", "puntos_max": 3.75, "detalle": "Actuaciones en Red Natura 2000 (ZEC/ZEPA), Hábitats de Interés Comunitario, Catálogo Regional de Especies Amenazadas, Árboles Singulares y adaptación al cambio climático."},
            {"dimension": "Dimensión Social", "puntos_max": 0.5, "detalle": "Accesibilidad universal en espacios naturales y participación ciudadana / agentes locales."},
            {"dimension": "Dimensión Divulgativa", "puntos_max": 0.75, "detalle": "Acciones de divulgación en redes, jornadas abiertas y publicaciones técnicas/científicas."},
        ]
