"""Application configuration loaded from environment variables.

All secrets and environment-specific values live here so nothing is
hard-coded in the codebase. Values are read once at startup and cached.
"""
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/  ->  project root is two levels up from this file's app/core
BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    # --- App ---
    APP_NAME: str = "NEET Medical College Prediction Portal"
    ENVIRONMENT: str = "development"
    API_PREFIX: str = "/api"

    # --- Security ---
    SECRET_KEY: str = "change-me-in-production-please-use-a-long-random-string"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ALGORITHM: str = "HS256"

    # --- Database ---
    # Render supplies postgres:// which SQLAlchemy 2.x rejects; we fix the scheme below.
    DATABASE_URL: str = "sqlite:///./local.db"

    # --- CORS ---
    # Comma-separated in env; parsed into a list via the cors_origins property below.
    CORS_ORIGINS: str = "http://localhost:3000"

    # --- First admin (seeded on startup if no admin exists) ---
    FIRST_ADMIN_EMAIL: str = "admin@medpredict.local"
    FIRST_ADMIN_PASSWORD: str = "Admin@12345"
    FIRST_ADMIN_NAME: str = "Super Admin"

    # --- Dataset ---
    DATASET_PATH: str = str(PROJECT_ROOT / "data" / "All_Medical_College_Last_Cutoff.xlsx")
    DATASET_SHEET: str = "All Colleges"

    @field_validator("DATABASE_URL")
    @classmethod
    def _normalise_pg_scheme(cls, v: str) -> str:
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+psycopg2://", 1)
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+psycopg2://", 1)
        return v

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
