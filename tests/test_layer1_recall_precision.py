"""Comprehensive Recall & Precision Tests for Layer 1 Hybrid Filter (ES/CA/GL/EU/EN + CPV + Anti-Noise)."""
import pytest
from app.pipeline.layer1_regex import detect_language, evaluate_layer1


@pytest.mark.parametrize(
    ("titulo", "organo", "texto", "expected_cat"),
    [
        # Spanish direct reforestation & wildfire
        (
            "Subvenciones para repoblación forestal y cortafuegos en montes vecinales",
            "Junta de Castilla y León",
            "Plantación de frondosas autóctonas y fajas auxiliares.",
            "reforestacion",
        ),
        (
            "Ayudas para restauración hidrológico-forestal de zonas quemadas",
            "Junta de Andalucía",
            "Recuperación de superficie incendiada y prevención de erosión.",
            "restauracion_post_incendio",
        ),
        # Riparian, urban greening, nature-based solutions, agroforestry (High-recall expansions!)
        (
            "Ayudas para restauración fluvial y recuperación del bosque de ribera en la cuenca del Tajo",
            "Confederación Hidrográfica del Tajo",
            "Revegetación de sotos fluviales, estabilización de taludes y conectividad ecológica.",
            "reforestacion",
        ),
        (
            "Convocatoria municipal para anillo verde y arbolado urbano contra islas de calor",
            "Ayuntamiento de Vitoria-Gasteiz",
            "Infraestructura verde urbana con especies arbóreas autóctonas y educación ambiental.",
            "reforestacion",
        ),
        (
            "Subvenciones para mosaico agroforestal, silvopastoralismo y quemas prescritas preventivas",
            "Gobierno de Aragón",
            "Puntos de agua contra incendios, balsas contra incendios y pistas forestales.",
            "prevencion_incendios",
        ),
        (
            "Programa estatal de conservación de encinares, alcornocales y dehesas",
            "MITECO",
            "Gestión sostenible de robledales, hayedos, castañares y custodia forestal.",
            "silvicultura",
        ),
        (
            "Convocatoria Motor Verde para sumideros de carbono y bonos de carbono MITECO",
            "Fundación Repsol / Motor Verde",
            "Captura de carbono y fijación de CO2 mediante plantaciones forestales.",
            "absorcion_carbono",
        ),
        (
            "Ayudas a proyectos de voluntariado ambiental y educación ambiental en espacios protegidos",
            "Fundación Biodiversidad",
            "Voluntariado forestal, custodia del territorio y recuperación de áreas degradadas.",
            "restauracion_ecologica",
        ),
        # Co-official languages & English
        (
            "Subvencions per a la restauració d'hàbitats, bosc de ribera i prevenció d'incendis forestals",
            "Generalitat de Catalunya",
            "Tallafocs, franges de protecció i gestió forestal sostenible a la Xarxa Natura 2000.",
            "prevencion_incendios",
        ),
        (
            "Orde pola que se convocan axudas para repoboación forestal, soutos e faixas de xestión da biomasa",
            "Xunta de Galicia",
            "Prevención e defensa contra os lumes forestais en comunidades de montes veciñais.",
            "prevencion_incendios",
        ),
        (
            "Diru-laguntzak baso-berritze, zuhaitz landaketa eta baso-suteen prebentziorako",
            "Gipuzkoako Foru Aldundia",
            "Baso-kudeaketa iraunkorra eta natura-ondarea.",
            "reforestacion",
        ),
        (
            "Call for proposals: Urban greening, riparian restoration and nature-based solutions in Europe",
            "European Commission - Horizon Europe",
            "Scaling up tree canopy, soil restoration and wildfire resilience.",
            "reforestacion",
        ),
    ],
)
def test_layer1_high_recall_positive_cases(titulo: str, organo: str, texto: str, expected_cat: str):
    res = evaluate_layer1(titulo=titulo, organo=organo, texto=texto)
    assert res.passed is True, f"False negative for: {titulo}"
    assert res.score >= 25
    assert expected_cat in res.matched_categories


