"""Structured Metadata Extractor for Frontend Integration: Ubicación, Plazos & Dinero."""
from datetime import date
import re
from typing import TYPE_CHECKING, Any
from app.config import settings
from app.geo import CCAA_CATALOG, CCAA_COORDINATES, extract_natural_area_or_comarca
from app.pipeline.date_resolver import count_business_days_remaining, parse_spanish_date

if TYPE_CHECKING:
    from app.models import Opportunity


def _parse_euro_number(raw_num: str, multiplier: float = 1.0) -> float | None:
    """Parse Spanish ('17.389.322,52') or English ('5,000,000.00' / '2.5') currency strings into float."""
    s = raw_num.strip()
    if not s:
        return None
    # If both '.' and ',' exist: whichever comes last is the decimal separator
    if "." in s and "," in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        parts = s.split(",")
        if len(parts) == 2 and len(parts[1]) in (1, 2):
            s = s.replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "." in s:
        parts = s.split(".")
        # In Spanish '500.000' or '1.200.000', groups of 3 digits are thousands unless multiplier > 1 (e.g. '2.5 millones')
        if multiplier > 1.0 and len(parts) == 2 and len(parts[1]) <= 2:
            pass
        elif all(len(p) == 3 for p in parts[1:]):
            s = s.replace(".", "")

    try:
        val = float(s) * multiplier
        return round(val, 2) if val > 0 else None
    except ValueError:
        return None


