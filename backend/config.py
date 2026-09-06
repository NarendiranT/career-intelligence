from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://career:career@localhost:5432/career_intelligence"
    groq_api_key: str = ""
    hf_token: str = ""
    extraction_model: str = "openai/gpt-oss-20b"
    router_model: str = "openai/gpt-oss-20b"
    generation_model: str = "openai/gpt-oss-120b"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_device: str = "cpu"
    data_dir: Path = Path("data")
    jwt_secret: str = "dev-insecure-change-me"
    jwt_alg: str = "HS256"
    jwt_expire_minutes: int = 1440
    jwt_remember_expire_minutes: int = 60 * 24 * 30
    google_client_id: str = ""
    microsoft_client_id: str = ""
    microsoft_tenant_id: str = "common"
    cors_origins: str = "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174"
    otel_enabled: bool = False
    otel_service_name: str = "career-intelligence-api"
    otel_exporter_otlp_endpoint: str = "http://localhost:4318"
    embedding_dim: int = 384
    max_upload_bytes: int = 10 * 1024 * 1024
    max_question_chars: int = 8000

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
