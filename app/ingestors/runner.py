"""Master Ingestion Runner & Live Background Sync Worker."""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Any
from sqlmodel import Session, select
from app.config import settings
from app.database import engine, query_cache
from app.ingestors.fuentes_local import load_candidates_from_fuentes
from app.ingestors.live_connectors import (
    fetch_live_bdns_candidates,
    fetch_live_boe_candidates,
    fetch_live_eu_sedia_candidates,
    fetch_live_placsp_candidates,
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

    catalog_candidates = get_multilevel_candidates()
    candidates.extend(catalog_candidates)

    live_counts: dict[str, int] = {
        "bdns_live": 0,
        "placsp_live": 0,
        "boe_live": 0,
        "eu_sedia_live": 0,
    }
    if include_live_apis:
        bdns_live, placsp_live, boe_live, eu_live = await asyncio.gather(
            fetch_live_bdns_candidates(max_per_keyword=12, timeout=5.0),
            fetch_live_placsp_candidates(timeout=5.0),
            fetch_live_boe_candidates(days_back=2, timeout=5.0),
            fetch_live_eu_sedia_candidates(timeout=5.0),
        )
        live_counts = {
            "bdns_live": len(bdns_live),
            "placsp_live": len(placsp_live),
            "boe_live": len(boe_live),
            "eu_sedia_live": len(eu_live),
        }
        candidates.extend(bdns_live)
        candidates.extend(placsp_live)
        candidates.extend(boe_live)
        candidates.extend(eu_live)

    total_scanned = 0
    passed_l1 = 0
    accepted_l2 = 0
    rejected_items: list[dict[str, Any]] = []

    for cand in candidates:
        total_scanned += 1
        res = process_candidate(cand, session=session, persist=True)
        if res.passed_layer1:
            passed_l1 += 1
        if res.accepted_layer2:
            accepted_l2 += 1
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
        "rejected_count": len(rejected_items),
        "rejected_sample": rejected_items[:10],
    }
    session.add(run_log)
    session.commit()
    session.refresh(run_log)
    query_cache.invalidate_all()
    return run_log


def ensure_initial_seed(session: Session) -> None:
    """Populate or synchronize database with all local PDFs and multilevel catalog on startup."""
    candidates = load_candidates_from_fuentes() + get_multilevel_candidates()
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
    """Recalculate ACTIVA/PROXIMA/CERRADA, dias_restantes and prioridad_score for all records in DB."""
    today = settings.get_today()
    opps = session.exec(select(Opportunity)).all()
    updated = 0
    for o in opps:
        resolved = compute_dates_and_status(
            fecha_publicacion=o.fecha_publicacion,
            fecha_inicio_solicitud=o.fecha_inicio_solicitud,
            fecha_fin_solicitud=o.fecha_fin_solicitud,
            plazo_texto_original=o.plazo_texto_original,
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


async def background_live_sync_daemon() -> None:
    """
    Background asyncio loop keeping the database alive:
    - Hot-reloads any new PDFs added to ./fuentes/
    - Recalculates deadline countdowns (dias_restantes) & statuses
    - Periodically syncs live official endpoints (BDNS, PLACSP, BOE, EU SEDIA)
    """
    interval_sec = max(60, settings.auto_sync_interval_minutes * 60)
    while True:
        try:
            await asyncio.sleep(interval_sec)
            with Session(engine) as session:
                await run_full_ingestion(session=session, include_live_apis=True)
                refresh_live_database_states(session)
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.debug("Background live sync cycle skipped: %s", exc)
