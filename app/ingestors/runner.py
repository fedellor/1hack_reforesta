"""Master Ingestion Runner & Live Background Sync Worker."""
import asyncio
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo
from sqlmodel import Session, select
from app.config import settings
from app.database import engine, query_cache
from app.ingestors.fuentes_local import load_candidates_from_fuentes
from app.ingestors.live_connectors import (
    enrich_candidates_with_linked_pdfs,
    fetch_live_bdns_candidates,
    fetch_live_boe_candidates,
    fetch_live_ccaa_rss_candidates,
    fetch_live_eu_sedia_candidates,
    fetch_live_placsp_candidates,
    fetch_live_private_foundation_candidates,
    fetch_live_public_portal_candidates,
    fetch_live_ted_candidates,
)
from app.ingestors.multilevel_catalog import get_multilevel_candidates
from app.models import IngestionRun, Opportunity
from app.pipeline.date_resolver import compute_dates_and_status
from app.pipeline.orchestrator import RawCandidate, process_candidate
from app.pipeline.prioritizer import calculate_priority

logger = logging.getLogger(__name__)


async def run_full_ingestion(
    session: Session,
    include_live_apis: bool = True,
) -> IngestionRun:
    """
    Execute the end-to-end ingestion & hybrid filtering pipeline concurrently:
    1. Local PDFs in ./fuentes/ (Golden Benchmark: MITECO 923290 + Madrid Orden 1689/2026)
    2. Multilevel catalog (2020-2026: EU, State, 19 CCAA, Diputaciones, Concellos/Ayuntamientos, PLACSP, Private Foundations + Noise)
    3. Concurrent Live APIs (BDNS, PLACSP Atom, BOE Open Data, EU SEDIA) when include_live_apis=True
    """
    run_log = IngestionRun(
        started_at=datetime.now(timezone.utc),
        sources=[
            "FUENTES_PDF",
            "BDNS",
            "PLACSP",
            "BOE",
            "BOLETIN_CCAA",
            "EU_SEDIA",
            "FUNDACION_PRIVADA",
        ],
        status="RUNNING",
    )
    session.add(run_log)
    session.commit()
    session.refresh(run_log)

    candidates: list[RawCandidate] = []
    fuentes_candidates = load_candidates_from_fuentes()
    candidates.extend(fuentes_candidates)

    catalog_candidates = (
        get_multilevel_candidates() if settings.include_catalog_templates else []
    )
    candidates.extend(catalog_candidates)

    live_counts: dict[str, int] = {
        "bdns_live": 0,
        "placsp_live": 0,
        "ted_live": 0,
        "boe_live": 0,
        "eu_sedia_live": 0,
        "ccaa_rss_live": 0,
        "private_foundations_live": 0,
        "public_portals_live": 0,
        "pdf_links_enriched": 0,
    }
    if include_live_apis:
        bdns_live, placsp_live, ted_live, boe_live, eu_live, rss_live, priv_live, pub_live = await asyncio.gather(
            fetch_live_bdns_candidates(max_per_keyword=100, timeout=12.0),
            fetch_live_placsp_candidates(timeout=14.0, max_pages=4),
            fetch_live_ted_candidates(timeout=9.0),
            fetch_live_boe_candidates(days_back=45, timeout=9.0),
            fetch_live_eu_sedia_candidates(timeout=7.0),
            fetch_live_ccaa_rss_candidates(timeout=5.0),
            fetch_live_private_foundation_candidates(timeout=6.0),
            fetch_live_public_portal_candidates(timeout=6.5),
        )
        live_batch = bdns_live + placsp_live + ted_live + boe_live + eu_live + rss_live + priv_live + pub_live
        enriched_pdfs = await enrich_candidates_with_linked_pdfs(live_batch, timeout=5.0, max_downloads=60)
        live_counts = {
            "bdns_live": len(bdns_live),
            "placsp_live": len(placsp_live),
            "ted_live": len(ted_live),
            "boe_live": len(boe_live),
            "eu_sedia_live": len(eu_live),
            "ccaa_rss_live": len(rss_live),
            "private_foundations_live": len(priv_live),
            "public_portals_live": len(pub_live),
            "pdf_links_enriched": enriched_pdfs,
        }
        candidates.extend(live_batch)

    total_scanned = 0
    passed_l1 = 0
    accepted_l2 = 0
    amendments_applied = 0
    rejected_items: list[dict[str, Any]] = []

    for cand in candidates:
        total_scanned += 1
        res = process_candidate(cand, session=session, persist=True)
        if res.passed_layer1:
            passed_l1 += 1
        if res.accepted_layer2:
            accepted_l2 += 1
            if res.amendment_applied:
                amendments_applied += 1
        else:
            rejected_items.append(
                {
                    "id": cand.id,
                    "titulo": cand.titulo[:120],
                    "score_capa1": res.layer1.score,
                    "motivo": res.layer1.rejection_reason
                    or (res.layer2.justificacion_juez_es if res.layer2 else "Descartada"),
                }
            )

    run_log.finished_at = datetime.now(timezone.utc)
    run_log.total_scanned = total_scanned
    run_log.passed_layer1 = passed_l1
    run_log.accepted_layer2 = accepted_l2
    run_log.upserted_db = accepted_l2
    run_log.status = "COMPLETED"
    run_log.details = {
        "fuentes_pdf_count": len(fuentes_candidates),
        "catalog_count": len(catalog_candidates),
        "live_api_fetched": live_counts,
        "amendments_applied": amendments_applied,
        "rejected_count": len(rejected_items),
        "rejected_sample": rejected_items[:10],
    }
    session.add(run_log)
    session.commit()
    session.refresh(run_log)
    query_cache.invalidate_all()
    return run_log


