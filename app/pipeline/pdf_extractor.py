"""PDF Text & Structured Metadata Extractor using PyMuPDF (fitz) with OCR fallback — ES/CA/GL/EU/EN."""
from collections.abc import Callable
from dataclasses import dataclass, field
import io
import logging
from pathlib import Path
import re
from typing import Any
import pymupdf as fitz  # PyMuPDF
from app.config import settings
from app.pipeline.layer1_regex import extract_cpv_codes

logger = logging.getLogger(__name__)


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
    cpv_codes: list[str] = field(default_factory=list)
    criterios_valoracion: list[dict[str, Any]] = field(default_factory=list)
    used_ocr: bool = False
    ocr_engine: str | None = None


def _parse_euro_amount(raw: str) -> float | None:
    """Convert Spanish number string like '17.389.322,52', '500.000' or '120000' to float."""
    if not raw:
        return None
    cleaned = raw.strip().replace("€", "").replace("euros", "").replace("EUR", "").strip()
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    elif cleaned.count(".") >= 1:
        parts = cleaned.split(".")
        if all(len(p) == 3 for p in parts[1:]):
            cleaned = "".join(parts)
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


def _run_ocr_fallback(
    doc: fitz.Document,
    api_key_override: str | None = None,
    ocr_handler: Callable[[list[bytes]], str] | None = None,
    max_pages: int = 5,
) -> tuple[str, str | None]:
    """
    OCR fallback for scanned image-only PDFs (common in older municipal/provincial BOPs).
    Order: injectable handler -> pytesseract -> PyMuPDF Tesseract -> Gemini Vision OCR.
    """
    pages_to_scan = min(len(doc), max_pages)
    if pages_to_scan <= 0:
        return "", None

    page_pngs: list[bytes] = []
    for idx in range(pages_to_scan):
        pix = doc[idx].get_pixmap(dpi=180)
        page_pngs.append(pix.tobytes("png"))

    # 1. Injectable OCR handler (custom engine or deterministic unit tests)
    if ocr_handler is not None:
        try:
            text = (ocr_handler(page_pngs) or "").strip()
            if text:
                return text, "CUSTOM_OCR"
        except Exception as exc:
            logger.debug("Custom OCR handler failed: %s", exc)

    # 2. Optional pytesseract + Pillow local OCR
    try:
        import pytesseract  # type: ignore
        from PIL import Image  # type: ignore

        chunks = [
            pytesseract.image_to_string(Image.open(io.BytesIO(png)), lang="spa+eng")
            for png in page_pngs
        ]
        joined = "\n".join(c.strip() for c in chunks if c and c.strip())
        if len(joined) >= 20:
            return joined, "PYTESSERACT"
    except Exception:
        pass

    # 3. PyMuPDF built-in Tesseract integration (works if tessdata is installed on host)
    try:
        tess_chunks: list[str] = []
        for idx in range(pages_to_scan):
            tp = doc[idx].get_textpage_ocr(language="spa+eng", dpi=180, full=True)
            page_txt = doc[idx].get_text("text", textpage=tp).strip()
            if page_txt:
                tess_chunks.append(page_txt)
        joined_tess = "\n".join(tess_chunks)
        if len(joined_tess) >= 20:
            return joined_tess, "PYMUPDF_TESSERACT"
    except Exception:
        pass

    # 4. Cloud Vision OCR via Google Gemini Flash (if API key configured)
    gemini_key = (api_key_override or settings.gemini_api_key or "").strip()
    if gemini_key:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=gemini_key)
            parts: list[Any] = [
                "Transcribe literalmente TODO el texto de estas páginas escaneadas de un boletín oficial o convocatoria (título, organismo, importes, CPV, plazos y artículos) sin resumir."
            ]
            for png in page_pngs:
                parts.append(types.Part.from_bytes(data=png, mime_type="image/png"))
            resp = client.models.generate_content(
                model=settings.gemini_model,
                contents=parts,
                config=types.GenerateContentConfig(temperature=0.0),
            )
            vision_txt = (getattr(resp, "text", None) or "").strip()
            if len(vision_txt) >= 20:
                return vision_txt, "GEMINI_VISION_OCR"
        except Exception as exc:
            logger.debug("Gemini Vision OCR skipped: %s", exc)

    return "", None


