"""Configuration settings for 1hack_reforesta backend."""
from datetime import date
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
FUENTES_DIR = BASE_DIR / "fuentes"
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env."""

    app_name: str = "1hack_reforesta API — Radar Vivo de Oportunidades de Reforestación e Incendios"
    app_version: str = "2.0.0"
    database_url: str = f"sqlite:///{(DATA_DIR / 'reforesta.db').as_posix()}"

    # Multi-provider LLM Judge configuration (Server env, HTTP header override, or zero-key fallback)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    openrouter_api_key: str = ""
    openrouter_model: str = "google/gemini-2.0-flash-lite-preview-02-05:free"
    enable_public_llm_fallback: bool = False  # Optional zero-key public LLM endpoint

    # Live Database & Ingestion Settings (desde 2016, sin límite superior rígido)
    ingest_start_year: int = 2016
    ingest_end_year: int = 2028
    ingest_concurrency: int = 12
    layer1_threshold: int = 25
    include_catalog_templates: bool = False  # Production uses ONLY real live sources + ./fuentes/*.pdf
    auto_sync_enabled: bool = True
    daily_sync_hour: int = 7
    daily_sync_minute: int = 0
    daily_sync_timezone: str = "Europe/Madrid"
    auto_sync_interval_minutes: int = 1440
    cache_ttl_seconds: int = 60
    public_backend_url: str = "http://localhost:8000"

    # Reference date for calculating active/closed status
    reference_date: date | None = None

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def get_today(self) -> date:
        """Return reference date if set, otherwise today's date."""
        return self.reference_date or date.today()


settings = Settings()
