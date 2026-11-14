"""Predictive Recurrence Calendar (2020-2026) and Direct Exporters (CSV, iCal .ics, Markdown Dossier)."""
import csv
from datetime import date, datetime, timedelta, timezone
import io
from typing import Any
from app.config import settings
from app.models import Opportunity

MESES_ES = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre",
}


def build_predictive_calendar(
    opps: list[Opportunity],
    ccaa_filter: str | None = None,
    today: date | None = None,
) -> dict[str, Any]:
    """
    Build the Predictive Annual Recurrence Calendar based on the 2020-2026 historical corpus.
    Solves Reforesta's #1 operational bottleneck: short application windows (10-15 business days)
    by alerting which recurring calls are open now or entering their pre-publication preparation window.
    """
    ref_today = today or settings.get_today()
    current_month = ref_today.month

    recurring_programs: list[dict[str, Any]] = [
        {
            "programa_id": "REC-MITECO-LINEA-A",
            "nombre_programa": "Subvenciones MITECO Línea A (Tercer Sector - Protección del Medio Ambiente)",
            "organo_convocante": "Ministerio para la Transición Ecológica y el Reto Demográfico (MITECO)",
            "nivel_territorial": "ESTADO",
            "ccaa_codigo": "ES",
            "mes_apertura_habitual": 10,
            "plazo_tipico": "15 días hábiles tras extracto BOE",
            "presupuesto_tipico_eur": 17389322.52,
            "importe_max_proyecto_tipico_eur": 150000.0,
            "porcentaje_financiacion_tipico": 85.0,
            "modalidad_pago_habitual": "anticipo",
            "keywords_match": ["923290", "línea a", "orden ted/898/2023", "interés general"],
            "checklist_preparacion_previa": [
                "Certificado vigente de inscripción en Registro Nacional de Asociaciones / Utilidad Pública",
                "Memoria técnica de proyecto de ámbito supraautonómico o interés general estatal",
                "Presupuesto desglosado por partidas conforme a Orden TED/898/2023",
            ],
        },
        {
            "programa_id": "REC-CAM-ORDEN-ESAL",
            "nombre_programa": "Subvenciones Comunidad de Madrid a Entidades sin Ánimo de Lucro (Proyectos Ambientales y Red Natura 2000)",
            "organo_convocante": "Consejería de Medio Ambiente, Agricultura e Interior - Comunidad de Madrid",
            "nivel_territorial": "CCAA",
            "ccaa_codigo": "ES-MD",
            "mes_apertura_habitual": 10,
            "plazo_tipico": "10 días hábiles tras extracto BOCM (¡Ventana crítica muy corta!)",
            "presupuesto_tipico_eur": 500000.0,
            "importe_max_proyecto_tipico_eur": 30000.0,
            "porcentaje_financiacion_tipico": 100.0,
            "modalidad_pago_habitual": "anticipo",
            "keywords_match": ["1689/2026", "comunidad de madrid", "sin ánimo de lucro", "red natura 2000"],
            "checklist_preparacion_previa": [
                "Acuerdos previos de disponibilidad de terrenos en ZEC/ZEPA de la Comunidad de Madrid",
                "Cartografía SIG de parcelas y listado de especies autóctonas / Árboles Singulares",
                "Acreditación de experiencia de la entidad y del equipo técnico (Art. 12: hasta 20 puntos)",
                "Solicitud de pago anticipado sin exigencia de aval (Art. 14)",
            ],
        },
        {
            "programa_id": "REC-FBIO-RESTAURACION",
            "nombre_programa": "Convocatorias Fundación Biodiversidad (Restauración de Ecosistemas, Bosques y Bioeconomía Forestal)",
            "organo_convocante": "Fundación Biodiversidad F.S.P. (MITECO)",
            "nivel_territorial": "ESTADO",
            "ccaa_codigo": "ES",
            "mes_apertura_habitual": 11,
            "plazo_tipico": "30 a 45 días hábiles",
            "presupuesto_tipico_eur": 12500000.0,
            "importe_max_proyecto_tipico_eur": 1500000.0,
            "porcentaje_financiacion_tipico": 90.0,
            "modalidad_pago_habitual": "anticipo",
            "keywords_match": ["fundación biodiversidad", "bioeconomía"],
            "checklist_preparacion_previa": [
                "Acuerdo de agrupación con universidad/centro de investigación (requisito habitual de consorcio Científico-ONG)",
                "Plan de medición de indicadores de biodiversidad y absorción de carbono (MITECO)",
                "Plan de comunicación y participación ciudadana",
            ],
        },
        {
            "programa_id": "REC-UE-LIFE-NATURE",
            "nombre_programa": "Programa Europeo LIFE — Subprograma Naturaleza y Biodiversidad (SAP-NAT)",
            "organo_convocante": "Comisión Europea — Agencia Ejecutiva CINEA",
            "nivel_territorial": "UE",
            "ccaa_codigo": "EU",
            "mes_apertura_habitual": 4,
            "plazo_tipico": "Cierre anual en Septiembre-Noviembre (Portal Funding & Tenders)",
            "presupuesto_tipico_eur": 155000000.0,
            "importe_max_proyecto_tipico_eur": 4500000.0,
            "porcentaje_financiacion_tipico": 60.0,
            "modalidad_pago_habitual": "anticipo",
            "keywords_match": ["life-", "cinea", "nature and biodiversity"],
            "checklist_preparacion_previa": [
                "Código PIC validado en el portal EU Funding & Tenders (SEDIA)",
                "Cartas de apoyo (Letters of Support) de autoridades competentes Red Natura 2000",
                "Plan de cofinanciación del 25%-40% restante (combinable con fondos privados/RSC)",
            ],
        },
        {
            "programa_id": "REC-PRIV-MOTOR-VERDE",
            "nombre_programa": "Fondo Motor Verde (Fundación Repsol + Grupo Sylvestris) — Reforestación Post-Incendio y Absorción CO2",
            "organo_convocante": "Fundación Repsol / Motor Verde",
            "nivel_territorial": "PRIVADA",
            "ccaa_codigo": "ES",
            "mes_apertura_habitual": 10,
            "plazo_tipico": "Ventana continua / cierres cuatrimestrales",
            "presupuesto_tipico_eur": 6000000.0,
            "importe_max_proyecto_tipico_eur": 350000.0,
            "porcentaje_financiacion_tipico": 100.0,
            "modalidad_pago_habitual": "anticipo",
            "keywords_match": ["motor verde", "repsol", "sylvestris"],
            "checklist_preparacion_previa": [
                "Cesión de derechos de absorción de CO2 o convenio con Ayuntamiento/Comunidad de Montes (>30 ha)",
                "Elegibilidad para inscripción en el Registro de Huella de Carbono del MITECO",
                "Plan de contratación de empleo local rural en la zona de actuación",
            ],
        },
        {
            "programa_id": "REC-PRIV-CAIXA-SANTANDER",
            "nombre_programa": "Convocatorias Privadas RSC: Fundación ”la Caixa” (Acción Ambiental) y Santander Natura",
            "organo_convocante": "Fundación ”la Caixa” / Fundación Banco Santander",
            "nivel_territorial": "PRIVADA",
            "ccaa_codigo": "ES",
            "mes_apertura_habitual": 10,
            "plazo_tipico": "30 días naturales",
            "presupuesto_tipico_eur": 2500000.0,
            "importe_max_proyecto_tipico_eur": 100000.0,
            "porcentaje_financiacion_tipico": 100.0,
            "modalidad_pago_habitual": "anticipo",
            "keywords_match": ["la caixa", "santander", "bbva", "iberdrola"],
            "checklist_preparacion_previa": [
                "Acreditación en plataforma de convocatorias Fundación ”la Caixa” / Santander ONG",
                "Memoria de impacto social (voluntariado ambiental, inserción sociolaboral forestal)",
                "Cuentas anuales auditadas o depositadas en el registro correspondiente",
            ],
        },
        {
            "programa_id": "REC-XUNTA-MONTES-INCENDIOS",
            "nombre_programa": "Ayudas Xunta de Galicia (Consellería do Medio Rural) — Prevención de Incendios y Montes Vecinales",
            "organo_convocante": "Xunta de Galicia - Consellería do Medio Rural (DOG)",
            "nivel_territorial": "CCAA",
            "ccaa_codigo": "ES-GA",
            "mes_apertura_habitual": 1,
            "plazo_tipico": "1 mes desde publicación en el DOG",
            "presupuesto_tipico_eur": 14800000.0,
            "importe_max_proyecto_tipico_eur": 90000.0,
            "porcentaje_financiacion_tipico": 100.0,
            "modalidad_pago_habitual": "mixto",
            "keywords_match": ["xunta de galicia", "medio rural", "man común", "concellos"],
            "checklist_preparacion_previa": [
                "Instrumento de ordenación o gestión forestal (IOGF) aprobado o en trámite",
                "Acuerdo de la Asamblea General de la Comunidad de Montes o convenio con Concello",
                "Tres ofertas de proveedores para trabajos silvícolas superiores al umbral de contrato menor",
            ],
        },
        {
            "programa_id": "REC-ANDALUCIA-FEADER-INCENDIOS",
            "nombre_programa": "Subvenciones Junta de Andalucía (BOJA) — Prevención de Incendios Forestales y Restauración FEADER",
            "organo_convocante": "Junta de Andalucía - Consejería de Sostenibilidad y Medio Ambiente",
            "nivel_territorial": "CCAA",
            "ccaa_codigo": "ES-AN",
            "mes_apertura_habitual": 10,
            "plazo_tipico": "20 días hábiles tras extracto BOJA",
            "presupuesto_tipico_eur": 22400000.0,
            "importe_max_proyecto_tipico_eur": 120000.0,
            "porcentaje_financiacion_tipico": 100.0,
            "modalidad_pago_habitual": "mixto",
            "keywords_match": ["junta de andalucía", "boja", "dehesas"],
            "checklist_preparacion_previa": [
                "Plan Técnico de Ordenación de Montes (PTOM) o Plan de Prevención de Incendios vigente",
                "Capas vectoriales (Shapefile) de los rodales de actuación según REDIAM",
            ],
        },
    ]

    if ccaa_filter and ccaa_filter.upper() not in ("TODAS", "ALL"):
        ccaa_up = ccaa_filter.upper()
        recurring_programs = [
            p
            for p in recurring_programs
            if p["ccaa_codigo"] in (ccaa_up, "ES", "EU")
        ]

    enriched_programs: list[dict[str, Any]] = []
    for prog in recurring_programs:
        kws = prog["keywords_match"]
        matched_opps = [
            o
            for o in opps
            if any(
                kw in o.titulo_original.lower()
                or kw in o.organo_convocante.lower()
                or kw in o.id.lower()
                or kw in o.codigo_oficial.lower()
                for kw in kws
            )
        ]
        matched_opps.sort(key=lambda x: x.anio_convocatoria, reverse=True)
        active_now = [o for o in matched_opps if o.estado == "ACTIVA"]

        mes_hab = prog["mes_apertura_habitual"]
        months_until = (mes_hab - current_month) % 12

        if active_now:
            estado_ciclo = "ABIERTA_ACTUALMENTE"
            alerta_accion = (
                f"¡CONVOCATORIA ABIERTA AHORA! Quedan {active_now[0].dias_restantes} días "
                f"({active_now[0].codigo_oficial}). Presentar solicitud inmediatamente."
            )
        elif months_until in (1, 2):
            estado_ciclo = "PREPARAR_MEMORIA_AHORA"
            alerta_accion = (
                f"Apertura prevista en ~{months_until} mes(es) ({MESES_ES[mes_hab]}). "
                "Iniciar redacción de memoria técnica y acuerdos de terrenos hoy."
            )
        elif months_until == 0:
            estado_ciclo = "APERTURA_INMINENTE_ESTE_MES"
            alerta_accion = (
                f"Mes habitual de publicación ({MESES_ES[mes_hab]}). "
                "Vigilar boletín a diario y tener firma electrónica y anexos listos."
            )
        else:
            estado_ciclo = "CICLO_ANUAL_PLANIFICADO"
            alerta_accion = (
                f"Próxima ventana estimada en {MESES_ES[mes_hab]} (en {months_until} meses)."
            )

        mes_prep_inicio = ((mes_hab - 2 - 1) % 12) + 1
        mes_prep_fin = ((mes_hab - 1 - 1) % 12) + 1

        enriched_programs.append(
            {
                "programa_id": prog["programa_id"],
                "nombre_programa": prog["nombre_programa"],
                "organo_convocante": prog["organo_convocante"],
                "nivel_territorial": prog["nivel_territorial"],
                "ccaa_codigo": prog["ccaa_codigo"],
                "frecuencia": "ANUAL_RECURRENTE",
                "mes_apertura_habitual": mes_hab,
                "mes_apertura_nombre": MESES_ES[mes_hab],
                "ventana_preparacion_recomendada": f"{MESES_ES[mes_prep_inicio]} - {MESES_ES[mes_prep_fin]}",
                "estado_ciclo_actual": estado_ciclo,
                "alerta_tactica_reforesta": alerta_accion,
                "plazo_tipico": prog["plazo_tipico"],
                "condiciones_economicas_tipicas": {
                    "presupuesto_linea_eur": prog["presupuesto_tipico_eur"],
                    "importe_max_proyecto_eur": prog["importe_max_proyecto_tipico_eur"],
                    "porcentaje_financiacion": prog["porcentaje_financiacion_tipico"],
                    "modalidad_pago": prog["modalidad_pago_habitual"],
                },
                "checklist_preparacion_previa": prog["checklist_preparacion_previa"],
                "convocatoria_activa_actual": (
                    {
                        "id": active_now[0].id,
                        "codigo_oficial": active_now[0].codigo_oficial,
                        "titulo_limpio": active_now[0].titulo_limpio,
                        "dias_restantes": active_now[0].dias_restantes,
                        "fecha_fin_solicitud": (
                            active_now[0].fecha_fin_solicitud.isoformat()
                            if active_now[0].fecha_fin_solicitud
                            else None
                        ),
                        "prioridad_score": active_now[0].prioridad_score,
                    }
                    if active_now
                    else None
                ),
                "historico_ediciones_detectadas": [
                    {
                        "id": o.id,
                        "anio": o.anio_convocatoria,
                        "codigo_oficial": o.codigo_oficial,
                        "estado": o.estado,
                        "presupuesto_eur": o.presupuesto_total,
                    }
                    for o in matched_opps[:5]
                ],
            }
        )

    return {
        "fecha_referencia": ref_today.isoformat(),
        "mes_actual": MESES_ES[current_month],
        "objetivo_estrategico": (
            "Anticipar la preparación técnica 45 días antes del boletín oficial para superar "
            "los plazos críticos de 10 a 15 días hábiles."
        ),
        "resumen_alertas": {
            "abiertas_actualmente": sum(1 for p in enriched_programs if p["estado_ciclo_actual"] == "ABIERTA_ACTUALMENTE"),
            "en_ventana_preparacion_inmediata": sum(
                1 for p in enriched_programs if p["estado_ciclo_actual"] in ("PREPARAR_MEMORIA_AHORA", "APERTURA_INMINENTE_ESTE_MES")
            ),
            "total_programas_recurrentes_monitorizados": len(enriched_programs),
        },
        "programas_recurrentes": enriched_programs,
    }


