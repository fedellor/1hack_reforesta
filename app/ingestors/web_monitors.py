"""Lightweight Async Web Monitors (RSS / Atom / WP-JSON / HTML Scrapers) & Extract->PDF Full-Text Enricher."""
import asyncio
from html.parser import HTMLParser
import hashlib
import html as html_lib
import json
import logging
import re
from typing import Any
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET
import httpx
from app.pipeline.layer1_regex import extract_cpv_codes
from app.pipeline.orchestrator import RawCandidate
from app.pipeline.pdf_extractor import extract_pdf_from_bytes

logger = logging.getLogger(__name__)

MAX_LINKED_PDF_BYTES = 6 * 1024 * 1024  # 6 MB safety cap per remote bulletin PDF

PRIVATE_FOUNDATION_SOURCES: list[dict[str, str]] = [
    {
        "id": "priv-web-lacaixa",
        "kind": "listing",
        "fuente": "FUNDACION_PRIVADA",
        "tipo_oportunidad": "CONVOCATORIA_PRIVADA",
        "nombre": "Fundación ”la Caixa” (Convocatorias Sociales y Medio Ambiente)",
        "url": "https://fundacionlacaixa.org/es/convocatorias-proyectos-sociales",
        "region_hint": "Privada / RSC España",
    },
    {
        "id": "priv-web-motorverde",
        "kind": "direct_call",
        "fuente": "FUNDACION_PRIVADA",
        "tipo_oportunidad": "CONVOCATORIA_PRIVADA",
        "nombre": "Fundación Repsol & Grupo Sylvestris (Motor Verde)",
        "url": "https://www.fundacionrepsol.com/es/que-hacemos/motor-verde/",
        "region_hint": "Privada / RSC España",
    },
    {
        "id": "priv-web-santander",
        "kind": "listing",
        "fuente": "FUNDACION_PRIVADA",
        "tipo_oportunidad": "CONVOCATORIA_PRIVADA",
        "nombre": "Fundación Banco Santander (Convocatorias)",
        "url": "https://www.fundacionbancosantander.com/es/convocatorias",
        "region_hint": "Privada / RSC España",
    },
    {
        "id": "priv-web-santander-ayuda",
        "kind": "direct_call",
        "fuente": "FUNDACION_PRIVADA",
        "tipo_oportunidad": "CONVOCATORIA_PRIVADA",
        "nombre": "Fundación Banco Santander (Santander Ayuda)",
        "url": "https://www.fundacionbancosantander.com/es/accion-social/santander-ayuda",
        "region_hint": "Privada / RSC España",
    },
    {
        "id": "priv-web-bbva-sitemap",
        "kind": "sitemap",
        "fuente": "FUNDACION_PRIVADA",
        "tipo_oportunidad": "CONVOCATORIA_PRIVADA",
        "nombre": "Fundación BBVA (Ecología y Biología de la Conservación)",
        "url": "https://www.fbbva.es/ayudas-sitemap.xml",
        "region_hint": "Privada / RSC España",
    },
    {
        "id": "priv-web-biophilia-bbva",
        "kind": "direct_call",
        "fuente": "FUNDACION_PRIVADA",
        "tipo_oportunidad": "CONVOCATORIA_PRIVADA",
        "nombre": "Fundación BBVA - Biophilia (Conservación de la Biodiversidad)",
        "url": "https://www.biophilia-fbbva.es/",
        "region_hint": "Privada / RSC España",
    },
    {
        "id": "priv-web-biodiversidad",
        "kind": "wp_json",
        "fuente": "FUNDACION_BIODIVERSIDAD",
        "tipo_oportunidad": "SUBVENCION",
        "nombre": "Fundación Biodiversidad F.S.P. (MITECO)",
        "url": "https://fundacion-biodiversidad.es/wp-json/wp/v2/pages?search=ayudas&per_page=30",
        "region_hint": "ES - España",
    },
    {
        "id": "priv-web-endesa",
        "kind": "direct_call",
        "fuente": "FUNDACION_PRIVADA",
        "tipo_oportunidad": "CONVOCATORIA_PRIVADA",
        "nombre": "Fundación Endesa (Biodiversidad y Renaturalización)",
        "url": "https://www.fundacionendesa.org/es/biodiversidad",
        "region_hint": "Privada / RSC España",
    },
    {
        "id": "priv-web-endesa-verde",
        "kind": "direct_call",
        "fuente": "FUNDACION_PRIVADA",
        "tipo_oportunidad": "CONVOCATORIA_PRIVADA",
        "nombre": "Fundación Endesa (II Convocatoria Emprendimiento Verde)",
        "url": "https://www.fundacionendesa.org/es/formacion-empleo/ii-convocatoria-de-ayudas-a-proyectos-de-emprendimiento-verde",
        "region_hint": "Privada / RSC España",
    },
    {
        "id": "priv-web-montemadrid",
        "kind": "listing",
        "fuente": "FUNDACION_PRIVADA",
        "tipo_oportunidad": "CONVOCATORIA_PRIVADA",
        "nombre": "Fundación Montemadrid (Convocatorias)",
        "url": "https://www.fundacionmontemadrid.es/convocatorias/",
        "region_hint": "ES-MD - Comunidad de Madrid (Privada / RSC)",
    },
    {
        "id": "priv-web-montemadrid-clima",
        "kind": "direct_call",
        "fuente": "FUNDACION_PRIVADA",
        "tipo_oportunidad": "CONVOCATORIA_PRIVADA",
        "nombre": "Fundación Montemadrid (Compromiso con el Clima)",
        "url": "https://www.fundacionmontemadrid.es/convocatorias/convocatoria-compromiso-con-el-clima/",
        "region_hint": "ES-MD - Comunidad de Madrid (Privada / RSC)",
    },
    {
        "id": "priv-web-ibercaja",
        "kind": "listing",
        "fuente": "FUNDACION_PRIVADA",
        "tipo_oportunidad": "CONVOCATORIA_PRIVADA",
        "nombre": "Fundación Ibercaja (Convocatorias Sostenibilidad y Medio Ambiente)",
        "url": "https://www.fundacionibercaja.es/convocatorias/",
        "region_hint": "Privada / RSC España",
    },
    {
        "id": "priv-web-moeve-valor",
        "kind": "direct_call",
        "fuente": "FUNDACION_PRIVADA",
        "tipo_oportunidad": "CONVOCATORIA_PRIVADA",
        "nombre": "Fundación Moeve (Premios al Valor Social)",
        "url": "https://fundacion.moeveglobal.com/es/premios-al-valor-social",
        "region_hint": "Privada / RSC España",
    },
    {
        "id": "priv-web-moeve-bio",
        "kind": "direct_call",
        "fuente": "FUNDACION_PRIVADA",
        "tipo_oportunidad": "CONVOCATORIA_PRIVADA",
        "nombre": "Fundación Moeve (Biodiversidad y Humedales)",
        "url": "https://fundacion.moeveglobal.com/es/biodiversidad",
        "region_hint": "Privada / RSC España",
    },
    {
        "id": "priv-web-cajacanarias",
        "kind": "listing",
        "fuente": "FUNDACION_PRIVADA",
        "tipo_oportunidad": "CONVOCATORIA_PRIVADA",
        "nombre": "Fundación CajaCanarias (Convocatorias)",
        "url": "https://www.cajacanarias.com/convocatorias-2",
        "region_hint": "ES-CN - Canarias (Privada / RSC)",
    },
    {
        "id": "priv-web-cajacanarias-inv",
        "kind": "direct_call",
        "fuente": "FUNDACION_PRIVADA",
        "tipo_oportunidad": "CONVOCATORIA_PRIVADA",
        "nombre": "Fundación CajaCanarias (Ayudas a Proyectos de Investigación)",
        "url": "https://www.cajacanarias.com/agenda/bases-ayudas-a-proyectos-de-investigacion-2026/",
        "region_hint": "ES-CN - Canarias (Privada / RSC)",
    },
    {
        "id": "priv-web-bbk",
        "kind": "listing",
        "fuente": "FUNDACION_PRIVADA",
        "tipo_oportunidad": "CONVOCATORIA_PRIVADA",
        "nombre": "Fundación BBK (Convocatorias y Ayudas)",
        "url": "https://www.bbk.eus/es/agenda/convocatorias-y-ayudas/",
        "region_hint": "ES-PV - País Vasco (Privada / RSC)",
    },
]

