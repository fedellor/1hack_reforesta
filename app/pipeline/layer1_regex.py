"""Layer 1: Multilingual Rigid Filter (Regex ES/CA/GL/EU/EN + CPV + Issuing Body + Anti-Noise)."""
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


# Block 1: Reforestation, Afforestation, Silviculture & Forest Management (+50 pts)
PATTERNS_REFORESTATION: list[tuple[str, re.Pattern[str]]] = [
    (
        "reforestacion",
        re.compile(
            r"\b("
            r"reforest\w*|repoblaci[oó]n\s+forestal|forestaci[oó]n|plantaci[oó]n\s+de\s+[aá]rbol\w*|"
            r"especies\s+arb[oó]reas|especies\s+aut[oó]ctonas|vivero[s]?\s+forestal\w*|"
            r"restauraci[oó]n\s+forestal|restauraci[oó]n\s+hidrol[oó]gico[-\s]?forestal|"
            r"cubierta\s+vegetal|infraestructura\s+verde|renaturalizaci[oó]n|"
            # Catalan
            r"repoblaci[oó]\s+forestal|infraestructura\s+verda|renaturalitzaci[oó]|"
            # Galician
            r"repoboaci[oó]n\s+forestal|frondosas\s+aut[oó]ctonas|"
            # Basque
            r"baso[-\s]?berritze\w*|"
            # English (EU calls)
            r"afforest\w*|tree\s+planting|forest\s+restoration|forest\s+landscape\s+restoration|"
            r"urban\s+greening|rewilding"
            r")\b",
            re.IGNORECASE,
        ),
    ),
    (
        "silvicultura",
        re.compile(
            r"\b("
            r"silvicult\w*|selvicult\w*|masa[s]?\s+forestal\w*|gesti[oó]n\s+forestal|"
            r"monte[s]?\s+(p[uú]blico|vecinal|comunal|protector|ordenado)\w*|"
            r"aprovechamiento[s]?\s+forestal\w*|ordenaci[oó]n\s+de\s+montes|arboricult\w*|"
            r"dehesa[s]?|agroforest\w*|sistemas\s+agroforestales|bosque[s]?|"
            # Catalan / Galician / Basque / English
            r"gesti[oó]\s+forestal|massa\s+forestal|bosc(?:os)?|monte[s]?\s+veci[ñn]al\w*|"
            r"comunidade[s]?\s+de\s+montes|basogintza\w*|baso[-\s]?kudeaketa\w*|"
            r"forest\s+management|sustainable\s+forestry|agroforestry|woodland\w*"
            r")\b",
            re.IGNORECASE,
        ),
    ),
    (
        "absorcion_carbono",
        re.compile(
            r"\b("
            r"sumidero[s]?\s+de\s+carbono|absorci[oó]n\s+de\s+co2|cr[eé]dito[s]?\s+de\s+carbono|"
            r"huella\s+de\s+carbono.*(?:absorci[oó]n|forestal|compensaci[oó]n)|"
            r"secuestro\s+de\s+carbono|carbon\s+sink\w*|carbon\s+farming|carbon\s+sequestration"
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
            r"extinci[oó]n\s+de\s+incendios\s+forestales|cortafuego[s]?|"
            r"faja[s]?\s+(?:auxiliar|pir[oó]fuga|secundaria)\w*|desbroce[s]?\s+(?:forestal|preventivo)\w*|"
            r"biomasa\s+forestal|limpieza\s+de\s+montes|tratamiento[s]?\s+selv[ií]cola\w*\s+preventivo\w*|"
            r"vigilancia\s+forestal|brigada[s]?\s+forestal\w*|medios\s+a[eé]reos.*incendios|"
            # Catalan / Galician / Basque / English
            r"incendi[s]?\s+forestal\w*|prevenci[oó]\s+d['’]incendis|tallafoc[s]?|franges\s+de\s+protecci[oó]|"
            r"lume[s]?\s+forestal\w*|devasa[s]?|roza[s]?\s+forestal\w*|baso[-\s]?sute\w*|"
            r"wildfire[s]?|forest\s+fire[s]?|fire\s+prevention|fuel\s+management|prescribed\s+burning|"
            r"integrated\s+fire\s+management"
            r")\b",
            re.IGNORECASE,
        ),
    ),
    (
        "restauracion_post_incendio",
        re.compile(
            r"\b("
            r"zona[s]?\s+(?:incendiada|quemada|afectada[s]?\s+por\s+incendio)\w*|"
            r"restauraci[oó]n\s+de\s+(?:montes|zonas|terrenos)\s+(?:incendiad|quemad)\w*|"
            r"recuperaci[oó]n\s+(?:forestal|ambiental)\s+tras\s+incendio\w*|"
            r"da[ñn]os\s+en\s+bosques\s+por\s+incendios|post[-\s]?fire\s+(?:restoration|recovery|rehabilitation)"
            r")\b",
            re.IGNORECASE,
        ),
    ),
]

