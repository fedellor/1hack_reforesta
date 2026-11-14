"""Official institutional & statutory profile of Asociación Reforesta (from reforesta.es)."""
from dataclasses import dataclass
import re
from typing import Any

REFORESTA_STATUTORY_FINES: list[dict[str, Any]] = [
    {
        "codigo": "Fin 1",
        "titulo": "Desarrollo rural compatible con la conservación",
        "keywords": ("rural", "desarrollo sostenible", "custodia", "comarca", "pueblos", "agroforestal"),
    },
    {
        "codigo": "Fin 2",
        "titulo": "Lucha contra la desertificación, deforestación y erosión",
        "keywords": ("desertific", "deforest", "erosi", "reforest", "repoblac", "suelo", "cuenca", "acuifero", "acuífero"),
    },
    {
        "codigo": "Fin 3",
        "titulo": "Protección, recuperación y gestión de espacios naturales y especies",
        "keywords": ("natura 2000", "espacio natural", "biodiversidad", "flora", "fauna", "monte", "bosque", "incendio", "restaurac", "habitat", "hábitat", "silvicultura"),
    },
    {
        "codigo": "Fin 4",
        "titulo": "Educación ambiental y sensibilización ciudadana",
        "keywords": ("educacion ambiental", "educación ambiental", "sensibiliz", "voluntariado", "divulgacion", "concienci"),
    },
    {
        "codigo": "Fin 5",
        "titulo": "Cooperación internacional para el desarrollo",
        "keywords": ("cooperacion internacional", "cooperación", "internacional", "ue", "horizon", "life"),
    },
    {
        "codigo": "Fin 6",
        "titulo": "Equidad de género e inserción laboral de mujeres",
        "keywords": ("mujer", "genero", "género", "igualdad", "insercion", "inserción"),
    },
    {
        "codigo": "Fin 7",
        "titulo": "Inclusión de personas en riesgo de exclusión social y voluntariado",
        "keywords": ("exclusion", "exclusión", "vulnerable", "voluntariado", "cohesion social"),
    },
    {
        "codigo": "Fin 8",
        "titulo": "Participación de personas con diversidad funcional",
        "keywords": ("discapacidad", "diversidad funcional", "accesibilidad"),
    },
    {
        "codigo": "Fin 9",
        "titulo": "Formación profesional y empleo verde inclusivo",
        "keywords": ("empleo verde", "formacion profesional", "formación", "capacitacion", "contratacion"),
    },
    {
        "codigo": "Fin 10",
        "titulo": "Mejora ambiental y RSC de organizaciones y empresas",
        "keywords": ("empresa", "rsc", "mecenazgo", "responsabilidad social", "patrocinio", "huella de carbono", "corporativ"),
    },
    {
        "codigo": "Fin 11",
        "titulo": "Diálogo intercultural ligado a la sostenibilidad",
        "keywords": ("intercultural", "participacion ciudadana", "comunidad"),
    },
]

REFORESTA_ACTIVE_TERRITORIES: dict[str, str] = {
    "ES-MD": "Presencia consolidada en la Comunidad de Madrid (Sierra de Guadarrama, Alto Manzanares, Meco, Tres Cantos, Villarejo, Navacerrada)",
    "ES-CT": "Actuaciones activas en Barcelona (Garraf/Begues, Montnegre/Dosrius, Sant Llorenç/Matadepera, Montseny/El Brull)",
    "ES-CM": "Actuaciones activas en Castilla-La Mancha (Almonacid de Toledo · Red de Custodia)",
    "ES-AR": "Actuaciones activas en Aragón (Galachos de la Alfranca / Pastriz, Zaragoza)",
    "ES-AN": "Actuaciones activas en Andalucía (Parque de las Canteras / La Zubia, Granada)",
    "ES-VC": "Actuaciones activas en Comunitat Valenciana (Cañada Real de San Juan / Requena, Valencia)",
}


