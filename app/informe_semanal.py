"""Informe semanal de nuevas convocatorias en HTML autocontenido (sin dependencias externas)."""
from __future__ import annotations

import html
import re
from datetime import date, datetime
from urllib.parse import urlparse

MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def fecha_corta(iso: str | None) -> str:
    if not iso:
        return "—"
    d = datetime.strptime(iso[:10], "%Y-%m-%d")
    return f"{d.day} {MESES[d.month - 1]} {d.year}"


def euros(n: float) -> str:
    return f"{n:,.0f} €".replace(",", ".")


def limpiar_organismo(org: str) -> str:
    t = re.sub(r"^\s*(AUTONOMICA|AUTONÓMICA|LOCAL|ESTADO|OTROS|PROVINCIAL|MUNICIPAL)\s*-\s*", "", org or "")
    letras = re.sub(r"[^A-Za-zÀ-ÿ]", "", t)
    mayus = len(re.sub(r"[^A-ZÀ-Þ]", "", letras))
    if letras and mayus / len(letras) > 0.7:
        t = t.title()
    return re.sub(r"\s+", " ", t).strip()


def sin_plazo(c: dict) -> bool:
    """Abierta sin fecha de cierre real: el backend rellena una fecha ficticia y 0 días (misma regla que la web)."""
    pl = c.get("plazos") or {}
    vigente = c.get("estado") != "CERRADA"
    return vigente and (pl.get("urgencia") == "abierta_pendiente_plazo" or (pl.get("fecha_fin_solicitud") is None and c.get("diasRestantes", 0) <= 0))


def es_licitacion(c: dict) -> bool:
    return bool(re.match(r"^(ted|placsp)[-\s]", c["id"], re.I) or re.match(r"^(TED|PLACSP)\b", c.get("codigoOficial", ""), re.I))


def importe(c: dict) -> str:
    n = c.get("cuantiaMaximaProyecto") or 0
    if es_licitacion(c):
        return f"Licitación · {euros(n)}" if n > 0 else "Licitación · importe no publicado"
    return euros(n) if n > 0 else "Según bases"


def enlace(c: dict) -> str:
    def concreta(u: str | None) -> bool:
        if not u:
            return False
        return len(urlparse(u).path.rstrip("/")) > 1

    for u in (c.get("fuenteUrl"), c.get("urlSedeElectronica"), c.get("urlBasesPdf")):
        if concreta(u):
            return u
    return c.get("fuenteUrl") or c.get("urlSedeElectronica") or c.get("urlBasesPdf") or ""


def cierre(c: dict) -> str:
    if c.get("estado") == "PROXIMA":
        ini = (c.get("plazos") or {}).get("fecha_inicio_solicitud")
        return f"Abre {fecha_corta(ini)} · cierra {fecha_corta(c['fechaCierre'])}" if ini else f"Por abrir · cierra {fecha_corta(c['fechaCierre'])}"
    if sin_plazo(c):
        return "Sin plazo publicado"
    return f"{fecha_corta(c['fechaCierre'])} · {c['diasRestantes']} d"


CODIGOS = {
    "ONG_FUNDACIONES": "ONG y fundaciones", "AYUNTAMIENTO": "ayuntamientos", "COMUNIDAD_MONTES": "comunidades de montes",
    "EMPRESA_PYME": "pymes", "EMPRESA": "empresas", "UNIVERSIDAD": "universidades", "PERSONA_FISICA": "personas físicas",
}
TEMAS = {
    "prevencion_incendios": "prevención de incendios", "reforestacion": "reforestación", "restauracion_ecologica": "restauración ecológica",
    "educacion_ambiental": "educación ambiental", "custodia_territorio": "custodia del territorio",
    "conservacion_habitats": "conservación de hábitats", "absorcion_carbono": "absorción de carbono", "investigacion_ambiental": "investigación ambiental",
}


