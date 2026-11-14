"""Lightweight Async Web Monitors (RSS / Atom / HTML Scrapers) & Extract->PDF Full-Text Enricher."""
from html.parser import HTMLParser
import hashlib
import logging
import re
from typing import Any
from urllib.parse import urljoin
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
        "fuente": "FUNDACION_PRIVADA",
        "tipo_oportunidad": "CONVOCATORIA_PRIVADA",
        "nombre": "Fundación ”la Caixa” (Medio Ambiente y Convocatorias)",
        "url": "https://fundacionlacaixa.org/es/",
        "region_hint": "Privada / RSC España",
    },
    {
        "id": "priv-web-motorverde",
        "fuente": "FUNDACION_PRIVADA",
        "tipo_oportunidad": "CONVOCATORIA_PRIVADA",
        "nombre": "Fundación Repsol & Grupo Sylvestris (Motor Verde)",
        "url": "https://www.fundacionrepsol.com/es/que-hacemos/motor-verde/",
        "region_hint": "Privada / RSC España",
    },
    {
        "id": "priv-web-santander",
        "fuente": "FUNDACION_PRIVADA",
        "tipo_oportunidad": "CONVOCATORIA_PRIVADA",
        "nombre": "Fundación Banco Santander (Acción Sostenible)",
        "url": "https://www.fundacionbancosantander.com/es/inicio",
        "region_hint": "Privada / RSC España",
    },
    {
        "id": "priv-web-bbva",
        "fuente": "FUNDACION_PRIVADA",
        "tipo_oportunidad": "CONVOCATORIA_PRIVADA",
        "nombre": "Fundación BBVA (Ayudas Ecología y Conservación)",
        "url": "https://www.fbbva.es/",
        "region_hint": "Privada / RSC España",
    },
    {
        "id": "priv-web-biodiversidad",
        "fuente": "FUNDACION_BIODIVERSIDAD",
        "tipo_oportunidad": "SUBVENCION",
        "nombre": "Fundación Biodiversidad F.S.P. (MITECO)",
        "url": "https://fundacion-biodiversidad.es/fb_en_los_medios/convocatorias",
        "region_hint": "ES - España",
    },
    {
        "id": "priv-web-iberdrola",
        "fuente": "FUNDACION_PRIVADA",
        "tipo_oportunidad": "CONVOCATORIA_PRIVADA",
        "nombre": "Fundación Iberdrola España (Biodiversidad)",
        "url": "https://www.fundacioniberdrolaespana.org/",
        "region_hint": "Privada / RSC España",
    },
    {
        "id": "priv-web-endesa",
        "fuente": "FUNDACION_PRIVADA",
        "tipo_oportunidad": "CONVOCATORIA_PRIVADA",
        "nombre": "Fundación Endesa (Biodiversidad y Renaturalización)",
        "url": "https://www.fundacionendesa.org/es/biodiversidad",
        "region_hint": "Privada / RSC España",
    },
    {
        "id": "priv-web-afundacion",
        "fuente": "FUNDACION_PRIVADA",
        "tipo_oportunidad": "CONVOCATORIA_PRIVADA",
        "nombre": "Obra Social ABANCA / Afundación",
        "url": "https://www.afundacion.org/",
        "region_hint": "Privada / RSC España",
    },
    {
        "id": "priv-web-eoca",
        "fuente": "FUNDACION_PRIVADA",
        "tipo_oportunidad": "CONVOCATORIA_PRIVADA",
        "nombre": "EOCA (European Outdoor Conservation Association)",
        "url": "https://www.outdoorconservation.eu/",
        "region_hint": "Privada / RSC España",
    },
    {
        "id": "priv-web-onetreeplanted",
        "fuente": "FUNDACION_PRIVADA",
        "tipo_oportunidad": "CONVOCATORIA_PRIVADA",
        "nombre": "One Tree Planted & 1% for the Planet",
        "url": "https://onetreeplanted.org/",
        "region_hint": "Privada / RSC España",
    },
]

_HTML_RELEVANT_CUE_RE = re.compile(
    r"(?:subvenci[oó]n|subvencions|ayuda|axuda|ajut|diru-laguntza|convocatoria|"
    r"beca|grant|call|licitaci[oó]n|contrato|orden\b|orde\b|resoluci[oó]n|decreto|"
    r"reforest|forestal|repoblaci|incendio|lume|incendi|biodivers|natura\s*2000|"
    r"medio\s*ambiente|medi\s*ambient|bosque|monte|carbono|ribera|"
    r"restauraci[oó]n|custodia|\.pdf\b)",
    re.IGNORECASE,
)

