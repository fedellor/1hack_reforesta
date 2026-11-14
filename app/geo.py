"""Spanish Geography, NUTS-2/NUTS-3, Administrative Level & Private Entity Resolver."""
import re
import unicodedata
from dataclasses import dataclass


def normalize_text(text: str) -> str:
    """Lowercase and strip accents for robust matching."""
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _contains_kw(text_norm: str, kw: str) -> bool:
    """
    Match keyword with word boundaries so short bulletin acronyms
    (e.g. 'bon', 'bor', 'dog', 'boa', 'doe') never match substrings like 'carbono' or 'elaboracion'.
    """
    if len(kw) <= 5 and " " not in kw and "-" not in kw:
        return bool(re.search(rf"\b{re.escape(kw)}\b", text_norm))
    return kw in text_norm


@dataclass(frozen=True)
class TerritoryInfo:
    nivel_territorial: str  # UE | ESTADO | CCAA | PROVINCIA | MUNICIPIO | PRIVADA
    ccaa_codigo: str        # ES-AN, ES-MD, ..., ES, EU
    ccaa_nombre: str
    provincia_codigo: str | None = None
    provincia_nombre: str | None = None
    municipio_nombre: str | None = None


# Canonical CCAA catalog (ISO 3166-2:ES + ES + EU)
CCAA_CATALOG: dict[str, dict[str, str]] = {
    "ES-AN": {"nombre": "Andalucía", "nuts": "ES61"},
    "ES-AR": {"nombre": "Aragón", "nuts": "ES24"},
    "ES-AS": {"nombre": "Principado de Asturias", "nuts": "ES12"},
    "ES-CB": {"nombre": "Cantabria", "nuts": "ES13"},
    "ES-CE": {"nombre": "Ceuta", "nuts": "ES63"},
    "ES-CL": {"nombre": "Castilla y León", "nuts": "ES41"},
    "ES-CM": {"nombre": "Castilla-La Mancha", "nuts": "ES42"},
    "ES-CN": {"nombre": "Canarias", "nuts": "ES70"},
    "ES-CT": {"nombre": "Cataluña", "nuts": "ES51"},
    "ES-EX": {"nombre": "Extremadura", "nuts": "ES43"},
    "ES-GA": {"nombre": "Galicia", "nuts": "ES11"},
    "ES-IB": {"nombre": "Illes Balears", "nuts": "ES53"},
    "ES-MC": {"nombre": "Región de Murcia", "nuts": "ES62"},
    "ES-MD": {"nombre": "Comunidad de Madrid", "nuts": "ES30"},
    "ES-ML": {"nombre": "Melilla", "nuts": "ES64"},
    "ES-NC": {"nombre": "Comunidad Foral de Navarra", "nuts": "ES22"},
    "ES-PV": {"nombre": "País Vasco", "nuts": "ES21"},
    "ES-RI": {"nombre": "La Rioja", "nuts": "ES23"},
    "ES-VC": {"nombre": "Comunitat Valenciana", "nuts": "ES52"},
    "ES": {"nombre": "Toda España (Estatal / Nacional)", "nuts": "ES"},
    "EU": {"nombre": "Unión Europea (Aplicable en España)", "nuts": "EU"},
}

NUTS_TO_CCAA: dict[str, str] = {
    info["nuts"]: code for code, info in CCAA_CATALOG.items()
}