def get_reforesta_profile() -> dict[str, Any]:
    """Return Reforesta's verified institutional, statutory, fiscal and territorial dossier."""
    return {
        "nombre": "ASOCIACIÓN REFORESTA",
        "nif": "G80428204",
        "anio_fundacion": 1991,
        "registro_nacional": "Grupo 1, Sección 1, Número Nacional 162965",
        "utilidad_publica": True,
        "domicilio_social": "Sector Foresta 43, Oficina 33 (28760 Tres Cantos, Madrid)",
        "telefono": "918046509",
        "email": "info@reforesta.es",
        "web": "https://reforesta.es/",
        "documentos": {
            "estatutos_pdf": "https://reforesta.es/wp-content/uploads/2026/09/Estatutos-2026-Web.pdf",
            "utilidad_publica_pdf": "https://reforesta.es/wp-content/uploads/2024/02/UTILIDAD-PUBLICA-2024.pdf",
            "memoria_2024_pdf": "https://reforesta.es/wp-content/uploads/2026/05/Memoria-Reforesta-2024.pdf",
        },
        "fines_estatutarios": [f"{f['codigo']}: {f['titulo']}" for f in REFORESTA_STATUTORY_FINES],
        "proyectos_activos_espana": list(REFORESTA_ACTIVE_TERRITORIES.values()),
        "alianzas": [
            "Forética",
            "Asociación Española de Ecología Terrestre (AEET)",
            "Red de Custodia de Madrid y Castilla-La Mancha",
        ],
        "deducciones_fiscales": {
            "personas_juridicas": "Empresas: 40% en Impuesto sobre Sociedades (50% desde 3er año consecutivo, límite 15% BI)",
            "personas_fisicas": "Particulares: 80% primeros 250 € + 40% resto (45% desde 3er año, límite 10% base liquidable)",
        },
    }


def match_statute_alignment(
    titulo: str,
    texto: str,
    categorias: list[str] | None = None,
    ccaa_codigo: str | None = None,
) -> dict[str, Any]:
    """Match an opportunity against Reforesta's 11 official statutory goals & active territories."""
    haystack = f"{titulo} {texto} {' '.join(categorias or [])}".lower()
    matched = [
        f"{fine['codigo']} · {fine['titulo']}"
        for fine in REFORESTA_STATUTORY_FINES
        if any(kw in haystack for kw in fine["keywords"])
    ]
    if not matched:
        matched = ["Fin 3 · Protección, recuperación y gestión de espacios naturales y especies"]

    territory_note = REFORESTA_ACTIVE_TERRITORIES.get(ccaa_codigo or "")
    return {
        "fines_alineados": matched[:4],
        "presencia_territorial_previa": territory_note,
        "elegibilidad_juridica": "Asociación sin ánimo de lucro declarada de Utilidad Pública (NIF G80428204 · Reg. 162965 · 35 años de experiencia desde 1991)",
    }


_EXCLUSION_CLAUSE_RE = re.compile(
    r"(?:no\s+podr[aá]n\s+ser\s+beneficiar[ia]s|quedan\s+excluid[oa]s|se\s+excluye(?:n)?|"
    r"no\s+ser[aá]n\s+elegibles|est[aá]n\s+excluid[oa]s|excluidas?\s+expresamente)"
    r"[^.;\n]{0,220}",
    re.IGNORECASE,
)

_NGO_BAN_RE = re.compile(
    r"(?:"
    r"(?:no\s+podr[aá]n\s+ser\s+beneficiar[ia]s|quedan\s+excluid[oa]s|se\s+excluyen?)\s+"
    r"(?:las?\s+)?(?:entidades\s+sin\s+[aá]nimo\s+de\s+lucro|asociaciones|fundaciones|ong|esal|entidades\s+privadas)"
    r"|"
    r"(?:exclusivamente|solo|solamente|[uú]nicamente)\s+(?:para\s+|dirigid[oa]s?\s+a\s+)?"
    r"(?:empresas|pymes|aut[oó]nomos|sociedades\s+mercantiles|ayuntamientos|entidades\s+locales|"
    r"corporaciones\s+locales|concellos|universidades|propietarios\s+forestales|comunidades\s+de\s+montes|"
    r"titulares\s+de\s+explotaciones|agricultores|ganaderos|personas\s+f[ií]sicas)"
    r")",
    re.IGNORECASE,
)

