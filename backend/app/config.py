from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="BASEERAH_", extra="ignore")

    app_name: str = "Baseerah API"
    environment: str = "development"

    # Frontend origins allowed to call the API (comma-separated in env).
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # SQLite for dev; swap to a Postgres URL in production, e.g.
    # postgresql+psycopg://user:pass@host:5432/baseerah
    database_url: str = "sqlite:///./baseerah.db"

    # Analysis tuning — see app/services/analysis.py
    anomaly_z_threshold: float = 2.0
    leak_ratio_threshold: float = 1.4  # sustained consumption vs. baseline that hints at a leak

    # Auth — DEV DEFAULT ONLY. Set BASEERAH_SECRET_KEY in every non-dev environment.
    secret_key: str = "dev-insecure-change-me-in-production-0123456789"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    # LLM explanation layer (optional). Set BASEERAH_ANTHROPIC_API_KEY to enable;
    # when unset, the /explanation endpoint reports enabled=false and the app works fine.
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-opus-4-8"

    # OCR bill extraction (optional). When the Tesseract binary is missing the
    # /bills/extract endpoint reports enabled=false and the app works fine.
    tesseract_cmd: str = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    tessdata_dir: str | None = None  # defaults to <repo>/backend/tessdata when present
    ocr_languages: str = "eng+ara"


@lru_cache
def get_settings() -> Settings:
    return Settings()