# Provinces -> (provincia_codigo, provincia_nombre, ccaa_codigo, patterns)
PROVINCES: list[tuple[str, str, str, list[str]]] = [
    ("ES-A", "Alicante / Alacant", "ES-VC", ["alicante", "alacant", "alcoy", "elche", "elx", "denia"]),
    ("ES-AB", "Albacete", "ES-CM", ["albacete", "hellin", "almansa"]),
    ("ES-AL", "Almería", "ES-AN", ["almeria", "filabres", "alpujarra almeriense"]),
    ("ES-AV", "Ávila", "ES-CL", ["avila", "gredos", "valle del tietar"]),
    ("ES-B", "Barcelona", "ES-CT", ["barcelona", "bergueda", "osona", "maresme", "valles", "bages"]),
    ("ES-BA", "Badajoz", "ES-EX", ["badajoz", "merida", "tentudia", "siberia extremena"]),
    ("ES-BI", "Bizkaia", "ES-PV", ["bizkaia", "bizkaiko", "vizcaya", "bilbao", "bilboko", "urdaibai", "gorbeia"]),
    ("ES-BU", "Burgos", "ES-CL", ["burgos", "aranda de duero", "merindades", "demanda"]),
    ("ES-C", "A Coruña", "ES-GA", ["a coruna", "la coruna", "coruna", "santiago de compostela", "ferrol", "carballo", "as pontes"]),
    ("ES-CA", "Cádiz", "ES-AN", ["cadiz", "alcornocales", "grazalema", "jerez"]),
    ("ES-CC", "Cáceres", "ES-EX", ["caceres", "monfrague", "hurdes", "gata", "jerte", "vera"]),
    ("ES-CE", "Ceuta", "ES-CE", ["ceuta", "garcia aldave", "monte hacho"]),
    ("ES-CO", "Córdoba", "ES-AN", ["cordoba", "hornachuelos", "los pedroches", "cardena"]),
    ("ES-CR", "Ciudad Real", "ES-CM", ["ciudad real", "cabaneros", "valdepenas", "alcudia"]),
    ("ES-CS", "Castellón / Castelló", "ES-VC", ["castellon", "castello", "espadan", "els ports", "alto palancia"]),
    ("ES-CU", "Cuenca", "ES-CM", ["cuenca", "serrania de cuenca"]),
    ("ES-GC", "Las Palmas", "ES-CN", ["las palmas", "gran canaria", "fuerteventura", "lanzarote", "tamadaba"]),
    ("ES-GI", "Girona", "ES-CT", ["girona", "gerona", "garrotxa", "emporda", "ripolles", "les gavarres"]),
    ("ES-GR", "Granada", "ES-AN", ["granada", "sierra nevada", "baza", "castril"]),
    ("ES-GU", "Guadalajara", "ES-CM", ["guadalajara", "alto tajo", "molina de aragon", "sierra norte de guadalajara"]),
    ("ES-H", "Huelva", "ES-AN", ["huelva", "donana", "aracena", "andevalo"]),
    ("ES-HU", "Huesca", "ES-AR", ["huesca", "ordesa", "pirineo aragones", "sobrarbe", "ribagorza", "jaca"]),
    ("ES-J", "Jaén", "ES-AN", ["jaen", "cazorla", "segura", "las villas", "andujar", "despenaperros"]),
    ("ES-L", "Lleida", "ES-CT", ["lleida", "lerida", "pirineu", "pallars", "aran", "alt urgell", "solsones"]),
    ("ES-LE", "León", "ES-CL", ["leon", "el bierzo", "ponferrada", "babia", "riano", "cabrera"]),
    ("ES-LO", "La Rioja", "ES-RI", ["la rioja", "logrono", "cebollera", "demanda riojana"]),
    ("ES-LU", "Lugo", "ES-GA", ["lugo", "ancares", "courel", "terra cha", "viveiro", "monforte"]),
    ("ES-M", "Madrid", "ES-MD", ["madrid", "guadarrama", "sierra del rincon", "manzanares"]),
    ("ES-MA", "Málaga", "ES-AN", ["malaga", "sierra de las nieves", "sierra bermeja", "ronda", "antequera"]),
    ("ES-ML", "Melilla", "ES-ML", ["melilla", "rostrogordo"]),
    ("ES-MU", "Murcia", "ES-MC", ["murcia", "sierra espuna", "calblanque", "caravaca", "lorca"]),
    ("ES-NA", "Navarra", "ES-NC", ["navarra", "nafarroa", "pamplona", "irati", "urbasa", "baztan", "roncal"]),
    ("ES-O", "Asturias", "ES-AS", ["asturias", "oviedo", "gijon", "cangas del narcea", "muniellos", "somiedo", "redes"]),
    ("ES-OR", "Ourense", "ES-GA", ["ourense", "orense", "invernadeiro", "xures", "valdeorras", "verin", "allariz"]),
    ("ES-P", "Palencia", "ES-CL", ["palencia", "montana palentina", "guardo", "cervera de pisuerga"]),
    ("ES-PM", "Illes Balears", "ES-IB", ["baleares", "illes balears", "mallorca", "menorca", "ibiza", "eivissa", "formentera", "tramuntana"]),
    ("ES-PO", "Pontevedra", "ES-GA", ["pontevedra", "vigo", "lalin", "tui", "ponteareas", "deza"]),
    ("ES-S", "Cantabria", "ES-CB", ["cantabria", "santander", "saja", "besaya", "liebana", "campoo"]),
    ("ES-SA", "Salamanca", "ES-CL", ["salamanca", "las batuecas", "sierra de francia", "ciudad rodrigo"]),
    ("ES-SE", "Sevilla", "ES-AN", ["sevilla", "sierra norte de sevilla", "aznalcollar"]),
    ("ES-SG", "Segovia", "ES-CL", ["segovia", "valsain", "cuellar", "riaza"]),
    ("ES-SO", "Soria", "ES-CL", ["soria", "urbion", "pinares", "valonsadero", "covaleda", "vinuesa"]),
    ("ES-SS", "Gipuzkoa", "ES-PV", ["gipuzkoa", "gipuzkoako", "guipuzcoa", "donostia", "donostiako", "san sebastian", "aralar", "aizkorri", "onati", "onatiko", "bergara"]),
    ("ES-T", "Tarragona", "ES-CT", ["tarragona", "els ports", "prades", "priorat", "ebre"]),
    ("ES-TE", "Teruel", "ES-AR", ["teruel", "maestrazgo", "albarracin", "gudar", "javalambre"]),
    ("ES-TF", "Santa Cruz de Tenerife", "ES-CN", ["tenerife", "la palma", "la gomera", "el hierro", "garajonay", "teide", "corona forestal"]),
    ("ES-TO", "Toledo", "ES-CM", ["toledo", "montes de toledo", "talavera", "la jara"]),
    ("ES-V", "Valencia / València", "ES-VC", ["valencia", "calderona", "caroig", "requena", "utiel", "albufera"]),
    ("ES-VA", "Valladolid", "ES-CL", ["valladolid", "torozos", "tierra de pinares"]),
    ("ES-VI", "Álava / Araba", "ES-PV", ["alava", "araba", "arabako", "vitoria", "gasteiz", "izki", "valdegovia"]),
    ("ES-Z", "Zaragoza", "ES-AR", ["zaragoza", "moncayo", "cinco villas", "calatayud"]),
    ("ES-ZA", "Zamora", "ES-CL", ["zamora", "sierra de la culebra", "sanabria", "aliste"]),
]

