"""Strategic Prioritization Engine for Reforesta ('Encontrar y Priorizar')."""
from dataclasses import dataclass


@dataclass(frozen=True)
class PriorityAssessment:
    prioridad_score: int        # 0..100
    prioridad_nivel: str        # CRITICA | ALTA | MEDIA | BAJA | HISTORICO
    urgencia_label: str         # CIERRE_INMINENTE | VENTANA_OPTIMA | PLAZO_AMPLIO | CERRADA
    recomendacion_tactica: str  # 1-line explanation of WHY this opportunity is prioritized


def calculate_priority(
    estado: str,
    dias_restantes: int | None,
    relevancia_tipo: str,
    relevancia_score: int,
    beneficiarios_tipos: list[str],
    porcentaje_financiacion: float | None,
    presupuesto_total: float | None,
    importe_max_proyecto: float | None,
    nivel_territorial: str,
) -> PriorityAssessment:
    """
    Compute an actionable priority score (0-100) to help Reforesta decide
    which open calls to apply to first, without writing the proposal itself.

    Weights:
    - 40% Thematic Fit (relevancia_score & DIRECTA vs INDIRECTA_ELEGIBLE)
    - 25% NGO / Environmental Entity Eligibility (ONG_FUNDACIONES, COMUNIDAD_MONTES, AYUNTAMIENTO partnership)
    - 20% Financial Attractiveness (% financing intensity + project/total grant size)
    - 15% Deadline Window Urgency (sweet spot: 5 to 30 days remaining)
    """
    if estado == "CERRADA":
        return PriorityAssessment(
            prioridad_score=min(50, int(relevancia_score * 0.5)),
            prioridad_nivel="HISTORICO",
            urgencia_label="CERRADA",
            recomendacion_tactica="Convocatoria cerrada (Archivo Histórico): útil como referencia de bases, importes y recurrencia anual.",
        )

    # 1. Thematic Fit (0..40 pts)
    thematic_pts = (relevancia_score / 100.0) * 34.0
    if relevancia_tipo == "DIRECTA":
        thematic_pts += 6.0
    else:
        thematic_pts += 3.0
    thematic_pts = min(40.0, thematic_pts)

    # 2. NGO / Reforesta Eligibility (0..25 pts)
    benef_set = {b.upper() for b in (beneficiarios_tipos or [])}
    if "ONG_FUNDACIONES" in benef_set:
        elig_pts = 25.0
        elig_note = "Elegible directamente para ONG/Asociación sin ánimo de lucro"
    elif "COMUNIDAD_MONTES" in benef_set or "AYUNTAMIENTO" in benef_set:
        elig_pts = 18.0
        elig_note = "Ideal para acudir en agrupación/convenio con Ayuntamiento o Comunidad de Montes"
    elif "UNIVERSIDAD_INVESTIGACION" in benef_set:
        elig_pts = 15.0
        elig_note = "Elegible en consorcio científico/técnico"
    else:
        elig_pts = 12.0
        elig_note = "Licitación/contrato técnico"

    # 3. Financial Attractiveness (0..20 pts)
    fin_pts = 10.0
    if porcentaje_financiacion is not None:
        if porcentaje_financiacion >= 95.0:
            fin_pts = 15.0
        elif porcentaje_financiacion >= 80.0:
            fin_pts = 13.0
        elif porcentaje_financiacion >= 60.0:
            fin_pts = 10.0
        else:
            fin_pts = 7.0

    ref_amount = importe_max_proyecto or presupuesto_total or 0.0
    if ref_amount >= 100000.0:
        fin_pts += 5.0
    elif ref_amount >= 25000.0:
        fin_pts += 4.0
    elif ref_amount > 0:
        fin_pts += 2.5
    fin_pts = min(20.0, fin_pts)

    # 4. Deadline Urgency Window (0..15 pts)
    if dias_restantes is None:
        urg_pts = 11.0
        urg_label = "VENTANA_OPTIMA"
        urg_note = "Plazo abierto vinculado a extracto oficial"
    elif dias_restantes <= 4:
        urg_pts = 13.0
        urg_label = "CIERRE_INMINENTE"
        urg_note = f"¡Cierre inminente en {dias_restantes} días!"
    elif 5 <= dias_restantes <= 25:
        urg_pts = 15.0
        urg_label = "VENTANA_OPTIMA"
        urg_note = f"Ventana óptima de preparación ({dias_restantes} días restantes)"
    else:
        urg_pts = 11.0
        urg_label = "PLAZO_AMPLIO"
        urg_note = f"Plazo holgado ({dias_restantes} días restantes)"

    total_score = int(round(min(100.0, thematic_pts + elig_pts + fin_pts + urg_pts)))

    if total_score >= 88:
        nivel = "CRITICA"
    elif total_score >= 76:
        nivel = "ALTA"
    elif total_score >= 60:
        nivel = "MEDIA"
    else:
        nivel = "BAJA"

    pct_str = f", financia hasta el {int(porcentaje_financiacion)}%" if porcentaje_financiacion else ""
    origen_tag = "RSC/Fundación Privada" if nivel_territorial == "PRIVADA" else f"Ámbito {nivel_territorial}"
    recomendacion = f"Prioridad {nivel} ({total_score}/100) [{origen_tag}]: {elig_note}{pct_str}. {urg_note}."

    return PriorityAssessment(
        prioridad_score=total_score,
        prioridad_nivel=nivel,
        urgencia_label=urg_label,
        recomendacion_tactica=recomendacion,
    )
