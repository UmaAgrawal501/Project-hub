from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_name: str = "ProjectHub API"
    api_v1_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000"
    log_level: str = "INFO"

    database_url: str

    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    supabase_jwt_secret: str

    password_reset_redirect_url: str = "http://localhost:3000/reset-password"

    storage_bucket: str = "project-files"
    signed_upload_ttl_seconds: int = 300
    signed_download_ttl_seconds: int = 120
    upload_token_secret: str | None = None

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def upload_signing_secret(self) -> str:
        return self.upload_token_secret or self.supabase_jwt_secret


@lru_cache
def get_settings() -> Settings:
    return Settings()
