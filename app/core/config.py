from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    API_V1_STR: str = "/v1"
    PROJECT_NAME: str = "LLM API"

    LLAMA_SERVER_URL: str = "http://host.containers.internal:8080"
    LLAMA_TIMEOUT: int = 300

    # Seguridad
    API_KEY: str | None = None

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
