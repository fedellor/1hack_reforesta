"""Layer 1: High-Recall Multilingual Rigid Filter (Regex ES/CA/GL/EU/EN + Tiered CPV + Issuing Body + Anti-Noise)."""
import re
from dataclasses import dataclass, field
from app.config import settings


@dataclass
class Layer1Result:
    passed: bool
    decision: str  # PASS_HIGH | PASS_CANDIDATE | REJECT
    score: int
    preliminary_relevance: str  # DIRECTA | INDIRECTA_ELEGIBLE | DESCARTADA
    detected_language: str
    matched_categories: list[str] = field(default_factory=list)
    matched_terms: list[str] = field(default_factory=list)
    rejection_reason: str | None = None


# Block 1: Reforestation, Afforestation, Silviculture, Riparian Forests & Carbon (+50 pts)
PATTERNS_REFORESTATION: list[tuple[str, re.Pattern[str]]] = [
    (
        "reforestacion",
        re.compile(
            r"\b("
            r"reforest\w*|repoblaci[oó]n\s+forestal|forestaci[oó]n|plantaci[oó]n\s+de\s+[aá]rbol\w*|"
            r"plantaci[oó]n\s+(?:forestal|de\s+frondosas|con\s+especies\s+aut[oó]ctonas)|"
            r"especies\s+arb[oó]reas|especies\s+aut[oó]ctonas|vivero[s]?\s+forestal\w*|"
            r"restauraci[oó]n\s+forestal|restauraci[oó]n\s+hidrol[oó]gico[-\s]?forestal|"
            r"restauraci[oó]n\s+fluvial|bosque[s]?\s+de\s+ribera|vegetaci[oó]n\s+de\s+ribera|sotos?\s+fluvial\w*|"
            r"cubierta\s+vegetal|revegetaci[oó]n|hidrosiembra|estabilizaci[oó]n\s+de\s+taludes|"
            r"infraestructura\s+verde(?:\s+urbana)?|anillo\s+verde|renaturalizaci[oó]n(?:\s+(?:urbana|fluvial))?|"
            r"arbolado\s+urbano|arboleda[s]?|islas?\s+de\s+calor|patrimonio\s+forestal|"
            # Catalan / Valencian / Balearic
            r"repoblaci[oó]\s+forestal|infraestructura\s+verda|renaturalitzaci[oó]|"
            r"bosc(?:os)?\s+de\s+ribera|arbrat\s+urb[àa]|vegetaci[oó]\s+aut[oò]ctona|"
            # Galician
            r"repoboaci[oó]n\s+forestal|frondosas\s+aut[oó]ctonas|restauraci[oó]n\s+hidrol[oó]xico[-\s]?forestal|"
            r"arboredo|souto[s]?|carballeira[s]?|fragas|"
            # Basque
            r"baso[-\s]?berritze\w*|zuhaitz\s+landaketa\w*|ibai[-\s]?baso\w*|"
            # English (EU & RSC calls)
            r"reforest\w*|afforest\w*|replant\w*|tree\s+planting|tree\s+canopy|native\s+trees|"
            r"forest\s+restoration|forest\s+landscape\s+restoration|riparian\s+(?:forest|restoration)|"
            r"urban\s+(?:forest|greening)|green\s+infrastructure|rewilding"
            r")\b",
            re.IGNORECASE,
        ),
    ),
    (
        "silvicultura",
        re.compile(
            r"\b("
            r"silvicult\w*|selvicult\w*|masa[s]?\s+forestal\w*|gesti[oó]n\s+forestal|"
            r"monte[s]?\s+(?:p[uú]blico|vecinal|comunal|protector|ordenado|demanial|catalogado)\w*|"
            r"aprovechamiento[s]?\s+forestal\w*|ordenaci[oó]n\s+de\s+montes|arboricult\w*|parcelas?\s+forestal\w*|"
            r"dehesa[s]?|agroforest\w*|sistemas?\s+agroforestal\w*|silvopastor\w*|mosaico\s+agroforestal|"
            r"ganader[ií]a\s+extensiva\s+preventiva|custodia\s+forestal|bosque[s]?|"
            r"encinar(?:es)?|alcornocal(?:es)?|robledal(?:es)?|hayedo[s]?|casta[ñn]ar(?:es)?|pinar(?:es)?|sabinar(?:es)?|"
            # Catalan / Galician / Basque / English
            r"gesti[oó]\s+forestal|massa\s+forestal|bosc(?:os)?|bosc\s+p[uú]blic|xesti[oó]n\s+forestal|"
            r"monte[s]?\s+veci[ñn]a(?:l|is)|comunidade[s]?\s+de\s+montes|man\s+com[uú]n|"
            r"basogintza\w*|baso[-\s]?kudeaketa\w*|zuhaizti\w*|"
            r"forest\s+management|sustainable\s+forestry|agroforestry|woodland\w*"
            r")\b",
            re.IGNORECASE,
        ),
    ),
    (
        "absorcion_carbono",
        re.compile(
            r"\b("
            r"sumidero[s]?\s+de\s+carbono|absorci[oó]n\s+de\s+co2|captura\s+de\s+carbono|"
            r"fijaci[oó]n\s+de\s+carbono|secuestro\s+de\s+carbono|cr[eé]dito[s]?\s+de\s+carbono|"
            r"bono[s]?\s+de\s+carbono|huella\s+de\s+carbono.*(?:absorci[oó]n|forestal|compensaci[oó]n)|"
            r"carbon\s+sink\w*|carbon\s+farming|carbon\s+sequestration|carbon\s+offset\w*"
            r")\b",
            re.IGNORECASE,
        ),
    ),
]

