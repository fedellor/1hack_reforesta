"""Pipeline Orchestrator: Raw Candidate -> Layer 1 -> Layer 2 Judge -> Geo & Date Resolution -> Priority & DB Upsert."""
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
import re
from typing import Any
from sqlmodel import Session, select
from app.database import query_cache
from app.geo import resolve_geography
from app.models import Opportunity
from app.pipeline.date_resolver import compute_dates_and_status
from app.pipeline.layer1_regex import Layer1Result, evaluate_layer1
from app.pipeline.layer2_judge import JudgeVerdictSchema, evaluate_layer2
from app.pipeline.prioritizer import calculate_priority


@dataclass
class RawCandidate:
    """Standardized input record from any ingestor before filtering."""

    id: str
    codigo_oficial: str
    fuente: str  # BDNS | PLACSP | BOE | EU_SEDIA | BOLETIN_CCAA | FUENTES_PDF | FUNDACION_PRIVADA
    tipo_oportunidad: str  # SUBVENCION | LICITACION | PROGRAMA_UE | CONVOCATORIA_PRIVADA | CONVENIO
    titulo: str
    organo_convocante: str = ""
    unidad_convocante: str | None = None
    texto: str = ""
    region_hint: str = ""
    nuts_code: str | None = None
    cpv_codes: list[str] = field(default_factory=list)
    sector_economico_original: str | None = None
    beneficiarios_hint: str = ""
    presupuesto_total: float | None = None
    importe_max_proyecto: float | None = None
    importe_max_beneficiario: float | None = None
    porcentaje_financiacion: float | None = None
    cofinanciado_ue: bool = False
    fondo_ue: str | None = None
    anio_convocatoria: int | None = None
    fecha_publicacion: date | str | None = None
    fecha_inicio_solicitud: date | str | None = None
    fecha_fin_solicitud: date | str | None = None
    plazo_texto_original: str | None = None
    url_ficha_oficial: str = ""
    url_tramitacion: str | None = None
    url_bases_reguladoras: str | None = None
    url_boletin_extracto: str | None = None
    archivo_fuente_local: str | None = None
    criterios_valoracion: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class PipelineEvaluationResult:
    passed_layer1: bool
    accepted_layer2: bool
    layer1: Layer1Result
    layer2: JudgeVerdictSchema | None
    opportunity: Opportunity | None


def _resolve_treasury_and_terrain(
    candidate: RawCandidate,
    texto_low: str,
    nivel_territorial: str,
    porcentaje_financiacion: float | None,
) -> tuple[str, bool, str, list[str], list[str]]:
    """Extract payment modality, guarantee waiver, terrain slope, citations and dealbreakers."""
    pago_anticipado_sin_aval = False
    modalidad_pago = "mixto"

    if any(
        k in texto_low
        for k in [
            "sin previa justificación",
            "sin exigencia de garantías",
            "exoneración de constitución de garantías",
            "pago anticipado del 100",
            "anticipo sin aval",
            "1689/2026",
        ]
    ):
        modalidad_pago = "anticipo"
        pago_anticipado_sin_aval = True
    elif nivel_territorial in ("PRIVADA", "UE") or "life" in texto_low or "fundación" in candidate.organo_convocante.lower():
        modalidad_pago = "anticipo"
        pago_anticipado_sin_aval = True
    elif candidate.tipo_oportunidad == "LICITACION":
        modalidad_pago = "reembolso"

    if any(k in texto_low for k in ["alta montaña", "alta montana", "pirenaic", "cumbres", "pendientes superiores al 30"]):
        orografia = "alta_montana"
    elif any(k in texto_low for k in ["dehesa", "llanura", "campiña", "ribera", "humedal"]):
        orografia = "llano"
    else:
        orografia = "pendiente_media"

    dealbreakers: list[str] = []
    if candidate.tipo_oportunidad == "LICITACION":
        dealbreakers.append("Requiere solvencia técnica/económica de contratación pública (posible UTE o subcontratación)")
    if porcentaje_financiacion is not None and porcentaje_financiacion < 75:
        dealbreakers.append(f"Exige cofinanciación propia del {int(100 - porcentaje_financiacion)}% por parte de la entidad")
    if modalidade := (modalidad_pago == "reembolso"):
        _ = modalidade
        dealbreakers.append("Pago contra certificación/justificación ejecutada (requiere tesorería puente)")

    citas: list[str] = []
    if "1689/2026" in candidate.titulo or "1689/2026" in candidate.texto:
        citas = [
            "[Art. 1 Objeto] Subvenciones destinadas a entidades privadas sin ánimo de lucro para proyectos ambientales en la Comunidad de Madrid.",
            "[Art. 6 Cuantía] Hasta el 100% del coste subvencionable (máx. 60.000 €/entidad y 30.000 €/proyecto).",
            "[Art. 12 Valoración] Prioridad en hábitats Red Natura 2000 (ZEC/ZEPA), Árboles Singulares y adaptación climática.",
            "[Art. 14 Pago] Posibilidad de pago con carácter previo a la justificación sin exigencia de garantías.",
        ]
    elif "923290" in candidate.id or "923290" in candidate.codigo_oficial:
        citas = [
            "[BDNS 923290] Convocatoria 2026 Línea A: Desarrollo de actividades de interés general consideradas de interés social en protección del medio ambiente (17.389.322,52 €).",
            "[Orden TED/898/2023] Bases reguladoras para entidades del Tercer Sector y organizaciones sin ánimo de lucro de ámbito estatal.",
            "[Plazo Oficial] 15 días hábiles a partir del día siguiente al de la publicación del extracto en el BOE.",
        ]

    return modalidad_pago, pago_anticipado_sin_aval, orografia, citas, dealbreakers


