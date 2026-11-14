"""Pytest isolation fixture so test runs never pollute live production data/reforesta.db."""
import os
from pathlib import Path

TEST_DB_PATH = (Path(__file__).resolve().parent.parent / "data" / "test_suite.db").resolve()
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
os.environ["INCLUDE_CATALOG_TEMPLATES"] = "true"
# Las pruebas no deben lanzar una sincronización real contra BDNS/BOE/TED al arrancar la app
os.environ["SYNC_CATCHUP_ON_STARTUP"] = "false"
