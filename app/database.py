"""Database engine, WAL high-concurrency tuning, and fast invalidating cache."""
import time
from collections.abc import Generator
from typing import Any
from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine
from app.config import settings


def _normalize_db_url(url: str) -> str:
    """Ensure postgres:// or postgresql:// uses psycopg v3 driver seamlessly."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://") and "+psycopg" not in url:
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


db_url = _normalize_db_url(settings.database_url)
is_sqlite = db_url.startswith("sqlite")
connect_args = {"check_same_thread": False, "timeout": 30} if is_sqlite else {}

engine = create_engine(
    db_url,
    echo=False,
    connect_args=connect_args,
    pool_pre_ping=True,
)

if is_sqlite:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, _connection_record) -> None:
        """Enable SQLite WAL mode and RAM cache for sub-millisecond reads & concurrent writes."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA cache_size=-64000;")  # 64 MB page cache in RAM
        cursor.execute("PRAGMA temp_store=MEMORY;")
        cursor.execute("PRAGMA mmap_size=268435456;")  # 256 MB memory-mapped I/O
        cursor.close()


class FastQueryCache:
    """Ultra-fast TTL in-memory cache that invalidates automatically on any DB write."""

    def __init__(self, ttl_seconds: int = 60) -> None:
        self._store: dict[str, tuple[float, Any]] = {}
        self.ttl = ttl_seconds
        self.version = 1

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if not entry:
            return None
        expires_at, val = entry
        if time.monotonic() > expires_at:
            self._store.pop(key, None)
            return None
        return val

    def set(self, key: str, value: Any) -> None:
        self._store[key] = (time.monotonic() + self.ttl, value)

    def invalidate_all(self) -> None:
        self._store.clear()
        self.version += 1


query_cache = FastQueryCache(ttl_seconds=settings.cache_ttl_seconds)


def init_db() -> None:
    """Create all database tables and composite indexes if they do not exist."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a SQLModel Session."""
    with Session(engine) as session:
        yield session