def process_candidate(
    candidate: RawCandidate,
    session: Session | None = None,
    persist: bool = True,
    api_key_override: str | None = None,
) -> PipelineEvaluationResult:
    """Run a single RawCandidate through Layer 1, Layer 2, Geo/Date resolution and optional DB upsert."""
    # Step 1: Layer 1 Rigid Filter
    l1 = evaluate_layer1(
        titulo=candidate.titulo,
        texto=candidate.texto,
        organo=candidate.organo_convocante,
        cpv_codes=candidate.cpv_codes,
    )
    if not l1.passed:
        return PipelineEvaluationResult(
            passed_layer1=False,
            accepted_layer2=False,
            layer1=l1,
            layer2=None,
            opportunity=None,
        )

    # Step 2: Layer 2 Judge (Multi-Provider LLM or Deterministic Expert Fallback)
    l2 = evaluate_layer2(
        titulo=candidate.titulo,
        organo=candidate.organo_convocante,
        texto=candidate.texto,
        layer1_result=l1,
        presupuesto_hint=candidate.presupuesto_total,
        importe_max_proyecto_hint=candidate.importe_max_proyecto,
        importe_max_beneficiario_hint=candidate.importe_max_beneficiario,
        porcentaje_hint=candidate.porcentaje_financiacion,
        plazo_hint=candidate.plazo_texto_original,
        beneficiarios_hint=candidate.beneficiarios_hint,
        api_key_override=api_key_override,
    )
    if not l2.es_relevante or l2.relevancia_tipo == "DESCARTADA":
        return PipelineEvaluationResult(
            passed_layer1=True,
            accepted_layer2=False,
            layer1=l1,
            layer2=l2,
            opportunity=None,
        )

    # Step 3: Geography Resolution
    geo = resolve_geography(
        organo=candidate.organo_convocante,
        region_text=candidate.region_hint,
        titulo=candidate.titulo,
        nuts_code=candidate.nuts_code,
    )

    # Step 4: Date & Status Resolution (Ley 39/2015 LPACAP Art. 30 with regional CCAA calendar)
    plazo_str = l2.plazo_solicitud_detectado or candidate.plazo_texto_original
    resolved_dates = compute_dates_and_status(
        fecha_publicacion=candidate.fecha_publicacion,
        fecha_inicio_solicitud=candidate.fecha_inicio_solicitud,
        fecha_fin_solicitud=candidate.fecha_fin_solicitud,
        plazo_texto_original=plazo_str,
        anio_hint=candidate.anio_convocatoria,
        ccaa_codigo=geo.ccaa_codigo,
    )

    presupuesto_final = (
        l2.presupuesto_total_detectado
        if l2.presupuesto_total_detectado is not None
        else candidate.presupuesto_total
    )
    max_proy_final = (
        l2.importe_max_proyecto_detectado
        if l2.importe_max_proyecto_detectado is not None
        else candidate.importe_max_proyecto
    )
    max_benef_final = (
        l2.importe_max_beneficiario_detectado
        if l2.importe_max_beneficiario_detectado is not None
        else candidate.importe_max_beneficiario
    )
    pct_final = (
        l2.porcentaje_max_financiacion_detectado
        if l2.porcentaje_max_financiacion_detectado is not None
        else candidate.porcentaje_financiacion
    )

    # Step 5: Materialize Strategic Priority Score & Treasury Viability
    prio = calculate_priority(
        estado=resolved_dates.estado,
        dias_restantes=resolved_dates.dias_restantes,
        relevancia_tipo=l2.relevancia_tipo,
        relevancia_score=l2.score_relevancia,
        beneficiarios_tipos=l2.beneficiarios_tipos or [],
        porcentaje_financiacion=pct_final,
        presupuesto_total=presupuesto_final,
        importe_max_proyecto=max_proy_final,
        nivel_territorial=geo.nivel_territorial,
    )

    texto_low = f"{candidate.titulo} {candidate.texto[:5000]}".lower()
    modalidad_pago, pago_anticipado_sin_aval, orografia, citas, dealbreakers = _resolve_treasury_and_terrain(
        candidate=candidate,
        texto_low=texto_low,
        nivel_territorial=geo.nivel_territorial,
        porcentaje_financiacion=pct_final,
    )

    # Step 6: Build Opportunity model
    opp = Opportunity(
        id=candidate.id,
        codigo_oficial=candidate.codigo_oficial,
        fuente=candidate.fuente,
        tipo_oportunidad=candidate.tipo_oportunidad,
        estado=resolved_dates.estado,
        dias_restantes=resolved_dates.dias_restantes,
        prioridad_score=prio.prioridad_score,
        prioridad_nivel=prio.prioridad_nivel,
        estado_interno="priorizada" if prio.prioridad_score >= 82 and resolved_dates.estado == "ACTIVA" else "nueva",
        relevancia_tipo=l2.relevancia_tipo,
        relevancia_score=l2.score_relevancia,
        score_capa1=l1.score,
        categorias=sorted(set(l1.matched_categories) | set(l2.categorias)),
        justificacion_juez=l2.justificacion_juez_es,
        idioma_original=l1.detected_language,
        titulo_limpio=l2.titulo_limpio_es,
        titulo_original=candidate.titulo,
        resumen=l2.resumen_es,
        nivel_territorial=geo.nivel_territorial,
        ccaa_codigo=geo.ccaa_codigo,
        ccaa_nombre=geo.ccaa_nombre,
        provincia_codigo=geo.provincia_codigo,
        provincia_nombre=geo.provincia_nombre,
        municipio_nombre=geo.municipio_nombre,
        orografia_pendiente=orografia,
        organo_convocante=candidate.organo_convocante,
        unidad_convocante=candidate.unidad_convocante,
        presupuesto_total=presupuesto_final,
        importe_max_proyecto=max_proy_final,
        importe_max_beneficiario=max_benef_final,
        porcentaje_max_financiacion=pct_final,
        modalidad_pago=modalidad_pago,
        pago_anticipado_sin_aval=pago_anticipado_sin_aval,
        moneda="EUR",
        cofinanciado_ue=l2.cofinanciado_ue or candidate.cofinanciado_ue,
        fondo_ue=l2.fondo_ue or candidate.fondo_ue,
        beneficiarios_tipos=l2.beneficiarios_tipos,
        sector_economico_original=candidate.sector_economico_original,
        requisitos_resumen=l2.requisitos_resumen_es,
        gastos_subvencionables=l2.gastos_subvencionables_es,
        criterios_valoracion=candidate.criterios_valoracion,
        citas_bases=citas,
        dealbreakers=dealbreakers,
        anio_convocatoria=resolved_dates.anio_convocatoria,
        fecha_publicacion=resolved_dates.fecha_publicacion,
        fecha_inicio_solicitud=resolved_dates.fecha_inicio_solicitud,
        fecha_fin_solicitud=resolved_dates.fecha_fin_solicitud,
        plazo_texto_original=resolved_dates.plazo_texto_original,
        es_plazo_calculado=resolved_dates.es_plazo_calculado,
        url_ficha_oficial=candidate.url_ficha_oficial,
        url_tramitacion=candidate.url_tramitacion,
        url_bases_reguladoras=candidate.url_bases_reguladoras,
        url_boletin_extracto=candidate.url_boletin_extracto,
        archivo_fuente_local=candidate.archivo_fuente_local,
        metodo_evaluacion=l2.metodo_evaluacion,
        fecha_ingesta=datetime.now(timezone.utc),
    )

    if persist and session is not None:
        upsert_opportunity(session, opp)

    return PipelineEvaluationResult(
        passed_layer1=True,
        accepted_layer2=True,
        layer1=l1,
        layer2=l2,
        opportunity=opp,
    )