def humanizar(t: str) -> str:
    for k, v in CODIGOS.items():
        t = t.replace(k, v)
    for k, v in TEMAS.items():
        t = t.replace(k, v)
    t = re.sub(r"\b[A-Z]{3,}(?:_[A-Z]+)+\b", lambda m: m.group(0).lower().replace("_", " "), t)
    return re.sub(r"\b[a-z]+(?:_[a-z]+)+\b", lambda m: m.group(0).replace("_", " "), t)


def limpiar_justificacion(t: str) -> str:
    t = re.sub(r"^\s*(\[[^\]]+\]\s*)+", "", t)
    m = re.search(r"actuaciones de (.+?) promovidas por", t, re.I)
    if m:
        t = f"Aborda directamente: {m.group(1)}."
    t = re.sub(r"^Aprobada como [A-Za-z_ ]+:\s*", "", t)
    return humanizar(t).strip()


def titulo_limpio(t: str) -> str:
    return re.sub(r"\s*\[UE - Traducido del ingl[eé]s\]", "", t).strip()


def por_que(c: dict) -> str:
    """Una línea con el motivo de la recomendación (sin citas literales largas)."""
    for t in c.get("citasBasesJustificacion") or []:
        t = re.sub(r"\s+", " ", limpiar_justificacion(t)).strip()
        if t and not t.startswith(("«", '"', "“")):
            t = t[0].upper() + t[1:]
            return t if len(t) <= 150 else t[:150].rsplit(" ", 1)[0].rstrip(",;: ") + "…"
    return ""


def dominio(u: str) -> str:
    return urlparse(u).netloc.replace("www.", "") if u else ""


def fila(c: dict, modo: str) -> str:
    """modo: 'plazo' (cierre) o 'apertura' (fecha de apertura)."""
    h = html.escape
    url = enlace(c)
    etiqueta = '<span class="tag">Licitación</span>' if es_licitacion(c) else ""
    motivo = por_que(c) if modo != "apertura" else ""  # en las próximas aperturas se omite para no alargar el informe
    if modo == "apertura":
        ini = (c.get("plazos") or {}).get("fecha_inicio_solicitud")
        fecha = f'<b>{h(fecha_corta(ini))}</b><span>cierra {h(fecha_corta(c["fechaCierre"]))}</span>'
    elif sin_plazo(c):
        fecha = "<b>Sin plazo publicado</b>"
    else:
        dias = c.get("diasRestantes", 0)
        clase = "urg" if dias <= 7 else ""
        fecha = f'<b class="{clase}">{h(fecha_corta(c["fechaCierre"]))}</b><span>{dias} días</span>'
    enlace_html = f'<a class="btn" href="{h(url)}">Convocatoria oficial</a><span class="dom">{h(dominio(url))}</span>' if url else ""
    return (
        "<tr>"
        f'<td class="t"><strong>{h(titulo_limpio(c["titulo"]))}</strong> {etiqueta}<span class="org">{h(limpiar_organismo(c["organismo"]))}</span>'
        + (f'<span class="why">{h(motivo)}</span>' if motivo else "")
        + "</td>"
        f'<td class="n">{h(importe(c))}</td>'
        f'<td class="f">{fecha}</td>'
        f'<td class="n"><b>{c.get("matchingGlobal", 0)}%</b></td>'
        f'<td class="l">{enlace_html}</td>'
        "</tr>"
    )


def tabla(titulo: str, subtitulo: str, lista: list[dict], modo: str = "plazo", destacada: bool = False) -> str:
    if not lista:
        return ""
    cab = "Apertura" if modo == "apertura" else "Cierre"
    filas = "".join(fila(c, modo) for c in lista)
    clase = "destacada" if destacada else ""
    return (
        f'<section class="{clase}"><h2>{html.escape(titulo)} <span>{len(lista)}</span></h2><p class="sub">{html.escape(subtitulo)}</p>'
        f'<table><thead><tr><th>Convocatoria</th><th>Importe</th><th>{cab}</th><th>Afinidad</th><th>Enlace</th></tr></thead>'
        f"<tbody>{filas}</tbody></table></section>"
    )