# Block 3: Biodiversity, Natura 2000, Climate Adaptation & Environmental Protection (+25 pts)
PATTERNS_BIODIVERSITY_ENV: list[tuple[str, re.Pattern[str]]] = [
    (
        "biodiversidad",
        re.compile(
            r"\b("
            r"biodiversidad\w*|biodiversitat|biodiversity|patrimonio\s+natural|patrimoni\s+natural|"
            r"red\s+natura\s+2000|xarxa\s+natura\s+2000|natura\s+2000|"
            r"espacios\s+naturales\s+protegidos|h[aá]bitats\s+de\s+inter[eé]s\s+comunitario|"
            r"[aá]rboles\s+singulares|flora\s+silvestre|especies\s+amenazadas|"
            r"custodia\s+del\s+territorio|conservaci[oó]n\s+de\s+la\s+naturaleza"
            r")\b",
            re.IGNORECASE,
        ),
    ),
    (
        "restauracion_ecologica",
        re.compile(
            r"\b("
            r"restauraci[oó]n\s+(?:ecol[oó]gica|ambiental|de\s+ecosistemas|del\s+medio\s+natural)|"
            r"protecci[oó]n\s+(?:del\s+)?medio\s+ambiente|proyectos\s+ambientales|proyectos\s+medioambientales|"
            r"adaptaci[oó]n\s+al\s+cambio\s+clim[aá]tico|resiliencia\s+del\s+ecosistema|"
            r"lucha\s+contra\s+la\s+desertificaci[oó]n|erosi[oó]n\s+de\s+suelos|"
            r"ecological\s+restoration|nature\s+restoration|climate\s+change\s+adaptation|"
            r"ecosystem\s+resilience|soil\s+restoration"
            r")\b",
            re.IGNORECASE,
        ),
    ),
    (
        "investigacion_forestal",
        re.compile(
            r"\b("
            r"investigaci[oó]n\s+forestal|sanidad\s+forestal|plagas\s+forestales|"
            r"investigaci[oó]n\s+cient[ií]fica\s+y\s+t[eé]cnica\s+y\s+protecci[oó]n\s+medio\s+ambiente|"
            r"forest\s+research|forest\s+health|forest\s+monitoring"
            r")\b",
            re.IGNORECASE,
        ),
    ),
]

# Issuing body boost (+20 pts)
ORGANO_BOOST_PATTERN = re.compile(
    r"\b("
    r"miteco|transici[oó]n\s+ecol[oó]gica|medio\s+ambiente|medi\s+ambient|medio\s+rural|"
    r"montes|pol[ií]tica\s+forestal|biodiversidad|parques\s+nacionales|"
    r"confederaci[oó]n\s+hidrogr[aá]fica|desarrollo\s+rural|ingurumena|"
    r"cinea|programa\s+life|life\s+programme|horizon\s+europe|interreg|"
    r"fundaci[oó]n\s+la\s+caixa|fundaci[oó]n\s+banco\s+santander|fundaci[oó]n\s+bbva|"
    r"fundaci[oó]n\s+repsol|motor\s+verde|fundaci[oó]n\s+iberdrola|fundaci[oó]n\s+endesa|"
    r"fundaci[oó]n\s+naturgy|retree|bosques\s+sostenibles|sylvestris"
    r")\b",
    re.IGNORECASE,
)

# CPV codes for Forestry, Wildfire Prevention, and Environmental Restoration (+60 pts)
FORESTRY_CPV_PREFIXES = (
    "772",       # 77200000-2 Servicios forestales, 77231000 Gestión forestal, 77231600 Repoblación
    "75251120",  # 75251120-7 Servicios de prevención de incendios forestales
    "9071",      # 90710000-7 Gestión medioambiental
    "90721800",  # 90721800-5 Servicios de protección contra riesgos o peligros naturales
)