# Block 2: Wildfires Prevention, Suppression & Post-Fire Restoration (+50 pts)
PATTERNS_WILDFIRES: list[tuple[str, re.Pattern[str]]] = [
    (
        "prevencion_incendios",
        re.compile(
            r"\b("
            r"incendio[s]?\s+forestal\w*|prevenci[oó]n\s+de\s+incendios(?:\s+forestales)?|"
            r"defensa\s+contra\s+(?:los\s+)?incendios(?:\s+forestales)?|lucha\s+contra\s+incendios\s+forestales|"
            r"extinci[oó]n\s+de\s+incendios\s+forestales|cortafuego[s]?|"
            r"faja[s]?\s+(?:auxiliar|pir[oó]fuga|secundaria|de\s+gesti[oó]n\s+de\s+biomasa)\w*|"
            r"desbroce[s]?\s+(?:forestal|preventivo|de\s+montes|de\s+matorral)\w*|"
            r"biomasa\s+forestal|limpieza\s+de\s+montes|tratamiento[s]?\s+s[ei]lv[ií]cola\w*\s+preventivo\w*|"
            r"quema[s]?\s+(?:prescrita|controlada)\w*|punto[s]?\s+de\s+agua\s+contra\s+incendios|"
            r"balsa[s]?\s+contra\s+incendios|pista[s]?\s+forestal\w*|red\s+de\s+caminos\s+forestales|"
            r"vigilancia\s+forestal|brigada[s]?\s+forestal\w*|medios\s+a[eé]reos.*incendios|"
            r"autoprotecci[oó]n\s+forestal|plan(?:es)?\s+local(?:es)?\s+de\s+prevenci[oó]n\s+de\s+incendios|"
            # Catalan / Valencian / Balearic
            r"incendi[s]?\s+forestal\w*|prevenci[oó]\s+d\s*['’]?\s*incendis|tallafoc[s]?|"
            r"franges\s+(?:de\s+protecci[oó]|perimetrals)|basses?\s+d\s*['’]?\s*incendis|xarxa\s+de\s+camins\s+forestals|"
            # Galician
            r"lume[s]?\s+forestal\w*|prevenci[oó]n\s+e\s+defensa\s+contra\s+(?:os\s+)?incendios|"
            r"faixas?\s+de\s+xesti[oó]n\s+da\s+biomasa|devasa[s]?|roza[s]?\s+forestal\w*|puntos?\s+de\s+auga|"
            # Basque
            r"baso[-\s]?sute\w*|sute(?:en)?\s+prebentzio\w*|"
            # English
            r"wildfire[s]?|forest\s+fire[s]?|fire\s+prevention|fuel\s+management|prescribed\s+(?:burning|fire)|"
            r"integrated\s+fire\s+management|fire[-\s]?resilient\s+landscape\w*"
            r")\b",
            re.IGNORECASE,
        ),
    ),
    (
        "restauracion_post_incendio",
        re.compile(
            r"\b("
            r"zona[s]?\s+(?:incendiada|quemada|afectada[s]?\s+por\s+incendio)\w*|"
            r"superficie[s]?\s+(?:quemada|incendiada)\w*|"
            r"restauraci[oó]n\s+de\s+(?:montes|zonas|terrenos|bosques)\s+(?:incendiad|quemad)\w*|"
            r"recuperaci[oó]n\s+(?:forestal|ambiental|ecol[oó]gica)\s+tras\s+(?:el\s+|un\s+)?incendio\w*|"
            r"da[ñn]os\s+en\s+bosques\s+por\s+incendios|post[-\s]?fire\s+(?:restoration|recovery|rehabilitation)"
            r")\b",
            re.IGNORECASE,
        ),
    ),
]