def test_layer1_cpv_tiers_and_inline_cpv_detection():
    # Tier A forestry CPV without explicit keyword in title -> MUST PASS DIRECTA
    tier_a = evaluate_layer1(
        titulo="Servicio técnico en parcelas municipales del término municipal",
        organo="Ayuntamiento de Cuenca",
        cpv_codes=["77231600-4"],
    )
    assert tier_a.passed is True
    assert tier_a.preliminary_relevance == "DIRECTA"
    assert "reforestacion" in tier_a.matched_categories

    # Inline CPV hidden inside body text (no cpv_codes arg) + environmental agency
    inline_cpv = evaluate_layer1(
        titulo="Contrato de actuaciones en zona rural Lote 2",
        organo="TRAGSA",
        texto="Objeto del pliego según codificación CPV 75251120-7 para trabajos anuales.",
    )
    assert inline_cpv.passed is True
    assert inline_cpv.preliminary_relevance == "DIRECTA"
    assert "prevencion_incendios" in inline_cpv.matched_categories

    # Tier B environmental CPV (90710000) -> MUST PASS as candidate
    tier_b = evaluate_layer1(
        titulo="Asistencia técnica ambiental municipal",
        organo="Diputación de León",
        cpv_codes=["90710000-7"],
    )
    assert tier_b.passed is True
    assert tier_b.score >= 35


def test_layer1_immune_to_bdns_mislabeled_sector():
    # Simulates BDNS MITECO bug where sector says ACTIVIDADES INMOBILIARIAS
    res = evaluate_layer1(
        titulo="LÍNEA A DESARROLLO ACTIVIDADES INTERÉS GENERAL PROTECCIÓN DEL MEDIO AMBIENTE",
        organo="MINISTERIO PARA LA TRANSICIÓN ECOLÓGICA Y EL RETO DEMOGRÁFICO",
        texto="Sector económico: ACTIVIDADES INMOBILIARIAS. Fomento investigación y protección ambiental.",
    )
    assert res.passed is True
    assert res.preliminary_relevance == "INDIRECTA_ELEGIBLE"
    assert res.score >= 45


@pytest.mark.parametrize(
    ("titulo", "organo", "texto", "cpvs"),
    [
        (
            "Suministro y recarga de extintores portátiles en centros escolares",
            "Ayuntamiento de Madrid",
            "Mantenimiento de bocas de incendio equipadas.",
            [],
        ),
        (
            "Instalación de detección de incendios en edificio administrativo y garaje",
            "Consejería de Hacienda",
            "Protección pasiva contra incendios en edificio.",
            [],
        ),
        (
            "Subasta judicial por extinción de condominio y Monte de Piedad",
            "Juzgado de Primera Instancia",
            "Bien inmueble urbano.",
            [],
        ),
        (
            "Renovación de césped artificial en campo de fútbol municipal",
            "Patronato Municipal de Deportes",
            "Obra civil deportiva.",
            ["45112720"],
        ),
        (
            "Suministro de plantas de temporada para rotondas urbanas",
            "Concejalía de Tráfico",
            "Petunias y geranios ornamentales.",
            ["77310000"],
        ),
        (
            "Contratación de licencias de software ERP y ciberseguridad",
            "Diputación de Sevilla",
            "Transformación digital administrativa.",
            ["48000000"],
        ),
        (
            "Reforzar la investigación forestal para apoyar a Ucrania",
            "European Commission - Horizon Europe",
            "Strengthening forest research for the support of Ukraine. HORIZON-RIA Research and Innovation Actions.",
            [],
        ),
        (
            "Becas predoctorales para formación de personal investigador en ecología y bosques",
            "Ministerio de Ciencia, Innovación y Universidades",
            "Tesis doctoral y estancias de investigación en centros universitarios.",
            ["73110000"],
        ),
        (
            "Subvenciones para proyectos de cooperación internacional al desarrollo y reforestación en África Subsahariana y América Latina",
            "AECID / Diputación Provincial",
            "Actuaciones de agroforestería en Senegal, Perú y Colombia.",
            [],
        ),
        (
            "Obras de rehabilitación de cuarteladas interiores y laterales y paramentos verticales",
            "Ministerio de Defensa",
            "Reforma de edificio y patio interior.",
            ["45112700"],
        ),
        (
            "Servicios de mantenimiento de jardines de en los Centros de Acogida de Menores",
            "Consejería de Bienestar Social",
            "Siega y jardinería de edificios administrativos.",
            ["77310000"],
        ),
        (
            "GC Subvención nominativa a favor de empresa pública para gestión medioambiental",
            "Cabildo de Gran Canaria",
            "Concesión directa nominativa cerrada.",
            [],
        ),
        (
            "Anuncio de formalización de contratos de: Consejo de Administración del Patrimonio Nacional",
            "BOE - Patrimonio Nacional",
            "Formalización de contrato ya adjudicado de poda de arbolado.",
            ["77340000"],
        ),
    ],
)
def test_layer1_rejects_administrative_noise(titulo: str, organo: str, texto: str, cpvs: list[str]):
    res = evaluate_layer1(titulo=titulo, organo=organo, texto=texto, cpv_codes=cpvs or None)
    assert res.passed is False, f"False positive noise leaked through: {titulo}"
    assert res.decision == "REJECT"