def extract_money_metadata(
    titulo: str,
    texto: str,
    presupuesto_hint: float | None = None,
    max_proy_hint: float | None = None,
    max_benef_hint: float | None = None,
    pct_hint: float | None = None,
) -> dict[str, float | None]:
    """
    Extract financial figures (presupuesto_total, importe_max_proyecto, importe_max_beneficiario,
    importe_min_proyecto, ayuda_por_hectarea_euros, porcentaje_max_financiacion) from call text.
    """
    combined = f"{titulo}\n{texto[:10000]}"
    presupuesto = presupuesto_hint
    max_proy = max_proy_hint
    max_benef = max_benef_hint
    min_proy: float | None = None
    eur_ha: float | None = None
    pct = pct_hint

    # 1. Millions shorthand ("17,38 millones de euros", "2.5 M€", "EUR 9 million")
    if presupuesto is None:
        m_mill = re.search(
            r"\b(\d+(?:[.,]\d{1,3})?)\s*(?:millones?\s+de\s+euros|m€|millones?\s*€|million\s+eur(?:os)?)\b",
            combined,
            re.IGNORECASE,
        )
        if m_mill:
            presupuesto = _parse_euro_number(m_mill.group(1), multiplier=1_000_000.0)

    # 2. Explicit total budget ("dotación de X €", "presupuesto total de X euros", "importe total de X €")
    if presupuesto is None:
        m_pres = re.search(
            r"(?:dotaci[oó]n(?:\s+global|\s+total|\s+m[aá]xima)?|dotad[ao]\s+con|presupuesto(?:\s+total|\s+base|\s+global)?|"
            r"cr[eé]dito\s+presupuestario|importe\s+(?:total|global)|cuant[ií]a\s+total|valor\s+estimado|total\s+budget)"
            r"[^.\n€]{0,55}?\b(\d{1,3}(?:[.,]\d{3})+(?:[.,]\d{1,2})?|\d{4,9}(?:[.,]\d{1,2})?)\s*(?:euros|€|EUR)\b",
            combined,
            re.IGNORECASE,
        )
        if m_pres:
            presupuesto = _parse_euro_number(m_pres.group(1))

    # 3. Maximum grant per project / application ("hasta 30.000 € por proyecto", "máximo de 40.000 euros por solicitud")
    if max_proy is None:
        m_proy = re.search(
            r"(?:m[aá]ximo\s+(?:de\s+)?|hasta\s+(?:un\s+m[aá]ximo\s+de\s+)?|subvenci[oó]n\s+m[aá]xima\s+de\s+|ayuda\s+m[aá]xima\s+de\s+)"
            r"(\d{1,3}(?:[.,]\d{3})+(?:[.,]\d{1,2})?|\d{4,7})\s*(?:euros|€|EUR)\s*(?:por\s+|/\s*)?(?:proyecto|solicitud|actuaci[oó]n|propuesta)",
            combined,
            re.IGNORECASE,
        )
        if not m_proy:
            m_proy = re.search(
                r"(?:por\s+proyecto|por\s+solicitud|por\s+actuaci[oó]n)[^.\n€]{0,40}?\b(\d{1,3}(?:[.,]\d{3})+(?:[.,]\d{1,2})?|\d{4,7})\s*(?:euros|€|EUR)",
                combined,
                re.IGNORECASE,
            )
        if m_proy:
            max_proy = _parse_euro_number(m_proy.group(1))

    # 4. Maximum grant per beneficiary / entity ("60.000 € por entidad", "por beneficiario")
    if max_benef is None:
        m_ben = re.search(
            r"(\d{1,3}(?:[.,]\d{3})+(?:[.,]\d{1,2})?|\d{4,7})\s*(?:euros|€|EUR)\s*(?:por\s+|/\s*)(?:entidad|beneficiario|asociaci[oó]n|ayuntamiento|concello)",
            combined,
            re.IGNORECASE,
        )
        if m_ben:
            max_benef = _parse_euro_number(m_ben.group(1))

    # 5. Minimum grant per project ("mínimo de 5.000 €", "importe mínimo de 10.000 euros")
    m_min = re.search(
        r"(?:m[ií]nimo\s+de|importe\s+m[ií]nimo(?:\s+de)?|presupuesto\s+m[ií]nimo(?:\s+de)?)\s*"
        r"(\d{1,3}(?:[.,]\d{3})+(?:[.,]\d{1,2})?|\d{3,6})\s*(?:euros|€|EUR)",
        combined,
        re.IGNORECASE,
    )
    if m_min:
        min_proy = _parse_euro_number(m_min.group(1))

    # 6. Per-hectare reforestation rate ("3.200 €/ha", "2.500 euros/hectárea", "euros por hectárea")
    m_ha = re.search(
        r"\b(\d{1,2}(?:[.,]\d{3})|\d{3,5}(?:,\d{1,2})?)\s*(?:euros|€|EUR)\s*(?:/\s*ha\b|/\s*hect[aá]rea|por\s+hect[aá]rea)",
        combined,
        re.IGNORECASE,
    )
    if m_ha:
        eur_ha = _parse_euro_number(m_ha.group(1))

    # 7. Fallback: if presupuesto is still None, find the largest explicit Euro amount >= 3,000 € in text
    if presupuesto is None:
        all_amounts: list[float] = []
        for m_any in re.finditer(
            r"\b(\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?|\d{4,9}(?:,\d{1,2})?)\s*(?:euros|€|EUR)\b",
            combined,
            re.IGNORECASE,
        ):
            val = _parse_euro_number(m_any.group(1))
            if val and val >= 3000.0 and (eur_ha is None or val != eur_ha):
                all_amounts.append(val)
        if all_amounts:
            presupuesto = max(all_amounts)
            if max_proy is None and len(set(all_amounts)) >= 2:
                smaller = sorted({a for a in all_amounts if a < presupuesto}, reverse=True)
                if smaller:
                    max_proy = smaller[0]

    # 8. Co-financing percentage ("hasta el 100%", "80% del coste subvencionable", "financiación del 85%")
    if pct is None:
        m_pct = re.search(
            r"(?:hasta\s+(?:el|un)|alcanzar\s+el|financiaci[oó]n\s+del|cofinanciaci[oó]n\s+del|"
            r"intensidad\s+(?:m[aá]xima\s+)?del|subvencionable\s+al|cubrir[aá]\s+el|financia\s+el)\s*(\d{1,3})\s*%",
            combined,
            re.IGNORECASE,
        )
        if not m_pct:
            m_pct = re.search(r"\b(100|95|90|85|80|75|70|60|50)\s*%\s*(?:de\s+los\s+(?:costes|gastos)|del\s+presupuesto|subvencionable)", combined, re.IGNORECASE)
        if m_pct:
            pct_val = float(m_pct.group(1))
            if 10.0 <= pct_val <= 100.0:
                pct = pct_val

    return {
        "presupuesto_total": presupuesto,
        "importe_max_proyecto": max_proy,
        "importe_max_beneficiario": max_benef,
        "importe_min_proyecto": min_proy,
        "ayuda_por_hectarea_euros": eur_ha,
        "porcentaje_max_financiacion": pct,
    }


