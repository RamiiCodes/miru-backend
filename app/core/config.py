from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Miru API"
    environment: str = "local"
    database_url: str

    jwt_secret_key: str = "miru-local-dev-secret-change-later"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:1b"

    journal_analyzer_provider: str = "keyword"
    journal_analyzer_fallback_provider: str = "keyword"

    nvidia_api_key: str | None = None
    nvidia_nim_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_nim_model: str = "mistralai/mistral-medium-3.5-128b"
    nvidia_nim_timeout_seconds: int = 30
    nvidia_nim_max_tokens: int = 1200

    journal_analyzer_debug: bool = False


settings = Settings()