def export_opportunities_csv(opps: list[Opportunity]) -> str:
    """Generate a UTF-8 with BOM CSV spreadsheet of prioritized opportunities for Excel / Google Sheets."""
    output = io.StringIO()
    output.write("\ufeff")  # UTF-8 BOM so Microsoft Excel opens Spanish accents and € symbols cleanly
    writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_MINIMAL)

    writer.writerow(
        [
            "Prioridad_Score",
            "Prioridad_Nivel",
            "Estado",
            "Estado_Interno",
            "Dias_Restantes",
            "Codigo_Oficial",
            "Titulo_Espanol",
            "Organo_Convocante",
            "Nivel_Territorial",
            "CCAA_Codigo",
            "CCAA_Nombre",
            "Provincia",
            "Municipio",
            "Tipo_Oportunidad",
            "Relevancia_Tipo",
            "Presupuesto_Total_EUR",
            "Max_Proyecto_EUR",
            "Max_Beneficiario_EUR",
            "Porcentaje_Financiacion",
            "Modalidad_Pago",
            "Anticipo_Sin_Aval",
            "Fecha_Publicacion",
            "Fecha_Fin_Solicitud",
            "Plazo_Oficial_Texto",
            "Categorias",
            "Beneficiarios",
            "URL_Ficha_Oficial",
            "Justificacion_Juez",
        ]
    )

    sorted_opps = sorted(
        opps,
        key=lambda o: (o.estado == "ACTIVA", o.prioridad_score or 0, o.relevancia_score or 0),
        reverse=True,
    )

    for o in sorted_opps:
        writer.writerow(
            [
                o.prioridad_score,
                o.prioridad_nivel,
                o.estado,
                o.estado_interno,
                o.dias_restantes if o.dias_restantes is not None else "",
                o.codigo_oficial,
                o.titulo_limpio,
                o.organo_convocante,
                o.nivel_territorial,
                o.ccaa_codigo,
                o.ccaa_nombre,
                o.provincia_nombre or "",
                o.municipio_nombre or "",
                o.tipo_oportunidad,
                o.relevancia_tipo,
                f"{o.presupuesto_total:.2f}" if o.presupuesto_total is not None else "",
                f"{o.importe_max_proyecto:.2f}" if o.importe_max_proyecto is not None else "",
                f"{o.importe_max_beneficiario:.2f}" if o.importe_max_beneficiario is not None else "",
                f"{o.porcentaje_max_financiacion:.0f}%" if o.porcentaje_max_financiacion is not None else "",
                o.modalidad_pago,
                "SI" if o.pago_anticipado_sin_aval else "NO",
                o.fecha_publicacion.isoformat() if o.fecha_publicacion else "",
                o.fecha_fin_solicitud.isoformat() if o.fecha_fin_solicitud else "",
                o.plazo_texto_original or "",
                ", ".join(o.categorias or []),
                ", ".join(o.beneficiarios_tipos or []),
                o.url_ficha_oficial,
                o.justificacion_juez,
            ]
        )

    return output.getvalue()


