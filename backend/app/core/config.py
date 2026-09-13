from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Server-only runtime settings loaded from the environment."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "MailOps Agent"
    database_url: str = "sqlite:///./mailops.db"
    openai_api_key: SecretStr | None = None
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_model: str = "deepseek-chat"
    google_client_id: str | None = None
    google_client_secret: SecretStr | None = None
    google_redirect_uri: str = "http://localhost:8000/api/integrations/google/callback"
    token_encryption_key: SecretStr | None = None
    auto_sync_seconds: int = 0
    demo_mode: bool = False
    static_dir: str | None = None

    @property
    def llm_configured(self) -> bool:
        return self.openai_api_key is not None and bool(self.openai_api_key.get_secret_value())

    @property
    def google_configured(self) -> bool:
        return bool(
            self.google_client_id
            and self.google_client_secret
            and self.google_client_secret.get_secret_value()
            and self.token_encryption_key
            and self.token_encryption_key.get_secret_value()
        )


def get_settings() -> Settings:
    """Return a fresh settings object so tests and workers see current environment."""

    return Settings()