_DOMICILE_OUTSIDE_MADRID_RE = re.compile(
    r"(?:domicilio\s+social(?:\s+(?:y|o)\s+fiscal)?|sede\s+social|domicilio\s+fiscal|"
    r"radicad[oa]s?(?:\s+legalmente)?|inscrit[oa]s?\s+en\s+el\s+registro(?:\s+de\s+asociaciones)?)"
    r"\s+(?:en|de)\s+(?:la\s+(?:comunidad|regi[oó]n)\s+(?:aut[oó]noma\s+)?de\s+)?"
    r"(andaluc[ií]a|arag[oó]n|asturias|principado\s+de\s+asturias|ill?es?\s+balears?|baleares|"
    r"canarias|cantabria|castilla[\s\-]+la\s+mancha|castilla\s+y\s+le[oó]n|"
    r"catalu[nñ]a|catalunya|comunitat\s+valenciana|comunidad\s+valenciana|extremadura|"
    r"galicia|la\s+rioja|regi[oó]n\s+de\s+murcia|murcia|navarra|comunidad\s+foral\s+de\s+navarra|"
    r"pa[ií]s\s+vasco|euskadi|ceuta|melilla|bizkaia|gipuzkoa|[aá]lava|"
    r"a\s+coru[nñ]a|lugo|ourense|pontevedra|barcelona|girona|lleida|tarragona|"
    r"sevilla|m[aá]laga|granada|c[oó]rdoba|c[aá]diz|huelva|ja[eé]n|almer[ií]a|"
    r"valencia|alicante|castell[oó]n|zaragoza|huesca|teruel|badajoz|c[aá]ceres)\b",
    re.IGNORECASE,
)

_NGO_POSITIVE_PATTERNS = (
    re.compile(r"sin\s+[aá]nimo\s+de\s+lucro", re.IGNORECASE),
    re.compile(r"sin\s+fin(?:es)?\s+de\s+lucro", re.IGNORECASE),
    re.compile(r"\besal\b", re.IGNORECASE),
    re.compile(r"tercer\s+sector", re.IGNORECASE),
    re.compile(r"inter[eé]s\s+social", re.IGNORECASE),
    re.compile(r"entidad(?:es)?\s+no\s+lucrativ[ao]s?", re.IGNORECASE),
    re.compile(r"organizaciones?\s+no\s+gubernamentales?", re.IGNORECASE),
    re.compile(r"\bongs?\b", re.IGNORECASE),
    re.compile(r"\b(?:non[\s\-]?profit|not[\s\-]?for[\s\-]?profit|ngos?)\b", re.IGNORECASE),
    re.compile(
        r"asociaciones?\s+(?:privadas?|sin|de\s+utilidad\s+p[uú]blica|ecologistas?|ambientales?|ciudadanas?|forestales?|y\s+fundaciones)",
        re.IGNORECASE,
    ),
    re.compile(r"custodia\s+del\s+territorio|entidades?\s+de\s+custodia", re.IGNORECASE),
    re.compile(r"personas\s+jur[ií]dicas\s+que\s+no\s+desarrollan\s+actividad\s+econ[oó]mica", re.IGNORECASE),
    re.compile(r"entidades?\s+sociales?(?:\s+del|\s+y\s+ambientales|\s+que|\s+para|\b)", re.IGNORECASE),
    re.compile(r"orden\s+ted/898/2023|1689/2026|923290", re.IGNORECASE),
)

_MITECO_LINEA_A_OVERRIDE_RE = re.compile(
    r"(?:923290|orden\s+ted/898/2023|concurrencia\s+competitiva\s+l[ií]nea\s+a|"
    r"actividades\s+(?:de\s+)?inter[eé]s\s+general\s+consideradas\s+(?:de\s+)?inter[eé]s\s+social)",
    re.IGNORECASE,
)

_EU_SME_ONLY_RE = re.compile(
    r"\b(?:eic\s+accelerator|smes?\s+only|only\s+for\s+smes?|exclusively\s+for\s+smes?|startups?\s+only)\b",
    re.IGNORECASE,
)

_NON_NGO_ONLY_STARTUP_INDIVIDUAL_RE = re.compile(
    r"\b(?:startups?|empresas?\s+emergentes?|spin[\s\-]?offs?|aceleradora|tesis\s+doctoral(?:es)?|"
    r"investigadores\s+individuales|j[oó]venes\s+investigadores|equipos\s+de\s+investigaci[oó]n)\b",
    re.IGNORECASE,
)