def ensure_initial_seed(session: Session) -> None:
    """Populate or synchronize database with all local PDFs (and optional catalog fixtures in test mode)."""
    candidates = load_candidates_from_fuentes() + (
        get_multilevel_candidates() if settings.include_catalog_templates else []
    )
    existing_ids = set(session.exec(select(Opportunity.id)).all())

    total_scanned = 0
    passed_l1 = 0
    accepted_l2 = 0
    new_upserts = 0
    rejected_items: list[dict[str, Any]] = []

    for cand in candidates:
        total_scanned += 1
        if cand.id in existing_ids:
            passed_l1 += 1
            accepted_l2 += 1
            continue
        res = process_candidate(cand, session=session, persist=True)
        if res.passed_layer1:
            passed_l1 += 1
        if res.accepted_layer2:
            accepted_l2 += 1
            new_upserts += 1
        else:
            rejected_items.append(
                {
                    "id": cand.id,
                    "titulo": cand.titulo[:120],
                    "score_capa1": res.layer1.score,
                    "motivo": res.layer1.rejection_reason or "Descartada",
                }
            )

    if new_upserts > 0 or not existing_ids:
        run_log = IngestionRun(
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
            sources=[
                "FUENTES_PDF",
                "BDNS",
                "PLACSP",
                "BOE",
                "BOLETIN_CCAA",
                "EU_SEDIA",
                "FUNDACION_PRIVADA",
            ],
            total_scanned=total_scanned,
            passed_layer1=passed_l1,
            accepted_layer2=accepted_l2,
            upserted_db=accepted_l2,
            status="COMPLETED",
            details={
                "rejected_count": len(rejected_items),
                "rejected_sample": rejected_items,
            },
        )
        session.add(run_log)
        session.commit()

    # Always refresh active/closed statuses against today's date
    refresh_live_database_states(session)