def construir(nuevas: list[dict], desde: date, hasta: date) -> str:
    def clave(c: dict):
        return ("9999" if sin_plazo(c) else c["fechaCierre"] or "9999", -c.get("matchingGlobal", 0))

    aptas = [c for c in nuevas if c["elegible"]]
    excluidas = [c for c in nuevas if not c["elegible"]]
    abren = sorted(
        [c for c in aptas if c.get("estado") == "PROXIMA"],
        key=lambda c: ((c.get("plazos") or {}).get("fecha_inicio_solicitud") or "9999", -c.get("matchingGlobal", 0)),
    )
    abiertas = [c for c in aptas if c.get("estado") != "PROXIMA"]
    urgentes = sorted([c for c in abiertas if not sin_plazo(c) and c.get("diasRestantes", 9999) <= 14], key=clave)
    ids_urg = {c["id"] for c in urgentes}
    resto = sorted([c for c in abiertas if c["id"] not in ids_urg], key=clave)

    ayudas = [c for c in aptas if not es_licitacion(c)]
    fondos = sum((c.get("cuantiaMaximaProyecto") or 0) for c in ayudas)
    proximo = min((c for c in abiertas if not sin_plazo(c)), key=lambda c: c["diasRestantes"], default=None)
    rango = f"{fecha_corta(desde.isoformat())} – {fecha_corta(hasta.isoformat())}"

    kpis = [
        (len(nuevas), "convocatorias nuevas"),
        (len(aptas), "aptas para Reforesta"),
        (len(urgentes), "con cierre en 14 días o menos"),
        (euros(fondos) if fondos else "—", "importe máximo de las ayudas aptas"),
    ]
    kpi_html = "".join(f'<div><b>{html.escape(str(v))}</b><span>{html.escape(t)}</span></div>' for v, t in kpis)

    if not nuevas:
        resumen = "Esta semana no se ha publicado ninguna convocatoria nueva."
    else:
        partes = [f"Se han detectado <b>{len(nuevas)}</b> convocatorias nuevas, <b>{len(aptas)}</b> aptas para Reforesta"]
        if urgentes:
            u = urgentes[0]
            partes.append(f"La más urgente cierra el <b>{html.escape(fecha_corta(u['fechaCierre']))}</b> ({u['diasRestantes']} días): {html.escape(titulo_limpio(u['titulo'])[:90].rstrip(' .'))}")
        if abren:
            partes.append(f"<b>{len(abren)}</b> confirmadas abrirán plazo en los próximos meses")
        resumen = ". ".join(partes) + "."
    vacio = '<p class="vacio">No se ha publicado ninguna convocatoria nueva en este periodo.</p>' if not nuevas else ""
    nota_excl = (
        f'<p class="nota">Además se han detectado <b>{len(excluidas)}</b> convocatorias que no son aptas para Reforesta por sus bases; no se detallan.</p>'
        if excluidas
        else ""
    )

    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Informe semanal de convocatorias · Reforesta · {fecha_corta(hasta.isoformat())}</title>
