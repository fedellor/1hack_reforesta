"""FastAPI Application for 1hack_reforesta — Radar Vivo de Oportunidades de Reforestación e Incendios."""
import asyncio
from contextlib import asynccontextmanager, suppress
from datetime import date, datetime, timezone
from typing import Any
from fastapi import Depends, FastAPI, File, Header, HTTPException, Query, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path
from sqlalchemy import func, or_
from sqlmodel import Session, select
from app.config import FUENTES_DIR, settings
from app.database import engine, get_session, init_db, query_cache
from app.domain.reforesta_profile import get_reforesta_profile
from app.geo import CCAA_CATALOG
from app.ingestors.fuentes_local import pdf_doc_to_candidate
from app.ingestors.live_connectors import SOURCES_REGISTRY
from app.ingestors.runner import (
    background_live_sync_daemon,
    ensure_initial_seed,
    refresh_live_database_states,
    run_full_ingestion,
    seconds_until_next_daily_sync,
)
from app.models import (
    AnalyzeTextRequest,
    IngestionRun,
    Opportunity,
    UpdateEstadoInternoRequest,
)
from app.pipeline.orchestrator import RawCandidate, process_candidate
from app.pipeline.pdf_extractor import extract_pdf_from_bytes
from app.pipeline.predictive_and_export import (
    build_predictive_calendar,
    export_opportunities_csv,
    export_opportunities_ics,
    export_opportunity_markdown,
)