CCAA_KEYWORDS: list[tuple[str, list[str]]] = [
    ("ES-AN", ["andalucia", "junta de andalucia", "boja"]),
    ("ES-AR", ["aragon", "gobierno de aragon", "boa"]),
    ("ES-AS", ["asturias", "principado de asturias", "bopa"]),
    ("ES-CB", ["cantabria", "gobierno de cantabria"]),
    ("ES-CE", ["ciudad de ceuta", "ciudad autonoma de ceuta"]),
    ("ES-CL", ["castilla y leon", "junta de castilla y leon", "bocyl"]),
    ("ES-CM", ["castilla-la mancha", "castilla la mancha", "junta de comunidades de castilla-la mancha", "docm"]),
    ("ES-CN", ["canarias", "gobierno de canarias", "islas canarias"]),
    ("ES-CT", ["cataluna", "catalunya", "generalitat de catalunya", "dogc"]),
    ("ES-EX", ["extremadura", "junta de extremadura", "doe", "infoex"]),
    ("ES-GA", ["galicia", "xunta de galicia", "dog"]),
    ("ES-IB", ["illes balears", "islas baleares", "govern de les illes balears", "fogaiba", "boib"]),
    ("ES-MC", ["region de murcia", "comunidad autonoma de la region de murcia", "borm"]),
    ("ES-MD", ["comunidad de madrid", "bocm"]),
    ("ES-ML", ["ciudad de melilla", "ciudad autonoma de melilla"]),
    ("ES-NC", ["navarra", "nafarroa", "gobierno de navarra", "comunidad foral de navarra", "bon"]),
    ("ES-PV", ["pais vasco", "euskadi", "gobierno vasco", "eusko jaurlaritza", "bopv", "ehaa"]),
    ("ES-RI", ["la rioja", "gobierno de la rioja", "bor"]),
    ("ES-VC", ["comunitat valenciana", "comunidad valenciana", "generalitat valenciana", "dogv"]),
]

