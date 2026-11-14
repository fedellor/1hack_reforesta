"""Pipeline Orchestrator: Raw Candidate -> Layer 1 -> Layer 2 Judge -> Geo & Date Resolution -> DB Upsert."""
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any
from sqlmodel import Session, select
from app.database import query_cache
from app.geo import resolve_geography
from app.models import Opportunity
from app.pipeline.date_resolver import compute_dates_and_status
from app.pipeline.layer1_regex import Layer1Result, evaluate_layer1
from app.pipeline.layer2_judge import JudgeVerdictSchema, evaluate_layer2


@dataclass
class RawCandidate:
    """Standardized input record from any ingestor before filtering."""

    id: str
    codigo_oficial: str
    fuente: str  # BDNS | PLACSP | BOE | EU_SEDIA | BOLETIN_CCAA | FUENTES_PDF
    tipo_oportunidad: str  # SUBVENCION | LICITACION | PROGRAMA_UE | CONVENIO
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

    # Step 4: Date & Status Resolution
    plazo_str = l2.plazo_solicitud_detectado or candidate.plazo_texto_original
    resolved_dates = compute_dates_and_status(
        fecha_publicacion=candidate.fecha_publicacion,
        fecha_inicio_solicitud=candidate.fecha_inicio_solicitud,
        fecha_fin_solicitud=candidate.fecha_fin_solicitud,
        plazo_texto_original=plazo_str,
        anio_hint=candidate.anio_convocatoria,
    )

    # Step 5: Build Opportunity model
    opp = Opportunity(
        id=candidate.id,
        codigo_oficial=candidate.codigo_oficial,
        fuente=candidate.fuente,
        tipo_oportunidad=candidate.tipo_oportunidad,
        estado=resolved_dates.estado,
        dias_restantes=resolved_dates.dias_restantes,
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
        organo_convocante=candidate.organo_convocante,
        unidad_convocante=candidate.unidad_convocante,
        presupuesto_total=l2.presupuesto_total_detectado if l2.presupuesto_total_detectado is not None else candidate.presupuesto_total,
        importe_max_proyecto=l2.importe_max_proyecto_detectado if l2.importe_max_proyecto_detectado is not None else candidate.importe_max_proyecto,
        importe_max_beneficiario=l2.importe_max_beneficiario_detectado if l2.importe_max_beneficiario_detectado is not None else candidate.importe_max_beneficiario,
        porcentaje_max_financiacion=l2.porcentaje_max_financiacion_detectado if l2.porcentaje_max_financiacion_detectado is not None else candidate.porcentaje_financiacion,
        moneda="EUR",
        cofinanciado_ue=l2.cofinanciado_ue or candidate.cofinanciado_ue,
        fondo_ue=l2.fondo_ue or candidate.fondo_ue,
        beneficiarios_tipos=l2.beneficiarios_tipos,
        sector_economico_original=candidate.sector_economico_original,
        requisitos_resumen=l2.requisitos_resumen_es,
        gastos_subvencionables=l2.gastos_subvencionables_es,
        criterios_valoracion=candidate.criterios_valoracion,
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


def upsert_opportunity(session: Session, opp: Opportunity) -> Opportunity:
    """Insert or enrich existing Opportunity by id or codigo_oficial."""
    existing = session.get(Opportunity, opp.id)
    if not existing and opp.codigo_oficial:
        stmt = select(Opportunity).where(Opportunity.codigo_oficial == opp.codigo_oficial)
        existing = session.exec(stmt).first()

    if existing:
        # Enrich existing record without losing finer details from PDFs
        for attr in [
            "estado",
            "dias_restantes",
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
            "organo_convocante",
            "beneficiarios_tipos",
            "requisitos_resumen",
            "metodo_evaluacion",
            "fecha_ingesta",
        ]:
            val = getattr(opp, attr)
            if val:
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