def extract_deadline_clause_and_date(
    texto: str,
    existing_clause: str | None = None,
    existing_end_date: date | str | None = None,
) -> tuple[str | None, date | None]:
    """
    Extract deadline clause (plazo_texto_original) and explicit closing date (fecha_fin_solicitud)
    from call text when missing from structured API fields.
    """
    clause = existing_clause
    end_date = parse_spanish_date(existing_end_date)
    snippet = (texto or "")[:8000]

    if end_date is None:
        m_explicit = re.search(
            r"(?:hasta\s+el(?:\s+d[ií]a)?|finaliza\s+el|vence\s+el|fecha\s+l[ií]mite(?:\s+de\s+presentaci[oó]n)?\s*[:de]*|"
            r"plazo\s+de\s+presentaci[oó]n[^.\n]{0,35}?hasta\s+el|deadline\s*[:is]*)\s*"
            r"(\d{1,2}\s+(?:de\s+|d['’])[a-záéíóúñç]+\s+(?:de\s+|del\s+|do\s+)?20\d{2}|\d{1,2}[-/]\d{1,2}[-/]20\d{2}|20\d{2}-\d{2}-\d{2})",
            snippet,
            re.IGNORECASE,
        )
        if m_explicit:
            raw_d = m_explicit.group(1).strip()
            end_date = parse_spanish_date(raw_d)
            if not clause:
                clause = f"Hasta el {raw_d}"
        if end_date is None:
            m_range = re.search(
                r"\bdel?\s+\d{1,2}\s+(?:de\s+[a-záéíóúñ]+(?:\s+de\s+20\d{2})?)\s+al\s+"
                r"(\d{1,2}\s+de\s+[a-záéíóúñ]+\s+de\s+20\d{2})\b",
                snippet,
                re.IGNORECASE,
            )
            if m_range:
                raw_d = m_range.group(1).strip()
                end_date = parse_spanish_date(raw_d)
                if not clause:
                    clause = f"Hasta el {raw_d}"

    if not clause:
        m_plz = re.search(
            r"\b((?:\d+|un|una|dos|tres|diez|quince|veinte|treinta)\s+"
            r"(?:d[ií](?:as|es)\s+(?:h[aáà]bil(?:e?s)?|natural(?:e?s)?)|mes(?:es|os)?|working\s+days|months?)"
            r"(?:\s+a\s+(?:partir|contar)\s+del\s+d[ií]a\s+siguiente[^.;\n]{0,65})?)",
            snippet,
            re.IGNORECASE,
        )
        if m_plz:
            clause = re.sub(r"\s+", " ", m_plz.group(1)).strip()

    return clause, end_date


def _format_eur(val: float | None) -> str | None:
    if val is None or val <= 0:
        return None
    if val >= 1_000_000 and val % 10_000 == 0:
        return f"{val / 1_000_000:,.2f} M€".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{val:,.0f} €".replace(",", ".")