PRIVATE_ENTITY_KEYWORDS = [
    "fundacion la caixa",
    "fundacion ”la caixa”",
    "fundacion \"la caixa\"",
    "fundacio la caixa",
    "fundacion banco santander",
    "fundacion bbva",
    "fundacion repsol",
    "motor verde",
    "fundacion iberdrola",
    "fundacion endesa",
    "fundacion naturgy",
    "fundacion aquae",
    "fundacion daniel y nina carasso",
    "fundacion carasso",
    "fundacion montemadrid",
    "fundacion cajamar",
    "fundacion unicaja",
    "fundacion bancaja",
    "kutxa fundazioa",
    "vital fundazioa",
    "obra social",
    "abanca",
    "afundacion",
    "cajacanarias",
    "caja de burgos",
    "gutierrez manrique",
    "tatiana perez",
    "outdoor conservation",
    "eoca",
    "one tree planted",
    "1% for the planet",
    "plant-for-the-planet",
    "land life",
    "ecodes",
    "fsc espana",
    "pefc espana",
    "fundacion caja",
    "retree",
    "bosques sostenibles",
    "sylvestris",
    "wwf",
    "seo/birdlife",
    "seo birdlife",
]


def _extract_municipality(organo_norm: str, titulo_norm: str) -> str | None:
    """Detect municipality in Spanish, Galician, Catalan or Basque formats."""
    pat_prefix = re.compile(
        r"\b(?:ayuntamiento|concello|ajuntament|mancomunidad|junta\s+vecinal|concejo)\s+"
        r"(?:de\s+|do\s+|da\s+|del\s+|d['’])?([a-z0-9\s\-]{2,40})"
    )
    pat_basque = re.compile(r"\b([a-z0-9\-]{3,30}(?:ko|go))\s+udala\b")
    pat_udala_prefix = re.compile(r"\budala\s+(?:de\s+)?([a-z0-9\s\-]{3,35})")

    for source in (organo_norm, titulo_norm):
        m = pat_prefix.search(source)
        if m:
            raw_muni = re.split(r"[-|,(]|\bpara\b", m.group(1))[0].strip()
            if len(raw_muni) >= 2:
                return raw_muni.title()
        m_eu = pat_basque.search(source)
        if m_eu:
            stem = re.sub(r"(ko|go)$", "", m_eu.group(1)).strip()
            return (stem or m_eu.group(1)).title()
        m_up = pat_udala_prefix.search(source)
        if m_up:
            raw_muni = re.split(r"[-|,(]|\bpara\b", m_up.group(1))[0].strip()
            if len(raw_muni) >= 2:
                return raw_muni.title()
    return None