def test_foreign_aid_for_spain_accepted_but_foreign_territory_rejected():
    """Verify foreign/EU grants to reforest IN Spain pass, while calls for foreign territories are rejected."""
    eu_for_spain = evaluate_layer1(
        titulo="Call for proposals: LIFE Nature - Native Reforestation and Wildfire Prevention in Spain (Iberian Peninsula)",
        organo="European Commission - CINEA",
        texto="Tree planting and ecological restoration in Spanish Natura 2000 habitats.",
    )
    assert eu_for_spain.passed is True

    foreign_only = evaluate_layer1(
        titulo="Call for proposals: Forest restoration and tree planting in Ukraine and Moldova",
        organo="European Commission",
        texto="Afforestation in Eastern Partnership countries.",
    )
    assert foreign_only.passed is False
    assert "fuera de España" in (foreign_only.rejection_reason or "")


def test_language_detection_accuracy():
    assert detect_language("Convocatoria de ayudas para repoblación forestal y prevención") == "es"
    # Spanish text mentioning a single English acronym ("for") must stay Spanish!
    assert detect_language("Subvención MITECO para proyectos LIFE Nature and Biodiversity en España") == "es"
    assert detect_language("Call for proposals: Forest restoration under Horizon Europe grants and wildfires") == "en"
    assert detect_language("Subvencions de la Generalitat de Catalunya per a la gestió forestal i prevenció d'incendis forestals") == "ca"
    assert detect_language("Orde pola que se regulan subvencións da Xunta de Galicia en montes veciñais e lumes forestais") == "gl"
    assert detect_language("Bizkaiko Foru Aldundia: baso-berritze eta baso-suteen diru-laguntzak") == "eu"


@pytest.mark.parametrize(
    "titulo,organo,texto,sector",
    [
        (
            "AYUDAS CONCURRENCIA COMPETITIVA LÍNEA A DESARROLLO ACTIVIDADES INTERÉS GENERAL CONSIDERADAS INTERÉS SOCIAL, EN EL ÁMBITO DE LA INVESTIGACIÓN CIENTÍFICA Y TÉCNICA Y PROTECCIÓN MEDIO AMBIENTE EN MATERIAS DE COMPETENCIA ESTATAL. ANUALIDAD 2026.",
            "MINISTERIO PARA LA TRANSICIÓN ECOLÓGICA Y EL RETO DEMOGRÁFICO",
            "Orden TED/898/2023. Actividades de interés general en investigación científica y técnica y protección del medio ambiente, 2026.",
            "ACTIVIDADES INMOBILIARIAS",
        ),
        (
            "AYUDAS CONCURRENCIA COMPETITIVA LÍNEA A DESARROLLO ACTIVIDADES INTERÉS GENERAL CONSIDERADAS INTERÉS SOCIAL, EN EL ÁMBITO DE LA INVESTIGACIÓN CIENTÍFICA Y TÉCNICA Y PROTECCIÓN MEDIO AMBIENTE EN MATERIAS DE COMPETENCIA ESTATAL. ANUALIDAD 2025.",
            "MINISTERIO PARA LA TRANSICIÓN ECOLÓGICA Y EL RETO DEMOGRÁFICO",
            "Convocatoria estatal MITECO 2025 para investigación y protección del medio ambiente.",
            None,
        ),
        (
            "Ayudas a Proyectos de Investigación Científica en Ecología y Biología de la Conservación",
            "Fundación BBVA",
            "Convocatoria competitiva en España sobre ecología terrestre, biodiversidad y restauración de ecosistemas.",
            None,
        ),
        (
            "Presenta tu candidatura: II Convocatoria de Proyectos de Biodiversidad Fundación Endesa",
            "Fundación Endesa",
            "Bases legales II Convocatoria dotada con 200.000 euros para proyectos de conservación de la biodiversidad en España.",
            None,
        ),
        (
            "Convocatoria Emprendimiento Verde para entidades sin ánimo de lucro",
            "Fundación Endesa",
            "Ayudas para conservación de ecosistemas y transición ecológica.",
            None,
        ),
        (
            "Proyectos estratégicos orientados a la Transición Ecológica y a la Transición Digital",
            "Agencia Estatal de Investigación (AEI)",
            "I+D+i en mitigación del cambio climático, gestión forestal sostenible, incendios y biodiversidad.",
            None,
        ),
        (
            "Research and Innovation Actions: Restoring forest biodiversity and soil resilience in Mediterranean ecosystems",
            "European Commission - Horizon Europe",
            "Grants executable in Spain for scientific research and ecological restoration.",
            None,
        ),
        (
            "Abiertas Ayudas a Proyectos de Investigación 2026",
            "Fundación CajaCanarias",
            "Proyectos de investigación científica en medio ambiente, cambio climático y biodiversidad en Canarias.",
            None,
        ),
    ],
)
def test_layer1_and_layer2_accept_public_and_private_environmental_research(
    titulo: str,
    organo: str,
    texto: str,
    sector: str | None,
):
    from app.pipeline.layer2_judge import evaluate_layer2

    full_text = f"{texto}\nSector económico: {sector}" if sector else texto
    r1 = evaluate_layer1(titulo=titulo, organo=organo, texto=full_text)
    assert r1.passed is True, f"Rejected environmental research grant in Layer 1: {titulo} ({r1.rejection_reason})"
    r2 = evaluate_layer2(titulo=titulo, organo=organo, texto=full_text, layer1_result=r1, use_persistent_cache=False)
    assert r2.es_relevante is True, f"Rejected environmental research grant in Layer 2: {titulo} ({r2.justificacion_juez_es})"


