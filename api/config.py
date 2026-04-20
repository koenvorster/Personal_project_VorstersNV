"""
VorstersNV — Centrale applicatieconfiguratie via pydantic-settings.
Env vars worden geladen uit .env (dev) of de omgeving (Docker/CI).
"""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    db_url: str = Field(
        default="postgresql+asyncpg://vorstersNV:dev-password-change-me@localhost:5432/vorstersNV",
        alias="DB_URL",
    )

    # Frontend / API
    base_url: str = Field(default="http://localhost:3000", alias="BASE_URL")

    # Keycloak / JWT
    keycloak_url: str = Field(default="http://localhost:8080", alias="KEYCLOAK_URL")
    keycloak_realm: str = Field(default="vorstersNV", alias="KEYCLOAK_REALM")
    keycloak_client_id: str = Field(default="vorstersNV-api", alias="KEYCLOAK_CLIENT_ID")
    keycloak_verify_aud: bool = Field(default=False, alias="KEYCLOAK_VERIFY_AUD")

    # Mollie (mock in dev)
    mollie_api_key: str = Field(default="", alias="MOLLIE_API_KEY")
    mollie_webhook_secret: str = Field(default="", alias="MOLLIE_WEBHOOK_SECRET")

    # Ollama
    ollama_url: str = Field(default="http://localhost:11434", alias="OLLAMA_URL")
    ollama_model: str = Field(default="llama3.2", alias="OLLAMA_MODEL")

    # Redis (optioneel voor rate limiting)
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "https://vorstersNV.be"],
        alias="CORS_ORIGINS",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
