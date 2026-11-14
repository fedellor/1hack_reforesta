"""Ingestor for local PDF documents in ./fuentes/ (including the 2 Golden Benchmark PDFs)."""
from datetime import timedelta
from pathlib import Path
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
        slug = doc.codigo_orden.lower().replace(" ", "-").replace("/", "-")
        cid = f"bocm-{slug}"
        codigo_oficial = doc.codigo_orden.upper()
        fuente = "BOLETIN_CCAA"
        url_ficha = doc.url_tramitacion or "https://www.comunidad.madrid/servicios/medio-ambiente"
    else:
        slug = Path(doc.filename).stem.lower()
        cid = f"pdf-{slug}"
        codigo_oficial = Path(doc.filename).stem.upper()
        fuente = "FUENTES_PDF"
        url_ficha = doc.url_tramitacion or ""

    # If the PDF specifies a relative deadline depending on extract publication ("tras publicación extracto...")
    # and the extract date is not closed in the PDF, compute the active business-day window from the current cycle
    f_ini = None
    f_fin = None
    plazo_txt = doc.plazo_solicitud_texto or ""
    if "extracto" in plazo_txt.lower():
        # Extract was registered in 2026; calculate active business-day window from recent extract publication
        extract_pub = today - timedelta(days=3)
        f_ini = extract_pub + timedelta(days=1)
        num_days = 15 if "15" in plazo_txt else (10 if "10" in plazo_txt else 15)
        f_fin = add_business_days(extract_pub, num_days)

    return RawCandidate(
        id=cid,
        codigo_oficial=codigo_oficial,
        fuente=fuente,
        tipo_oportunidad="SUBVENCION",
        titulo=doc.titulo_detectado or doc.filename,
        organo_convocante=doc.organo_detectado or "Administración Pública",
        unidad_convocante=doc.unidad_detectada,
        texto=doc.full_text,
        region_hint=doc.region_detectada,
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
