from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "RPG Textual API"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "chave-secreta-para-desenvolvimento"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DB_NAME: str = "rpg_textual"

    MONGODB_URL: str = "mongodb://rpg_user:rpg_password123@db:27017"
    REDIS_URL: str = "redis://redis:6379"

    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"


settings = Settings()