def _ics_escape(text: str) -> str:
    return (
        (text or "")
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
    )


def export_opportunities_ics(opps: list[Opportunity]) -> str:
    """
    Generate an RFC 5545 iCalendar (.ics) file with deadline events and 7-day / 2-day alarms
    for Google Calendar, Outlook, and Apple Calendar.
    """
    now_str = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Reforesta//1hack_reforesta Radar de Convocatorias//ES",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Plazos de Convocatorias Reforesta",
        "X-WR-TIMEZONE:Europe/Madrid",
    ]

    for o in opps:
        if not o.fecha_fin_solicitud:
            continue
        dt_start = o.fecha_fin_solicitud.strftime("%Y%m%d")
        dt_end = (o.fecha_fin_solicitud + timedelta(days=1)).strftime("%Y%m%d")
        summary = f"[{o.prioridad_nivel} {o.prioridad_score}pts] CIERRE: {o.titulo_limpio[:90]}"
        desc = (
            f"Código Oficial: {o.codigo_oficial}\\n"
            f"Órgano: {o.organo_convocante} ({o.ccaa_nombre})\\n"
            f"Presupuesto Línea: {o.presupuesto_total or 0:,.2f} EUR | Financiación: {o.porcentaje_max_financiacion or 0}%\\n"
            f"Modalidad de Pago: {o.modalidad_pago} (Anticipo sin aval: {'Sí' if o.pago_anticipado_sin_aval else 'No'})\\n"
            f"Plazo Oficial: {o.plazo_texto_original or 'Ver bases'}\\n"
            f"Justificación Juez: {o.justificacion_juez}\\n"
            f"Enlace Oficial: {o.url_ficha_oficial}"
        )
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{o.id}@reforesta.onehack.es",
                f"DTSTAMP:{now_str}",
                f"DTSTART;VALUE=DATE:{dt_start}",
                f"DTEND;VALUE=DATE:{dt_end}",
                f"SUMMARY:{_ics_escape(summary)}",
                f"DESCRIPTION:{desc}",
                f"URL:{o.url_ficha_oficial}",
                f"LOCATION:{_ics_escape(o.ccaa_nombre or 'España')}",
                "BEGIN:VALARM",
                "TRIGGER:-P7D",
                "ACTION:DISPLAY",
                f"DESCRIPTION:Faltan 7 días para el cierre de {o.codigo_oficial}",
                "END:VALARM",
                "BEGIN:VALARM",
                "TRIGGER:-P2D",
                "ACTION:DISPLAY",
                f"DESCRIPTION:¡URGENTE! Faltan 48h para el cierre de {o.codigo_oficial}",
                "END:VALARM",
                "END:VEVENT",
            ]
        )

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def export_opportunity_markdown(opp: Opportunity) -> str:
    """Generate an executive Markdown Dossier for Reforesta's technical team to prepare a proposal."""
    data = opp.to_api_dict()
    prio = data["priorizacion"]
    eco = data["economia"]
    fechas = data["fechas"]
    geo = data["ambito_geografico"]

    criterios_md = ""
    if opp.criterios_valoracion:
        criterios_md = "\n".join(
            f"- **{c.get('criterio', 'Criterio')}**: hasta **{c.get('puntos_max', 0)} puntos** — {c.get('detalle', '')}"
            for c in opp.criterios_valoracion
        )
    else:
        criterios_md = "- Calidad técnica de la memoria de restauración ecológica, viabilidad económica e impacto ambiental/social."

    citas_md = "\n".join(f"> {c}" for c in (opp.citas_bases or [f"[{opp.codigo_oficial}] {opp.justificacion_juez}"]))
    dealbreakers_md = (
        "\n".join(f"- ⚠️ {d}" for d in opp.dealbreakers)
        if opp.dealbreakers
        else "- ✅ Sin bloqueos (dealbreakers) críticos de tesorería o solvencia detectados para ONG/Asociación."
    )

    return f"""# Ficha Técnica de Oportunidad — Reforesta
## {opp.titulo_limpio}

- **ID / Código Oficial:** `{opp.id}` (`{opp.codigo_oficial}`)
- **Estado:** `{opp.estado}` ({opp.dias_restantes if opp.dias_restantes is not None else 'N/A'} días restantes)
- **Prioridad Estratégica Reforesta:** **{prio['nivel']} ({prio['score']}/100)** — *{prio['urgencia_plazo']}*
- **Recomendación Táctica:** {prio['recomendacion_tactica']}

---

### 1. Datos del Órgano y Ámbito Territorial
| Campo | Detalle |
| :--- | :--- |
| **Órgano Convocante** | {opp.organo_convocante} ({opp.unidad_convocante or 'Unidad Gestora'}) |
| **Nivel Territorial** | `{geo['nivel']}` |
| **Comunidad Autónoma** | {geo['ccaa_nombre']} (`{geo['ccaa_codigo']}`) |
| **Provincia / Municipio** | {geo['provincia_nombre'] or '-'} / {geo['municipio'] or '-'} |
| **Orografía / Terreno** | `{geo['orografia_pendiente']}` |

---

### 2. Cuadro Económico y Viabilidad de Tesorería
| Indicador Financiero | Valor |
| :--- | :--- |
| **Presupuesto Total de la Línea** | {f"{eco['presupuesto_total']:,.2f} €" if eco['presupuesto_total'] else 'Según disponibilidad presupuestaria'} |
| **Importe Máximo por Proyecto** | {f"{eco['importe_max_proyecto']:,.2f} €" if eco['importe_max_proyecto'] else 'No especificado / Según presupuesto total'} |
| **Importe Máximo por Entidad** | {f"{eco['importe_max_beneficiario']:,.2f} €" if eco['importe_max_beneficiario'] else 'No especificado'} |
| **Intensidad de Financiación** | **{f"{eco['porcentaje_max_financiacion']:.0f}%" if eco['porcentaje_max_financiacion'] else 'Hasta 100%'}** |
| **Modalidad de Pago** | `{eco['modalidad_pago'].upper()}` |
| **Pago Anticipado sin Aval** | **{'SÍ (Óptimo para tesorería ONG)' if eco['pago_anticipado_sin_aval'] else 'Según bases reguladoras'}** |
| **Cofinanciación Europea** | {'Sí (' + (eco['fondo_ue'] or 'UE') + ')' if eco['cofinanciado_ue'] else 'Fondos propios / nacionales'} |

---

### 3. Calendario y Cómputo de Plazos (Ley 39/2015 LPACAP Art. 30)
- **Fecha de Publicación:** `{fechas['fecha_publicacion'] or 'N/A'}`
- **Inicio de Solicitudes:** `{fechas['fecha_inicio_solicitud'] or 'N/A'}`
- **Fecha Límite de Cierre:** **`{fechas['fecha_fin_solicitud'] or 'Abierta según bases'}`**
- **Texto Oficial del Plazo:** *{fechas['plazo_texto_original'] or 'Consultar convocatoria'}*

---

### 4. Evaluación del Juez Experto y Citas de las Bases
- **Tipo de Relevancia:** `{opp.relevancia_tipo}` (Afinidad: `{opp.relevancia_score}/100`)
- **Categorías Detectadas:** `{', '.join(opp.categorias or [])}`
- **Resumen Ejecutivo:** {opp.resumen}

#### Citas Clave de las Bases:
{citas_md}

#### Alertas de Elegibilidad / Dealbreakers:
{dealbreakers_md}

---

### 5. Requisitos, Gastos Subvencionables y Criterios de Puntuación
- **Beneficiarios Elegibles:** `{', '.join(opp.beneficiarios_tipos or [])}`
- **Requisitos Esenciales:** {opp.requisitos_resumen}
- **Gastos Subvencionables:** {opp.gastos_subvencionables or 'Actuaciones de reforestación, silvicultura preventiva y restauración ambiental.'}

#### Criterios de Valoración:
{criterios_md}

---

### 6. Enlaces Oficiales Directos
- **Ficha Oficial / Convocatoria:** {opp.url_ficha_oficial}
- **Sede Electrónica / Tramitación:** {opp.url_tramitacion or opp.url_ficha_oficial}
- **Bases Reguladoras / PDF:** {opp.url_bases_reguladoras or opp.url_boletin_extracto or opp.url_ficha_oficial}
"""