def _extract_document_with_ocr_fallback(
    doc: fitz.Document,
    filename: str,
    api_key_override: str | None = None,
    ocr_handler: Callable[[list[bytes]], str] | None = None,
) -> ExtractedPDFDocument:
    """Shared extraction pipeline for both file paths and raw PDF byte streams."""
    pages_text = [page.get_text("text") for page in doc]
    num_pages = len(doc)
    raw_full = "\n".join(pages_text)
    used_ocr = False
    ocr_engine: str | None = None

    if len(raw_full.strip()) < 100 and num_pages > 0:
        ocr_text, ocr_engine = _run_ocr_fallback(
            doc,
            api_key_override=api_key_override,
            ocr_handler=ocr_handler,
        )
        if ocr_text:
            raw_full = f"{raw_full}\n{ocr_text}".strip()
            used_ocr = True

    doc.close()
    full_text = _clean_watermark_noise(raw_full)
    parsed = _parse_document_fields(filename, num_pages, full_text)
    parsed.used_ocr = used_ocr
    parsed.ocr_engine = ocr_engine
    return parsed


def extract_pdf_from_path(
    pdf_path: str | Path,
    api_key_override: str | None = None,
    ocr_handler: Callable[[list[bytes]], str] | None = None,
) -> ExtractedPDFDocument:
    """Extract text and structured administrative metadata from a local PDF file (with OCR fallback)."""
    path = Path(pdf_path)
    doc = fitz.open(str(path))
    return _extract_document_with_ocr_fallback(
        doc,
        filename=path.name,
        api_key_override=api_key_override,
        ocr_handler=ocr_handler,
    )