# Block 3: Biodiversity, Natura 2000, Climate Adaptation, Education & Environmental Protection (+25 pts)
PATTERNS_BIODIVERSITY_ENV: list[tuple[str, re.Pattern[str]]] = [
    (
        "biodiversidad",
        re.compile(
            r"\b("
            r"biodiversidad\w*|biodiversitat|biodiversity|biodibertsitate\w*|"
            r"patrimonio\s+natural|patrimoni\s+natural|natura[-\s]?ondarea|"
            r"red\s+natura\s+2000|xarxa\s+natura\s+2000|natura\s+2000|"
            r"espacios?\s+natural(?:es)?\s+protegido[s]?|espais\s+naturals\s+protegits|"
            r"h[aá]bitat(?:s)?(?:\s+de\s+inter[eé]s\s+comunitario|\s+forestal\w*|\s+natural\w*)?|"
            r"[aá]rbol(?:es)?\s+singular(?:es)?|flora\s+silvestre|especie[s]?\s+amenazada[s]?|"
            r"custodia\s+del\s+territorio|cust[oò]dia\s+del\s+territori|custodia\s+fluvial|"
            r"corredor(?:es)?\s+ecol[oó]gico[s]?|conectividad\s+ecol[oó]gica|microrreserva[s]?|"
            r"conservaci[oó]n\s+de\s+la\s+naturaleza|natural\s+heritage"
            r")\b",
            re.IGNORECASE,
        ),
    ),
    (
        "restauracion_ecologica",
        re.compile(
            r"\b("
            r"restauraci[oó]n\s+(?:ecol[oó]gica|ambiental|de\s+ecosistemas|del\s+medio\s+natural|d['’]h[àa]bitats)|"
            r"protecci[oó]n\s+(?:del\s+|al\s+)?medio\s+ambiente|conservaci[oó]n\s+ambiental|"
            r"proyecto[s]?\s+(?:medio)?ambiental\w*|actuaci[oó]n(?:es)?\s+(?:medio)?ambiental\w*|"
            r"iniciativa[s]?\s+(?:medio)?ambiental\w*|educaci[oó]n\s+ambiental|"
            r"voluntariado\s+(?:ambiental|forestal)|sensibilizaci[oó]n\s+ambiental|"
            r"adaptaci[oó]n\s+al\s+cambio\s+clim[aá]tico|canvi\s+clim[àa]tic|resiliencia\s+del\s+ecosistema|"
            r"soluciones\s+basadas\s+en\s+la\s+naturaleza|lucha\s+contra\s+la\s+desertificaci[oó]n|"
            r"erosi[oó]n\s+de\s+suelos|suelos?\s+degradados|recuperaci[oó]n\s+de\s+[aá]reas\s+degradadas|"
            r"ecological\s+restoration|nature\s+restoration(?:\s+law)?|ecosystem\s+restoration|"
            r"habitat\s+restoration|climate\s+change\s+adaptation|ecosystem\s+resilience|"
            r"soil\s+(?:restoration|erosion)|desertification|nature[-\s]?based\s+solutions"
            r")\b",
            re.IGNORECASE,
        ),
    ),
    (
        "investigacion_forestal",
        re.compile(
            r"\b("
            r"investigaci[oó]n\s+forestal|sanidad\s+forestal|plagas\s+forestales|"
            r"investigaci[oó]n\s+cient[ií]fica\s+y\s+t[eé]cnica.*medio\s+ambiente|"
            r"bioeconom[ií]a\s+forestal|innovaci[oó]n\s+forestal|"
            r"forest\s+research|forest\s+health|forest\s+monitoring"
            r")\b",
            re.IGNORECASE,
        ),
    ),
]

