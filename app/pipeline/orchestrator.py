"""Pipeline Orchestrator: Raw Candidate -> Layer 1 -> Layer 2 Judge -> Geo & Date Resolution -> Dedup/Amendments -> Priority & DB Upsert."""
from dataclasses import dataclass, replace, field
from datetime import date, datetime, timezone
from difflib import SequenceMatcher
import re
from typing import Any
import unicodedata
from sqlmodel import Session, select
from app.config import settings
from app.database import query_cache
from app.domain.reforesta_profile import assess_reforesta_eligibility
from app.geo import resolve_geography
from app.models import Opportunity
from app.pipeline.date_resolver import add_business_days, compute_dates_and_status, parse_spanish_date
from app.pipeline.layer1_regex import Layer1Result, evaluate_layer1
from app.pipeline.layer2_judge import JudgeVerdictSchema, evaluate_layer2
from app.pipeline.metadata_extractor import extract_deadline_clause_and_date
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
    amendment_applied: str | None = None


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
    """
    Run a single RawCandidate through Layer 1, Layer 2 (with persistent DB cache),
    Geo/Date resolution, Amendment (Ampliación/Corrección) detection, Semantic Dedup and DB Upsert.
    """
    amendment_type = _detect_amendment_type(candidate.titulo, candidate.texto)
    referenced_existing: Opportunity | None = None

    # Step 1: Layer 1 Rigid Filter
    l1 = evaluate_layer1(
        titulo=candidate.titulo,
        texto=candidate.texto,
        organo=candidate.organo_convocante,
        cpv_codes=candidate.cpv_codes,
    )
    if not l1.passed:
        # Amendment Rescue: if an official bulletin publishes a terse "Ampliación de plazo" /
        # "Corrección de errores" referencing an already-approved call in DB (and is not noise), apply it.
        if (
            amendment_type is not None
            and session is not None
            and not (l1.rejection_reason or "").startswith("Ruido")
        ):
            referenced_existing = _find_amendment_target(
                session=session,
                codigo_oficial=candidate.codigo_oficial,
                titulo=candidate.titulo,
                organo=candidate.organo_convocante,
                ccaa_hint=candidate.region_hint,
            )
            if referenced_existing is not None:
                l1 = Layer1Result(
                    passed=True,
                    decision="PASS_CANDIDATE",
                    score=60,
                    preliminary_relevance=referenced_existing.relevancia_tipo,
                    detected_language=l1.detected_language,
                    matched_categories=referenced_existing.categorias or [],
                    matched_terms=[amendment_type.lower(), referenced_existing.codigo_oficial],
                )

    if not l1.passed:
        return PipelineEvaluationResult(
            passed_layer1=False,
            accepted_layer2=False,
            layer1=l1,
            layer2=None,
            opportunity=None,
        )

    # If this is an amendment that directly references an existing approved record, apply amendment fast/accurately
    if amendment_type is not None and session is not None:
        if referenced_existing is None:
            referenced_existing = _find_amendment_target(
                session=session,
                codigo_oficial=candidate.codigo_oficial,
                titulo=candidate.titulo,
                organo=candidate.organo_convocante,
                ccaa_hint=candidate.region_hint,
            )
        if referenced_existing is not None and persist:
            updated_opp = _apply_amendment_to_existing(
                session=session,
                existing=referenced_existing,
                amendment_type=amendment_type,
                candidate=candidate,
            )
            synthetic_verdict = JudgeVerdictSchema(
                es_relevante=True,
                relevancia_tipo=updated_opp.relevancia_tipo if updated_opp.relevancia_tipo in ("DIRECTA", "INDIRECTA_ELEGIBLE") else "INDIRECTA_ELEGIBLE",
                score_relevancia=updated_opp.relevancia_score,
                categorias=updated_opp.categorias or [],
                titulo_limpio_es=updated_opp.titulo_limpio,
                resumen_es=updated_opp.resumen,
                justificacion_juez_es=f"Actualizada automáticamente mediante {amendment_type} ({candidate.codigo_oficial}).",
                beneficiarios_tipos=updated_opp.beneficiarios_tipos or [],
                metodo_evaluacion="AMENDMENT_SYNC",
            )
            return PipelineEvaluationResult(
                passed_layer1=True,
                accepted_layer2=True,
                layer1=l1,
                layer2=synthetic_verdict,
                opportunity=updated_opp,
                amendment_applied=amendment_type,
            )

    # Step 2: Layer 2 Judge (Multi-Provider LLM + Persistent DB Cache + Deterministic Expert Fallback)
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
        session=session,
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
    if candidate.fuente == "FUNDACION_PRIVADA" or candidate.tipo_oportunidad == "CONVOCATORIA_PRIVADA":
        geo = replace(geo, nivel_territorial="PRIVADA")

    # Step 4: Date & Status Resolution (Ley 39/2015 LPACAP Art. 30 with regional CCAA calendar)
    plazo_str, extracted_end_date = extract_deadline_clause_and_date(
        texto=f"{candidate.titulo}\n{candidate.texto}",
        existing_clause=l2.plazo_solicitud_detectado or candidate.plazo_texto_original,
        existing_end_date=candidate.fecha_fin_solicitud,
    )
    resolved_end_str = extracted_end_date or candidate.fecha_fin_solicitud
    resolved_anio_hint = candidate.anio_convocatoria
    # Detect explicitly closed past-year titles without explicit deadline (e.g. "Cerrada Ayudas ... 2025")
    if not resolved_end_str:
        m_past_closed = re.search(
            r"\b(?:cerrad[oa]|plazo\s+cerrado|finalizad[oa])\b[^0-9]{0,60}\b(20(?:1[6-9]|2[0-5]))\b",
            f"{candidate.titulo} {candidate.texto[:300]}",
            re.IGNORECASE,
        )
        if m_past_closed:
            past_yr = int(m_past_closed.group(1))
            resolved_anio_hint = resolved_anio_hint or past_yr
            if past_yr < settings.get_today().year:
                resolved_end_str = f"{past_yr}-12-31"
    resolved_dates = compute_dates_and_status(
        fecha_publicacion=candidate.fecha_publicacion,
        fecha_inicio_solicitud=candidate.fecha_inicio_solicitud,
        fecha_fin_solicitud=resolved_end_str,
        plazo_texto_original=plazo_str,
        anio_hint=resolved_anio_hint,
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

    # Step 5: Strict Eligibility Verification for Asociación Reforesta & Strategic Prioritization
    requisitos_final = l2.requisitos_resumen_es
    if candidate.beneficiarios_hint and "Beneficiarios oficiales:" not in requisitos_final:
        requisitos_final = f"Beneficiarios oficiales: {candidate.beneficiarios_hint}. {requisitos_final}".strip()

    elig = assess_reforesta_eligibility(
        titulo=candidate.titulo,
        organo=candidate.organo_convocante,
        texto=candidate.texto,
        beneficiarios_hint=candidate.beneficiarios_hint,
        tipo_oportunidad=candidate.tipo_oportunidad,
        nivel_territorial=geo.nivel_territorial,
        ccaa_codigo=geo.ccaa_codigo,
        ccaa_nombre=geo.ccaa_nombre,
        requisitos_resumen=requisitos_final,
        codigo_oficial=candidate.codigo_oficial,
        justificacion_juez=l2.justificacion_juez_es,
    )

    prio = calculate_priority(
        estado=resolved_dates.estado,
        dias_restantes=resolved_dates.dias_restantes,
        relevancia_tipo=l2.relevancia_tipo,
        relevancia_score=l2.score_relevancia,
        beneficiarios_tipos=elig.beneficiarios_tipos,
        porcentaje_financiacion=pct_final,
        presupuesto_total=presupuesto_final,
        importe_max_proyecto=max_proy_final,
        nivel_territorial=geo.nivel_territorial,
    )

    texto_low = f"{candidate.titulo} {candidate.texto[:5000]}".lower()
    modalidad_pago, pago_anticipado_sin_aval, orografia, citas, treasury_dealbreakers = _resolve_treasury_and_terrain(
        candidate=candidate,
        texto_low=texto_low,
        nivel_territorial=geo.nivel_territorial,
        porcentaje_financiacion=pct_final,
    )
    dealbreakers = list(dict.fromkeys([*elig.dealbreakers, *treasury_dealbreakers]))

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
        estado_interno="priorizada" if elig.elegible and prio.prioridad_score >= 82 and resolved_dates.estado == "ACTIVA" else "nueva",
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
        beneficiarios_tipos=elig.beneficiarios_tipos,
        sector_economico_original=candidate.sector_economico_original,
        requisitos_resumen=requisitos_final,
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


_STOPWORDS_SIM = {
    "de", "del", "la", "las", "el", "los", "un", "una", "unos", "unas",
    "para", "por", "con", "sin", "sobre", "entre", "hacia", "mediante",
    "y", "e", "o", "u", "en", "a", "al", "se", "su", "sus",
    "per", "amb", "els", "les", "als", "dels", "pola", "polos", "das", "dos",
    "the", "and", "for", "of", "in", "to", "on", "with", "by",
}

_BOILERPLATE_PREFIX_RE = re.compile(
    r"^(?:"
    r"ampliacion\s+(?:de\s+|del\s+)?plazo\s+(?:de\s+(?:presentacion\s+de\s+solicitudes\s+)?)?(?:de\s+la\s+|de\s+)?|"
    r"prorroga\s+(?:de\s+|del\s+)?plazo\s+(?:de\s+)?|"
    r"correccion\s+de\s+errores\s+(?:de\s+la\s+|del\s+|de\s+)?|"
    r"modificacion\s+(?:de\s+la\s+|del\s+)?|"
    r"extracto\s+de\s+la\s+(?:orden|resolucion)\s+(?:de\s+[^,]{3,40},\s+)?(?:por\s+la\s+que\s+se\s+)?|"
    r"(?:orden|resolucion|decreto|orde|resolucio)\s+(?:[a-z0-9/.\-]+\s+)?por\s+(?:la|a)\s+que\s+se\s+"
    r"(?:convocan|aprueban|establecen|regulan)\s+"
    r")",
    re.IGNORECASE,
)


def _strip_accents(text: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", text) if not unicodedata.combining(ch)
    )


def _normalize_for_similarity(text: str, strip_amendment_prefix: bool = True) -> tuple[str, set[str]]:
    clean = _strip_accents(text.lower())
    if strip_amendment_prefix:
        clean = _BOILERPLATE_PREFIX_RE.sub("", clean).strip()
    tokens = [
        tok
        for tok in re.findall(r"[a-z0-9]+", clean)
        if tok not in _STOPWORDS_SIM and (len(tok) >= 3 or tok in {"a", "b", "ue"})
    ]
    return " ".join(tokens), set(tokens)


def _char_trigrams(s: str) -> set[str]:
    padded = f"  {s}  "
    if len(padded) < 3:
        return {padded}
    return {padded[i : i + 3] for i in range(len(padded) - 2)}


def _semantic_similarity(
    title_a: str,
    org_a: str,
    title_b: str,
    org_b: str,
) -> tuple[float, float]:
    """Return (title_similarity, org_overlap) using normalized trigram Jaccard + token Jaccard + SequenceMatcher."""
    norm_a, tok_a = _normalize_for_similarity(title_a)
    norm_b, tok_b = _normalize_for_similarity(title_b)
    if not norm_a or not norm_b:
        return 0.0, 0.0

    tri_a = _char_trigrams(norm_a)
    tri_b = _char_trigrams(norm_b)
    tri_jaccard = len(tri_a & tri_b) / max(1, len(tri_a | tri_b))
    tok_jaccard = len(tok_a & tok_b) / max(1, len(tok_a | tok_b))
    seq_ratio = SequenceMatcher(None, norm_a, norm_b).ratio()
    title_sim = 0.45 * tri_jaccard + 0.35 * tok_jaccard + 0.20 * seq_ratio

    _, org_tok_a = _normalize_for_similarity(org_a, strip_amendment_prefix=False)
    _, org_tok_b = _normalize_for_similarity(org_b, strip_amendment_prefix=False)
    if org_tok_a and org_tok_b:
        org_overlap = len(org_tok_a & org_tok_b) / max(1, len(org_tok_a | org_tok_b))
    else:
        org_overlap = 0.0

    return title_sim, org_overlap


def _detect_amendment_type(titulo: str, texto: str) -> str | None:
    """Detect whether a bulletin notice extends a deadline or corrects an existing call."""
    head = f"{titulo} {texto[:800]}".lower()
    if re.search(
        r"\b(ampliaci[oó]n\s+(?:de\s+|del\s+)?plazo|se\s+ampl[ií]a\s+(?:el\s+|en\s+[\w]+\s+[^.]{0,30})?plazo|"
        r"pr[oó]rroga\s+(?:de\s+|del\s+)?plazo|se\s+prorroga\s+el\s+plazo|ampliaci[oó]\s+de\s+termini|ampliaci[oó]n\s+do\s+prazo)\b",
        head,
    ):
        return "AMPLIACION_PLAZO"
    if re.search(
        r"\b(correcci[oó]n\s+de\s+errores|modificaci[oó]n\s+del?\s+extracto|correcci[oó]\s+d['’]?errades|correcci[oó]n\s+de\s+erros)\b",
        head,
    ):
        return "CORRECCION_ERRORES"
    return None


def _extract_normative_signatures(codigo_oficial: str, titulo: str) -> list[str]:
    """
    Extract canonical regulation/call signatures (e.g. ['ORDEN-1689/2026', 'BDNS-923290'])
    to deduplicate across BDNS, BOE and regional bulletins.
    """
    combined = f"{codigo_oficial} {titulo}".upper()
    sigs: list[str] = []
    m_orden = re.search(r"ORDEN\s+(?:[A-Z]{2,5}/)?(\d{1,5}/\d{4})", combined)
    if m_orden:
        sigs.append(f"ORDEN-{m_orden.group(1)}")
    m_bdns = re.search(r"BDNS[-\s:]*(\d{6,7})", combined)
    if m_bdns:
        sigs.append(f"BDNS-{m_bdns.group(1)}")
    return sigs


def _have_conflicting_signatures(sigs_a: list[str], sigs_b: list[str]) -> bool:
    """Prevent semantic dedup from merging two calls that explicitly carry different BDNS or Orden codes."""
    ord_a = {s for s in sigs_a if s.startswith("ORDEN-")}
    ord_b = {s for s in sigs_b if s.startswith("ORDEN-")}
    if ord_a and ord_b and ord_a.isdisjoint(ord_b):
        return True
    bdns_a = {s for s in sigs_a if s.startswith("BDNS-")}
    bdns_b = {s for s in sigs_b if s.startswith("BDNS-")}
    if bdns_a and bdns_b and bdns_a.isdisjoint(bdns_b):
        return True
    return False


def _find_by_normative_signature(
    session: Session,
    sigs: list[str],
    ccaa_codigo: str | None = None,
    anio: int | None = None,
) -> Opportunity | None:
    for sig in sigs:
        if sig.startswith("ORDEN-"):
            order_num = sig.replace("ORDEN-", "")
            stmt = select(Opportunity).where(
                Opportunity.titulo_original.ilike(f"%{order_num}%")
                | Opportunity.codigo_oficial.ilike(f"%{order_num}%")
            )
            if anio:
                stmt = stmt.where(Opportunity.anio_convocatoria == anio)
            if ccaa_codigo and ccaa_codigo not in ("ES", "EU"):
                matches = list(session.exec(stmt).all())
                for m in matches:
                    if m.ccaa_codigo in (ccaa_codigo, "ES"):
                        return m
            else:
                first = session.exec(stmt).first()
                if first:
                    return first
        elif sig.startswith("BDNS-"):
            stmt = select(Opportunity).where(Opportunity.codigo_oficial == sig)
            first = session.exec(stmt).first()
            if first:
                return first
    return None


def _find_amendment_target(
    session: Session,
    codigo_oficial: str,
    titulo: str,
    organo: str,
    ccaa_hint: str = "",
) -> Opportunity | None:
    """Locate the original DB Opportunity referenced by a deadline extension or errata bulletin."""
    sigs = _extract_normative_signatures(codigo_oficial, titulo)
    if sigs:
        hit = _find_by_normative_signature(session, sigs)
        if hit is not None:
            return hit

    # Fallback: semantic match against existing records without requiring date proximity
    all_opps = list(session.exec(select(Opportunity)).all())
    best: Opportunity | None = None
    best_score = 0.0
    for candidate_opp in all_opps:
        if _detect_amendment_type(candidate_opp.titulo_original or "", ""):
            continue
        title_sim, org_ov = _semantic_similarity(
            titulo,
            organo,
            candidate_opp.titulo_limpio or candidate_opp.titulo_original,
            candidate_opp.organo_convocante,
        )
        ccaa_bonus = 0.08 if ccaa_hint and candidate_opp.ccaa_codigo == ccaa_hint else 0.0
        combined = title_sim + 0.15 * org_ov + ccaa_bonus
        if title_sim >= 0.45 and combined > best_score:
            best_score = combined
            best = candidate_opp
    return best if best_score >= 0.56 else None


def _apply_amendment_to_existing(
    session: Session,
    existing: Opportunity,
    amendment_type: str,
    candidate: RawCandidate,
) -> Opportunity:
    """
    Update an existing Opportunity in-place when an Ampliación de Plazo or Corrección de Errores
    is published: updates fecha_fin_solicitud, status, countdown, citations & priority score.
    """
    new_fin: date | None = parse_spanish_date(candidate.fecha_fin_solicitud)
    new_plazo_text = candidate.plazo_texto_original

    if new_fin is None and new_plazo_text:
        new_fin = parse_spanish_date(new_plazo_text)

    combined_text = f"{candidate.titulo}. {candidate.texto}"
    if new_fin is None:
        m_until = re.search(
            r"(?:hasta\s+el|fins\s+al|ata\s+o|nueva\s+fecha[^:]{0,20}:)\s*([^\n.;]{5,45})",
            combined_text,
            re.IGNORECASE,
        )
        if m_until:
            new_fin = parse_spanish_date(m_until.group(1))

    if new_fin is None:
        m_ext_days = re.search(
            r"(?:ampl[ií]a|prorroga)(?:\s+el\s+plazo(?:\s+de\s+presentaci[oó]n(?:\s+de\s+solicitudes)?)?)?"
            r"\s+(?:en\s+)?(\d+|cinco|diez|quince|veinte)\s+d[ií]as\s+(h[aá]biles|naturales)?",
            combined_text,
            re.IGNORECASE,
        )
        word_map = {"cinco": 5, "diez": 10, "quince": 15, "veinte": 20}
        if m_ext_days:
            raw_n = m_ext_days.group(1).lower()
            kind = (m_ext_days.group(2) or "hábiles").lower()
            extra_days = int(raw_n) if raw_n.isdigit() else word_map.get(raw_n, 0)
            if extra_days > 0:
                anchor = existing.fecha_fin_solicitud or parse_spanish_date(candidate.fecha_publicacion) or settings.get_today()
                if "natural" in kind:
                    from datetime import timedelta as _td
                    from app.pipeline.date_resolver import roll_to_next_business_day
                    new_fin = roll_to_next_business_day(anchor + _td(days=extra_days), ccaa_codigo=existing.ccaa_codigo)
                else:
                    new_fin = add_business_days(anchor, extra_days, ccaa_codigo=existing.ccaa_codigo)
                new_plazo_text = f"Ampliación de {extra_days} días {kind} sobre el cierre previo"

    if new_fin is not None and (
        existing.fecha_fin_solicitud is None
        or amendment_type == "CORRECCION_ERRORES"
        or new_fin >= existing.fecha_fin_solicitud
    ):
        existing.fecha_fin_solicitud = new_fin
        if new_plazo_text:
            existing.plazo_texto_original = new_plazo_text
        else:
            existing.plazo_texto_original = f"{amendment_type}: hasta el {new_fin.isoformat()}"

    # Apply revised budget if published in Corrección de Errores
    if amendment_type == "CORRECCION_ERRORES" and candidate.presupuesto_total is not None:
        existing.presupuesto_total = candidate.presupuesto_total

    # Recompute status & remaining days under today's date
    resolved = compute_dates_and_status(
        fecha_publicacion=existing.fecha_publicacion,
        fecha_inicio_solicitud=existing.fecha_inicio_solicitud,
        fecha_fin_solicitud=existing.fecha_fin_solicitud,
        plazo_texto_original=existing.plazo_texto_original,
        anio_hint=existing.anio_convocatoria,
        ccaa_codigo=existing.ccaa_codigo,
    )
    existing.estado = resolved.estado
    existing.dias_restantes = resolved.dias_restantes

    # Append trace note in citations and enrich official links
    fin_label = existing.fecha_fin_solicitud.isoformat() if existing.fecha_fin_solicitud else "según texto"
    note = f"[{amendment_type} - {candidate.codigo_oficial}] Actualización aplicada (cierre: {fin_label}): {candidate.titulo[:140]}"
    existing_citas = list(existing.citas_bases or [])
    if note not in existing_citas:
        existing_citas.append(note)
        existing.citas_bases = existing_citas
    if candidate.url_ficha_oficial and not existing.url_boletin_extracto:
        existing.url_boletin_extracto = candidate.url_ficha_oficial
    if candidate.url_bases_reguladoras and not existing.url_bases_reguladoras:
        existing.url_bases_reguladoras = candidate.url_bases_reguladoras

    prio = calculate_priority(
        estado=existing.estado,
        dias_restantes=existing.dias_restantes,
        relevancia_tipo=existing.relevancia_tipo,
        relevancia_score=existing.relevancia_score,
        beneficiarios_tipos=existing.beneficiarios_tipos or [],
        porcentaje_financiacion=existing.porcentaje_max_financiacion,
        presupuesto_total=existing.presupuesto_total,
        importe_max_proyecto=existing.importe_max_proyecto,
        nivel_territorial=existing.nivel_territorial,
    )
    existing.prioridad_score = prio.prioridad_score
    existing.prioridad_nivel = prio.prioridad_nivel
    existing.fecha_ingesta = datetime.now(timezone.utc)

    session.add(existing)
    session.commit()
    session.refresh(existing)
    query_cache.invalidate_all()
    return existing


def _extract_track_markers(text: str) -> set[str]:
    """Identify distinct sub-tracks (Línea A vs Línea B, Modalidad 1 vs 2, Lote 1 vs 2, Fase I vs II)."""
    clean = _strip_accents(text.lower())
    return {
        f"{m.group(1)}:{m.group(2)}"
        for m in re.finditer(
            r"\b(linea|modalidad|subprograma|lote|eje|fase|programa|anexo)\s+([a-z0-9]{1,4})\b",
            clean,
        )
    }


def _find_semantic_duplicate(session: Session, opp: Opportunity) -> Opportunity | None:
    """
    Fuzzy + trigram cross-portal semantic deduplication:
    Catches duplicates between regional portals, press releases, PLACSP and BDNS that lack
    a shared BDNS/Orden identifier while strictly respecting distinct explicit codes, sub-tracks and dates.
    """
    opp_sigs = _extract_normative_signatures(opp.codigo_oficial, opp.titulo_original)
    opp_tracks = _extract_track_markers(f"{opp.titulo_original} {opp.titulo_limpio}")
    stmt = select(Opportunity).where(Opportunity.anio_convocatoria == opp.anio_convocatoria)
    if opp.ccaa_codigo not in ("ES", "EU"):
        stmt = stmt.where(Opportunity.ccaa_codigo.in_([opp.ccaa_codigo, "ES"]))
    candidates = list(session.exec(stmt).all())

    for row in candidates:
        row_sigs = _extract_normative_signatures(row.codigo_oficial, row.titulo_original)
        if _have_conflicting_signatures(opp_sigs, row_sigs):
            continue

        row_tracks = _extract_track_markers(f"{row.titulo_original} {row.titulo_limpio}")
        if opp_tracks != row_tracks:
            continue

        # Date compatibility: within 7 days or at least one unknown
        if opp.fecha_fin_solicitud and row.fecha_fin_solicitud:
            if abs((opp.fecha_fin_solicitud - row.fecha_fin_solicitud).days) > 7:
                continue

        sim_orig, org_ov = _semantic_similarity(
            opp.titulo_original,
            opp.organo_convocante,
            row.titulo_original,
            row.organo_convocante,
        )
        sim_clean, _ = _semantic_similarity(
            opp.titulo_limpio,
            opp.organo_convocante,
            row.titulo_limpio,
            row.organo_convocante,
        )
        best_sim = max(sim_orig, sim_clean)
        if best_sim >= 0.76 or (best_sim >= 0.60 and org_ov >= 0.40):
            return row
    return None


def upsert_opportunity(session: Session, opp: Opportunity) -> Opportunity:
    """Insert or enrich existing Opportunity by id, codigo_oficial, normative signature, or semantic similarity."""
    existing = session.get(Opportunity, opp.id)
    if not existing and opp.codigo_oficial and opp.codigo_oficial != "LIVE-EVAL":
        stmt = select(Opportunity).where(Opportunity.codigo_oficial == opp.codigo_oficial)
        existing = session.exec(stmt).first()

    if not existing:
        sigs = _extract_normative_signatures(opp.codigo_oficial, opp.titulo_original)
        if sigs:
            existing = _find_by_normative_signature(
                session,
                sigs,
                ccaa_codigo=opp.ccaa_codigo,
                anio=opp.anio_convocatoria,
            )

    if not existing:
        existing = _find_semantic_duplicate(session, opp)

    if existing:
        # Enrich existing record without losing finer details or dates from PDFs
        for attr in [
            "relevancia_tipo",
            "score_capa1",
            "categorias",
            "nivel_territorial",
            "ccaa_codigo",
            "ccaa_nombre",
            "provincia_codigo",
            "provincia_nombre",
            "municipio_nombre",
            "orografia_pendiente",
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

        if opp.relevancia_score and opp.relevancia_score > (existing.relevancia_score or 0):
            existing.relevancia_score = opp.relevancia_score

        for text_attr in ("titulo_limpio", "resumen", "justificacion_juez", "organo_convocante"):
            old_val = getattr(existing, text_attr) or ""
            new_val = getattr(opp, text_attr) or ""
            if len(new_val) > len(old_val):
                setattr(existing, text_attr, new_val)

        # Preserve curated active window from local fuentes/ PDFs when an API omits dates
        if opp.archivo_fuente_local and opp.estado in ("ACTIVA", "PROXIMA"):
            if existing.estado == "CERRADA" and opp.fecha_fin_solicitud is not None:
                existing.estado = opp.estado
                existing.fecha_fin_solicitud = opp.fecha_fin_solicitud
                existing.dias_restantes = opp.dias_restantes
                if opp.fecha_inicio_solicitud is not None:
                    existing.fecha_inicio_solicitud = opp.fecha_inicio_solicitud
                if opp.plazo_texto_original:
                    existing.plazo_texto_original = opp.plazo_texto_original
            existing.archivo_fuente_local = opp.archivo_fuente_local

        # Prefer specific PDF links over generic portal URLs when enriching
        for url_attr in ("url_bases_reguladoras", "url_boletin_extracto"):
            cur_u = (getattr(existing, url_attr) or "").lower()
            new_u = getattr(opp, url_attr) or ""
            if new_u and (
                not cur_u
                or (".pdf" in new_u.lower() or "iddocumento=" in new_u.lower())
                and not (".pdf" in cur_u or "iddocumento=" in cur_u)
            ):
                setattr(existing, url_attr, new_u)

        # Preserve existing non-null financial/date/link details; fill missing gaps from new source
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
            "dias_restantes",
            "url_ficha_oficial",
            "url_tramitacion",
            "url_bases_reguladoras",
            "url_boletin_extracto",
            "archivo_fuente_local",
        ]:
            val = getattr(opp, opt_attr)
            if val is not None and val != "" and val != []:
                if getattr(existing, opt_attr) in (None, "", []):
                    setattr(existing, opt_attr, val)

        enriched_prio = calculate_priority(
            estado=existing.estado,
            dias_restantes=existing.dias_restantes,
            relevancia_tipo=existing.relevancia_tipo,
            relevancia_score=existing.relevancia_score,
            beneficiarios_tipos=existing.beneficiarios_tipos or [],
            porcentaje_financiacion=existing.porcentaje_max_financiacion,
            presupuesto_total=existing.presupuesto_total,
            importe_max_proyecto=existing.importe_max_proyecto,
            nivel_territorial=existing.nivel_territorial,
        )
        existing.prioridad_score = enriched_prio.prioridad_score
        existing.prioridad_nivel = enriched_prio.prioridad_nivel

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