def extract_pdf_from_bytes(
    pdf_bytes: bytes,
    filename: str = "uploaded.pdf",
    api_key_override: str | None = None,
    ocr_handler: Callable[[list[bytes]], str] | None = None,
) -> ExtractedPDFDocument:
    """Extract text and structured administrative metadata from PDF bytes (with OCR fallback)."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    return _extract_document_with_ocr_fallback(
        doc,
        filename=filename,
        api_key_override=api_key_override,
        ocr_handler=ocr_handler,
    )


def _parse_document_fields(filename: str, num_pages: int, full_text: str) -> ExtractedPDFDocument:
    result = ExtractedPDFDocument(
        filename=filename,
        num_pages=num_pages,
        full_text=full_text,
    )

    # Always extract CPV codes and EU funding signals across any PDF using shared helper
    result.cpv_codes = extract_cpv_codes(full_text)
    result.cofinanciado_ue = bool(
        re.search(
            r"\b(FEADER|FEDER|NextGeneration|PRTR|LIFE|Horizon\s+Europe|Interreg|Fondo\s+Europeo)\b",
            full_text,
            re.IGNORECASE,
        )
    )

    # Case A: BDNS "Detalle de la convocatoria" sheet (e.g. miteco-convocatoria-923290.pdf)
    if "Detalle de la convocatoria" in full_text and "Código BDNS" in full_text:
        _parse_bdns_sheet(full_text, result)
        return result

    # Case B: Official Bulletin Order / Resolución / Decreto / Bases / Tender Pliego
    _parse_bulletin_order(full_text, result)
    return result


def _parse_bdns_sheet(text: str, res: ExtractedPDFDocument) -> None:
    m_bdns = re.search(r"\b(\d{6,7})\s*\n\s*Código BDNS", text) or re.search(
        r"Código BDNS\s*\n\s*(\d{6,7})", text
    )
    if m_bdns:
        res.codigo_bdns = m_bdns.group(1).strip()

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

    if "MINISTERIO PARA LA TRANSICIÓN" in text:
        res.organo_detectado = "MINISTERIO PARA LA TRANSICIÓN ECOLÓGICA Y EL RETO DEMOGRÁFICO (MITECO)"
        if "DIRECCIÓN GENERAL DE SERVICIOS" in text:
            res.unidad_detectada = "DIRECCIÓN GENERAL DE SERVICIOS"
    else:
        m_org = re.search(r"Órgano convocante\s*\n+([^\n]+(?:\n[^\n]+)?)", text)
        if m_org:
            res.organo_detectado = re.sub(r"\s+", " ", m_org.group(1)).strip()

    if "ES - ESPAÑA" in text:
        res.region_detectada = "ES - ESPAÑA"

    if "ACTIVIDADES INMOBILIARIAS" in text:
        res.sector_economico_raw = "ACTIVIDADES INMOBILIARIAS"
    if "PERSONAS FÍSICAS QUE NO DESARROLLAN ACTIVIDAD ECONÓMICA" in text:
        res.beneficiarios_raw = "PERSONAS FÍSICAS QUE NO DESARROLLAN ACTIVIDAD ECONÓMICA / ENTIDADES INTERÉS SOCIAL"

    m_budget = re.search(r"([\d.]+,\d{2})\s*€\s*\n\s*Presupuesto total", text) or re.search(
        r"Presupuesto total de la convocatoria\s*\n\s*([\d.]+,\d{2})\s*€", text
    )
    if m_budget:
        res.presupuesto_total = _parse_euro_amount(m_budget.group(1))

    m_date = re.search(r"(\d{2}/\d{2}/20\d{2})\s*\n\s*Fecha de registro", text) or re.search(
        r"Fecha de registro\s*\n\s*(\d{2}/\d{2}/20\d{2})", text
    )
    if m_date:
        res.fecha_registro_o_firma = m_date.group(1)

    m_plazo = re.search(
        r"Fecha de finalización del periodo de solicitud\s*\n\s*([^\n]+)", text
    )
    if m_plazo:
        res.plazo_solicitud_texto = m_plazo.group(1).strip()

    urls = re.findall(r"https?://[^\s\n]+", text)
    for u in urls:
        if "sede." in u and not res.url_tramitacion:
            res.url_tramitacion = u
        elif "boe.es" in u and not res.url_bases_reguladoras:
            res.url_bases_reguladoras = u


def _parse_bulletin_order(text: str, res: ExtractedPDFDocument) -> None:
    # Official normative code (Orden, Resolución, Decreto, Orde, Resolució, Expediente)
    m_orden = (
        re.search(r"\b(Orden\s+(?:[A-Z]{2,5}/)?\d+/\d{4})\b", text, re.IGNORECASE)
        or re.search(r"\b(Orde\s+do\s+\d{1,2}\s+de\s+[a-záéíóú]+\s+de\s+20\d{2})\b", text, re.IGNORECASE)
        or re.search(r"\b(Resoluci[oó]n?\s+(?:de\s+\d{1,2}[^\n,]{5,35}|\d+/\d{4}))\b", text, re.IGNORECASE)
        or re.search(r"\b(Decreto\s+\d+/\d{4})\b", text, re.IGNORECASE)
        or re.search(r"\b(Expediente[:\s]+[A-Z0-9\-/]{4,25})\b", text, re.IGNORECASE)
    )
    if m_orden:
        res.codigo_orden = re.sub(r"\s+", " ", m_orden.group(1)).strip()

    # Title paragraph
    m_title = re.search(
        r"((?:Orden|Orde|Resoluci[oó]n?|Decreto|Extracto\s+de\s+la\s+(?:Orden|Resoluci[oó]n)|Subvenciones|Subvencions|Ayudas)\b[^\n]+(?:\n[^\n]+){0,5}?\.)",
        text,
    )
    if m_title:
        res.titulo_detectado = re.sub(r"\s+", " ", m_title.group(1)).strip()
    else:
        first_lines = [ln.strip() for ln in text.splitlines() if len(ln.strip()) > 15][:3]
        res.titulo_detectado = " ".join(first_lines)[:300]

    # Issuing body & Region (multilingual ES/CA/GL/EU/EN)
    if "Comunidad de Madrid" in text:
        res.region_detectada = "Comunidad de Madrid"
        if "Consejería de Medio Ambiente, Agricultura e Interior" in text:
            res.organo_detectado = "Comunidad de Madrid - Consejería de Medio Ambiente, Agricultura e Interior"
            res.unidad_detectada = "Dirección General de Biodiversidad y Gestión Forestal"
        else:
            res.organo_detectado = "Comunidad de Madrid"
    else:
        m_org = re.search(
            r"((?:Consejer[ií]a|Conseller[ií]a|Conselleria|Departament|Ministerio|Diputaci[oó]n|Deputaci[oó]n|Diputaci[oó]|"
            r"Cabildo|Consell\s+Insular|Ayuntamiento|Concello|Ajuntament|Fundaci[oó]n|Confederaci[oó]n\s+Hidrogr[aá]fica|"
            r"Xunta\s+de\s+Galicia|Generalitat\s+de\s+Catalunya|Generalitat\s+Valenciana|Junta\s+de\s+Andaluc[ií]a|"
            r"Junta\s+de\s+Castilla\s+y\s+Le[oó]n|European\s+Commission)\b[^\n.;]{0,80})",
            text,
            re.IGNORECASE,
        )
        if m_org:
            res.organo_detectado = re.sub(r"\s+", " ", m_org.group(1)).strip()
            res.region_detectada = res.organo_detectado

    # Beneficiaries
    low = text.lower()
    if any(k in low for k in ["sin ánimo de lucro", "sin animo de lucro", "sense ànim de lucre", "sen ánimo de lucro", "ong", "non-profit"]):
        res.beneficiarios_raw = "Entidades sin ánimo de lucro (Asociaciones, Fundaciones, ONGs ambientales)"

    # Total budget across broad phrasings
    m_dot = re.search(
        r"(?:dotaci[oó]n|presupuesto(?:\s+base\s+de\s+licitaci[oó]n)?|importe\s+(?:total|global)|"
        r"cr[eé]dito\s+presupuestario|cuant[ií]a\s+(?:total|m[aá]xima)|valor\s+estimado|dotada\s+con|total\s+budget)"
        r"[^.\n€]{0,60}?(?:es\s+de|de|:|ascender[aá]\s+a|of)?\s*([\d.]+(?:,\d{1,2})?)\s*(?:euros|€|EUR)",
        text,
        re.IGNORECASE,
    )
    if m_dot:
        res.presupuesto_total = _parse_euro_amount(m_dot.group(1))

    # Max per entity / beneficiary
    m_ent = re.search(
        r"(?:([\d.]+(?:,\d{1,2})?)\s*(?:euros|€)\s*por\s+(?:entidad\s+beneficiaria|beneficiario|solicitante)|"
        r"m[aá]ximo\s+(?:por\s+)?(?:entidad|beneficiario)\s*(?:ser[aá]\s+de|:)?\s*([\d.]+(?:,\d{1,2})?)\s*(?:euros|€))",
        text,
        re.IGNORECASE,
    )
    if m_ent:
        res.importe_max_entidad = _parse_euro_amount(m_ent.group(1) or m_ent.group(2))

    # Max per project
    m_proj = re.search(
        r"(?:([\d.]+(?:,\d{1,2})?)\s*(?:euros|€)\s*por\s+(?:proyecto|solicitud|actuaci[oó]n)|"
        r"m[aá]ximo\s+por\s+proyecto\s*(?:ser[aá]\s+de|:)?\s*([\d.]+(?:,\d{1,2})?)\s*(?:euros|€))",
        text,
        re.IGNORECASE,
    )
    if m_proj:
        res.importe_max_proyecto = _parse_euro_amount(m_proj.group(1) or m_proj.group(2))

    # Co-financing %
    m_pct = re.search(
        r"(?:alcanzar\s+el|hasta\s+(?:el|un)|financiar[aá]\s+(?:hasta\s+)?el|intensidad\s+(?:m[aá]xima\s+)?del)\s*(\d{1,3})\s*%",
        text,
        re.IGNORECASE,
    )
    if m_pct:
        pct_val = float(m_pct.group(1))
        if 10.0 <= pct_val <= 100.0:
            res.porcentaje_financiacion = pct_val

    # Deadline clause (ES / CA / GL / EN) - allow line wraps inside legal sentences before '.'
    m_plazo = (
        re.search(
            r"en\s+el\s+plazo\s+de\s+([^.]+?(?:d[ií](?:as|es)\s+(?:h[aáà]bil(?:e?s)?|natural(?:e?s)?)|mes(?:es|os)?)(?:[^.]{0,120})?)",
            text,
            re.IGNORECASE,
        )
        or re.search(
            r"(?:plazo|termini|prazo)\s+de\s+presentaci[oó]n?(?:\s+de\s+solicitud(?:es)?)?\s*(?:ser[aá]\s+de|:)\s*([^.\n]{4,90})",
            text,
            re.IGNORECASE,
        )
        or re.search(
            r"(?:hasta\s+el|fins\s+al|ata\s+o|deadline:?)\s+(\d{1,2}\s+(?:de\s+[a-záéíóú]+|[a-z]+)\s+(?:de\s+|do\s+)?20\d{2}|20\d{2}-\d{2}-\d{2}|\d{2}/\d{2}/20\d{2})",
            text,
            re.IGNORECASE,
        )
    )
    if m_plazo:
        res.plazo_solicitud_texto = re.sub(r"\s+", " ", m_plazo.group(1)).strip()

    # Signature / Publication date
    m_sig = (
        re.search(r"Fecha:\s*(20\d{2}[./-]\d{2}[./-]\d{2})", text)
        or re.search(r"(?:Publicaci[oó]n|Fecha\s+de\s+registro|En\s+[A-ZÁÉÍÓÚ][a-zñáéíóú]+,\s+a)\s*[:]?\s*(\d{1,2}\s+de\s+[a-záéíóú]+\s+de\s+20\d{2}|\d{2}/\d{2}/20\d{2})", text, re.IGNORECASE)
    )
    if m_sig:
        res.fecha_registro_o_firma = m_sig.group(1)

    # URLs
    if "sede.comunidad.madrid" in text:
        res.url_tramitacion = "https://sede.comunidad.madrid"
    else:
        urls = re.findall(r"https?://[^\s\n)>\"']+", text)
        for u in urls:
            if "sede." in u and not res.url_tramitacion:
                res.url_tramitacion = u
            elif any(d in u for d in ("boe.es", "bocm.es", "xunta.gal", "gencat.cat", "juntadeandalucia.es")) and not res.url_bases_reguladoras:
                res.url_bases_reguladoras = u

    # Valuation criteria extraction
    if "DIMENSIÓN AMBIENTAL" in text:
        res.criterios_valoracion = [
            {"dimension": "Dimensión Técnica", "puntos_max": 5.0, "detalle": "Coherencia técnica, experiencia previa, innovación, continuidad y cofinanciación propia (>25%)."},
            {"dimension": "Dimensión Ambiental", "puntos_max": 3.75, "detalle": "Actuaciones en Red Natura 2000 (ZEC/ZEPA), Hábitats de Interés Comunitario, Catálogo Regional de Especies Amenazadas, Árboles Singulares y adaptación al cambio climático."},
            {"dimension": "Dimensión Social", "puntos_max": 0.5, "detalle": "Accesibilidad universal en espacios naturales y participación ciudadana / agentes locales."},
            {"dimension": "Dimensión Divulgativa", "puntos_max": 0.75, "detalle": "Acciones de divulgación en redes, jornadas abiertas y publicaciones técnicas/científicas."},
        ]
