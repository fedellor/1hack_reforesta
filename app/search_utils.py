"""Utilidades de búsqueda normalizada, tolerante a tildes/guiones y sinónimos españoles."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

_STOPWORDS_ES = {
    "a", "al", "con", "de", "del", "e", "el", "en", "la", "las", "lo", "los",
    "o", "para", "por", "su", "sus", "u", "un", "una", "unas", "unos", "y",
}

_GRUPOS_EQUIVALENTES: list[list[str]] = [
    [
        "miteco",
        "ministerio para la transicion ecologica",
        "transicion ecologica y el reto demografico",
        "orden ted",
        "secretaria de estado de medio ambiente",
        "direccion general de biodiversidad bosques y desertificacion",
        "magrama",
        "mapama",
    ],
    ["oapn", "organismo autonomo parques nacionales"],
    ["pepac", "plan estrategico de la pac", "feader"],
    ["prtr", "nextgeneration", "next generation", "plan de recuperacion transformacion y resiliencia", "mrr"],
    ["placsp", "perfil del contratante", "contratacion del sector publico"],
    ["boe", "boletin oficial del estado"],
    ["bocm", "boletin oficial de la comunidad de madrid"],
    ["xunta", "xunta de galicia"],
    ["jcyl", "junta de castilla y leon"],
    ["jccm", "junta de comunidades de castilla la mancha"],
    ["gva", "generalitat valenciana", "comunitat valenciana"],
    ["dga", "gobierno de aragon"],
    ["ue", "union europea", "europa", "europea", "programa life", "horizon europe", "interreg", "feder"],
    ["anticipo", "pago anticipado", "sin aval"],
    ["incendios", "incendio", "postincendio", "post incendio", "cortafuegos"],
    ["selvicultura", "silvicultura", "selvicola", "silvicola"],
    ["cataluna", "catalunya"],
    ["illes balears", "islas baleares", "baleares"],
    ["pais vasco", "euskadi"],
    ["aei", "agencia estatal de investigacion"],
    ["fbbva", "fundacion bbva"],
]

_EXPANSIONES_ORIGEN: dict[str, list[str]] = {
    "ong": ["ong", "esal", "sin animo de lucro", "tercer sector", "utilidad publica", "asociacion", "fundacion"],
    "esal": ["esal", "ong", "sin animo de lucro", "tercer sector", "utilidad publica", "asociacion", "fundacion"],
    "tercer sector": ["tercer sector", "sin animo de lucro", "ong", "esal", "utilidad publica"],
    "fb": ["fb", "fundacion biodiversidad"],
    "empleaverde": ["empleaverde", "fundacion biodiversidad"],
    "pleamar": ["pleamar", "fundacion biodiversidad"],
    "cam": ["cam", "comunidad de madrid", "bocm"],
    "galicia": ["galicia", "xunta"],
    "aragon": ["aragon", "dga", "gobierno de aragon"],
    "valenciana": ["valenciana", "comunitat valenciana", "comunidad valenciana", "gva", "generalitat valenciana"],
    "valencia": ["valencia", "comunitat valenciana", "comunidad valenciana", "gva", "generalitat valenciana"],
    "reforestacion": ["reforest", "repobl", "plantacion", "restauracion forestal", "selvic", "silvic", "masas forestales"],
    "reforestar": ["reforest", "repobl", "plantacion", "restauracion forestal", "selvic", "silvic"],
    "repoblacion": ["repobl", "reforest", "restauracion forestal"],
    "licitacion": ["licita", "placsp", "contrato"],
    "licitaciones": ["licita", "placsp", "contrato"],
    "subvencion": ["subvenc", "bdns", "ayuda"],
    "subvenciones": ["subvenc", "bdns", "ayuda"],
    "estatal": ["estatal", "nacional", "administracion general del estado"],
    "100%": ["100%", "sin cofinanciacion", "financiado al 100"],
}


def normalize_search_text(text: str | None) -> str:
    """Elimina tildes, pasa a minúsculas y unifica separadores a espacios simples."""
    if not text:
        return ""
    nfd = unicodedata.normalize("NFD", str(text))
    sin_tildes = "".join(ch for ch in nfd if unicodedata.category(ch) != "Mn").lower()
    cleaned = re.sub(r"[^a-z0-9%]+", " ", sin_tildes)
    return re.sub(r"\s+", " ", cleaned).strip()


def _tokenize_query(query: str) -> list[str]:
    norm = normalize_search_text(query)
    if not norm:
        return []
    raw = [t for t in norm.split(" ") if t]
    meaningful = [t for t in raw if (t not in _STOPWORDS_ES) or (len(raw) == 1)]
    return meaningful if meaningful else raw


def _token_variants(token: str) -> list[str]:
    out = [token]
    if len(token) >= 6 and token.endswith("es"):
        out.append(token[:-2])
    if len(token) >= 5 and token.endswith("s") and not token.endswith("es"):
        out.append(token[:-1])
    for pref in ("reforest", "repobl", "subvenc", "licita"):
        if token.startswith(pref) and len(token) >= len(pref):
            out.append(pref)
    if token.startswith(("selvic", "silvic")):
        out.extend(["selvic", "silvic"])
    return list(dict.fromkeys(out))


def _expand_token(token: str, query_norm: str) -> list[str]:
    variants = _token_variants(token)
    syns: list[str] = []
    for v in variants:
        if v in _EXPANSIONES_ORIGEN:
            syns.extend(_EXPANSIONES_ORIGEN[v])
    if query_norm in _EXPANSIONES_ORIGEN:
        syns.extend(_EXPANSIONES_ORIGEN[query_norm])
    for group in _GRUPOS_EQUIVALENTES:
        matched = False
        for phrase in group:
            if len(phrase) <= 3:
                if phrase in variants or query_norm == phrase:
                    matched = True
                    break
            elif " " in phrase:
                if phrase in query_norm:
                    matched = True
                    break
            elif phrase in variants:
                matched = True
                break
        if matched:
            syns.extend(group)
    return list(dict.fromkeys([*variants, *syns]))


def _matches_term(text: str, words: set[str], term: str, compact: str | None = None) -> bool:
    if not term:
        return False
    if len(term) <= 3:
        return term in words
    if term in text:
        return True
    if compact and len(term) >= 5 and term.replace(" ", "") in compact:
        return True
    return False


def score_convocatoria_dict(conv: dict[str, Any], query: str | None) -> int:
    """Devuelve relevancia > 0 si todos los términos coinciden, o 0 si no encaja."""
    query_norm = normalize_search_text(query)
    if not query_norm:
        return 1
    tokens = _tokenize_query(query or "")
    if not tokens:
        return 1

    meta_extra: list[str] = []
    if conv.get("porcentajeCofinanciacion") == 0:
        meta_extra.append("100% financiado sin cofinanciacion")
    if conv.get("modalidadPago") == "anticipo" or conv.get("pagoAnticipadoSinAval"):
        meta_extra.append("anticipo pago anticipado sin aval")
    cid = str(conv.get("id") or "")
    if cid.startswith("bdns-"):
        meta_extra.append("bdns subvencion ayudas")
    if cid.startswith("placsp-"):
        meta_extra.append("placsp licitacion contrato publico perfil del contratante")
    if str(conv.get("ambitoTerritorial") or "").lower() == "estatal":
        meta_extra.append("estatal nacional administracion general del estado")

    codigo = normalize_search_text(f"{conv.get('codigoOficial', '')} {cid}")
    codigo_compacto = codigo.replace(" ", "")
    titulo = normalize_search_text(
        f"{conv.get('titulo') or ''} {conv.get('tituloOriginal') or ''}"
    )
    organismo = normalize_search_text(conv.get("organismo"))
    territorio = normalize_search_text(
        " ".join(
            str(x)
            for x in [
                conv.get("ambitoTerritorial") or "",
                conv.get("provincia") or "",
                conv.get("ccaaCodigo") or "",
                conv.get("nivelTerritorial") or "",
                conv.get("anio") or "",
                str(conv.get("fechaCierre") or "")[:4],
                conv.get("estado") or "",
                str(conv.get("tipoFuente") or "").replace("_", " "),
            ]
        )
    )
    detalles = normalize_search_text(
        " ".join(
            [
                str(conv.get("orografiaPendiente") or ""),
                str(conv.get("motivoElegibilidad") or ""),
                *(conv.get("accionesSubvencionables") or []),
                *(conv.get("citasBasesJustificacion") or []),
            ]
        )
    )
    fondo = normalize_search_text(
        " ".join(
            [
                str(conv.get("resumenEjecutivo") or ""),
                *(conv.get("requisitosSolvencia") or []),
                *(conv.get("gastosNoSubvencionables") or []),
                str(conv.get("urlBasesPdf") or ""),
                str(conv.get("fuenteUrl") or ""),
                *meta_extra,
            ]
        )
    )

    cod_w = set(codigo.split())
    tit_w = set(titulo.split())
    org_w = set(organismo.split())
    ter_w = set(territorio.split())
    det_w = set(detalles.split())
    fon_w = set(fondo.split())

    score = 0
    if query_norm in codigo or query_norm.replace(" ", "") in codigo_compacto:
        score += 140
    if query_norm in titulo:
        score += 110
    elif query_norm in organismo:
        score += 80

    for tok in tokens:
        exact_vars = set(_token_variants(tok))
        candidates = _expand_token(tok, query_norm)
        hit = False
        best_tok = 0
        for cand in candidates:
            factor = 1.0 if cand in exact_vars else 0.72
            if _matches_term(codigo, cod_w, cand, codigo_compacto):
                hit = True
                best_tok = max(best_tok, round(65 * factor))
            if _matches_term(titulo, tit_w, cand):
                hit = True
                best_tok = max(best_tok, round(50 * factor))
            if _matches_term(organismo, org_w, cand):
                hit = True
                best_tok = max(best_tok, round(40 * factor))
            if _matches_term(territorio, ter_w, cand):
                hit = True
                best_tok = max(best_tok, round(32 * factor))
            if _matches_term(detalles, det_w, cand):
                hit = True
                best_tok = max(best_tok, round(20 * factor))
            if _matches_term(fondo, fon_w, cand):
                hit = True
                best_tok = max(best_tok, round(12 * factor))
        if not hit:
            return 0
        score += best_tok

    estado = str(conv.get("estado") or "")
    if estado == "ACTIVA":
        score += 6
    elif estado == "PROXIMA":
        score += 3
    if conv.get("elegible"):
        score += 3
    return max(1, score)