# Anti-noise negative patterns (-100 pts if no explicit forestry/wildfire term)
NEGATIVE_NOISE_PATTERN = re.compile(
    r"\b("
    r"extinci[oó]n\s+de\s+condominio|extinci[oó]n\s+de\s+contrato|monte\s+de\s+piedad|"
    r"extintor(?:es)?\s+port[aá]til\w*|detecci[oó]n\s+de\s+incendios\s+en\s+(?:edificio|colegio|hospital|oficina|pabell[oó]n|nave)|"
    r"protecci[oó]n\s+pasiva\s+contra\s+incendios\s+en\s+edificio\w*|c[eé]sped\s+artificial|"
    r"suministro\s+de\s+plantas\s+de\s+temporada\s+para\s+rotondas"
    r")\b",
    re.IGNORECASE,
)


def detect_language(text: str) -> str:
    """Detect whether the call text is in Spanish, Catalan, Galician, Basque or English."""
    low = text.lower()
    if re.search(r"\b(the|and|for|call\s+for\s+proposals|european\s+commission|wildfire|forest\s+restoration)\b", low):
        return "en"
    if re.search(r"\b(dels|les|amb|per\s+a\s+la|generalitat|subvencions|incendis|gesti[oó])\b", low):
        return "ca"
    if re.search(r"\b(dos|das|unha|pola\s+que|xunta\s+de\s+galicia|subvenci[oó]ns|repoboaci[oó]n|veci[ñn]al)\b", low):
        return "gl"
    if re.search(r"\b(diru[-\s]?laguntza\w*|foru\s+aldundia|eusko\s+jaurlaritza|baso\w*)\b", low):
        return "eu"
    return "es"


def evaluate_layer1(
    titulo: str,
    texto: str = "",
    organo: str = "",
    cpv_codes: list[str] | None = None,
    threshold: int | None = None,
) -> Layer1Result:
    """
    Run Layer 1 deterministic multilingual filter.
    Never discards based on BDNS economic sector (which is frequently mislabeled).
    """
    min_score = threshold if threshold is not None else settings.layer1_threshold
    combined = f"{titulo}\n{organo}\n{texto}"
    lang = detect_language(f"{titulo} {texto[:1000]}")

    score = 0
    categories: set[str] = set()
    matched_terms: list[str] = []
    has_direct_match = False

    # 1. Check CPV codes
    if cpv_codes:
        for cpv in cpv_codes:
            clean_cpv = cpv.strip()
            if any(clean_cpv.startswith(pref) for pref in FORESTRY_CPV_PREFIXES):
                score += 60
                has_direct_match = True
                matched_terms.append(f"CPV:{clean_cpv}")
                if clean_cpv.startswith("75251120"):
                    categories.add("prevencion_incendios")
                elif clean_cpv.startswith("772316"):
                    categories.add("reforestacion")
                elif clean_cpv.startswith("772"):
                    categories.add("silvicultura")

    # 2. Check Block 1 (Reforestation & Silviculture)
    for cat, pattern in PATTERNS_REFORESTATION:
        matches = [m.group(0) for m in pattern.finditer(combined)]
        if matches:
            score += 50
            has_direct_match = True
            categories.add(cat)
            matched_terms.extend(list({m.lower() for m in matches[:3]}))

    # 3. Check Block 2 (Wildfires)
    for cat, pattern in PATTERNS_WILDFIRES:
        matches = [m.group(0) for m in pattern.finditer(combined)]
        if matches:
            score += 50
            has_direct_match = True
            categories.add(cat)
            matched_terms.extend(list({m.lower() for m in matches[:3]}))

    # 4. Check Block 3 (Biodiversity, Natura 2000, Environmental Projects)
    for cat, pattern in PATTERNS_BIODIVERSITY_ENV:
        matches = [m.group(0) for m in pattern.finditer(combined)]
        if matches:
            score += 25
            categories.add(cat)
            matched_terms.extend(list({m.lower() for m in matches[:3]}))

    # 5. Check Issuing Body boost
    organo_matches = [m.group(0) for m in ORGANO_BOOST_PATTERN.finditer(f"{organo} {titulo}")]
    if organo_matches:
        score += 20
        matched_terms.append(f"ORGANO:{organo_matches[0].lower()}")

    # 6. Check Negative Anti-Noise rules
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