PUBLIC_PORTAL_SOURCES: list[dict[str, str]] = [
    {
        "id": "pub-miteco-social",
        "fuente": "BOE",
        "tipo_oportunidad": "SUBVENCION",
        "nombre": "MITECO - Subvenciones de Interés General e Interés Social (Línea A)",
        "url": "https://www.miteco.gob.es/es/ministerio/servicios/ayudas-subvenciones/social.html",
        "region_hint": "ES - España",
    },
    {
        "id": "pub-miteco-biodiversidad",
        "fuente": "BOE",
        "tipo_oportunidad": "SUBVENCION",
        "nombre": "MITECO - Biodiversidad y Bosques",
        "url": "https://www.miteco.gob.es/es/biodiversidad/ayudas-y-subvenciones.html",
        "region_hint": "ES - España",
    },
    {
        "id": "pub-miteco-esal",
        "fuente": "BOE",
        "tipo_oportunidad": "SUBVENCION",
        "nombre": "MITECO - Reto Demográfico Proyectos Innovadores ESAL",
        "url": "https://www.miteco.gob.es/es/reto-demografico/recursos-economicos-subvenciones/proyectos-innovadores/esal.html",
        "region_hint": "ES - España",
    },
    {
        "id": "pub-miteco-esal-2026",
        "fuente": "BOE",
        "tipo_oportunidad": "SUBVENCION",
        "nombre": "MITECO - Reto Demográfico Convocatoria ESAL 2026",
        "url": "https://www.miteco.gob.es/es/reto-demografico/recursos-economicos-subvenciones/proyectos-innovadores/esal/2026.html",
        "region_hint": "ES - España",
    },
    {
        "id": "pub-miteco-life",
        "fuente": "EU_SEDIA",
        "tipo_oportunidad": "SUBVENCION",
        "nombre": "MITECO - Programa LIFE Convocatorias Abiertas",
        "url": "https://www.miteco.gob.es/es/ministerio/fondos-europeos/life/convocatorias/convocatorias-abiertas.html",
        "region_hint": "UE - España",
    },
    {
        "id": "pub-miteco-prtr-bio",
        "fuente": "BOE",
        "tipo_oportunidad": "SUBVENCION",
        "nombre": "MITECO PRTR - Ayudas Biodiversidad",
        "url": "https://www.prtr.miteco.gob.es/es/ayudas/ayudas-biodiversidad.html",
        "region_hint": "ES - España",
    },
    {
        "id": "pub-fb-wp-pages",
        "fuente": "FUNDACION_BIODIVERSIDAD",
        "tipo_oportunidad": "SUBVENCION",
        "nombre": "Fundación Biodiversidad F.S.P. (MITECO)",
        "url": "https://fundacion-biodiversidad.es/wp-json/wp/v2/pages?search=convocatoria&per_page=30",
        "region_hint": "ES - España",
    },
    {
        "id": "pub-fb-wp-subv",
        "fuente": "FUNDACION_BIODIVERSIDAD",
        "tipo_oportunidad": "SUBVENCION",
        "nombre": "Fundación Biodiversidad F.S.P. (MITECO)",
        "url": "https://fundacion-biodiversidad.es/wp-json/wp/v2/pages?search=subvenciones&per_page=30",
        "region_hint": "ES - España",
    },
    {
        "id": "pub-aei-buscador",
        "fuente": "BOE",
        "tipo_oportunidad": "SUBVENCION",
        "nombre": "Agencia Estatal de Investigación (AEI)",
        "url": "https://www.aei.gob.es/convocatorias/buscador-convocatorias?status=1",
        "region_hint": "ES - España",
    },
]