# Global lock to prevent concurrent ingestion runs from colliding
_INGEST_LOCK = asyncio.Lock()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Initialize DB tables, seed dataset, and launch the live background sync daemon."""
    init_db()
    with Session(engine) as session:
        ensure_initial_seed(session)

    bg_task: asyncio.Task[None] | None = None
    if settings.auto_sync_enabled:
        bg_task = asyncio.create_task(background_live_sync_daemon())
    try:
        yield
    finally:
        if bg_task:
            bg_task.cancel()
            with suppress(asyncio.CancelledError):
                await bg_task


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Backend API en tiempo real para centralizar subvenciones, ayudas, licitaciones públicas, "
        "programas europeos (LIFE, Horizon, Interreg, FEADER) y convocatorias privadas/fundaciones "
        "de reforestación, gestión forestal y prevención/restauración de incendios en España (2020–2026)."
    ),
    lifespan=lifespan,
)

# Enable CORS for Frontend integration (roialtra) and GZip payload compression
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=500)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
@app.get("/radar", response_class=HTMLResponse, tags=["System"])
def live_backend_radar_inspector() -> HTMLResponse:
    """Self-contained live backend diagnostic inspector (usable without Frontend)."""
    html = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <title>1hack_reforesta — Inspector Vivo de Backend</title>
  <style>
    body { font-family: system-ui, -apple-system, sans-serif; margin: 24px auto; max-width: 1180px; padding: 0 16px; color: #162419; background: #f6f8f5; }
    h1 { margin: 0 0 6px; font-size: 1.5rem; }
    .sub { color: #475b4c; margin-bottom: 16px; font-size: 0.95rem; }
    .bar { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; margin-bottom: 18px; }
    button { background: #1f6f3d; color: #fff; border: 0; padding: 9px 14px; border-radius: 6px; cursor: pointer; font-weight: 600; }
    button.sec { background: #36493c; }
    button:disabled { opacity: 0.6; cursor: wait; }
    select { padding: 8px 10px; border-radius: 6px; border: 1px solid #c6d1c8; background: #fff; }
    .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(175px, 1fr)); gap: 12px; margin-bottom: 20px; }
    .card { background: #fff; border: 1px solid #dce5de; border-radius: 8px; padding: 12px; }
    .card b { display: block; font-size: 1.4rem; margin-top: 4px; color: #174e2b; }
    .panel { background: #fff; border: 1px solid #dce5de; border-radius: 8px; padding: 14px; margin-bottom: 18px; overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
    th, td { text-align: left; padding: 8px; border-bottom: 1px solid #ecf1ed; vertical-align: top; }
    th { color: #475b4c; font-weight: 600; }
    .tag { display: inline-block; padding: 2px 7px; border-radius: 4px; font-size: 0.78rem; font-weight: 600; background: #e8f3eb; color: #174e2b; }
    .links a { margin-right: 14px; color: #1f6f3d; font-weight: 600; text-decoration: none; }
    #status { font-size: 0.9rem; color: #1f6f3d; font-weight: 600; }
  </style>
</head>
<body>
  <h1>Inspector Vivo del Backend — 1hack_reforesta</h1>
  <div class="sub">Auditoría en tiempo real de conectores (BDNS, BOE, PLACSP, UE SEDIA, 19 CCAA, Fundaciones Privadas y <code>./fuentes/</code>).</div>
  <div class="bar">
    <button id="syncBtn" onclick="runLiveSync()">Sincronizar Fuentes en Vivo Ahora</button>
    <button class="sec" onclick="loadAll()">Refrescar Vista</button>
    <select id="fuenteFilter" onchange="loadOpps()">
      <option value="">Todas las fuentes</option>
      <option value="BDNS">BDNS</option>
      <option value="PLACSP">PLACSP (Licitaciones)</option>
      <option value="BOE">BOE</option>
      <option value="EU_SEDIA">UE (SEDIA / LIFE / Horizon)</option>
      <option value="BOLETIN_CCAA">Boletines CCAA</option>
      <option value="FUNDACION_PRIVADA">Fundaciones Privadas / RSC</option>
      <option value="FUNDACION_BIODIVERSIDAD">Fundación Biodiversidad</option>
      <option value="FUENTES_PDF">PDFs locales (./fuentes/)</option>
    </select>
    <select id="estadoFilter" onchange="loadOpps()">
      <option value="TODAS">Activas + Histórico</option>
      <option value="ACTIVA">Solo Activas</option>
      <option value="CERRADA">Solo Histórico (Cerradas)</option>
    </select>
    <span class="links"><a href="/docs" target="_blank">Swagger /docs</a><a href="/api/v1/export/csv" target="_blank">Descargar CSV</a></span>
    <span id="status"></span>
  </div>
  <div id="cards" class="cards"></div>
  <div class="panel"><strong>Última ejecución de ingesta y telemetría por conector</strong><pre id="runLog" style="font-size:0.82rem;white-space:pre-wrap;margin:8px 0 0;"></pre></div>
  <div class="panel">
    <strong>Oportunidades capturadas (<span id="oppCount">0</span>)</strong>
    <table><thead><tr><th>Fuente</th><th>Ubicación (España)</th><th>Plazos (Cierre / Días)</th><th>Dinero (Dotación / Máx.)</th><th>Score</th><th>Código & Título</th><th>Enlace</th></tr></thead><tbody id="tbody"></tbody></table>
  </div>
<script>
function el(tag, text) { const e = document.createElement(tag); if (text !== undefined) e.textContent = text; return e; }
async function loadSummary() {
  const [h, r, runs] = await Promise.all([
    fetch('/api/v1/health').then(x => x.json()),
    fetch('/api/v1/sources/registry').then(x => x.json()),
    fetch('/api/v1/ingest/runs?limit=1').then(x => x.json())
  ]);
  const cards = document.getElementById('cards');
  cards.innerHTML = '';
  const items = [
    ['Total en BD', h.counts.total_opportunities],
    ['Activas', h.counts.activas],
    ['Histórico', h.counts.historico_cerradas],
    ['Privadas / RSC', h.counts.convocatorias_privadas],
    ['Benchmark PDFs', h.golden_benchmark.passed ? 'OK (2/2)' : 'FAIL'],
    ['Tier LLM Juez', h.llm_judge_tier.replace(/_/g, ' ')]
  ];
  for (const [k, v] of items) { const c = el('div'); c.className = 'card'; c.appendChild(el('span', k)); c.appendChild(el('b', String(v))); cards.appendChild(c); }
  for (const [fn, cnt] of Object.entries(r.oportunidades_por_conector || {})) {
    const c = el('div'); c.className = 'card'; c.appendChild(el('span', 'Conector ' + fn)); c.appendChild(el('b', String(cnt))); cards.appendChild(c);
  }
  document.getElementById('runLog').textContent = JSON.stringify(runs.runs[0] || {}, null, 2);
}
async function loadOpps() {
  const f = document.getElementById('fuenteFilter').value;
  const est = document.getElementById('estadoFilter').value;
  const q = new URLSearchParams({ estado: est, limit: '60', sort_by: 'fecha_publicacion' });
  if (f) q.set('fuente', f);
  const data = await fetch('/api/v1/opportunities?' + q.toString()).then(x => x.json());
  const rows = f ? data.items.filter(i => i.metadatos_fuente.fuente_primaria === f) : data.items;
  document.getElementById('oppCount').textContent = rows.length + ' mostradas de ' + data.total;
  const tb = document.getElementById('tbody'); tb.innerHTML = '';
  for (const it of rows) {
    const tr = el('tr');
    const mf = it.metadatos_front || {};
    tr.appendChild(el('td')).appendChild(el('span', it.metadatos_fuente.fuente_primaria)).className = 'tag';
    tr.appendChild(el('td', (mf.ubicacion && mf.ubicacion.etiqueta_front) || (it.ambito_geografico.nivel + ' / ' + it.ambito_geografico.ccaa_codigo)));
    tr.appendChild(el('td', (mf.plazos && mf.plazos.etiqueta_front) || it.estado));
    tr.appendChild(el('td', (mf.dinero && mf.dinero.etiqueta_front) || 'Según bases'));
    tr.appendChild(el('td', it.priorizacion.nivel + ' (' + it.priorizacion.score + ')'));
    tr.appendChild(el('td', '[' + it.codigo_oficial + '] ' + it.titulo_limpio));
    const linkTd = el('td');
    if (it.enlaces.url_ficha_oficial) { const a = el('a', 'Abrir'); a.href = it.enlaces.url_ficha_oficial; a.target = '_blank'; linkTd.appendChild(a); }
    tr.appendChild(linkTd);
    tb.appendChild(tr);
  }
}
async function runLiveSync() {
  const btn = document.getElementById('syncBtn'); const st = document.getElementById('status');
  btn.disabled = true; st.textContent = 'Consultando BDNS, BOE, PLACSP, UE SEDIA, 19 CCAA y Fundaciones...';
  try {
    const res = await fetch('/api/v1/ingest/trigger?include_live_apis=true', { method: 'POST' }).then(x => x.json());
    st.textContent = 'Listo: escaneadas ' + res.total_scanned + ', aprobadas ' + res.accepted_layer2;
    await loadAll();
  } catch (e) { st.textContent = 'Error: ' + e; }
  finally { btn.disabled = false; }
}
async function loadAll() { await Promise.all([loadSummary(), loadOpps()]); }
loadAll();
</script>
</body>
</html>"""
    return HTMLResponse(content=html)


@app.get("/api/v1/health", tags=["System"])
def health_check(session: Session = Depends(get_session)) -> dict[str, Any]:
    """System status, WAL database metrics, LLM judge mode, and Golden Benchmark verification."""
    all_opps = session.exec(select(Opportunity)).all()
    activas = [o for o in all_opps if o.estado == "ACTIVA"]
    cerradas = [o for o in all_opps if o.estado == "CERRADA"]
    privadas = [o for o in all_opps if o.nivel_territorial == "PRIVADA"]
    municipales = [o for o in all_opps if o.nivel_territorial == "MUNICIPIO"]
    provinciales = [o for o in all_opps if o.nivel_territorial == "PROVINCIA"]
    ids = {o.id for o in all_opps}

    benchmark_miteco = "bdns-923290" in ids
    benchmark_madrid = "bocm-orden-1689-2026" in ids

    active_llm_tier = (
        "GEMINI_CLOUD"
        if settings.gemini_api_key.strip()
        else (
            "GROQ_CLOUD"
            if settings.groq_api_key.strip()
            else (
                "OPENROUTER_CLOUD"
                if settings.openrouter_api_key.strip()
                else ("PUBLIC_ZERO_KEY_LLM" if settings.enable_public_llm_fallback else "LOCAL_EXPERT_ENGINE_ZERO_DEPENDENCY")
            )
        )
    )

    _, next_sync_dt = seconds_until_next_daily_sync()
    return {
        "status": "ok",
        "version": settings.app_version,
        "database_engine": "postgresql" if "postgres" in settings.database_url else "sqlite_wal",
        "auto_sync_daemon_active": settings.auto_sync_enabled,
        "daily_sync_schedule": f"{settings.daily_sync_hour:02d}:{settings.daily_sync_minute:02d} {settings.daily_sync_timezone}",
        "next_daily_sync_at": next_sync_dt.isoformat(),
        "include_catalog_templates": settings.include_catalog_templates,
        "llm_judge_tier": active_llm_tier,
        "llm_model": settings.gemini_model,
        "counts": {
            "total_opportunities": len(all_opps),
            "activas": len(activas),
            "historico_cerradas": len(cerradas),
            "convocatorias_privadas": len(privadas),
            "concellos_ayuntamientos": len(municipales),
            "diputaciones_provincias": len(provinciales),
        },
        "golden_benchmark": {
            "passed": benchmark_miteco and benchmark_madrid,
            "miteco_bdns_923290_detected": benchmark_miteco,
            "madrid_orden_1689_2026_detected": benchmark_madrid,
        },
    }