# Issuing body & strategic forestry agency boost (+20 pts)
ORGANO_BOOST_PATTERN = re.compile(
    r"\b("
    r"miteco|transici[oó]n\s+ecol[oó]gica|medio\s+ambiente|medi\s+ambient|medio\s+rural|"
    r"montes|pol[ií]tica\s+forestal|biodiversidad|parques\s+nacionales|oapn|"
    r"confederaci[oó]n\s+hidrogr[aá]fica|confederaci[oó]\s+hidrogr[aà]fica|desarrollo\s+rural|ingurumena|"
    r"tragsa\w*|geacam|vaersa|sarga|seaga|hazi|cesefor|ctfc|infoca\w*|pladiga|"
    r"feader|prtr|nextgeneration\w*|mecanismo\s+de\s+recuperaci[oó]n|"
    r"cinea|programa\s+life|life\s+programme|horizon\s+europe|interreg|"
    r"fundaci[oó]n\s+la\s+caixa|fundaci[oó]n\s+banco\s+santander|fundaci[oó]n\s+bbva|"
    r"fundaci[oó]n\s+repsol|motor\s+verde|fundaci[oó]n\s+iberdrola|fundaci[oó]n\s+endesa|"
    r"fundaci[oó]n\s+naturgy|afundaci[oó]n|retree|bosques\s+sostenibles|sylvestris|"
    r"eoca|one\s+tree\s+planted"
    r")\b",
    re.IGNORECASE,
)

# Tier A CPVs: Direct Forestry, Seeds, Wildfire Prevention & Protection (+60 pts, marks DIRECTA)
TIER_A_CPV_PREFIXES = (
    "772",       # 77200000-2 Servicios forestales, 77231000 Gestión forestal, 77231600 Repoblación
    "75251120",  # 75251120-7 Servicios de prevención de incendios forestales
    "034",       # 03400000 Productos de la silvicultura, semillas/plantones forestales
    "03121",     # 03121100 Plantas vivas, árboles y arbustos
)

# Tier B CPVs: Environmental Engineering, Natural Hazards & Green Infrastructure (+35 pts, lets Layer 2 evaluate)
TIER_B_CPV_PREFIXES = (
    "9071",      # 90710000-7 Gestión medioambiental
    "9072",      # 90721800-5 Protección contra riesgos o peligros naturales / protección ambiental
    "7731",      # 77310000 Plantación y mantenimiento de zonas verdes
    "7734",      # 77340000 Poda de árboles y setos / arboricultura
    "451127",    # 45112700 Trabajos de paisajismo / reforestación / anillos verdes
    "71313",     # 71313000 Servicios de consultoría en ingeniería ambiental
    "7311",      # 73110000 Servicios de investigación ambiental
)

INLINE_CPV_PATTERN = re.compile(
    r"\b((?:772\d{5}|75251120|9071\d{4}|9072\d{4}|7731\d{4}|7734\d{4}|451127\d{2}|71313\d{3}|7311\d{4}|034\d{5}|03121\d{3})(?:-\d)?)\b"
)