_TITLE_EXCLUSIVE_RECIPIENT_RE = re.compile(
    r"\b(?:dirigid[oa]s?\s+(?:exclusivamente\s+)?a|destinad[oa]s?\s+(?:exclusivamente\s+)?a|"
    r"subvenciones?\s+(?:a|para)|ayudas?\s+(?:p[uú]blicas?\s+)?(?:a|para))\s+"
    r"(?:las?\s+|los?\s+)?(?:"
    r"entidades?\s+locales?|ayuntamientos?|municipios?|corporaciones?\s+locales?|concellos?|"
    r"empresas?|pymes?|aut[oó]nomos?|sociedades?\s+mercantiles?|"
    r"centros?\s+(?:escolares?|educativos?|docentes?)|colegios?|institutos?|"
    r"propietarios?\s+forestales?|agricultores?|ganaderos?|comunidades?\s+de\s+montes|cazadores"
    r")\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ReforestaEligibility:
    """Strict eligibility assessment for Asociación Reforesta (ESAL, NIF G80428204, domicilio ES-MD)."""

    elegible: bool
    beneficiarios_tipos: list[str]
    motivo_elegibilidad: str
    dealbreakers: list[str]


def assess_reforesta_eligibility(
    titulo: str,
    organo: str = "",
    texto: str = "",
    beneficiarios_hint: str = "",
    tipo_oportunidad: str = "SUBVENCION",
    nivel_territorial: str = "ESTADO",
    ccaa_codigo: str = "ES",
    ccaa_nombre: str = "",
    requisitos_resumen: str = "",
    codigo_oficial: str = "",
    justificacion_juez: str = "",
) -> ReforestaEligibility:
    """
    Evaluate whether Asociación Reforesta (Asociación privada sin ánimo de lucro,
    Utilidad Pública, sede Tres Cantos - Madrid) can apply directly.

    Never scans `organo` for beneficiary category (avoiding false positives from
    "Fundación Biodiversidad" grants meant for municipalities or companies) and
    strips negative exclusion clauses before detecting positive NGO eligibility.
    """
    raw_body = f"{titulo}\n{texto}\n{requisitos_resumen}\n{codigo_oficial}"
    cleaned_body = _EXCLUSION_CLAUSE_RE.sub(" ", raw_body)

    # BDNS 923290 carries a ministerial entry quirk listing "PERSONAS FÍSICAS QUE NO DESARROLLAN ACTIVIDAD ECONÓMICA"
    # despite Orden TED/898/2023 restricting Línea A to Tercer Sector / interés social entities.
    is_miteco_linea_a = bool(_MITECO_LINEA_A_OVERRIDE_RE.search(raw_body))

    b_pos_text = f"{beneficiarios_hint} {cleaned_body}".lower()
    b_raw_text = f"{beneficiarios_hint} {raw_body}".lower()

    benef_types: list[str] = []

    has_ngo_marker = is_miteco_linea_a or any(
        pat.search(f"{beneficiarios_hint}\n{cleaned_body}") for pat in _NGO_POSITIVE_PATTERNS
    )
    is_eu_open = (
        tipo_oportunidad == "PROGRAMA_UE"
        or (nivel_territorial == "UE" and ("life" in b_raw_text or "horizon" in b_raw_text or "interreg" in b_raw_text))
    ) and not _EU_SME_ONLY_RE.search(b_raw_text)

    if is_eu_open:
        has_ngo_marker = True

    # Corporate/foundation grants mentioning NGOs/social entities/territorial conservation
    # without startup/company/academic-only restriction qualify for ESAL unless banned below.
    if (
        not has_ngo_marker
        and tipo_oportunidad == "CONVOCATORIA_PRIVADA"
        and not _NON_NGO_ONLY_STARTUP_INDIVIDUAL_RE.search(b_raw_text)
        and not _NGO_BAN_RE.search(b_raw_text)
        and not any(k in b_pos_text for k in ("pyme", "autónomos", "sociedades mercantiles", "contratista"))
        and any(
            k in b_pos_text
            for k in (
                "entidades sociales",
                "proyecto ambiental",
                "proyectos ambientales",
                "conservación",
                "biodiversidad",
                "reforestación",
                "renaturalización",
                "emprendimiento verde",
                "valor social",
                "sostenibilidad",
                "medioambiente",
                "medio ambiente",
                "clima",
                "climática",
            )
        )
    ):
        has_ngo_marker = True

    # If the title itself explicitly addresses a non-NGO audience without mentioning associations/ESAL/ONG,
    # reject NGO eligibility even if BDNS checked "PERSONAS JURÍDICAS QUE NO DESARROLLAN ACTIVIDAD ECONÓMICA".
    if (
        not is_miteco_linea_a
        and _TITLE_EXCLUSIVE_RECIPIENT_RE.search(titulo or "")
        and not re.search(
            r"sin\s+[aá]nimo\s+de\s+lucro|sin\s+fin(?:es)?\s+de\s+lucro|\besal\b|asociaci[oó]n|asociaciones|fundaci[oó]n|fundaciones|tercer\s+sector|\bong\b",
            titulo or "",
            re.IGNORECASE,
        )
    ):
        has_ngo_marker = False

    if has_ngo_marker:
        benef_types.append("ONG_FUNDACIONES")

    if any(
        k in b_pos_text
        for k in (
            "ayuntamiento",
            "entidades locales",
            "municipios",
            "corporaciones locales",
            "diputaci",
            "cabildo",
            "consell",
            "concello",
            "ajuntament",
            "udala",
            "mancomunidad",
            "administraciones públicas",
            "local authorities",
        )
    ):
        benef_types.append("AYUNTAMIENTO")

    if any(
        k in b_pos_text
        for k in (
            "empresas",
            "pyme",
            "pymes",
            "autónomos",
            "personas jurídicas que desarrollan actividad económica",
            "personas físicas que desarrollan actividad económica",
            "gran empresa",
            "startups",
            "startup",
            "emprendedores",
            "sociedades mercantiles",
            "contratista",
            "licitador",
            "sme",
            "explotaciones agrarias",
        )
    ):
        benef_types.append("EMPRESA_PYME")

    if not is_miteco_linea_a and any(
        k in b_pos_text
        for k in (
            "personas físicas que no desarrollan actividad económica",
            "propietarios forestales",
            "titulares de terrenos",
            "particulares",
            "agricultores",
            "ganaderos",
            "silvicultores",
            "becas individuales",
            "dehesas",
        )
    ):
        benef_types.append("PARTICULAR_PROPIETARIO")

    if any(
        k in b_pos_text
        for k in (
            "montes vecinales",
            "mano común",
            "man comun",
            "man común",
            "comunidades de montes",
            "agrupaciones de propietarios forestales",
            "agrupaciones forestales",
            "juntas vecinales",
            "sofor",
        )
    ):
        benef_types.append("COMUNIDAD_MONTES")

    if any(
        k in b_pos_text
        for k in (
            "universidad",
            "organismos públicos de investigación",
            "centros de investigación",
            "centros tecnológicos",
            "equipos de investigación",
            "investigadores",
            "centros educativos",
            "colegios",
            "institutos",
            "csic",
            "opis",
        )
    ):
        benef_types.append("UNIVERSIDAD_INVESTIGACION")

    # Apply explicit bans & restrictions for Asociación Reforesta
    ngo_banned = bool(_NGO_BAN_RE.search(f"{beneficiarios_hint}\n{raw_body}")) and not is_miteco_linea_a
    if ngo_banned and not has_ngo_marker:
        benef_types = [b for b in benef_types if b != "ONG_FUNDACIONES"]

    dealbreakers: list[str] = []

    domicile_match = None
    if ccaa_codigo not in ("ES", "EU", "ES-MD"):
        domicile_match = _DOMICILE_OUTSIDE_MADRID_RE.search(raw_body)

    if domicile_match:
        req_place = domicile_match.group(1).strip()
        benef_clean = benef_types or ["ESPECIFICO_TERRITORIAL"]
        msg = f"Exige domicilio o sede social en {req_place} (Reforesta tiene domicilio social en Tres Cantos, Madrid)."
        dealbreakers.append(msg)
        return ReforestaEligibility(
            elegible=False,
            beneficiarios_tipos=benef_clean,
            motivo_elegibilidad=f"Excluida para Reforesta: {msg}",
            dealbreakers=dealbreakers,
        )

    if ngo_banned and ("ONG_FUNDACIONES" not in benef_types or _EXCLUSION_CLAUSE_RE.search(raw_body)):
        # Re-check whether ban specifically excludes NGOs even if text mentioned NGO inside exclusion clause
        excl_chunks = " ".join(_EXCLUSION_CLAUSE_RE.findall(raw_body)).lower()
        if any(k in excl_chunks for k in ("sin ánimo de lucro", "sin animo de lucro", "asociaciones", "fundaciones", "esal")):
            benef_clean = [b for b in benef_types if b != "ONG_FUNDACIONES"] or ["EXCLUIDO_ESAL"]
            msg = "Las bases excluyen expresamente a asociaciones o entidades sin ánimo de lucro."
            dealbreakers.append(msg)
            return ReforestaEligibility(
                elegible=False,
                beneficiarios_tipos=benef_clean,
                motivo_elegibilidad=f"Excluida para Reforesta: {msg}",
                dealbreakers=dealbreakers,
            )

    if tipo_oportunidad == "LICITACION" and not has_ngo_marker:
        tender_body = f"{titulo}\n{texto}\n{requisitos_resumen}".lower()
        heavy_or_non_ngo_tender_re = re.compile(
            r"\b(?:"
            r"licitaci[oó]n\s+de\s+obras?|contrato\s+de\s+obras?|ejecuci[oó]n\s+de\s+obras?|mantenimiento\s+y\s+obra\b|"
            r"obras?\s+(?:de\s+)?(?:construcci[oó]n|rehabilitaci[oó]n|urbanizaci[oó]n|sellado|encauzamiento|abastecimiento|saneamiento|edificaci[oó]n|equipamiento|viales?|infraestructuras?)|"
            r"suministro\s+de\b|veh[ií]culos?|autobombas?|camiones?|maquinaria\s+(?:pesada|forestal|agr[ií]cola)|"
            r"ahoyado\s+mecanizado|tratamientos?\s+mecanizados?|desbroce\s+mecanizado|mantenimiento\s+mecanizado|"
            r"redes?\s+de\s+distribuci[oó]n\s+el[eé]ctrica|"
            r"sistema\s+din[aá]mico\s+de\s+adquisici[oó]n|\bestablecimiento\s+sda\b|"
            r"seguridad\s+y\s+salud\s+para\s+las\s+actuaciones|"
            r"desarrollo\s+de\s+(?:una\s+)?plataforma|sistemas?\s+de\s+gesti[oó]n\s+de\s+informaci[oó]n|aplicaci[oó]n\s+inform[aá]tica|software\b|"
            r"limpieza\s+viaria|limpieza\s+(?:y\s+mantenimiento\s+)?(?:de\s+)?playas|recogida\s+de\s+residuos|residuos\s+peligrosos|"
            r"centros?\s+residencia(?:les)?|quir[oó]fanos?|"
            r"parques?\s+y\s+jardines|zonas?\s+verdes?|arbolado\s+viario|poda\s+y\s+tratamiento\s+de\s+plagas|"
            r"palmeral(?:es)?|jardin(?:er[ií]a|es\s+en\s+centros)"
            r")\b",
            re.IGNORECASE,
        )
        statutory_service_re = re.compile(
            r"\b(?:"
            r"reforest\w*|repobl\w*|plantaci[oó]n\w*|restauraci[oó]n\s+(?:forestal|ecol[oó]gica|ambiental|de\s+h[aá]bitats?|hidrol[oó]gico)|"
            r"selvic\w*|silvic\w*|tratamientos?\s+silv[ií]colas?|trabajos?\s+silv[ií]colas?|tratamiento\s+de\s+la\s+vegetaci[oó]n|"
            r"prevenci[oó]n\s+de\s+incendios|emergencias\s+por\s+incendios\s+forestales|"
            r"biodiversidad|conservaci[oó]n\s+de\s+(?:la\s+)?(?:flora|fauna|h[aá]bitats?|especies|ecosistemas?)|"
            r"conservaci[oó]n,\s+mantenimiento\s+y\s+gesti[oó]n\s+de\s+(?:la\s+)?finca|"
            r"compensaci[oó]n\s+(?:voluntaria\s+)?de\s+(?:emisiones|huella\s+de\s+carbono)|sumideros?\s+de\s+carbono|"
            r"uso\s+p[uú]blico\s+e\s+informaci[oó]n\s+ambiental|informaci[oó]n\s+ambiental|\b(?:lic|zec|zepa)\s+[a-záéíóúñ]+|"
            r"educaci[oó]n\s+ambiental|sensibilizaci[oó]n\s+ambiental|voluntariado\s+ambiental|custodia\s+del\s+territorio|"
            r"inventario\s+forestal|gesti[oó]n\s+forestal|ordenaci[oó]n\s+de\s+montes|servicios?\s+forestal\w*"
            r")\b",
            re.IGNORECASE,
        )
        m_heavy = heavy_or_non_ngo_tender_re.search(tender_body)
        has_service_fit = bool(statutory_service_re.search(tender_body))
        if m_heavy or ngo_banned or not has_service_fit:
            reason_detail = (
                f"Licitación de obras, maquinaria o suministros ({m_heavy.group(0)})"
                if m_heavy
                else "Licitación de contratación pública (LCSP) ajena al objeto técnico o restringida a empresas"
            )
            msg = (
                f"{reason_detail}: orientada a contratistas industriales; "
                "Reforesta no es elegible como adjudicataria directa."
            )
            dealbreakers.append(msg)
            return ReforestaEligibility(
                elegible=False,
                beneficiarios_tipos=benef_types or ["EMPRESA_PYME"],
                motivo_elegibilidad=f"Excluida por requisitos de contratación: {msg}",
                dealbreakers=dealbreakers,
            )
        benef_types = list(dict.fromkeys([*benef_types, "ONG_FUNDACIONES", "CONTRATISTA_LCSP"]))
        return ReforestaEligibility(
            elegible=True,
            beneficiarios_tipos=benef_types,
            motivo_elegibilidad=(
                "Apta (LCSP Art. 65 · Contrato de servicios ambientales/forestales accesible a Asociación Reforesta "
                "por fines estatutarios acordes y solvencia técnica propia o en UTE)."
            ),
            dealbreakers=[],
        )

    if "ONG_FUNDACIONES" not in benef_types:
        if "EMPRESA_PYME" in benef_types:
            msg = "Reservada a empresas, PYMEs, autónomos o startups con actividad económica (no elegible para ESAL sin ánimo de lucro)."
        elif "AYUNTAMIENTO" in benef_types:
            msg = "Reservada exclusivamente a Ayuntamientos, Entidades Locales o Administraciones Públicas."
        elif "COMUNIDAD_MONTES" in benef_types:
            msg = "Reservada exclusivamente a Comunidades de Montes Vecinales en Mano Común (MVMC) o agrupaciones forestales."
        elif "PARTICULAR_PROPIETARIO" in benef_types:
            msg = "Reservada a personas físicas, agricultores o propietarios privados de terrenos."
        elif "UNIVERSIDAD_INVESTIGACION" in benef_types:
            msg = "Reservada a universidades, organismos públicos de investigación (OPIs), investigadores individuales o centros educativos."
        else:
            msg = "No acredita elegibilidad para asociaciones privadas sin ánimo de lucro (ESAL) en BDNS ni en las bases extractadas."
        dealbreakers.append(msg)
        return ReforestaEligibility(
            elegible=False,
            beneficiarios_tipos=benef_types or ["NO_ESPECIFICADO"],
            motivo_elegibilidad=f"Excluida para Reforesta: {msg}",
            dealbreakers=dealbreakers,
        )

    detail_tail = f" {justificacion_juez}" if justificacion_juez else ""
    return ReforestaEligibility(
        elegible=True,
        beneficiarios_tipos=benef_types,
        motivo_elegibilidad=(
            f"Apta para Asociación Reforesta ({', '.join(benef_types)}).{detail_tail}".strip()
        ),
        dealbreakers=[],
    )
