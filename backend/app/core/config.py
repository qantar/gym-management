from pydantic_settings import BaseSettings
from pydantic import field_validator, ConfigDict
from typing import List, Union
import json


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    # App
    APP_NAME: str = "GymOS Enterprise"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://gymos:gymos_secret_change_me@localhost:5432/gymos"

    # Redis
    REDIS_URL: str = "redis://:redis_secret_change_me@localhost:6379/0"

    # JWT
    SECRET_KEY: str = "dev_secret_key_change_in_production_min_32_chars_abc123"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "app://localhost",
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [o.strip() for o in v.split(",") if o.strip()]
        return v

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    MEDIA_DIR: str = "media"


settings = Settings()