def extract_cpv_codes(text: str) -> list[str]:
    """Extract normalized 8-digit relevant forestry/environmental CPV codes from arbitrary text."""
    return sorted({m.split("-")[0] for m in INLINE_CPV_PATTERN.findall(text or "")})


# Anti-noise negative patterns (Reject ONLY when no explicit forestry/wildfire match)
NEGATIVE_NOISE_PATTERN = re.compile(
    r"\b("
    r"extinci[oó]n\s+de\s+condominio|extinci[oó]n\s+de\s+contrato|monte\s+de\s+piedad|"
    r"extintor(?:es)?\s+port[aá]til\w*|recarga\s+de\s+extintores|"
    r"detecci[oó]n\s+de\s+incendios\s+en\s+(?:edificio|colegio|hospital|oficina|pabell[oó]n|nave|parking|garaje)|"
    r"protecci[oó]n\s+pasiva\s+contra\s+incendios\s+en\s+edificio\w*|boca[s]?\s+de\s+incendio\s+equipad\w*|"
    r"c[eé]sped\s+artificial|campo\s+de\s+f[uú]tbol|pista\s+de\s+p[aá]del|"
    r"suministro\s+de\s+plantas\s+de\s+temporada\s+para\s+rotondas|flor\s+cortada"
    r")\b",
    re.IGNORECASE,
)


def detect_language(text: str) -> str:
    """Detect whether the call text is in Spanish, Catalan, Galician, Basque or English."""
    low = text.lower()

    # English check: explicit EU phrases or multiple English markers
    en_explicit = bool(
        re.search(
            r"\b(call\s+for\s+proposals|european\s+commission|forest\s+restoration|"
            r"nature\s+restoration\s+law|wildfire\s+prevention|afforestation|carbon\s+farming)\b",
            low,
        )
    )
    en_stops = len(re.findall(r"\b(the|and|for|with|under|grants?|wildfires?|forestry)\b", low))
    if en_explicit or en_stops >= 3:
        return "en"

    # Basque
    if re.search(r"\b(diru[-\s]?laguntza\w*|foru\s+aldundia|eusko\s+jaurlaritza|baso[-\s]?berritze\w*|baso[-\s]?sute\w*|udala|zuhaitz)\b", low):
        return "eu"

    # Galician (require unambiguous Galician forms so Catalan 'subvencions' never triggers 'gl')
    if re.search(r"\b(pola\s+que|xunta\s+de\s+galicia|subvenci[oó]ns\b(?!.*catalunya)|repoboaci[oó]n|veci[ñn]a(?:l|is)|lumes?\s+forestais|concello\s+d[aeo]|deputaci[oó]n)\b", low) and "subvencions" not in low:
        return "gl"

    # Catalan / Valencian
    if re.search(r"\b(generalitat\s+de\s+catalunya|subvencions|incendis\s+forestals|gesti[oó]\s+forestal|ajuntament|diputaci[oó]|per\s+a\s+la|d['’]incendis|bosc)\b", low):
        return "ca"

    return "es"