_HTML_CALL_ACTION_CUE_RE = re.compile(
    r"(?:subvenci[oó]n|subvencions|ayuda|axuda|ajut|diru-laguntza|convocatoria|"
    r"bases\b|solicitud|beca|grant|call|licitaci[oó]n|contrato|orden\b|orde\b|"
    r"resoluci[oó]n|decreto|financiaci[oó]n|\.pdf\b)",
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
    r"generaci[oó]n\s+y\s+gesti[oó]n\s+del\s+conocimiento|estudio\s+complementario)",
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
        self._in_anchor = False
        self._anchor_href = ""
        self._anchor_chunks: list[str] = []
        self._in_heading = False
        self._heading_chunks: list[str] = []
        self._last_heading = ""
        self._block_chunks: list[str] = []
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

        if t == "link":
            rel = attr_map.get("rel", "").lower()
            ctype = attr_map.get("type", "").lower()
            href = attr_map.get("href", "").strip()
            if href and "alternate" in rel and ("rss" in ctype or "atom" in ctype or "xml" in ctype):
                self.rss_links.append(href)
            return

        if t in self._BLOCK_TAGS:
            if self._block_depth == 0:
                self._block_chunks = []
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
            if heading:
                self._last_heading = heading[:180]
        if t == "a" and self._in_anchor:
            self._in_anchor = False
            a_text = re.sub(r"\s+", " ", " ".join(self._anchor_chunks)).strip()
            ctx = re.sub(r"\s+", " ", " ".join(self._block_chunks)).strip()
            if not ctx and self._last_heading:
                ctx = self._last_heading
            elif self._last_heading and self._last_heading not in ctx:
                ctx = f"{self._last_heading}. {ctx}"
            if self._anchor_href:
                self.anchors.append((self._anchor_href, a_text[:260], ctx[:360]))
        if t in self._BLOCK_TAGS and self._block_depth > 0:
            self._block_depth -= 1
            if self._block_depth == 0:
                self._block_chunks = []

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        txt = data.strip()
        if not txt:
            return
        if self._block_depth > 0:
            self._block_chunks.append(txt)
        if self._in_heading:
            self._heading_chunks.append(txt)
        if self._in_anchor:
            self._anchor_chunks.append(txt)


def parse_rss_or_atom_xml(xml_text: str, source_cfg: dict[str, Any]) -> list[RawCandidate]:
    """
    Namespace-agnostic parser supporting RSS 2.0 (<item>), RDF/RSS 1.0 (<item>) and Atom 1.0 (<entry>).
    """
    items_out: list[RawCandidate] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    seen_keys: set[str] = set()
    entries = [el for el in root.iter() if _local_tag(el.tag) in ("item", "entry")][:60]
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
        low_href = href.lower().strip()
        if not low_href or low_href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        abs_url = urljoin(base_url, href)
        if abs_url in seen_urls:
            continue

        is_pdf = _is_pdf_link(abs_url)
        if len(a_text.strip()) < 12 and not is_pdf:
            continue

        combined = f"{a_text} {ctx}".strip()
        if len(combined) < 18 or _HTML_NOISE_CUE_RE.search(combined) or _HTML_NOISE_CUE_RE.search(low_href):
            continue
        if not _HTML_RELEVANT_CUE_RE.search(combined) and not is_pdf:
            continue
        if not _HTML_CALL_ACTION_CUE_RE.search(f"{a_text} {low_href}") and not is_pdf:
            continue

        clean_title = a_text if len(a_text) >= 18 else (ctx[:200] or a_text)
        if is_pdf and len(clean_title) < 24 and ctx:
            clean_title = ctx[:200]
        norm_t = re.sub(r"\s+", " ", clean_title.lower()).strip()
        if norm_t in seen_titles:
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


async def poll_web_source(
    client: httpx.AsyncClient,
    source_cfg: dict[str, Any],
) -> list[RawCandidate]:
    """
    Unified poller for RSS, Atom, or HTML official bulletin / private foundation pages.
    If an HTML portal declares <link rel="alternate" type="application/rss+xml">, also follows it.
    """
    try:
        resp = await client.get(source_cfg["url"])
        if resp.status_code != 200 or not resp.text.strip():
            return []
        stripped = resp.text.lstrip()
        lower_head = stripped[:400].lower()

        is_xml_feed = (
            "<rss" in lower_head
            or "<feed" in lower_head
            or "<rdf:rdf" in lower_head
            or ("<?xml" in lower_head and "<html" not in lower_head)
        )
        if is_xml_feed:
            return parse_rss_or_atom_xml(resp.text, source_cfg)

        html_cands, rss_urls = extract_candidates_from_html(
            resp.text,
            source_cfg=source_cfg,
            base_url=str(resp.url),
        )
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
    Follow an extract's linked official PDF when candidate text is short (< 900 chars),
    extract full regulatory text/CPVs/budgets/deadlines with OCR fallback, and enrich candidate.
    """
    if cand.fuente == "FUENTES_PDF" or len(cand.texto or "") >= 900:
        return False
    pdf_url = _candidate_linked_pdf_url(cand)
    if not pdf_url:
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