_HTML_RELEVANT_CUE_RE = re.compile(
    r"(?:subvenci[oó]n|subvencions|ayuda|axuda|ajut|diru-laguntza|convocatoria|"
    r"beca|grant|call|licitaci[oó]n|contrato|orden\b|orde\b|resoluci[oó]n|decreto|"
    r"reforest|forestal|repoblaci|incendio|lume|incendi|biodivers|natura\s*2000|"
    r"medio\s*ambiente|medi\s*ambient|bosque|monte|carbono|ribera|"
    r"restauraci[oó]n|custodia|investigaci[oó]n|cient[ií]fic\w*|ecolog[ií]a|"
    r"ecosistema\w*|transici[oó]n\s+ecol[oó]gic\w*|cambio\s+clim[aá]tic\w*|"
    r"emprendimiento\s+verde|despoblaci[oó]n|reto\s+demogr[aá]fico|"
    r"inter[eé]s\s+(?:general|social)|suelo\w*|i\+d\+i|esal\b|\.pdf\b)",
    re.IGNORECASE,
)

_HTML_CALL_ACTION_CUE_RE = re.compile(
    r"(?:subvenci[oó]n|subvencions|ayuda|axuda|ajut|diru-laguntza|convocatoria|"
    r"bases\b|solicitud|beca|grant|call|licitaci[oó]n|contrato|orden\b|orde\b|"
    r"resoluci[oó]n|decreto|financiaci[oó]n|investigaci[oó]n|premio\w*|"
    r"presenta|candidatura|accede|informaci[oó]n|leer\s+m[aá]s|ver\s+m[aá]s|"
    r"emprendimiento-verde|biodiversidad|\.pdf\b)",
    re.IGNORECASE,
)

_HTML_NOISE_CUE_RE = re.compile(
    r"(?:cookie|pol[ií]tica\s+de\s+privacidad|aviso\s+legal|accesibilidad|"
    r"mapa\s+web|iniciar\s+sesi[oó]n|cerrar\s+sesi[oó]n|trabaja\s+con\s+nosotros|"
    r"s[ií]guenos\s+en|twitter\.com|facebook\.com|instagram\.com|youtube\.com|linkedin\.com|"
    r"cont[aá]ctanos|qui[eé]nes\s+somos|d[oó]nde\s+actuamos|qu[eé]\s+hacemos|espa[ñn]ol\s+english|"
    r"sala\s+de\s+prensa|nota\s+de\s+prensa|suscr[ií]bete|newsletter|preguntas\s+frecuentes|"
    r"eficiencia\s+energ[eé]tica|movilidad\s+sostenible|reformas?\s+sostenibles?|te\s+contamos\s+m[aá]s|"
    r"premios?\s+fronteras|premios?\s+de\s+inform[aá]tica|red\s+leonardo|"
    r"objetivos\s+historia|transparencia|relaciones\s+internacionales|causas\s+de\s+p[eé]rdida|"
    r"generaci[oó]n\s+y\s+gesti[oó]n\s+del\s+conocimiento|estudio\s+complementario|"
    r"oficina\s+de\s+informaci[oó]n|unidad\s+de\s+informaci[oó]n|estad[ií]sticas\s+de\s+biodiversidad|"
    r"listas\s+patr[oó]n|servidor\s+cartogr[aá]fico|d[ií]as\s+mundiales|planes\s+estrat[eé]gicos|"
    r"proyectos\s+ganadores|formulaci[oó]n\s+de\s+quejas|banco\s+de\s+datos\s+de\s+la\s+naturaleza|/atencion-a-la-ciudadania/|/organigrama/|"
    r"/estadisticas/|/banco-datos-naturaleza/|/formacion-becas-convenios|/relaciones-internacionales/|"
    r"/enlaces-de-interes|/dias-mundiales|/participacion-publica|/campanas/|/agenda/evento/|"
    r"/sala-de-comunicacion/|/proyecto-conservacion-|/galardonados/|/gripe-aviar|/cites\b|"
    r"/temas/|/servicios/|/organizacion/|/premios/premios-miteco|/plan-estrategico|"
    r"saltar\s+al\s+contenido|arrow_right_alt|chevron_right|open_in_new|close\s+cerrar|"
    r"^\s*agenda\b.*\bcultura\b|ver\s+todo\b|todo\s+ver\s+m[aá]s|iniciativas\s+de\s+divulgaci[oó]n|"
    r"/agenda/cultura|/filmoteca|error\s*404|p[aá]gina\s+no\s+encontrada|page\s+not\s+found|404\s+not\s+found)",
    re.IGNORECASE,
)

_SITEMAP_ENV_RE = re.compile(
    r"(?:ecolog|biodivers|conservac|ambient|clim[aá]tic|forest|reforest|biophilia|ecosistem|bosque|natura)",
    re.IGNORECASE,
)

_SITEMAP_SKIP_RE = re.compile(
    r"(?:fronteras|informatica|leonardo|musica|humanidades|matem|fisica|quimica|biomed|economia|arte|video|galeria|jurado|premiados|comunicado)",
    re.IGNORECASE,
)

_SKIP_CONTAINER_ATTR_RE = re.compile(
    r"(?:^|[\s_-])(megamenu|mega-menu|navbar|nav-menu|main-menu|menu-principal|breadcrumb|migas|"
    r"footer|cabecera|header-nav|site-header|top-bar|cookie|social-links|sidebar-nav|menu-lateral)(?:$|[\s_-])",
    re.IGNORECASE,
)

_PRE_FETCH_HINT_RE = re.compile(
    r"(?:subvenci|ayuda|axuda|ajut|convocat|orden|orde|resoluci|decreto|licitaci|"
    r"forest|reforest|repobl|incend|biodivers|natura|medio\s*ambient|bosque|monte|carbono|ribera|life|horizon|ecolog)",
    re.IGNORECASE,
)


def stable_short_hash(value: str) -> str:
    """Deterministic cross-process 10-char ID hash (never randomized by PYTHONHASHSEED)."""
    return hashlib.sha1(value.encode("utf-8", errors="ignore")).hexdigest()[:10]


def _is_pdf_link(url: str) -> bool:
    low = url.lower()
    return low.endswith(".pdf") or ".pdf?" in low or "/pdfs/" in low or "format=pdf" in low or "verpdf" in low


def _local_tag(tag: str) -> str:
    return tag.split("}", 1)[-1].lower() if "}" in tag else tag.lower()