def resolve_geography(
    organo: str = "",
    region_text: str = "",
    titulo: str = "",
    nuts_code: str | None = None,
) -> TerritoryInfo:
    """Resolve administrative level (UE, ESTADO, CCAA, PROVINCIA, MUNICIPIO, PRIVADA) and geography."""
    organo_norm = normalize_text(organo)
    region_norm = normalize_text(region_text)
    titulo_norm = normalize_text(titulo)
    combined = f"{organo_norm} | {region_norm} | {titulo_norm}"

    # 0. Check Private Foundation / Corporate ESG Fund level
    is_private = (
        any(k in organo_norm for k in PRIVATE_ENTITY_KEYWORDS)
        and "fundacion biodiversidad" not in organo_norm
    )

    # 1. Check European Union level
    if (
        (nuts_code and nuts_code.upper().startswith("EU"))
        or any(
            k in organo_norm
            for k in [
                "european commission",
                "comision europea",
                "cinea",
                "horizon europe",
                "programa life",
                "life programme",
                "interreg",
                "union europea",
            ]
        )
    ):
        return TerritoryInfo(
            nivel_territorial="UE",
            ccaa_codigo="EU",
            ccaa_nombre=CCAA_CATALOG["EU"]["nombre"],
        )

    # 2. Check Municipality level
    municipio_detected = _extract_municipality(organo_norm, titulo_norm)

    # 3. Check Provincial level ("Diputación", "Deputación", "Diputació", "Foru Aldundia", "Cabildo", "Consell ...")
    is_provincial_body = any(
        k in organo_norm
        for k in [
            "diputacion",
            "deputacion",
            "diputacio",
            "foru aldundia",
            "cabildo",
            "consell insular",
            "consell de mallorca",
            "consell de menorca",
            "consell d'eivissa",
            "consell de formentera",
        ]
    )

    # 4. Check explicit State/National Ministry level
    is_state_body = any(
        k in organo_norm
        for k in [
            "ministerio",
            "miteco",
            "estado",
            "organismo autonomo parques nacionales",
            "fundacion biodiversidad",
            "confederacion hidrografica",
            "agencia estatal",
            "csic",
            "tragsa",
        ]
    ) and not any(k in organo_norm for k in ["comunidad", "junta", "generalitat", "xunta", "gobierno de"])

    def _pick_level(default_lvl: str) -> str:
        if is_private:
            return "PRIVADA"
        if municipio_detected:
            return "MUNICIPIO"
        if is_provincial_body:
            return "PROVINCIA"
        return default_lvl

    # 5. Match NUTS code if provided
    if nuts_code:
        nuts_clean = nuts_code.strip().upper()[:4]
        if nuts_clean in NUTS_TO_CCAA:
            ccaa_code = NUTS_TO_CCAA[nuts_clean]
            prov_code, prov_name = _find_province(combined, filter_ccaa=ccaa_code)
            return TerritoryInfo(
                nivel_territorial=_pick_level("ESTADO" if ccaa_code == "ES" else "CCAA"),
                ccaa_codigo=ccaa_code,
                ccaa_nombre=CCAA_CATALOG[ccaa_code]["nombre"],
                provincia_codigo=prov_code,
                provincia_nombre=prov_name,
                municipio_nombre=municipio_detected,
            )

    # 6. Match CCAA directly in organo or region_text
    for ccaa_code, keywords in CCAA_KEYWORDS:
        if any(_contains_kw(organo_norm, kw) or _contains_kw(region_norm, kw) for kw in keywords):
            prov_code, prov_name = _find_province(combined, filter_ccaa=ccaa_code)
            return TerritoryInfo(
                nivel_territorial=_pick_level("CCAA"),
                ccaa_codigo=ccaa_code,
                ccaa_nombre=CCAA_CATALOG[ccaa_code]["nombre"],
                provincia_codigo=prov_code,
                provincia_nombre=prov_name,
                municipio_nombre=municipio_detected,
            )

    # 7. Match by Province if provincial/municipal or mentioned in region/organo/title
    prov_code, prov_name, prov_ccaa = _find_province_with_ccaa(
        f"{organo_norm} {region_norm} {titulo_norm}"
    )
    if prov_code and prov_ccaa and not is_state_body:
        return TerritoryInfo(
            nivel_territorial=_pick_level("CCAA"),
            ccaa_codigo=prov_ccaa,
            ccaa_nombre=CCAA_CATALOG[prov_ccaa]["nombre"],
            provincia_codigo=prov_code,
            provincia_nombre=prov_name,
            municipio_nombre=municipio_detected,
        )

    # 8. Match CCAA in full text (including title) if not explicitly state (now safe with word boundaries!)
    if not is_state_body:
        for ccaa_code, keywords in CCAA_KEYWORDS:
            if any(_contains_kw(combined, kw) for kw in keywords):
                prov_code, prov_name = _find_province(combined, filter_ccaa=ccaa_code)
                return TerritoryInfo(
                    nivel_territorial=_pick_level("CCAA"),
                    ccaa_codigo=ccaa_code,
                    ccaa_nombre=CCAA_CATALOG[ccaa_code]["nombre"],
                    provincia_codigo=prov_code,
                    provincia_nombre=prov_name,
                    municipio_nombre=municipio_detected,
                )

    # Default to State / National level (ES)
    return TerritoryInfo(
        nivel_territorial="PRIVADA" if is_private else ("MUNICIPIO" if municipio_detected else "ESTADO"),
        ccaa_codigo="ES",
        ccaa_nombre=CCAA_CATALOG["ES"]["nombre"],
        municipio_nombre=municipio_detected,
    )


def _find_province(text_norm: str, filter_ccaa: str | None = None) -> tuple[str | None, str | None]:
    for p_code, p_name, ccaa, patterns in PROVINCES:
        if filter_ccaa and ccaa != filter_ccaa:
            continue
        for pat in patterns:
            if re.search(rf"\b{re.escape(pat)}\b", text_norm):
                return p_code, p_name
    return None, None


def _find_province_with_ccaa(text_norm: str) -> tuple[str | None, str | None, str | None]:
    for p_code, p_name, ccaa, patterns in PROVINCES:
        for pat in patterns:
            if re.search(rf"\b{re.escape(pat)}\b", text_norm):
                return p_code, p_name, ccaa
    return None, None, None
