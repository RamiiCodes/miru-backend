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
    journal_analyzer_provider: str = "keyword"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:1b"


settings = Settings()