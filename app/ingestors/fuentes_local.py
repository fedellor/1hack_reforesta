"""Ingestor for local PDF documents in ./fuentes/ (including the 2 Golden Benchmark PDFs)."""
from datetime import timedelta
from pathlib import Path
import re
from app.config import FUENTES_DIR, settings
from app.pipeline.date_resolver import add_business_days, parse_spanish_date
from app.pipeline.orchestrator import RawCandidate
from app.pipeline.pdf_extractor import ExtractedPDFDocument, extract_pdf_from_path


def load_candidates_from_fuentes(directory: Path | None = None) -> list[RawCandidate]:
    """Scan all PDF files in ./fuentes/ and convert them into RawCandidates."""
    target_dir = directory or FUENTES_DIR
    if not target_dir.exists():
        return []

    candidates: list[RawCandidate] = []
    for pdf_path in sorted(target_dir.glob("*.pdf")):
        doc = extract_pdf_from_path(pdf_path)
        candidates.append(pdf_doc_to_candidate(doc))
    return candidates


def pdf_doc_to_candidate(doc: ExtractedPDFDocument) -> RawCandidate:
    """Convert an ExtractedPDFDocument into a standardized RawCandidate."""
    today = settings.get_today()
    pub_date = parse_spanish_date(doc.fecha_registro_o_firma)

    # Determine unique ID and official code
    if doc.codigo_bdns:
        cid = f"bdns-{doc.codigo_bdns}"
        codigo_oficial = f"BDNS-{doc.codigo_bdns}"
        fuente = "BDNS"
        url_ficha = f"https://www.pap.hacienda.gob.es/bdnstrans/ge/es/convocatorias/{doc.codigo_bdns}"
    elif doc.codigo_orden:
        slug = re.sub(r"[^a-z0-9]+", "-", doc.codigo_orden.lower()).strip("-")
        is_madrid = "madrid" in (doc.region_detectada + doc.organo_detectado + doc.filename).lower()
        cid = f"bocm-{slug}" if is_madrid else f"pdf-{slug}"
        codigo_oficial = doc.codigo_orden.upper()
        fuente = "BOLETIN_CCAA" if is_madrid or "orden" in doc.codigo_orden.lower() else "FUENTES_PDF"
        url_ficha = doc.url_tramitacion or (
            "https://www.comunidad.madrid/servicios/medio-ambiente" if is_madrid else ""
        )
    else:
        slug = re.sub(r"[^a-z0-9]+", "-", Path(doc.filename).stem.lower()).strip("-")
        cid = f"pdf-{slug}"
        codigo_oficial = Path(doc.filename).stem.upper()
        fuente = "FUENTES_PDF"
        url_ficha = doc.url_tramitacion or ""

    tipo_oportunidad = (
        "LICITACION"
        if (doc.cpv_codes and "licitaci" in doc.full_text.lower())
        else ("PROGRAMA_UE" if "european commission" in doc.organo_detectado.lower() else "SUBVENCION")
    )

    # Compute active business-day window when extract publication triggers a relative deadline
    f_ini = None
    f_fin = None
    plazo_txt = doc.plazo_solicitud_texto or ""
    if "extracto" in plazo_txt.lower():
        extract_pub = today - timedelta(days=3)
        f_ini = extract_pub + timedelta(days=1)
        m_days = re.search(r"\b(\d+)\b", plazo_txt)
        num_days = int(m_days.group(1)) if m_days else 15
        ccaa_hint = "ES-MD" if "madrid" in (doc.region_detectada + doc.organo_detectado).lower() else None
        f_fin = add_business_days(extract_pub, num_days, ccaa_codigo=ccaa_hint)

    return RawCandidate(
        id=cid,
        codigo_oficial=codigo_oficial,
        fuente=fuente,
        tipo_oportunidad=tipo_oportunidad,
        titulo=doc.titulo_detectado or doc.filename,
        organo_convocante=doc.organo_detectado or "Administración Pública",
        unidad_convocante=doc.unidad_detectada,
        texto=doc.full_text,
        region_hint=doc.region_detectada,
        cpv_codes=doc.cpv_codes,
        sector_economico_original=doc.sector_economico_raw,
        beneficiarios_hint=doc.beneficiarios_raw,
        presupuesto_total=doc.presupuesto_total,
        importe_max_proyecto=doc.importe_max_proyecto,
        importe_max_beneficiario=doc.importe_max_entidad,
        porcentaje_financiacion=doc.porcentaje_financiacion,
        cofinanciado_ue=doc.cofinanciado_ue,
        anio_convocatoria=pub_date.year if pub_date else today.year,
        fecha_publicacion=pub_date or today,
        fecha_inicio_solicitud=f_ini,
        fecha_fin_solicitud=f_fin,
        plazo_texto_original=doc.plazo_solicitud_texto,
        url_ficha_oficial=url_ficha,
        url_tramitacion=doc.url_tramitacion,
        url_bases_reguladoras=doc.url_bases_reguladoras,
        archivo_fuente_local=f"fuentes/{doc.filename}",
        criterios_valoracion=doc.criterios_valoracion,
    )