def build_frontend_metadata_bundle(opp: "Opportunity") -> dict[str, Any]:
    """
    Build the canonical, Frontend-ready metadata bundle for:
    1. Ubicación (Territorio español, CCAA, Provincia, Municipio, Espacio Natural, Coordenadas)
    2. Plazos (Estado, Fechas ISO, Días naturales y hábiles LPACAP restantes, Urgencia)
    3. Dinero (Presupuesto total, Máx por proyecto/entidad, €/ha, % financiación, Anticipo sin aval)
    """
    ref_today = settings.get_today()
    combined_txt = f"{opp.titulo_limpio} {opp.titulo_original} {opp.resumen} {opp.organo_convocante}"

    # 1. Ubicación
    ccaa_info = CCAA_CATALOG.get(opp.ccaa_codigo, CCAA_CATALOG["ES"])
    nuts_code = ccaa_info.get("nuts", "ES")
    coords = CCAA_COORDINATES.get(opp.ccaa_codigo, CCAA_COORDINATES["ES"])
    espacio_natural = extract_natural_area_or_comarca(combined_txt)
    es_extranjera_para_espana = opp.nivel_territorial == "UE" or any(
        k in (opp.organo_convocante or "").lower()
        for k in ["european", "cinea", "eoca", "one tree planted", "outdoor conservation"]
    )

    parts_loc: list[str] = []
    if opp.municipio_nombre:
        parts_loc.append(f"Municipio: {opp.municipio_nombre}")
    if opp.provincia_nombre and opp.provincia_nombre != opp.ccaa_nombre:
        parts_loc.append(opp.provincia_nombre)
    if opp.ccaa_codigo not in ("ES", "EU"):
        parts_loc.append(f"{opp.ccaa_nombre} ({opp.ccaa_codigo})")
    elif es_extranjera_para_espana:
        parts_loc.append("Ayuda Internacional/UE → Para Reforestar en España")
    else:
        parts_loc.append("Toda España (Ámbito Estatal)")
    if espacio_natural:
        parts_loc.append(espacio_natural)
    etiqueta_ubicacion = " · ".join(parts_loc)

    ubicacion_dict = {
        "aplica_en_espana": True,
        "es_ayuda_extranjera_para_espana": es_extranjera_para_espana,
        "pais_codigo": "ES",
        "pais_nombre": "España",
        "nivel": opp.nivel_territorial,
        "ccaa_codigo": opp.ccaa_codigo,
        "ccaa_nombre": opp.ccaa_nombre,
        "nuts_codigo": nuts_code,
        "provincia_codigo": opp.provincia_codigo,
        "provincia_nombre": opp.provincia_nombre,
        "municipio": opp.municipio_nombre,
        "espacio_natural_o_comarca": espacio_natural,
        "orografia_pendiente": opp.orografia_pendiente,
        "coordenadas_mapa": coords,
        "etiqueta_front": etiqueta_ubicacion,
    }

    # 2. Plazos
    dias_nat = opp.dias_restantes
    dias_hab: int | None = None
    if opp.fecha_fin_solicitud and opp.estado in ("ACTIVA", "PROXIMA"):
        dias_hab = count_business_days_remaining(
            start_date=ref_today,
            end_date=opp.fecha_fin_solicitud,
            ccaa_codigo=opp.ccaa_codigo,
        )
    elif opp.estado == "CERRADA":
        dias_hab = 0

    if opp.estado == "PROXIMA":
        urgencia = "proxima_apertura"
        etiqueta_plazo = (
            f"Próxima apertura (Abre: {opp.fecha_inicio_solicitud or opp.anio_convocatoria}"
            f" · Cierre: {opp.fecha_fin_solicitud or 'Según bases'})"
        )
    elif opp.estado != "ACTIVA":
        urgencia = "cerrada"
        etiqueta_plazo = f"Cerrada (Histórico {opp.anio_convocatoria})"
    elif dias_nat is not None and dias_nat <= 12:
        urgencia = "critica"
        etiqueta_plazo = f"Urgente · {dias_nat}d naturales ({dias_hab}d hábiles) · Cierre {opp.fecha_fin_solicitud}"
    elif dias_nat is not None and dias_nat <= 30:
        urgencia = "moderada"
        etiqueta_plazo = f"Abierta · {dias_nat}d naturales ({dias_hab}d hábiles) · Cierre {opp.fecha_fin_solicitud}"
    elif dias_nat is not None:
        urgencia = "holgada"
        etiqueta_plazo = f"Abierta · {dias_nat}d naturales ({dias_hab}d hábiles) · Cierre {opp.fecha_fin_solicitud}"
    else:
        urgencia = "abierta_pendiente_plazo"
        etiqueta_plazo = f"Abierta ({opp.plazo_texto_original or 'Según bases reguladoras'})"

    plazos_dict = {
        "estado": opp.estado,
        "anio_convocatoria": opp.anio_convocatoria,
        "fecha_publicacion": opp.fecha_publicacion.isoformat() if opp.fecha_publicacion else None,
        "fecha_inicio_solicitud": opp.fecha_inicio_solicitud.isoformat() if opp.fecha_inicio_solicitud else None,
        "fecha_fin_solicitud": opp.fecha_fin_solicitud.isoformat() if opp.fecha_fin_solicitud else None,
        "dias_naturales_restantes": dias_nat,
        "dias_habiles_restantes": dias_hab,
        "plazo_texto_original": opp.plazo_texto_original,
        "es_plazo_calculado_lpacap": opp.es_plazo_calculado,
        "urgencia": urgencia,
        "etiqueta_front": etiqueta_plazo,
    }

    # 3. Dinero
    money_extra = extract_money_metadata(
        titulo=opp.titulo_original or opp.titulo_limpio,
        texto=f"{opp.resumen} {opp.requisitos_resumen} {opp.gastos_subvencionables or ''}",
        presupuesto_hint=opp.presupuesto_total,
        max_proy_hint=opp.importe_max_proyecto,
        max_benef_hint=opp.importe_max_beneficiario,
        pct_hint=opp.porcentaje_max_financiacion,
    )
    pres_total = money_extra["presupuesto_total"]
    max_proy = money_extra["importe_max_proyecto"]
    max_benef = money_extra["importe_max_beneficiario"]
    min_proy = money_extra["importe_min_proyecto"]
    eur_ha = money_extra["ayuda_por_hectarea_euros"]
    pct_fin = money_extra["porcentaje_max_financiacion"]
    pct_cofin = round(max(0.0, 100.0 - pct_fin), 1) if pct_fin is not None else None

    parts_money: list[str] = []
    if fmt_tot := _format_eur(pres_total):
        parts_money.append(f"{fmt_tot} total")
    if fmt_proy := _format_eur(max_proy):
        parts_money.append(f"Máx. {fmt_proy}/proyecto")
    elif fmt_ben := _format_eur(max_benef):
        parts_money.append(f"Máx. {fmt_ben}/entidad")
    if fmt_ha := _format_eur(eur_ha):
        parts_money.append(f"{fmt_ha}/ha")
    if pct_fin is not None:
        parts_money.append(f"{int(pct_fin)}% financiado")
    if opp.pago_anticipado_sin_aval:
        parts_money.append("Anticipo sin aval")
    etiqueta_dinero = " · ".join(parts_money) if parts_money else "Dotación según bases oficiales"

    dinero_dict = {
        "moneda": opp.moneda or "EUR",
        "presupuesto_total": pres_total,
        "importe_max_proyecto": max_proy,
        "importe_max_beneficiario": max_benef,
        "importe_min_proyecto": min_proy,
        "ayuda_por_hectarea_euros": eur_ha,
        "porcentaje_max_financiacion": pct_fin,
        "porcentaje_cofinanciacion_requerida": pct_cofin,
        "modalidad_pago": opp.modalidad_pago,
        "pago_anticipado_sin_aval": opp.pago_anticipado_sin_aval,
        "cofinanciado_ue": opp.cofinanciado_ue,
        "fondo_ue": opp.fondo_ue,
        "etiqueta_front": etiqueta_dinero,
    }

    return {
        "ubicacion": ubicacion_dict,
        "plazos": plazos_dict,
        "dinero": dinero_dict,
    }