class _HTMLOpportunityParser(HTMLParser):
    """Lightweight stdlib HTML parser collecting alternate RSS links and contextual call anchors."""

    _SKIP_TAGS = {"script", "style", "noscript", "svg", "nav", "header", "footer", "aside", "form"}
    _BLOCK_TAGS = {"article", "li", "tr", "section", "div", "p", "td"}
    _HEADING_TAGS = {"h1", "h2", "h3", "h4"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._nav_stack: list[str] = []
        self._in_anchor = False
        self._anchor_href = ""
        self._anchor_chunks: list[str] = []
        self._in_heading = False
        self._heading_chunks: list[str] = []
        self._last_heading = ""
        self._block_stack: list[list[str]] = []
        self._block_depth = 0
        self.rss_links: list[str] = []
        self.anchors: list[tuple[str, str, str]] = []  # (href, anchor_text, context_snippet)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        t = tag.lower()
        attr_map = {k.lower(): (v or "") for k, v in attrs}
        if t in self._SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth > 0:
            return

        cls_id = f"{attr_map.get('class', '')} {attr_map.get('id', '')}".strip()
        role = attr_map.get("role", "").lower()
        if (cls_id and _SKIP_CONTAINER_ATTR_RE.search(cls_id)) or role in ("navigation", "banner", "contentinfo"):
            self._nav_stack.append(t)

        if t == "link":
            rel = attr_map.get("rel", "").lower()
            ctype = attr_map.get("type", "").lower()
            href = attr_map.get("href", "").strip()
            if href and "alternate" in rel and ("rss" in ctype or "atom" in ctype or "xml" in ctype):
                self.rss_links.append(href)
            return

        if t in self._BLOCK_TAGS:
            self._block_stack.append([])
            self._block_depth += 1
        if t in self._HEADING_TAGS:
            self._in_heading = True
            self._heading_chunks = []
        if t == "a":
            self._in_anchor = True
            self._anchor_href = attr_map.get("href", "").strip()
            self._anchor_chunks = []

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if t in self._SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if self._skip_depth > 0:
            return

        if t in self._HEADING_TAGS and self._in_heading:
            self._in_heading = False
            heading = re.sub(r"\s+", " ", " ".join(self._heading_chunks)).strip()
            if heading and not self._nav_stack:
                self._last_heading = heading[:180]
        if t == "a" and self._in_anchor:
            self._in_anchor = False
            a_text = re.sub(r"\s+", " ", " ".join(self._anchor_chunks)).strip()
            # Walk up only this anchor's own ancestor blocks (no sibling card bleed)
            ctx_parts: list[str] = []
            acc_len = 0
            for blk in reversed(self._block_stack):
                piece = re.sub(r"\s+", " ", " ".join(blk)).strip()
                if not piece:
                    continue
                if acc_len >= 25 and len(piece) > 380:
                    break
                ctx_parts.append(piece)
                acc_len += len(piece)
                if acc_len >= 240:
                    break
            ctx = " ".join(reversed(ctx_parts)).strip()[:360]
            if not ctx and self._last_heading:
                ctx = self._last_heading
            elif self._last_heading and len(ctx) < 25 and self._last_heading not in ctx:
                ctx = f"{self._last_heading}. {ctx}"
            if self._anchor_href and not self._nav_stack:
                self.anchors.append((self._anchor_href, a_text[:260], ctx[:360]))
        if t in self._BLOCK_TAGS and self._block_stack:
            popped = self._block_stack.pop()
            self._block_depth = max(0, self._block_depth - 1)
            if self._block_stack and popped:
                # Propagate compact heading/date/summary children (< 220 chars) up to immediate enclosing card
                joined = " ".join(popped)
                if len(joined) <= 220 and sum(len(x) for x in self._block_stack[-1]) < 320:
                    self._block_stack[-1].append(joined)
        if self._nav_stack and t in self._nav_stack:
            while self._nav_stack:
                top = self._nav_stack.pop()
                if top == t:
                    break

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0 or self._nav_stack:
            return
        txt = data.strip()
        if not txt:
            return
        if self._block_stack:
            self._block_stack[-1].append(txt)
        if self._in_heading:
            self._heading_chunks.append(txt)
        if self._in_anchor:
            self._anchor_chunks.append(txt)


def parse_rss_or_atom_xml(xml_text: str, source_cfg: dict[str, Any]) -> list[RawCandidate]:
    """
    Namespace-agnostic parser supporting RSS 2.0 (<item>), RDF/RSS 1.0 (<item>),
    Atom 1.0 (<entry>), and XML sitemaps (<urlset><url><loc>).
    """
    items_out: list[RawCandidate] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    seen_keys: set[str] = set()
    entries = [el for el in root.iter() if _local_tag(el.tag) in ("item", "entry")][:60]
    if not entries and _local_tag(root.tag) == "urlset":
        url_nodes = [el for el in root.iter() if _local_tag(el.tag) == "url"]
        for unode in url_nodes:
            loc = ""
            lastmod = ""
            for ch in unode:
                ln = _local_tag(ch.tag)
                if ln == "loc" and ch.text:
                    loc = ch.text.strip()
                elif ln == "lastmod" and ch.text:
                    lastmod = ch.text.strip()
            if not loc or loc in seen_keys:
                continue
            if not _SITEMAP_ENV_RE.search(loc) or _SITEMAP_SKIP_RE.search(loc):
                continue
            seen_keys.add(loc)
            slug = urlparse(loc).path.rstrip("/").split("/")[-1]
            clean_title = slug.replace("-", " ").replace("_", " ").strip().capitalize()
            if len(clean_title) < 12:
                continue
            m_yr = re.search(r"\b(20\d{2})\b", loc)
            pub_date_hint = lastmod[:10] if len(lastmod) >= 10 else (f"{m_yr.group(1)}-01-15" if m_yr else None)
            uid = f"{source_cfg['id']}-{stable_short_hash(loc)}"
            items_out.append(
                RawCandidate(
                    id=uid,
                    codigo_oficial=source_cfg["id"].upper(),
                    fuente=source_cfg.get("fuente", "FUNDACION_PRIVADA"),
                    tipo_oportunidad=source_cfg.get("tipo_oportunidad", "CONVOCATORIA_PRIVADA"),
                    titulo=clean_title[:240],
                    organo_convocante=source_cfg["nombre"],
                    texto=clean_title,
                    region_hint=source_cfg.get("ccaa") or source_cfg.get("region_hint", ""),
                    fecha_publicacion=pub_date_hint,
                    url_ficha_oficial=loc,
                )
            )
        items_out.sort(key=lambda c: c.url_ficha_oficial, reverse=True)
        return items_out[:16]
    for entry in entries:
        title = ""
        link = source_cfg["url"]
        pdf_link: str | None = None
        desc = ""
        pub_date = None

        for child in entry:
            lname = _local_tag(child.tag)
            txt = (child.text or "").strip()
            if lname == "title" and txt:
                title = re.sub(r"\s+", " ", txt)
            elif lname == "link":
                href = (child.attrib.get("href") or txt).strip()
                ctype = (child.attrib.get("type") or "").lower()
                if href:
                    abs_href = urljoin(source_cfg["url"], href)
                    if "pdf" in ctype or _is_pdf_link(abs_href):
                        pdf_link = abs_href
                    if link == source_cfg["url"]:
                        link = abs_href
            elif lname == "enclosure":
                enc_url = (child.attrib.get("url") or "").strip()
                enc_type = (child.attrib.get("type") or "").lower()
                if enc_url and ("pdf" in enc_type or _is_pdf_link(enc_url)):
                    pdf_link = urljoin(source_cfg["url"], enc_url)
            elif lname in ("description", "summary", "content") and txt:
                clean_desc = re.sub(r"<[^>]+>", " ", txt)
                desc = re.sub(r"\s+", " ", clean_desc).strip()
            elif lname in ("pubdate", "published", "updated", "date") and txt and not pub_date:
                pub_date = txt[:16]

        if not title:
            continue
        dedup_key = f"{link}|{title}"
        if dedup_key in seen_keys:
            continue
        seen_keys.add(dedup_key)

        if pdf_link is None and _is_pdf_link(link):
            pdf_link = link

        uid = f"{source_cfg['id']}-{stable_short_hash(dedup_key)}"
        items_out.append(
            RawCandidate(
                id=uid,
                codigo_oficial=source_cfg["id"].upper(),
                fuente=source_cfg.get("fuente", "BOLETIN_CCAA"),
                tipo_oportunidad=source_cfg.get("tipo_oportunidad", "SUBVENCION"),
                titulo=title,
                organo_convocante=source_cfg["nombre"],
                texto=f"{title}. {desc}".strip(),
                region_hint=source_cfg.get("ccaa") or source_cfg.get("region_hint", ""),
                url_ficha_oficial=link,
                url_bases_reguladoras=pdf_link,
            )
        )
    return items_out


_GENERIC_CTA_TEXT_RE = re.compile(
    r"^(?:m[aá]s\s+informaci[oó]n|leer\s+m[aá]s|ver\s+m[aá]s|saber\s+m[aá]s|"
    r"presenta\s+tu\s+candidatura|accede\s+a\s+las\s+bases|bases\s+legales(?:\s+[ivx]+\s+convocatoria)?|"
    r"resoluci[oó]n(?:\s+de\s+la\s+convocatoria)?(?:\s+202[0-9])?|"
    r"convocatoria(?:\s+202[0-9])?|descargar(?:\s+pdf)?|ver\s+convocatoria|solicitar)$",
    re.IGNORECASE,
)


def _derive_html_candidate_title(a_text: str, ctx: str, abs_url: str) -> str:
    """Use anchor text when descriptive; fall back to card context or URL slug for generic CTA links."""
    clean_a = re.sub(r"\s+", " ", a_text).strip(" -|:\t\r\n")
    clean_ctx = re.sub(r"\s+", " ", ctx).strip()
    if clean_a and not _GENERIC_CTA_TEXT_RE.match(clean_a) and len(clean_a) >= 18:
        return clean_a
    if clean_ctx:
        # Strip trailing CTA phrases that often sit inside the same card context
        trimmed = _GENERIC_CTA_TEXT_RE.sub("", clean_ctx).strip(" -|:")
        for phrase in ("Más información", "MÁS INFORMACIÓN", "Leer más", "Saber más", "Accede a las bases", "Presenta tu candidatura"):
            trimmed = trimmed.replace(phrase, " ")
        trimmed = re.sub(r"\s+", " ", trimmed).strip(" .-|:")
        if len(trimmed) >= 18:
            return trimmed[:180]
    if clean_a and len(clean_a) >= 8 and not _GENERIC_CTA_TEXT_RE.match(clean_a):
        return clean_a
    slug = urlparse(abs_url).path.rstrip("/").split("/")[-1]
    slug = re.sub(r"\.pdf$|\.html?$", "", slug, flags=re.IGNORECASE).replace("-", " ").replace("_", " ").strip()
    return slug.capitalize() if len(slug) >= 10 else clean_a or "Convocatoria oficial"


def extract_candidates_from_html(
    html_text: str,
    source_cfg: dict[str, Any],
    base_url: str,
) -> tuple[list[RawCandidate], list[str]]:
    """Extract candidate grants/bulletins and alternate RSS links from an HTML portal page."""
    parser = _HTMLOpportunityParser()
    try:
        parser.feed(html_text)
        parser.close()
    except Exception:
        return [], []

    rss_urls = [urljoin(base_url, u) for u in parser.rss_links]
    candidates: list[RawCandidate] = []
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()

    for href, a_text, ctx in parser.anchors:
        low_href = href.lower().strip().rstrip("),;")
        if not low_href or low_href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        abs_url = urljoin(base_url, href.strip().rstrip("),;"))
        if abs_url in seen_urls or abs_url.rstrip("/") == base_url.rstrip("/"):
            continue

        is_pdf = _is_pdf_link(abs_url)
        clean_a = a_text.strip()
        if not clean_a and not is_pdf:
            continue
        is_relevant_slug = bool(re.search(r"/(?:ayudas?|convocatorias?|subvenciones?|premios?|biodiversidad|emprendimiento-verde|esal|life|investigacion)/", low_href))
        if len(clean_a) < 8 and not is_pdf and not (is_relevant_slug and len(ctx.strip()) >= 20):
            continue

        combined = f"{a_text} {ctx}".strip()
        if len(combined) < 18 or _HTML_NOISE_CUE_RE.search(f"{a_text} {low_href}"):
            continue
        if not _HTML_RELEVANT_CUE_RE.search(combined) and not is_pdf:
            continue
        if not _HTML_CALL_ACTION_CUE_RE.search(f"{a_text} {low_href}") and not is_pdf:
            continue

        clean_title = _derive_html_candidate_title(a_text, ctx, abs_url)
        clean_title = re.sub(r"\b(?:arrow_right_alt|chevron_right|open_in_new|close)\b", " ", clean_title, flags=re.IGNORECASE)
        clean_title = re.sub(r"\s+", " ", clean_title).strip(" .-|:")
        if is_pdf and len(clean_title) < 24 and ctx:
            clean_title = ctx[:200]
        if _GENERIC_CTA_TEXT_RE.match(clean_title):
            continue
        if len(re.findall(r"\bver\s+m[aá]s\b", clean_title, flags=re.IGNORECASE)) >= 2:
            continue
        norm_t = re.sub(r"\s+", " ", clean_title.lower()).strip()
        if norm_t in seen_titles or len(clean_title) < 12 or _HTML_NOISE_CUE_RE.search(clean_title):
            continue

        seen_urls.add(abs_url)
        seen_titles.add(norm_t)

        uid = f"{source_cfg['id']}-{stable_short_hash(f'{abs_url}|{clean_title}')}"
        candidates.append(
            RawCandidate(
                id=uid,
                codigo_oficial=source_cfg["id"].upper(),
                fuente=source_cfg.get("fuente", "FUNDACION_PRIVADA"),
                tipo_oportunidad=source_cfg.get("tipo_oportunidad", "CONVOCATORIA_PRIVADA"),
                titulo=clean_title[:240],
                organo_convocante=source_cfg["nombre"],
                texto=f"{clean_title}. {ctx}".strip(),
                region_hint=source_cfg.get("ccaa") or source_cfg.get("region_hint", "Privada / RSC España"),
                url_ficha_oficial=abs_url,
                url_bases_reguladoras=abs_url if _is_pdf_link(abs_url) else None,
            )
        )

    return candidates[:35], rss_urls


def parse_wp_json_candidates(json_text: str, source_cfg: dict[str, Any]) -> list[RawCandidate]:
    """Parse WordPress REST JSON feeds (e.g., Fundación Biodiversidad /wp-json/wp/v2/pages)."""
    try:
        items = json.loads(json_text)
    except Exception:
        return []
    if not isinstance(items, list):
        return []

    out: list[RawCandidate] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        raw_t = ((item.get("title") or {}).get("rendered") or "").strip()
        link = (item.get("link") or "").strip()
        if not raw_t or not link or link in seen:
            continue
        if "landing-convocatorias-test" in link.lower() or "test" in raw_t.lower().split():
            continue
        seen.add(link)

        clean_t = html_lib.unescape(re.sub(r"<[^>]+>", " ", raw_t))
        clean_t = re.sub(r"\s+", " ", clean_t).strip()
        raw_exc = ((item.get("excerpt") or {}).get("rendered") or "")
        raw_cnt = ((item.get("content") or {}).get("rendered") or "")
        body = html_lib.unescape(re.sub(r"<[^>]+>", " ", f"{raw_exc} {raw_cnt}"))
        body = re.sub(r"\s+", " ", body).strip()[:6000]
        pdf_m = re.search(r'https?://[^\s"\'<>]+\.pdf(?:\?[^\s"\'<>]*)?', raw_cnt, re.IGNORECASE)
        pub_date = (item.get("date") or "")[:10] or None

        uid = f"{source_cfg['id']}-{stable_short_hash(link)}"
        out.append(
            RawCandidate(
                id=uid,
                codigo_oficial=source_cfg["id"].upper(),
                fuente=source_cfg.get("fuente", "FUNDACION_BIODIVERSIDAD"),
                tipo_oportunidad=source_cfg.get("tipo_oportunidad", "SUBVENCION"),
                titulo=clean_t[:240],
                organo_convocante=source_cfg["nombre"],
                texto=f"{clean_t}. {body}".strip(),
                region_hint=source_cfg.get("ccaa") or source_cfg.get("region_hint", "ES - España"),
                fecha_publicacion=pub_date,
                url_ficha_oficial=link,
                url_bases_reguladoras=pdf_m.group(0) if pdf_m else None,
            )
        )
    return out[:30]


def _is_soft_404_html(html_body: str) -> bool:
    head_txt = html_body[:6000]
    title_m = re.search(r"<title[^>]*>(.*?)</title>", head_txt, re.IGNORECASE | re.DOTALL)
    h1_m = re.search(r"<h1[^>]*>(.*?)</h1>", html_body, re.IGNORECASE | re.DOTALL)
    check = html_lib.unescape(
        re.sub(r"<[^>]+>", " ", f"{title_m.group(1) if title_m else ''} {h1_m.group(1) if h1_m else ''}")
    ).lower()
    return any(tok in check for tok in ("error 404", "404 not found", "página no encontrada", "pagina no encontrada", "page not found"))


def _extract_focused_page_details(html_body: str, page_url: str) -> tuple[str, str, str | None]:
    """Extract clean H1/title, noise-stripped <main>/<article> text, and best bases PDF URL."""
    if not html_body or _is_soft_404_html(html_body):
        return "", "", None

    main_m = re.search(r"<main[^>]*>(.*?)</main>", html_body, re.IGNORECASE | re.DOTALL)
    art_m = re.search(r"<article[^>]*>(.*?)</article>", html_body, re.IGNORECASE | re.DOTALL)
    focused_html = (
        main_m.group(1)
        if main_m and len(main_m.group(1)) > 200
        else (art_m.group(1) if art_m and len(art_m.group(1)) > 200 else html_body)
    )
    h1_m = re.search(r"<h1[^>]*>(.*?)</h1>", focused_html, re.IGNORECASE | re.DOTALL)
    if not h1_m:
        h1_m = re.search(r"<h1[^>]*>(.*?)</h1>", html_body, re.IGNORECASE | re.DOTALL)
    title_m = re.search(r"<title[^>]*>(.*?)</title>", html_body, re.IGNORECASE | re.DOTALL)
    resolved_title = html_lib.unescape(
        re.sub(r"<[^>]+>", " ", (h1_m.group(1) if h1_m else title_m.group(1) if title_m else ""))
    )
    resolved_title = re.sub(r"\s+", " ", resolved_title).strip(" -|\t\r\n")

    stripped = re.sub(
        r"<(?:script|style|nav|header|footer|aside|noscript|form)[^>]*>.*?</(?:script|style|nav|header|footer|aside|noscript|form)>",
        " ",
        focused_html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    plain = html_lib.unescape(re.sub(r"<[^>]+>", " ", stripped))
    plain = re.sub(r"\{\{[^}]*\}\}", " ", plain)
    plain = re.split(
        r"\b(?:proyectos\s+relacionados|te\s+puede\s+interesar|noticias\s+relacionadas|otras\s+iniciativas)\b",
        plain,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    plain = re.sub(r"\s+", " ", plain).strip()

    best_pdf: str | None = None
    fallback_pdf: str | None = None
    for pm in re.finditer(r'href=["\']([^"\']+\.pdf(?:\?[^"\']*)?)["\']', focused_html, re.IGNORECASE):
        raw_pdf = pm.group(1).strip().rstrip("),;").replace(" ", "%20")
        pdf_abs = urljoin(page_url, raw_pdf)
        low_pdf = pdf_abs.lower()
        if any(bad in low_pdf for bad in ("cookie", "privacidad", "aviso-legal", "memoria-anual", "organigrama")):
            continue
        if any(k in low_pdf for k in ("base", "convocatoria", "regulad", "emprendimiento", "biodiversidad", "clima", "boe", "ayuda", "orden", "resoluc")):
            best_pdf = pdf_abs
            break
        if fallback_pdf is None:
            fallback_pdf = pdf_abs

    return resolved_title, plain, (best_pdf or fallback_pdf)


def _extract_direct_call_candidate(
    html_body: str,
    source_cfg: dict[str, Any],
    final_url: str,
) -> list[RawCandidate]:
    """Extract a concrete single environmental call page with full <main> text & linked bases PDF."""
    resolved_title, plain, best_pdf = _extract_focused_page_details(html_body, final_url)
    if len(plain) < 160 or not resolved_title or _HTML_NOISE_CUE_RE.search(resolved_title):
        return []
    clean_title = resolved_title.split(" | ")[0].split(" - Fundación")[0].strip()[:240] or resolved_title[:240]
    m_yr = re.search(r"\b(20\d{2})\b", f"{clean_title} {final_url}")
    pub_hint = f"{m_yr.group(1)}-01-15" if m_yr and int(m_yr.group(1)) < 2026 else None
    uid = f"{source_cfg['id']}-{stable_short_hash(final_url)}"
    return [
        RawCandidate(
            id=uid,
            codigo_oficial=source_cfg["id"].upper(),
            fuente=source_cfg.get("fuente", "FUNDACION_PRIVADA"),
            tipo_oportunidad=source_cfg.get("tipo_oportunidad", "CONVOCATORIA_PRIVADA"),
            titulo=clean_title,
            organo_convocante=source_cfg["nombre"],
            texto=f"{clean_title}. {plain[:5500]}".strip(),
            region_hint=source_cfg.get("ccaa") or source_cfg.get("region_hint", "Privada / RSC España"),
            fecha_publicacion=pub_hint,
            url_ficha_oficial=final_url,
            url_bases_reguladoras=best_pdf,
        )
    ]


async def _enrich_html_detail_pages(
    client: httpx.AsyncClient,
    cands: list[RawCandidate],
    limit: int = 24,
) -> None:
    """Resolve real H1/<title>/body/PDF links for generic or sparse HTML card links (FBBVA, Endesa, AEI, MITECO, etc.)."""
    targets = [
        c
        for c in cands
        if c.url_ficha_oficial
        and not _is_pdf_link(c.url_ficha_oficial)
        and (
            len(c.texto or "") < (1200 if c.fuente == "FUNDACION_PRIVADA" else 650)
            or _GENERIC_CTA_TEXT_RE.match(c.titulo or "")
        )
    ][:limit]
    if not targets:
        return

    dead_ids: set[str] = set()

    async def _fetch_one(cand: RawCandidate) -> None:
        try:
            r = await client.get(cand.url_ficha_oficial, timeout=6.0)
            if r.status_code != 200 or not r.text:
                return
            if _is_soft_404_html(r.text):
                dead_ids.add(cand.id)
                return
            resolved_h1, plain, best_pdf = _extract_focused_page_details(r.text, str(r.url))
            if len(resolved_h1) >= 16 and (
                _GENERIC_CTA_TEXT_RE.match(cand.titulo)
                or len(cand.titulo) < 32
                or "/" in cand.titulo
                or cand.fuente == "FUNDACION_PRIVADA"
                and cand.titulo.lower() in str(r.url).replace("-", " ").lower()
            ):
                cand.titulo = resolved_h1.split(" | ")[0].split(" - Fundación")[0].strip()[:240] or resolved_h1[:240]
            if len(plain) >= 180:
                cand.texto = f"{cand.titulo}. {plain[:5500]}".strip()
            if not cand.url_bases_reguladoras and best_pdf:
                cand.url_bases_reguladoras = best_pdf
        except Exception:
            pass

    await asyncio.gather(*[_fetch_one(tc) for tc in targets])
    if dead_ids:
        cands[:] = [c for c in cands if c.id not in dead_ids]


async def poll_web_source(
    client: httpx.AsyncClient,
    source_cfg: dict[str, Any],
) -> list[RawCandidate]:
    """
    Unified poller for RSS, Atom, XML Sitemap, WP-JSON, direct call pages,
    and listing portals with automatic RSS discovery and detail expansion.
    """
    try:
        resp = await client.get(source_cfg["url"])
        if resp.status_code != 200 or not resp.text.strip():
            return []
        stripped = resp.text.lstrip()
        lower_head = stripped[:400].lower()

        if stripped.startswith(("[", "{")) and "application/json" in (resp.headers.get("content-type") or "").lower():
            return parse_wp_json_candidates(resp.text, source_cfg)

        is_xml_feed = (
            "<rss" in lower_head
            or "<feed" in lower_head
            or "<rdf:rdf" in lower_head
            or "<urlset" in lower_head
            or ("<?xml" in lower_head and "<html" not in lower_head)
        )
        if is_xml_feed:
            xml_cands = parse_rss_or_atom_xml(resp.text, source_cfg)
            if source_cfg.get("kind") == "sitemap" and xml_cands:
                await _enrich_html_detail_pages(client, xml_cands, limit=16)
            return xml_cands

        if _is_soft_404_html(resp.text):
            return []

        final_url = str(resp.url)
        kind = source_cfg.get("kind", "listing")
        if kind == "direct_call" and source_cfg.get("id") != "priv-web-motorverde":
            direct = _extract_direct_call_candidate(resp.text, source_cfg, final_url)
            if direct:
                return direct

        html_cands, rss_urls = extract_candidates_from_html(
            resp.text,
            source_cfg=source_cfg,
            base_url=final_url,
        )
        if kind == "direct_call":
            if source_cfg.get("id") == "priv-web-motorverde" and any(
                "convocatoria" in c.url_ficha_oficial.lower() or "convocatoria" in c.titulo.lower()
                for c in html_cands
            ):
                pass
            else:
                direct = _extract_direct_call_candidate(resp.text, source_cfg, final_url)
                if direct:
                    return direct

        await _enrich_html_detail_pages(client, html_cands, limit=14)
        for rss_url in rss_urls[:1]:
            try:
                rss_resp = await client.get(rss_url)
                if rss_resp.status_code == 200 and rss_resp.text.lstrip().startswith("<"):
                    rss_cands = parse_rss_or_atom_xml(rss_resp.text, source_cfg)
                    existing_urls = {c.url_ficha_oficial for c in html_cands}
                    for rc in rss_cands:
                        if rc.url_ficha_oficial not in existing_urls:
                            html_cands.append(rc)
            except Exception:
                pass
        return html_cands
    except Exception as exc:
        logger.debug("Web monitor '%s' skipped: %s", source_cfg.get("id"), exc)
        return []


def _candidate_linked_pdf_url(cand: RawCandidate) -> str | None:
    for url in (cand.url_bases_reguladoras, cand.url_boletin_extracto, cand.url_ficha_oficial):
        if not url or not url.startswith(("http://", "https://")):
            continue
        if url == cand.url_bases_reguladoras or url == cand.url_boletin_extracto:
            if _is_pdf_link(url) or "boe.es/" in url or "bocm.es/" in url:
                return url
        elif _is_pdf_link(url):
            return url
    return None


async def enrich_candidate_from_linked_pdf(
    client: httpx.AsyncClient,
    cand: RawCandidate,
    api_key_override: str | None = None,
) -> bool:
    """
    Follow an extract's linked official PDF when candidate text is short (< 900 chars) or
    for private/biodiversity foundation calls with an attached regulatory bases PDF, extracting
    full text/CPVs/budgets/deadlines with OCR fallback.
    """
    pdf_url = _candidate_linked_pdf_url(cand)
    if cand.fuente == "FUENTES_PDF" or not pdf_url:
        return False
    if "[TEXTO COMPLETO PDF ENLAZADO" in (cand.texto or ""):
        return False
    is_foundation_pdf = cand.fuente in ("FUNDACION_PRIVADA", "FUNDACION_BIODIVERSIDAD") and _is_pdf_link(pdf_url)
    if len(cand.texto or "") >= 900 and not is_foundation_pdf:
        return False

    # Guard bandwidth: only follow PDFs for candidates showing domain or grant signals
    signal_text = f"{cand.titulo} {cand.organo_convocante} {cand.texto[:400]}"
    if not cand.cpv_codes and not _PRE_FETCH_HINT_RE.search(signal_text):
        return False

    try:
        resp = await client.get(pdf_url)
        if resp.status_code != 200 or not resp.content or len(resp.content) > MAX_LINKED_PDF_BYTES:
            return False
        ctype = (resp.headers.get("content-type") or "").lower()
        if not resp.content.startswith(b"%PDF") and "pdf" not in ctype:
            return False

        filename = pdf_url.rsplit("/", 1)[-1].split("?", 1)[0] or f"{cand.id}.pdf"
        doc = extract_pdf_from_bytes(
            resp.content,
            filename=filename,
            api_key_override=api_key_override,
        )
        if not doc.full_text:
            return False

        cand.texto = f"{cand.texto}\n\n[TEXTO COMPLETO PDF ENLAZADO ({filename})]:\n{doc.full_text[:12000]}".strip()
        cand.cpv_codes = sorted(set(cand.cpv_codes or []) | set(doc.cpv_codes or []) | set(extract_cpv_codes(doc.full_text)))
        if cand.presupuesto_total is None and doc.presupuesto_total is not None:
            cand.presupuesto_total = doc.presupuesto_total
        if cand.importe_max_proyecto is None and doc.importe_max_proyecto is not None:
            cand.importe_max_proyecto = doc.importe_max_proyecto
        if cand.importe_max_beneficiario is None and doc.importe_max_entidad is not None:
            cand.importe_max_beneficiario = doc.importe_max_entidad
        if cand.porcentaje_financiacion is None and doc.porcentaje_financiacion is not None:
            cand.porcentaje_financiacion = doc.porcentaje_financiacion
        if not cand.plazo_texto_original and doc.plazo_solicitud_texto:
            cand.plazo_texto_original = doc.plazo_solicitud_texto
        if not cand.beneficiarios_hint and doc.beneficiarios_raw:
            cand.beneficiarios_hint = doc.beneficiarios_raw
        if not cand.criterios_valoracion and doc.criterios_valoracion:
            cand.criterios_valoracion = doc.criterios_valoracion
        cand.cofinanciado_ue = cand.cofinanciado_ue or doc.cofinanciado_ue
        if not cand.url_tramitacion and doc.url_tramitacion:
            cand.url_tramitacion = doc.url_tramitacion
        if not cand.url_bases_reguladoras:
            cand.url_bases_reguladoras = pdf_url

        # Promote generic RSS/HTML ID code to official BDNS/Orden signature if found in full PDF
        if doc.codigo_bdns and not cand.codigo_oficial.startswith("BDNS-"):
            cand.codigo_oficial = f"BDNS-{doc.codigo_bdns}"
        elif doc.codigo_orden and cand.codigo_oficial.startswith(("RSS-", "PRIV-")):
            cand.codigo_oficial = doc.codigo_orden

        return True
    except Exception as exc:
        logger.debug("Linked PDF enrichment failed for '%s': %s", pdf_url, exc)
        return False