def evaluate_layer1(
    titulo: str,
    texto: str = "",
    organo: str = "",
    cpv_codes: list[str] | None = None,
    threshold: int | None = None,
) -> Layer1Result:
    """
    Run Layer 1 deterministic high-recall multilingual filter.
    Never discards based on BDNS economic sector (which is frequently mislabeled).
    """
    min_score = threshold if threshold is not None else settings.layer1_threshold
    combined = f"{titulo}\n{organo}\n{texto}"
    lang = detect_language(f"{titulo} {organo} {texto[:1500]}")

    score = 0
    categories: set[str] = set()
    matched_terms: list[str] = []
    has_direct_match = False

    # Also auto-extract inline 8-digit CPV codes mentioned inside title/text (e.g. "CPV 77231600-4" or "75251120-7")
    detected_cpvs = list(cpv_codes or [])
    detected_cpvs.extend(extract_cpv_codes(combined))

    # 1. Check Tier A & Tier B CPV codes
    seen_cpvs: set[str] = set()
    for cpv in detected_cpvs:
        clean_cpv = cpv.strip()
        if not clean_cpv or clean_cpv in seen_cpvs:
            continue
        seen_cpvs.add(clean_cpv)
        if any(clean_cpv.startswith(pref) for pref in TIER_A_CPV_PREFIXES):
            score += 60
            has_direct_match = True
            matched_terms.append(f"CPV:{clean_cpv}")
            if clean_cpv.startswith("75251120"):
                categories.add("prevencion_incendios")
            elif clean_cpv.startswith("772316") or clean_cpv.startswith("034") or clean_cpv.startswith("03121"):
                categories.add("reforestacion")
            elif clean_cpv.startswith("772"):
                categories.add("silvicultura")
        elif any(clean_cpv.startswith(pref) for pref in TIER_B_CPV_PREFIXES):
            score += 35
            matched_terms.append(f"CPV:{clean_cpv}")
            if clean_cpv.startswith("907"):
                categories.add("restauracion_ecologica")
            elif clean_cpv.startswith("7311"):
                categories.add("investigacion_forestal")
            else:
                categories.add("reforestacion")

    # 2. Check Block 1 (Reforestation & Silviculture & Carbon)
    for cat, pattern in PATTERNS_REFORESTATION:
        matches = [m.group(0) for m in pattern.finditer(combined)]
        if matches:
            score += 50
            has_direct_match = True
            categories.add(cat)
            matched_terms.extend(sorted({m.lower() for m in matches})[:3])

    # 3. Check Block 2 (Wildfires)
    for cat, pattern in PATTERNS_WILDFIRES:
        matches = [m.group(0) for m in pattern.finditer(combined)]
        if matches:
            score += 50
            has_direct_match = True
            categories.add(cat)
            matched_terms.extend(sorted({m.lower() for m in matches})[:3])

    # 4. Check Block 3 (Biodiversity, Natura 2000, Environmental Projects, Education)
    for cat, pattern in PATTERNS_BIODIVERSITY_ENV:
        matches = [m.group(0) for m in pattern.finditer(combined)]
        if matches:
            score += 25
            categories.add(cat)
            matched_terms.extend(sorted({m.lower() for m in matches})[:3])

    # 5. Check Issuing Body & Strategic Agency boost across organo + titulo + lead text
    organo_matches = [m.group(0) for m in ORGANO_BOOST_PATTERN.finditer(f"{organo} {titulo} {texto[:2500]}")]
    if organo_matches:
        score += 20
        matched_terms.append(f"ORGANO:{organo_matches[0].lower()}")

    # 6. Check Negative Anti-Noise rules (only reject if there's NO direct forestry/wildfire signal)
    neg_matches = [m.group(0) for m in NEGATIVE_NOISE_PATTERN.finditer(combined)]
    if neg_matches and not has_direct_match:
        return Layer1Result(
            passed=False,
            decision="REJECT",
            score=0,
            preliminary_relevance="DESCARTADA",
            detected_language=lang,
            matched_categories=[],
            matched_terms=[],
            rejection_reason=f"Excluido por regla anti-ruido: {neg_matches[0]}",
        )

    score = min(100, score)
    if score < min_score:
        return Layer1Result(
            passed=False,
            decision="REJECT",
            score=score,
            preliminary_relevance="DESCARTADA",
            detected_language=lang,
            matched_categories=sorted(categories),
            matched_terms=matched_terms[:8],
            rejection_reason=f"Score Capa 1 ({score}) inferior al umbral ({min_score})",
        )

    prelim_rel = "DIRECTA" if has_direct_match else "INDIRECTA_ELEGIBLE"
    decision = "PASS_HIGH" if score >= 50 else "PASS_CANDIDATE"

    return Layer1Result(
        passed=True,
        decision=decision,
        score=score,
        preliminary_relevance=prelim_rel,
        detected_language=lang,
        matched_categories=sorted(categories),
        matched_terms=matched_terms[:10],
    )
