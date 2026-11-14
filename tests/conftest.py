"""Pytest isolation fixture so test runs never pollute live production data/reforesta.db."""
import os
from pathlib import Path

TEST_DB_PATH = (Path(__file__).resolve().parent.parent / "data" / "test_suite.db").resolve()
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
os.environ["INCLUDE_CATALOG_TEMPLATES"] = "true"