@app.get("/api/convocatorias", tags=["Puente Directo Frontend (Next.js roialtra)"])
def get_frontend_convocatorias(
    estado: str | None = Query(default="ABIERTAS", description="ABIERTAS (ACTIVA+PROXIMA) | ACTIVA | PROXIMA | CERRADA | TODAS"),
    ccaa: str | None = Query(default=None, description="Filtrar por CCAA (ej. ES-MD, ES-GA)"),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """
    Plug-and-play endpoint consumed by Roi's Next.js Frontend (`frontend/src/services/api.ts`).
    Returns opportunities formatted directly into the TypeScript `Convocatoria` interface.
    """
    stmt = select(Opportunity)
    if estado and estado.upper() != "TODAS":
        if estado.upper() == "ABIERTAS":
            stmt = stmt.where(Opportunity.estado.in_(["ACTIVA", "PROXIMA"]))
        else:
            stmt = stmt.where(Opportunity.estado == estado.upper())
    if ccaa:
        ccaa_up = ccaa.upper()
        if ccaa_up not in ("ES", "EU"):
            stmt = stmt.where(Opportunity.ccaa_codigo.in_([ccaa_up, "ES", "EU"]))
        else:
            stmt = stmt.where(Opportunity.ccaa_codigo == ccaa_up)

    opps = list(session.exec(stmt).all())
    opps.sort(
        key=lambda o: (o.estado == "ACTIVA", o.prioridad_score or 0, o.relevancia_score or 0),
        reverse=True,
    )
    convocatorias = [o.to_frontend_convocatoria() for o in opps]
    return {
        "total": len(convocatorias),
        "convocatorias": convocatorias,
        "fuente": "backend_diego",
        "actualizadoAt": datetime.now(timezone.utc).isoformat(),
    }


@app.patch("/api/convocatorias/{opportunity_id}/estado", tags=["Puente Directo Frontend (Next.js roialtra)"])
@app.patch("/api/v1/opportunities/{opportunity_id}/estado", tags=["Motor de Priorización (Reforesta)"])
def update_opportunity_internal_state(
    opportunity_id: str,
    req: UpdateEstadoInternoRequest,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """Update the internal workflow state (`nueva` | `priorizada` | `en_preparacion` | `presentada` | `descartada`)."""
    valid_states = {"nueva", "priorizada", "en_preparacion", "presentada", "descartada"}
    new_state = req.estadoInterno.strip().lower()
    if new_state not in valid_states:
        raise HTTPException(
            status_code=400,
            detail=f"Estado interno inválido '{req.estadoInterno}'. Valores permitidos: {sorted(valid_states)}",
        )
    opp = session.get(Opportunity, opportunity_id)
    if not opp:
        opp = session.exec(
            select(Opportunity).where(Opportunity.codigo_oficial == opportunity_id.upper())
        ).first()
    if not opp:
        raise HTTPException(status_code=404, detail=f"Oportunidad '{opportunity_id}' no encontrada")

    opp.estado_interno = new_state
    session.add(opp)
    session.commit()
    session.refresh(opp)
    query_cache.invalidate_all()
    return {
        "id": opp.id,
        "codigo_oficial": opp.codigo_oficial,
        "estadoInterno": opp.estado_interno,
        "updated": True,
    }


@app.get("/api/v1/sources/registry", tags=["Fuentes Oficiales y Privadas"])
def get_sources_registry(session: Session = Depends(get_session)) -> dict[str, Any]:
    """
    Return the complete catalog of monitored sources across all 6 levels:
    UE (Comisión Europea), ESTADO (BOE/BDNS/PLACSP), 19 CCAA, 50 Provincias/Diputaciones,
    8.131 Municipios (Concellos/Ayuntamientos/Ajuntaments/Udalak) and Fundaciones Privadas.
    """
    all_opps = session.exec(select(Opportunity)).all()
    by_level: dict[str, int] = {}
    by_fuente: dict[str, int] = {}
    for o in all_opps:
        by_level[o.nivel_territorial] = by_level.get(o.nivel_territorial, 0) + 1
        by_fuente[o.fuente] = by_fuente.get(o.fuente, 0) + 1

    return {
        "total_fuentes_monitorizadas": len(SOURCES_REGISTRY),
        "cobertura_niveles": [
            "UE (Comisión Europea: LIFE, Horizon Europe, Interreg, FEADER, FEDER)",
            "ESTADO (BOE Datos Abiertos, BDNS/SNPSAP, PLACSP Contratación, MITECO, Fundación Biodiversidad)",
            "CCAA (19 Boletines Oficiales Autonómicos: DOG, DOGC, BOJA, BOCM, BOCYL, DOGV, BOPV, etc.)",
            "PROVINCIA (50 Diputaciones Provinciales, Deputacións, Diputacions, Diputaciones Forales, Cabildos y Consells + BOPs)",
            "MUNICIPIO (8.131 Ayuntamientos, Concellos, Ajuntaments, Udalak, Mancomunidades y Juntas Vecinales)",
            "PRIVADA (Fundación ”la Caixa”, Motor Verde Repsol/Sylvestris, Fundación Santander, Fundación BBVA, Fundación Iberdrola)",
        ],
        "oportunidades_por_nivel": by_level,
        "oportunidades_por_conector": by_fuente,
        "fuentes": SOURCES_REGISTRY,
    }


@app.get("/api/v1/map/summary", tags=["Mapa Interactivo CCAA"])
def get_map_summary(
    estado: str = Query(default="ACTIVA", description="ACTIVA | CERRADA | TODAS"),
    relevancia: str | None = Query(default=None, description="DIRECTA | INDIRECTA_ELEGIBLE"),
    categoria: str | None = Query(default=None, description="Filtrar por categoría temática"),
    anio: int | None = Query(default=None, description="Filtrar por año de convocatoria (2020-2026)"),
    incluir_nacionales_ue: bool = Query(
        default=True,
        description="Si es true, añade al resumen de cada CCAA el contador de ayudas Estatales (ES), Privadas Nacionales y Europeas (EU) aplicables en todo el territorio",
    ),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """
    Ultra-fast cached & indexed summary by Autonomous Community (17 CCAA + Ceuta/Melilla + ES + EU + Privadas)
    designed specifically to power the interactive choropleth map of Spain.
    """
    cache_key = f"map:{estado}:{relevancia}:{categoria}:{anio}:{incluir_nacionales_ue}"
    cached = query_cache.get(cache_key)
    if cached is not None:
        return cached

    stmt = select(Opportunity)
    if estado and estado.upper() != "TODAS":
        stmt = stmt.where(Opportunity.estado == estado.upper())
    if relevancia:
        stmt = stmt.where(Opportunity.relevancia_tipo == relevancia.upper())
    if anio:
        stmt = stmt.where(Opportunity.anio_convocatoria == anio)

    opps = session.exec(stmt).all()
    if categoria:
        cat_low = categoria.lower()
        opps = [o for o in opps if cat_low in [c.lower() for c in (o.categorias or [])]]

    es_public_opps = [o for o in opps if o.ccaa_codigo == "ES" and o.nivel_territorial != "PRIVADA"]
    priv_opps = [o for o in opps if o.nivel_territorial == "PRIVADA"]
    eu_opps = [o for o in opps if o.ccaa_codigo == "EU"]
    global_opps = [o for o in opps if o.ccaa_codigo in ("ES", "EU")]
    global_count = len(global_opps)
    global_budget = sum(o.presupuesto_total or 0.0 for o in global_opps)

    regiones: list[dict[str, Any]] = []
    for ccaa_code, info in CCAA_CATALOG.items():
        if ccaa_code in ("ES", "EU"):
            continue
        own_opps = [o for o in opps if o.ccaa_codigo == ccaa_code]
        own_count = len(own_opps)
        own_budget = sum(o.presupuesto_total or 0.0 for o in own_opps)
        directas_count = sum(1 for o in own_opps if o.relevancia_tipo == "DIRECTA")
        indirectas_count = sum(1 for o in own_opps if o.relevancia_tipo == "INDIRECTA_ELEGIBLE")
        muni_count = sum(1 for o in own_opps if o.nivel_territorial == "MUNICIPIO")
        prov_count = sum(1 for o in own_opps if o.nivel_territorial == "PROVINCIA")

        regiones.append(
            {
                "ccaa_codigo": ccaa_code,
                "nuts_codigo": info["nuts"],
                "ccaa_nombre": info["nombre"],
                "oportunidades_territoriales": own_count,
                "oportunidades_autonomicas": own_count - muni_count - prov_count,
                "oportunidades_provinciales": prov_count,
                "oportunidades_municipales_concellos": muni_count,
                "oportunidades_directas": directas_count,
                "oportunidades_indirectas": indirectas_count,
                "oportunidades_totales_aplicables": own_count + (global_count if incluir_nacionales_ue else 0),
                "presupuesto_territorial_eur": round(own_budget, 2),
                "presupuesto_total_aplicable_eur": round(
                    own_budget + (global_budget if incluir_nacionales_ue else 0.0), 2
                ),
                "destacadas": [
                    {
                        "id": o.id,
                        "titulo_limpio": o.titulo_limpio,
                        "nivel_territorial": o.nivel_territorial,
                        "tipo_oportunidad": o.tipo_oportunidad,
                        "relevancia_tipo": o.relevancia_tipo,
                        "prioridad_score": o.prioridad_score,
                        "presupuesto_total": o.presupuesto_total,
                        "dias_restantes": o.dias_restantes,
                    }
                    for o in sorted(own_opps, key=lambda x: (x.prioridad_score, x.relevancia_score), reverse=True)[:4]
                ],
            }
        )

    payload = {
        "filtro_estado": estado,
        "total_oportunidades_filtradas": len(opps),
        "resumen_estatal_es": {
            "ccaa_codigo": "ES",
            "nombre": CCAA_CATALOG["ES"]["nombre"],
            "oportunidades": len(es_public_opps),
            "presupuesto_eur": round(sum(o.presupuesto_total or 0.0 for o in es_public_opps), 2),
        },
        "resumen_privadas_es": {
            "nivel": "PRIVADA",
            "nombre": "Fundaciones Privadas y Fondos Corporativos ESG (Aplicables en España)",
            "oportunidades": len(priv_opps),
            "presupuesto_eur": round(sum(o.presupuesto_total or 0.0 for o in priv_opps), 2),
        },
        "resumen_europeo_eu": {
            "ccaa_codigo": "EU",
            "nombre": CCAA_CATALOG["EU"]["nombre"],
            "oportunidades": len(eu_opps),
            "presupuesto_eur": round(sum(o.presupuesto_total or 0.0 for o in eu_opps), 2),
        },
        "ccaa": regiones,
    }
    query_cache.set(cache_key, payload)
    return payload


@app.get("/api/v1/opportunities", tags=["Oportunidades (Activas e Histórico)"])
def list_opportunities(
    estado: str | None = Query(default=None, description="ACTIVA | CERRADA | PROXIMA | TODAS"),
    fuente: str | None = Query(default=None, description="Conector / fuente primaria exacta (ej. BDNS, BOE, PLACSP, EU_SEDIA, CCAA_RSS, FUNDACION_PRIVADA)"),
    ccaa: str | None = Query(default=None, description="Código CCAA (ej. ES-MD, ES-GA, ES-AN, ES, EU)"),
    incluir_nacionales_ue: bool = Query(
        default=False,
        description="Si se filtra por una CCAA (ej. ES-MD) y es true, incluye también las convocatorias Estatales (ES), Privadas y Europeas (EU)",
    ),
    provincia: str | None = Query(default=None, description="Código de provincia (ej. ES-LE, ES-M, ES-PO, ES-OR)"),
    nivel: str | None = Query(
        default=None,
        description="UE | ESTADO | CCAA | PROVINCIA | MUNICIPIO | PRIVADA",
    ),
    tipo: str | None = Query(
        default=None,
        description="SUBVENCION | LICITACION | PROGRAMA_UE | CONVOCATORIA_PRIVADA | CONVENIO",
    ),
    relevancia: str | None = Query(default=None, description="DIRECTA | INDIRECTA_ELEGIBLE"),
    categoria: str | None = Query(
        default=None,
        description="reforestacion | prevencion_incendios | restauracion_post_incendio | silvicultura | biodiversidad | restauracion_ecologica | absorcion_carbono | investigacion_forestal",
    ),
    beneficiario: str | None = Query(
        default=None,
        description="AYUNTAMIENTO | ONG_FUNDACIONES | EMPRESA_PYME | PARTICULAR_PROPIETARIO | COMUNIDAD_MONTES | UNIVERSIDAD_INVESTIGACION",
    ),
    modalidad_pago: str | None = Query(
        default=None,
        description="Filtrar por modalidad de pago: anticipo | reembolso | mixto",
    ),
    solo_anticipo_sin_aval: bool | None = Query(
        default=None,
        description="Si es true, devuelve únicamente convocatorias con pago anticipado sin exigencia de aval",
    ),
    anio: int | None = Query(default=None, description="Año de convocatoria (2020-2026)"),
    anio_desde: int | None = Query(default=None, description="Año inicial para rango histórico (ej. 2020)"),
    anio_hasta: int | None = Query(default=None, description="Año final para rango histórico (ej. 2026)"),
    fecha_desde: date | None = Query(default=None, description="Fecha publicación desde (YYYY-MM-DD)"),
    fecha_hasta: date | None = Query(default=None, description="Fecha publicación hasta (YYYY-MM-DD)"),
    presupuesto_min: float | None = Query(default=None, description="Presupuesto total mínimo en EUR"),
    cofinanciado_ue: bool | None = Query(default=None, description="Filtrar por cofinanciación europea"),
    q: str | None = Query(default=None, description="Búsqueda por texto libre en título, resumen, órgano, concello o código"),
    sort_by: str = Query(
        default="prioridad_score",
        description="prioridad_score | relevancia_score | dias_restantes | presupuesto_total | fecha_publicacion",
    ),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """Indexed SQL filter, search, prioritization and pagination across active and historical (2020-2026) calls."""
    stmt = select(Opportunity)

    if estado and estado.upper() != "TODAS":
        stmt = stmt.where(Opportunity.estado == estado.upper())
    if fuente:
        stmt = stmt.where(func.upper(Opportunity.fuente) == fuente.strip().upper())
    if ccaa:
        ccaa_up = ccaa.upper()
        if incluir_nacionales_ue and ccaa_up not in ("ES", "EU"):
            stmt = stmt.where(Opportunity.ccaa_codigo.in_([ccaa_up, "ES", "EU"]))
        else:
            stmt = stmt.where(Opportunity.ccaa_codigo == ccaa_up)
    if provincia:
        stmt = stmt.where(Opportunity.provincia_codigo == provincia.upper())
    if nivel:
        stmt = stmt.where(Opportunity.nivel_territorial == nivel.upper())
    if tipo:
        stmt = stmt.where(Opportunity.tipo_oportunidad == tipo.upper())
    if relevancia:
        stmt = stmt.where(Opportunity.relevancia_tipo == relevancia.upper())
    if modalidad_pago:
        stmt = stmt.where(Opportunity.modalidad_pago == modalidad_pago.lower())
    if solo_anticipo_sin_aval is True:
        stmt = stmt.where(Opportunity.pago_anticipado_sin_aval == True)  # noqa: E712
    if anio:
        stmt = stmt.where(Opportunity.anio_convocatoria == anio)
    if anio_desde:
        stmt = stmt.where(Opportunity.anio_convocatoria >= anio_desde)
    if anio_hasta:
        stmt = stmt.where(Opportunity.anio_convocatoria <= anio_hasta)
    if fecha_desde:
        stmt = stmt.where(Opportunity.fecha_publicacion >= fecha_desde)
    if fecha_hasta:
        stmt = stmt.where(Opportunity.fecha_publicacion <= fecha_hasta)
    if presupuesto_min is not None:
        stmt = stmt.where(Opportunity.presupuesto_total >= presupuesto_min)
    if cofinanciado_ue is not None:
        stmt = stmt.where(Opportunity.cofinanciado_ue == cofinanciado_ue)
    if q:
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Opportunity.titulo_limpio.ilike(pattern),
                Opportunity.titulo_original.ilike(pattern),
                Opportunity.resumen.ilike(pattern),
                Opportunity.organo_convocante.ilike(pattern),
                Opportunity.codigo_oficial.ilike(pattern),
                Opportunity.ccaa_nombre.ilike(pattern),
                Opportunity.municipio_nombre.ilike(pattern),
            )
        )

    results = list(session.exec(stmt).all())

    # JSON array filters (categoria, beneficiario)
    if categoria:
        cat_low = categoria.lower()
        results = [o for o in results if cat_low in [c.lower() for c in (o.categorias or [])]]
    if beneficiario:
        ben_up = beneficiario.upper()
        results = [o for o in results if ben_up in [b.upper() for b in (o.beneficiarios_tipos or [])]]

    # Sort on materialized model attributes before serializing the requested page
    if sort_by == "dias_restantes":
        results.sort(key=lambda o: (o.dias_restantes is None, o.dias_restantes or 999999))
    elif sort_by == "presupuesto_total":
        results.sort(key=lambda o: o.presupuesto_total or 0.0, reverse=True)
    elif sort_by == "fecha_publicacion":
        results.sort(key=lambda o: o.fecha_publicacion.isoformat() if o.fecha_publicacion else "1970-01-01", reverse=True)
    elif sort_by == "relevancia_score":
        results.sort(key=lambda o: (o.estado == "ACTIVA", o.relevancia_score), reverse=True)
    else:
        results.sort(
            key=lambda o: (o.estado == "ACTIVA", o.prioridad_score, o.relevancia_score),
            reverse=True,
        )

    total = len(results)
    start = (page - 1) * limit
    end = start + limit
    page_items = [o.to_api_dict() for o in results[start:end]]

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": page_items,
    }


@app.get("/api/v1/opportunities/prioritized", tags=["Motor de Priorización (Reforesta)"])
def get_prioritized_opportunities(
    ccaa: str | None = Query(default=None, description="Filtrar por CCAA (incluye automáticamente Estatales, Privadas y UE aplicables)"),
    perfil_beneficiario: str | None = Query(
        default=None,
        description="Opcional: ONG_FUNDACIONES | AYUNTAMIENTO | COMUNIDAD_MONTES | EMPRESA_PYME",
    ),
    solo_anticipo_sin_aval: bool = Query(
        default=False,
        description="Filtrar solo oportunidades con pago anticipado sin aval",
    ),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """
    Strategic Prioritization Queue ('Encontrar y Priorizar'):
    Ranks all open (ACTIVA) opportunities by tactical fit (thematic match, NGO eligibility,
    % financing intensity, grant amount, and deadline urgency window).
    """
    stmt = select(Opportunity).where(Opportunity.estado == "ACTIVA")
    if ccaa:
        ccaa_up = ccaa.upper()
        if ccaa_up not in ("ES", "EU"):
            stmt = stmt.where(Opportunity.ccaa_codigo.in_([ccaa_up, "ES", "EU"]))
        else:
            stmt = stmt.where(Opportunity.ccaa_codigo == ccaa_up)
    if solo_anticipo_sin_aval:
        stmt = stmt.where(Opportunity.pago_anticipado_sin_aval == True)  # noqa: E712

    active_opps = list(session.exec(stmt).all())
    if perfil_beneficiario:
        p_up = perfil_beneficiario.upper()
        active_opps = [
            o for o in active_opps if p_up in [b.upper() for b in (o.beneficiarios_tipos or [])]
        ]

    active_opps.sort(
        key=lambda o: (o.prioridad_score, o.relevancia_score),
        reverse=True,
    )
    items = [o.to_api_dict() for o in active_opps]

    criticas = [i for i in items if i["priorizacion"]["nivel"] == "CRITICA"]
    altas = [i for i in items if i["priorizacion"]["nivel"] == "ALTA"]
    medias_bajas = [i for i in items if i["priorizacion"]["nivel"] not in ("CRITICA", "ALTA")]

    return {
        "filosofia": "Reforesta ya sabe redactar propuestas; este motor encuentra y prioriza dónde presentarse primero.",
        "total_activas_analizadas": len(items),
        "resumen_prioridades": {
            "criticas_accion_inmediata": len(criticas),
            "altas_oportunidades": len(altas),
            "complementarias": len(medias_bajas),
        },
        "top_10_priorizadas": items[:10],
        "cola_critica": criticas,
        "cola_alta": altas,
        "cola_complementaria": medias_bajas,
    }


@app.get("/api/v1/opportunities/predictive-calendar", tags=["Calendario Predictivo y Exportadores"])
def get_predictive_recurrence_calendar(
    ccaa: str | None = Query(
        default=None,
        description="Código CCAA (ej. ES-MD, ES-GA, ES-AN) para filtrar programas autonómicos + estatales/UE",
    ),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """
    Predictive Annual Recurrence Calendar (2020-2026):
    Forecasts opening months and 45-day preparation windows for recurring forest/environmental calls
    so Reforesta can prepare technical memories before 10-day bulletin windows open.
    """
    all_opps = list(session.exec(select(Opportunity)).all())
    return build_predictive_calendar(opps=all_opps, ccaa_filter=ccaa)


@app.get("/api/v1/export/csv", tags=["Calendario Predictivo y Exportadores"])
def export_csv_endpoint(
    estado: str = Query(default="ACTIVA", description="ACTIVA | CERRADA | TODAS"),
    ccaa: str | None = Query(default=None, description="Filtrar por CCAA (incluye ES y EU si se desea)"),
    incluir_nacionales_ue: bool = Query(default=True),
    session: Session = Depends(get_session),
) -> Response:
    """Download prioritized opportunities as a UTF-8 with BOM CSV file ready for Microsoft Excel / Google Sheets."""
    stmt = select(Opportunity)
    if estado and estado.upper() != "TODAS":
        stmt = stmt.where(Opportunity.estado == estado.upper())
    if ccaa:
        ccaa_up = ccaa.upper()
        if incluir_nacionales_ue and ccaa_up not in ("ES", "EU"):
            stmt = stmt.where(Opportunity.ccaa_codigo.in_([ccaa_up, "ES", "EU"]))
        else:
            stmt = stmt.where(Opportunity.ccaa_codigo == ccaa_up)

    opps = list(session.exec(stmt).all())
    csv_content = export_opportunities_csv(opps)
    filename = f"reforesta_oportunidades_{(estado or 'todas').lower()}.csv"
    return Response(
        content=csv_content.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/v1/export/calendar.ics", tags=["Calendario Predictivo y Exportadores"])
def export_ics_calendar_endpoint(
    estado: str = Query(default="ACTIVA", description="ACTIVA | TODAS"),
    ccaa: str | None = Query(default=None, description="Filtrar por CCAA"),
    session: Session = Depends(get_session),
) -> Response:
    """Download an RFC 5545 iCalendar (.ics) file with deadline events and 7-day / 2-day alarms."""
    stmt = select(Opportunity)
    if estado and estado.upper() != "TODAS":
        stmt = stmt.where(Opportunity.estado == estado.upper())
    if ccaa:
        ccaa_up = ccaa.upper()
        if ccaa_up not in ("ES", "EU"):
            stmt = stmt.where(Opportunity.ccaa_codigo.in_([ccaa_up, "ES", "EU"]))
        else:
            stmt = stmt.where(Opportunity.ccaa_codigo == ccaa_up)

    opps = list(session.exec(stmt).all())
    ics_content = export_opportunities_ics(opps)
    return Response(
        content=ics_content.encode("utf-8"),
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="reforesta_plazos_convocatorias.ics"'},
    )


@app.get("/api/v1/export/markdown/{opportunity_id}", tags=["Calendario Predictivo y Exportadores"])
def export_markdown_dossier_endpoint(
    opportunity_id: str,
    session: Session = Depends(get_session),
) -> Response:
    """Export a complete technical preparation dossier in Markdown for a specific opportunity."""
    opp = session.get(Opportunity, opportunity_id)
    if not opp:
        opp = session.exec(
            select(Opportunity).where(Opportunity.codigo_oficial == opportunity_id.upper())
        ).first()
    if not opp:
        raise HTTPException(status_code=404, detail=f"Oportunidad '{opportunity_id}' no encontrada")

    md_content = export_opportunity_markdown(opp)
    safe_id = opp.id.replace("/", "-")
    return Response(
        content=md_content.encode("utf-8"),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="ficha_{safe_id}.md"'},
    )


@app.get("/api/v1/opportunities/{opportunity_id}", tags=["Oportunidades (Activas e Histórico)"])
def get_opportunity_detail(
    opportunity_id: str,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """Get full details of a specific opportunity by ID or official code."""
    opp = session.get(Opportunity, opportunity_id)
    if not opp:
        opp = session.exec(
            select(Opportunity).where(Opportunity.codigo_oficial == opportunity_id.upper())
        ).first()
    if not opp:
        raise HTTPException(status_code=404, detail=f"Oportunidad '{opportunity_id}' no encontrada")
    return opp.to_api_dict()


@app.get("/api/v1/stats/historical", tags=["Estadísticas e Histórico (2020-2026)"])
def get_historical_stats(session: Session = Depends(get_session)) -> dict[str, Any]:
    """Return cached multi-year series (2020-2026), category breakdowns, and filter audit stats."""
    cached = query_cache.get("stats:historical")
    if cached is not None:
        return cached

    all_opps = session.exec(select(Opportunity)).all()
    last_run = session.exec(select(IngestionRun).order_by(IngestionRun.id.desc())).first()

    by_year: dict[int, dict[str, Any]] = {}
    for yr in range(settings.ingest_start_year, settings.ingest_end_year + 1):
        by_year[yr] = {"anio": yr, "total": 0, "activas": 0, "cerradas": 0, "presupuesto_eur": 0.0}

    by_category: dict[str, int] = {}
    by_level: dict[str, int] = {}
    by_relevance: dict[str, int] = {"DIRECTA": 0, "INDIRECTA_ELEGIBLE": 0}

    for o in all_opps:
        yr = o.anio_convocatoria
        if yr not in by_year:
            by_year[yr] = {"anio": yr, "total": 0, "activas": 0, "cerradas": 0, "presupuesto_eur": 0.0}
        by_year[yr]["total"] += 1
        if o.estado == "ACTIVA":
            by_year[yr]["activas"] += 1
        else:
            by_year[yr]["cerradas"] += 1
        by_year[yr]["presupuesto_eur"] = round(
            by_year[yr]["presupuesto_eur"] + (o.presupuesto_total or 0.0), 2
        )

        for cat in o.categorias or []:
            by_category[cat] = by_category.get(cat, 0) + 1

        by_level[o.nivel_territorial] = by_level.get(o.nivel_territorial, 0) + 1
        by_relevance[o.relevancia_tipo] = by_relevance.get(o.relevancia_tipo, 0) + 1

    payload = {
        "rango_historico": f"{settings.ingest_start_year}-{settings.ingest_end_year}",
        "total_oportunidades": len(all_opps),
        "presupuesto_acumulado_eur": round(sum(o.presupuesto_total or 0.0 for o in all_opps), 2),
        "serie_anual": [by_year[k] for k in sorted(by_year.keys())],
        "por_categoria": by_category,
        "por_nivel_territorial": by_level,
        "por_tipo_relevancia": by_relevance,
        "auditoria_ultimo_filtrado": {
            "total_escaneadas": last_run.total_scanned if last_run else 0,
            "superaron_capa1_regex": last_run.passed_layer1 if last_run else 0,
            "aprobadas_capa2_juez": last_run.accepted_layer2 if last_run else 0,
            "ruido_descartado": (last_run.total_scanned - last_run.accepted_layer2) if last_run else 0,
            "ejemplos_ruido_descartado": (last_run.details or {}).get("rejected_sample", []) if last_run else [],
        },
    }
    query_cache.set("stats:historical", payload)
    return payload


@app.get("/api/v1/benchmark/verify", tags=["Golden Benchmark (fuentes/)"])
def verify_golden_benchmark(session: Session = Depends(get_session)) -> dict[str, Any]:
    """
    Verify that the 2 Golden Benchmark documents in ./fuentes/
    (MITECO BDNS-923290 and Comunidad de Madrid Orden 1689/2026) are detected and extracted.
    """
    miteco = session.get(Opportunity, "bdns-923290")
    madrid = session.get(Opportunity, "bocm-orden-1689-2026")
    return {
        "benchmark_passed": bool(miteco and madrid),
        "fuentes_detectadas": [
            miteco.to_api_dict() if miteco else None,
            madrid.to_api_dict() if madrid else None,
        ],
    }


@app.get("/api/v1/fuentes/{filename}", tags=["Golden Benchmark (fuentes/)"])
def serve_local_source_pdf(filename: str) -> FileResponse:
    """Serve any official PDF stored inside ./fuentes/ directly with inline PDF disposition."""
    safe_name = Path(filename).name
    if not safe_name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se pueden servir documentos PDF oficiales")
    target = (FUENTES_DIR / safe_name).resolve()
    if not str(target).startswith(str(FUENTES_DIR.resolve())) or not target.is_file():
        raise HTTPException(status_code=404, detail=f"Documento oficial '{safe_name}' no encontrado en ./fuentes/")
    return FileResponse(
        path=target,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{safe_name}"'},
    )


@app.get("/api/v1/reforesta/profile", tags=["Perfil Institucional Reforesta"])
def read_reforesta_institutional_profile() -> dict[str, Any]:
    """Return Reforesta's verified NIF, registry ID, 11 statutory fines, tax deductions & PDF URLs."""
    return get_reforesta_profile()


@app.get("/api/v1/ingest/runs", tags=["Ingesta y Pipeline Híbrido"])
def list_ingestion_runs(
    limit: int = Query(default=10, ge=1, le=50),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """Return recent ingestion runs with exact live connector counts, enrichments, and rejected noise samples."""
    rows = session.exec(select(IngestionRun).order_by(IngestionRun.id.desc()).limit(limit)).all()
    _, next_sync_dt = seconds_until_next_daily_sync()
    return {
        "total_returned": len(rows),
        "daily_sync_schedule": f"{settings.daily_sync_hour:02d}:{settings.daily_sync_minute:02d} {settings.daily_sync_timezone}",
        "next_daily_sync_at": next_sync_dt.isoformat(),
        "runs": [
            {
                "run_id": r.id,
                "status": r.status,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "finished_at": r.finished_at.isoformat() if r.finished_at else None,
                "sources": r.sources,
                "total_scanned": r.total_scanned,
                "passed_layer1": r.passed_layer1,
                "accepted_layer2": r.accepted_layer2,
                "upserted_db": r.upserted_db,
                "details": r.details,
            }
            for r in rows
        ],
    }


@app.post("/api/v1/ingest/trigger", tags=["Ingesta y Pipeline Híbrido"])
async def trigger_ingestion(
    include_live_apis: bool = Query(default=True, description="Consultar también APIs en vivo de BDNS, PLACSP, BOE y UE SEDIA"),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """Trigger a full concurrent ingestion and hybrid filtering run (protected by asyncio.Lock)."""
    async with _INGEST_LOCK:
        run_log = await run_full_ingestion(session=session, include_live_apis=include_live_apis)
        refresh_live_database_states(session)
        return {
            "run_id": run_log.id,
            "status": run_log.status,
            "total_scanned": run_log.total_scanned,
            "passed_layer1": run_log.passed_layer1,
            "accepted_layer2": run_log.accepted_layer2,
            "details": run_log.details,
        }


@app.post("/api/v1/analyze/text", tags=["Ingesta y Pipeline Híbrido"])
def analyze_custom_text(
    req: AnalyzeTextRequest,
    x_llm_api_key: str | None = Header(default=None, description="API Key opcional de Gemini si se desea forzar llamada cloud desde el cliente"),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """Evaluate any call text live through Layer 1 (Regex) + Layer 2 (LLM Judge)."""
    cand = RawCandidate(
        id=f"live-{abs(hash(req.titulo)) % 1000000}",
        codigo_oficial="LIVE-EVAL",
        fuente="LIVE_DEMO",
        tipo_oportunidad="SUBVENCION",
        titulo=req.titulo,
        organo_convocante=req.organo_convocante,
        texto=req.texto,
        fecha_publicacion=req.fecha_publicacion,
        plazo_texto_original=req.plazo_texto,
        presupuesto_total=req.presupuesto_total,
        url_ficha_oficial=req.url_oficial,
    )
    res = process_candidate(
        cand,
        session=session,
        persist=req.guardar_en_bd,
        api_key_override=x_llm_api_key,
    )
    return {
        "passed_layer1": res.passed_layer1,
        "accepted_layer2": res.accepted_layer2,
        "layer1_detail": {
            "decision": res.layer1.decision,
            "score": res.layer1.score,
            "preliminary_relevance": res.layer1.preliminary_relevance,
            "detected_language": res.layer1.detected_language,
            "matched_categories": res.layer1.matched_categories,
            "matched_terms": res.layer1.matched_terms,
            "rejection_reason": res.layer1.rejection_reason,
        },
        "layer2_verdict": res.layer2.model_dump() if res.layer2 else None,
        "opportunity": res.opportunity.to_api_dict() if res.opportunity else None,
    }


@app.post("/api/v1/analyze/pdf", tags=["Ingesta y Pipeline Híbrido"])
async def analyze_uploaded_pdf(
    file: UploadFile = File(...),
    guardar_en_bd: bool = Query(default=True),
    x_llm_api_key: str | None = Header(default=None, description="API Key opcional de Gemini"),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """Upload a PDF of an official bulletin or BDNS sheet to parse and evaluate live (with OCR fallback)."""
    pdf_bytes = await file.read()
    extracted = extract_pdf_from_bytes(
        pdf_bytes,
        filename=file.filename or "uploaded.pdf",
        api_key_override=x_llm_api_key,
    )
    cand = pdf_doc_to_candidate(extracted)
    res = process_candidate(
        cand,
        session=session,
        persist=guardar_en_bd,
        api_key_override=x_llm_api_key,
    )
    return {
        "filename": extracted.filename,
        "num_pages": extracted.num_pages,
        "used_ocr": extracted.used_ocr,
        "ocr_engine": extracted.ocr_engine,
        "passed_layer1": res.passed_layer1,
        "accepted_layer2": res.accepted_layer2,
        "amendment_applied": res.amendment_applied,
        "layer1_detail": {
            "decision": res.layer1.decision,
            "score": res.layer1.score,
            "detected_language": res.layer1.detected_language,
            "matched_categories": res.layer1.matched_categories,
            "matched_terms": res.layer1.matched_terms,
        },
        "opportunity": res.opportunity.to_api_dict() if res.opportunity else None,
    }