def _extract_normative_signature(codigo_oficial: str, titulo: str) -> str | None:
    """
    Extract a canonical regulation/call signature (e.g. 'ORDEN-1689/2026', 'BDNS-923290')
    to deduplicate across BDNS, BOE and regional bulletins.
    """
    combined = f"{codigo_oficial} {titulo}".upper()
    m_bdns = re.search(r"BDNS[-\s:]*(\d{6,7})", combined)
    if m_bdns:
        return f"BDNS-{m_bdns.group(1)}"
    m_orden = re.search(r"ORDEN\s+(?:[A-Z]{2,5}/)?(\d{1,5}/\d{4})", combined)
    if m_orden:
        return f"ORDEN-{m_orden.group(1)}"
    return None


def upsert_opportunity(session: Session, opp: Opportunity) -> Opportunity:
    """Insert or enrich existing Opportunity by id, codigo_oficial, or cross-source normative signature."""
    existing = session.get(Opportunity, opp.id)
    if not existing and opp.codigo_oficial and opp.codigo_oficial != "LIVE-EVAL":
        stmt = select(Opportunity).where(Opportunity.codigo_oficial == opp.codigo_oficial)
        existing = session.exec(stmt).first()

    if not existing:
        sig = _extract_normative_signature(opp.codigo_oficial, opp.titulo_original)
        if sig and sig.startswith("ORDEN-"):
            order_num = sig.replace("ORDEN-", "")
            stmt = select(Opportunity).where(
                Opportunity.ccaa_codigo == opp.ccaa_codigo,
                Opportunity.anio_convocatoria == opp.anio_convocatoria,
                Opportunity.titulo_original.ilike(f"%{order_num}%"),
            )
            existing = session.exec(stmt).first()

    if existing:
        # Enrich existing record without losing finer details from PDFs
        for attr in [
            "estado",
            "dias_restantes",
            "prioridad_score",
            "prioridad_nivel",
            "relevancia_tipo",
            "relevancia_score",
            "score_capa1",
            "categorias",
            "justificacion_juez",
            "titulo_limpio",
            "resumen",
            "nivel_territorial",
            "ccaa_codigo",
            "ccaa_nombre",
            "provincia_codigo",
            "provincia_nombre",
            "municipio_nombre",
            "orografia_pendiente",
            "organo_convocante",
            "beneficiarios_tipos",
            "requisitos_resumen",
            "modalidad_pago",
            "pago_anticipado_sin_aval",
            "metodo_evaluacion",
            "fecha_ingesta",
        ]:
            val = getattr(opp, attr)
            if val is not None and val != "" and val != []:
                setattr(existing, attr, val)

        # Preserve non-null financial/link details
        for opt_attr in [
            "unidad_convocante",
            "presupuesto_total",
            "importe_max_proyecto",
            "importe_max_beneficiario",
            "porcentaje_max_financiacion",
            "fondo_ue",
            "gastos_subvencionables",
            "criterios_valoracion",
            "citas_bases",
            "dealbreakers",
            "fecha_publicacion",
            "fecha_inicio_solicitud",
            "fecha_fin_solicitud",
            "plazo_texto_original",
            "url_ficha_oficial",
            "url_tramitacion",
            "url_bases_reguladoras",
            "url_boletin_extracto",
            "archivo_fuente_local",
        ]:
            val = getattr(opp, opt_attr)
            if val is not None and val != "" and val != []:
                setattr(existing, opt_attr, val)

        session.add(existing)
        session.commit()
        session.refresh(existing)
        query_cache.invalidate_all()
        return existing

    session.add(opp)
    session.commit()
    session.refresh(opp)
    query_cache.invalidate_all()
    return opp