def refresh_live_database_states(session: Session) -> int:
    """Recalculate ACTIVA/PROXIMA/CERRADA, dias_restantes and prioridad_score for all records in DB, and purge excluded items."""
    from app.pipeline.layer1_regex import HARD_EXCLUSION_PATTERN
    from app.pipeline.metadata_extractor import extract_deadline_clause_and_date

    today = settings.get_today()
    opps = session.exec(select(Opportunity)).all()
    updated = 0
    for o in opps:
        if HARD_EXCLUSION_PATTERN.search(f"{o.titulo_original or ''}\n{o.titulo_limpio or ''}\n{o.organo_convocante or ''}"):
            session.delete(o)
            updated += 1
            continue
        effective_fin = o.fecha_fin_solicitud
        effective_plazo = o.plazo_texto_original
        if effective_fin is None:
            ext_clause, ext_end = extract_deadline_clause_and_date(
                texto=f"{o.titulo_original or ''}\n{o.resumen or ''}",
                existing_clause=effective_plazo,
                existing_end_date=None,
            )
            if ext_end is not None:
                effective_fin = ext_end
                o.fecha_fin_solicitud = ext_end
                updated += 1
            if ext_clause and not effective_plazo:
                effective_plazo = ext_clause
                o.plazo_texto_original = ext_clause
                updated += 1
        if effective_fin is None and o.anio_convocatoria and o.anio_convocatoria < today.year:
            t_low = (o.titulo_original or o.titulo_limpio or "").lower()
            if (
                str(o.anio_convocatoria) in t_low
                and str(today.year) not in t_low
                and str(today.year + 1) not in t_low
                and ("disposición" in t_low or "cerrad" in t_low or "2025" in t_low)
            ):
                effective_fin = o.fecha_fin_solicitud = o.fecha_fin_solicitud or o.fecha_publicacion or date(o.anio_convocatoria, 12, 31)
                updated += 1
        resolved = compute_dates_and_status(
            fecha_publicacion=o.fecha_publicacion,
            fecha_inicio_solicitud=o.fecha_inicio_solicitud,
            fecha_fin_solicitud=effective_fin,
            plazo_texto_original=effective_plazo,
            anio_hint=o.anio_convocatoria,
            today=today,
            ccaa_codigo=o.ccaa_codigo,
        )
        prio = calculate_priority(
            estado=resolved.estado,
            dias_restantes=resolved.dias_restantes,
            relevancia_tipo=o.relevancia_tipo,
            relevancia_score=o.relevancia_score,
            beneficiarios_tipos=o.beneficiarios_tipos or [],
            porcentaje_financiacion=o.porcentaje_max_financiacion,
            presupuesto_total=o.presupuesto_total,
            importe_max_proyecto=o.importe_max_proyecto,
            nivel_territorial=o.nivel_territorial,
        )
        if (
            o.estado != resolved.estado
            or o.dias_restantes != resolved.dias_restantes
            or o.prioridad_score != prio.prioridad_score
            or o.prioridad_nivel != prio.prioridad_nivel
        ):
            o.estado = resolved.estado
            o.dias_restantes = resolved.dias_restantes
            o.prioridad_score = prio.prioridad_score
            o.prioridad_nivel = prio.prioridad_nivel
            session.add(o)
            updated += 1
    if updated > 0:
        session.commit()
        query_cache.invalidate_all()
    return updated


def seconds_until_next_daily_sync(
    now: datetime | None = None,
    hour: int | None = None,
    minute: int | None = None,
    tz_name: str | None = None,
) -> tuple[float, datetime]:
    """
    Compute remaining seconds and exact timestamp until the next daily 07:00 AM sync
    in the configured timezone (Europe/Madrid by default).
    """
    target_hour = settings.daily_sync_hour if hour is None else hour
    target_minute = settings.daily_sync_minute if minute is None else minute
    zone_name = tz_name or settings.daily_sync_timezone
    try:
        tz = ZoneInfo(zone_name)
    except Exception:
        tz = timezone(timedelta(hours=1))

    current = now.astimezone(tz) if now is not None else datetime.now(tz)
    target = current.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
    if current >= target:
        target = target + timedelta(days=1)

    wait_seconds = max(1.0, (target - current).total_seconds())
    return wait_seconds, target


