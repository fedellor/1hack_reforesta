"""Sincronización diaria: recuperación al arrancar, reintentos y reloj real."""
import asyncio
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.config import settings
from app.ingestors import runner
from app.models import IngestionRun

MADRID = ZoneInfo("Europe/Madrid")


@pytest.fixture()
def session():
    eng = create_engine("sqlite://")
    SQLModel.metadata.create_all(eng)
    with Session(eng) as s:
        yield s


def _run(session, cuando: datetime, status="COMPLETED", details=None):
    session.add(
        IngestionRun(
            started_at=cuando.astimezone(timezone.utc),
            status=status,
            details={"live_api_fetched": {}} if details is None else details,  # como una sincronización real
        )
    )
    session.commit()


def test_last_scheduled_slot_is_most_recent_0700():
    ahora = datetime(2026, 11, 14, 10, 0, tzinfo=MADRID)
    assert runner.last_scheduled_slot(ahora) == datetime(2026, 11, 14, 7, 0, tzinfo=MADRID)
    antes = datetime(2026, 11, 14, 6, 0, tzinfo=MADRID)
    assert runner.last_scheduled_slot(antes) == datetime(2026, 11, 13, 7, 0, tzinfo=MADRID)


def test_overdue_when_no_runs(session):
    assert runner.sync_overdue(session, now=datetime(2026, 11, 14, 10, 0, tzinfo=MADRID)) is True


def test_not_overdue_when_synced_after_last_slot(session):
    ahora = datetime(2026, 11, 14, 10, 0, tzinfo=MADRID)
    _run(session, datetime(2026, 11, 14, 7, 5, tzinfo=MADRID))
    assert runner.sync_overdue(session, now=ahora) is False


def test_overdue_when_last_sync_before_last_slot(session):
    ahora = datetime(2026, 11, 14, 10, 0, tzinfo=MADRID)
    _run(session, datetime(2026, 11, 13, 7, 5, tzinfo=MADRID))  # la de hoy a las 07:00 se perdió
    assert runner.sync_overdue(session, now=ahora) is True


def test_restart_before_0700_does_not_resync_if_yesterdays_ran(session):
    ahora = datetime(2026, 11, 14, 6, 0, tzinfo=MADRID)
    _run(session, datetime(2026, 11, 13, 7, 5, tzinfo=MADRID))
    assert runner.sync_overdue(session, now=ahora) is False


def test_failed_or_running_runs_do_not_count(session):
    ahora = datetime(2026, 11, 14, 10, 0, tzinfo=MADRID)
    _run(session, datetime(2026, 11, 14, 7, 5, tzinfo=MADRID), status="RUNNING")
    _run(session, datetime(2026, 11, 14, 7, 6, tzinfo=MADRID), status="FAILED")
    assert runner.sync_overdue(session, now=ahora) is True


def test_seed_only_run_does_not_count_as_a_sync(session):
    """El arranque con base vacía deja una ejecución COMPLETED que solo carga ./fuentes: no es una sincronización diaria."""
    ahora = datetime(2026, 11, 14, 10, 0, tzinfo=MADRID)
    _run(session, datetime(2026, 11, 14, 9, 59, tzinfo=MADRID), details={"rejected_count": 0, "rejected_sample": []})
    assert runner.sync_overdue(session, now=ahora) is True


def test_retries_until_success(monkeypatch):
    llamadas = []

    async def falsa(session, include_live_apis=True):
        llamadas.append(1)
        if len(llamadas) < 3:
            raise RuntimeError("BDNS caído")

    monkeypatch.setattr(runner, "run_full_ingestion", falsa)
    monkeypatch.setattr(runner, "refresh_live_database_states", lambda s: None)
    monkeypatch.setattr(settings, "sync_retry_attempts", 3)
    monkeypatch.setattr(settings, "sync_retry_delay_seconds", 0)
    assert asyncio.run(runner.run_sync_with_retries()) is True
    assert len(llamadas) == 3


def test_gives_up_after_max_attempts(monkeypatch):
    llamadas = []

    async def siempre_falla(session, include_live_apis=True):
        llamadas.append(1)
        raise RuntimeError("caído")

    monkeypatch.setattr(runner, "run_full_ingestion", siempre_falla)
    monkeypatch.setattr(settings, "sync_retry_attempts", 3)
    monkeypatch.setattr(settings, "sync_retry_delay_seconds", 0)
    assert asyncio.run(runner.run_sync_with_retries()) is False
    assert len(llamadas) == 3


def _arrancar_demonio(monkeypatch, eng, vencida: bool):
    """Arranca el planificador 0,3 s y devuelve cuántas sincronizaciones lanzó."""
    llamadas = []

    async def falsa(session, include_live_apis=True):
        llamadas.append(1)

    async def correr():
        tarea = asyncio.create_task(runner.background_live_sync_daemon())
        await asyncio.sleep(0.3)
        tarea.cancel()
        await tarea

    monkeypatch.setattr(runner, "engine", eng)
    monkeypatch.setattr(runner, "run_full_ingestion", falsa)
    monkeypatch.setattr(runner, "refresh_live_database_states", lambda s: None)
    monkeypatch.setattr(settings, "sync_catchup_on_startup", True)
    if not vencida:
        with Session(eng) as s:
            _run(s, datetime.now(MADRID) + timedelta(seconds=1))  # sincronizada "ahora": nada que recuperar
    asyncio.run(correr())
    return len(llamadas)


def test_daemon_catches_up_on_startup_when_overdue(monkeypatch):
    eng = create_engine("sqlite://")
    SQLModel.metadata.create_all(eng)
    assert _arrancar_demonio(monkeypatch, eng, vencida=True) == 1


def test_daemon_does_not_sync_on_startup_when_fresh(monkeypatch):
    eng = create_engine("sqlite://")
    SQLModel.metadata.create_all(eng)
    assert _arrancar_demonio(monkeypatch, eng, vencida=False) == 0


def test_daemon_survives_a_broken_startup_check(monkeypatch):
    eng = create_engine("sqlite://")  # sin tablas: la comprobación falla
    llamadas = []

    async def correr():
        tarea = asyncio.create_task(runner.background_live_sync_daemon())
        await asyncio.sleep(0.3)
        vivo = not tarea.done()
        tarea.cancel()
        await tarea
        return vivo

    monkeypatch.setattr(runner, "engine", eng)
    monkeypatch.setattr(settings, "sync_catchup_on_startup", True)
    assert asyncio.run(correr()) is True
    assert llamadas == []
