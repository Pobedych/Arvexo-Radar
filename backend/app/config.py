from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables.

    Only required settings for the currently selected provider/auth mode are
    validated at startup; see docs/12-backend.md section 9.
    """

    model_config = SettingsConfigDict(env_file=".env", env_prefix="ARVEXO_", extra="ignore")

    environment: Literal["demo", "api", "production"] = "demo"
    auth_mode: Literal["demo", "none"] = "demo"

    database_url: str = "postgresql+asyncpg://arvexo:arvexo@localhost:5432/arvexo_radar"

    storage_path: str = "/data/storage"

    max_upload_bytes: int = 25_000_000
    max_row_chars: int = 400_000

    llm_provider_mode: Literal["mock", "bothub", "local"] = "mock"
    bothub_api_key: str | None = None
    bothub_base_url: str | None = None
    bothub_model: str = "gemini-flash"
    llm_timeout_seconds: float = 30.0
    llm_max_retries: int = 2

    rate_limit_per_minute: int = 60

    log_level: str = "INFO"

    # DejaVu Sans covers Cyrillic (unlike the PDF base-14 fonts) and ships via
    # the `fonts-dejavu-core` apt package installed in the api/worker Docker
    # images (see backend/Dockerfile). Override for other environments.
    report_font_regular_path: str = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    report_font_bold_path: str = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


@lru_cache
def get_settings() -> Settings:
    return Settings()