def last_scheduled_slot(now: datetime | None = None) -> datetime:
    """Última cita de sincronización (07:00 Madrid por defecto) ya pasada respecto a `now`."""
    _, siguiente = seconds_until_next_daily_sync(now=now)
    return siguiente - timedelta(days=1)


def sync_overdue(session: Session, now: datetime | None = None) -> bool:
    """¿Se perdió la última sincronización programada?

    Es cierto si no hay ninguna sincronización real completada, o si la última es anterior a la última cita de las 07:00.
    Así, reiniciar el servicio varias veces el mismo día no dispara sincronizaciones de más, pero un reinicio tras una cita
    perdida (contenedor caído, equipo apagado) sí recupera los datos.
    """
    # Solo cuentan las sincronizaciones reales (con fuentes en vivo): el arranque con base vacía también deja una
    # ejecución COMPLETED que solo carga los PDF de ./fuentes, y no debe tomarse por una sincronización diaria.
    completadas = session.exec(
        select(IngestionRun).where(IngestionRun.status == "COMPLETED").order_by(IngestionRun.started_at.desc()).limit(50)
    ).all()
    ultima = next((r.started_at for r in completadas if "live_api_fetched" in (r.details or {})), None)
    if ultima is None:
        return True
    if ultima.tzinfo is None:
        ultima = ultima.replace(tzinfo=timezone.utc)
    return ultima < last_scheduled_slot(now)


async def run_sync_with_retries() -> bool:
    """Sincroniza las fuentes en vivo; si falla por una excepción, reintenta (varios intentos, con espera)."""
    intentos = max(1, settings.sync_retry_attempts)
    for n in range(1, intentos + 1):
        try:
            with Session(engine) as session:
                await run_full_ingestion(session=session, include_live_apis=True)
                refresh_live_database_states(session)
            return True
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("Sincronización fallida (intento %d de %d): %s", n, intentos, exc)
            if n < intentos:
                await asyncio.sleep(settings.sync_retry_delay_seconds)
    return False


async def _esperar_hasta(objetivo: datetime) -> None:
    """Espera hasta una hora concreta mirando el reloj real cada minuto: un único `sleep` largo se retrasa si el equipo se suspende."""
    while True:
        restante = (objetivo - datetime.now(objetivo.tzinfo)).total_seconds()
        if restante <= 0:
            return
        await asyncio.sleep(min(60.0, restante))


async def background_live_sync_daemon() -> None:
    """
    Planificador en segundo plano: sincroniza las fuentes oficiales cada día a las 07:00 (Europe/Madrid) y,
    al arrancar, recupera la sincronización si se perdió la última cita (ver `sync_overdue`).
    """
    try:
        if settings.sync_catchup_on_startup:
            try:
                with Session(engine) as session:
                    perdida = sync_overdue(session)
                if perdida:
                    logger.info("Al arrancar: la última sincronización programada no consta; sincronizando ahora...")
                    await run_sync_with_retries()
            except Exception as exc:  # una comprobación fallida no debe matar el planificador
                logger.warning("No se pudo comprobar/recuperar la sincronización al arrancar: %s", exc)
        while True:
            try:
                wait_sec, next_run = seconds_until_next_daily_sync()
                logger.info("Próxima actualización automática diaria programada: %s (en %.0f s)", next_run.isoformat(), wait_sec)
                await _esperar_hasta(next_run)
                logger.info("Iniciando actualización diaria automática de las 07:00h (Europe/Madrid)...")
                if not await run_sync_with_retries():
                    logger.error("La sincronización diaria falló tras %d intentos; se reintentará en la próxima cita.", settings.sync_retry_attempts)
                await asyncio.sleep(1)  # evita relanzar dentro de la misma cita
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning("Error en el planificador diario (reintento en 60 s): %s", exc)
                await asyncio.sleep(60)
    except asyncio.CancelledError:
        return