<style>
@page{{size:A4;margin:14mm 12mm 16mm}}
:root{{--verde:#6aa43a;--verde-osc:#3f6a2c;--oscuro:#1c1c1c;--papel:#f7f5f0;--linea:#e3dfd2;--texto:#27272a;--suave:#6b6b73;--rojo:#c1243c}}
*{{box-sizing:border-box;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
body{{margin:0;background:var(--papel);color:var(--texto);font:13px/1.45 "Open Sans",Helvetica,Arial,sans-serif}}
header{{background:var(--oscuro);color:#fff;padding:20px 28px;border-bottom:4px solid var(--verde)}}
header .marca{{color:var(--verde);letter-spacing:.3em;font-weight:700;font-size:12px}}
header h1{{margin:6px 0 2px;font:700 24px Georgia,serif}}header p{{margin:0;color:#cfcfcf;font-size:12.5px}}
main{{max-width:1000px;margin:0 auto;padding:20px 28px 36px}}
.resumen{{font-size:14.5px;margin:0 0 16px;line-height:1.55}}
.kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--linea);border:1px solid var(--linea);margin-bottom:22px}}
.kpis div{{background:#fff;padding:12px 14px}}.kpis b{{display:block;font:700 24px Georgia,serif}}.kpis span{{font-size:11px;color:var(--suave)}}
section{{margin-bottom:22px}}h2{{font:700 17px Georgia,serif;margin:0 0 1px}}h2 span{{font:600 12px Helvetica,Arial;color:var(--suave);margin-left:6px}}
.sub{{margin:0 0 8px;color:var(--suave);font-size:12px}}
section.destacada h2{{color:var(--rojo)}}section.destacada table{{border-top:3px solid var(--rojo)}}
table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--linea)}}
th{{text-align:left;font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:var(--suave);padding:7px 10px;border-bottom:1px solid var(--linea);background:#fbfaf6}}
td{{padding:9px 10px;border-bottom:1px dotted var(--linea);vertical-align:top;font-size:12.5px}}tr:last-child td{{border-bottom:0}}
tr{{break-inside:avoid;page-break-inside:avoid}}
td.t{{width:50%}}td.n{{white-space:nowrap}}td.f b{{display:block}}td.f span{{color:var(--suave);font-size:11.5px}}td.f b.urg{{color:var(--rojo)}}
td.l{{white-space:nowrap}}.dom{{display:block;color:var(--suave);font-size:10.5px;margin-top:3px}}
.org{{display:block;color:var(--suave);font-size:11.5px;margin-top:2px}}.why{{display:block;color:#4b5563;font-size:11.5px;margin-top:4px;border-left:2px solid var(--verde);padding-left:7px}}
.tag{{display:inline-block;background:#eef3e6;color:var(--verde-osc);font:700 9.5px Helvetica,Arial;letter-spacing:.06em;text-transform:uppercase;padding:2px 6px;border-radius:99px;vertical-align:middle}}
.btn{{display:inline-block;background:var(--verde);color:#fff;text-decoration:none;font:700 10px Helvetica,Arial;text-transform:uppercase;letter-spacing:.06em;padding:6px 11px;border-radius:99px}}
.nota{{color:var(--suave);font-size:12px}}.vacio{{padding:26px;text-align:center;color:var(--suave);background:#fff;border:1px dashed var(--linea)}}
footer{{color:var(--suave);font-size:10.5px;border-top:1px solid var(--linea);padding-top:12px;margin-top:8px}}
@media print{{body{{background:#fff}}main{{padding:14px 0 0;max-width:none}}header{{padding:16px 22px}}}}
@media(max-width:720px){{.kpis{{grid-template-columns:1fr 1fr}}main{{padding:14px}}}}
</style></head><body>
<header><div class="marca">REFORESTA · RADAR DE FINANCIACIÓN</div><h1>Nuevas convocatorias de la semana</h1><p>Del {rango} · generado el {fecha_corta(hasta.isoformat())}</p></header>
<main>
<p class="resumen">{resumen}</p>
<div class="kpis">{kpi_html}</div>
{vacio}
{tabla("Para actuar esta semana", "Cierran en 14 días o menos. Ordenadas por fecha de cierre.", urgentes, "plazo", True)}
{tabla("Abiertas", "Plazo abierto ahora. Las de plazo más cercano, primero.", resto)}
{tabla("Próximas aperturas", "Confirmadas, con el plazo de solicitud todavía sin abrir. Ordenadas por fecha de apertura.", abren, "apertura")}
{nota_excl}
<footer>Informe generado automáticamente por el Radar de Reforesta a partir de BDNS, BOE, TED/PLACSP, UE y fundaciones. La afinidad es una estimación. Compruebe siempre las bases en la convocatoria oficial antes de preparar una solicitud.</footer>
</main></body></html>"""


def nuevas_desde(convocatorias: list[dict], desde: date) -> list[dict]:
    """Convocatorias abiertas o por abrir publicadas desde la fecha dada."""
    return [c for c in convocatorias if c.get("fechaPublicacion") and c["fechaPublicacion"][:10] >= desde.isoformat()]
