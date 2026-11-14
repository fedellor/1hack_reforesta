"""Official institutional & statutory profile of Asociación Reforesta (from reforesta.es)."""
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
