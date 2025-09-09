from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    SECRET_KEY: str

    MONGODB_URL: str

    REDIS_URL: str

    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    PROJECT_NAME: str = "RPG Textual API"
    API_V1_STR: str = "/api/v1"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DB_NAME: str = "rpg_textual"

    class Config:
        env_file = ".env"


settings = Settings()