def test_layer1_still_rejects_non_environmental_research():
    r1 = evaluate_layer1(
        titulo="Premios de Investigación Matemática Vicent Caselles 2025",
        organo="Fundación BBVA",
        texto="Premios para investigación científica en matemáticas puras y estadística.",
    )
    assert r1.passed is False


@pytest.mark.parametrize(
    ("titulo", "organo", "texto"),
    [
        (
            "Anuncio de la Confederación Hidrográfica del Tajo sobre solicitud de concesión de aguas públicas",
            "Ministerio para la Transición Ecológica y el Reto Demográfico",
            "Información pública de expediente de aprovechamiento de 12,5 l/s para riego.",
        ),
        (
            "Resolución de la Dirección General de Calidad y Evaluación Ambiental por la que se formula declaración de impacto ambiental del proyecto Parque Eólico Las Lomas",
            "Ministerio para la Transición Ecológica y el Reto Demográfico",
            "Declaración de impacto ambiental favorable para planta fotovoltaica e hibridación.",
        ),
        (
            "BECAS PARA PRÁCTICAS DE ESTUDIANTES DEL MITECO",
            "Ministerio para la Transición Ecológica y el Reto Demográfico",
            "Becas de formación práctica para estudiantes universitarios.",
        ),
        (
            "Resolución de la Consejería de Transición Ecológica por la que se convoca el Concurso de Pieza Única de Artesanía Artística",
            "Consejería de Transición Ecológica",
            "Premios y talleres de artesanía artística y promoción comercial.",
        ),
        (
            "Ayudas para la creación de la Cátedra de Cambio Climático",
            "Gobierno de Canarias",
            "Convenio para la creación de la Cátedra de Cambio Climático en la universidad.",
        ),
        (
            "202604306014_Dir 22.2.c_Subvención nominativa",
            "Diputación Provincial",
            "Subvención concedida al amparo del artículo 22.2.c LGS.",
        ),
        (
            "Ayudas para ahorro y eficiencia energética en pymes",
            "Consejería de Transición Ecológica y Energía",
            "Subvenciones orientadas a ahorro y eficiencia energética en instalaciones industriales.",
        ),
        (
            "Mantenimiento de los medios y equipos que componen el sistema de defensa contra incendios en los edificios de la AEAT",
            "Ministerio de Hacienda - AEAT",
            "Mantenimiento de equipos de protección contra incendios en edificios administrativos.",
        ),
    ],
)
def test_layer1_rejects_administrative_boe_bdns_non_grant_noise(titulo: str, organo: str, texto: str):
    r1 = evaluate_layer1(titulo=titulo, organo=organo, texto=texto)
    assert r1.passed is False, f"False positive passed Layer 1: {titulo} (score={r1.score}, cats={r1.matched_categories})"

