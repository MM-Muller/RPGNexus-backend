# rpgnexus-backend/app/core/config.py

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Variáveis existentes
    SECRET_KEY: str
    MONGODB_URL: str
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001

    # Novas variáveis para as chaves de API das LLMs
    GOOGLE_AISTUDIO_KEY: Optional[str] = None
    GROQ_KEY: Optional[str] = None
    CLOUDFLARE_WORKERS_AI_KEY: Optional[str] = None
    CLOUDFLARE_ACCOUNT_ID: Optional[str] = None

    # Configurações do projeto
    PROJECT_NAME: str = "RPG Textual API"
    API_V1_STR: str = "/api/v1"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DB_NAME: str = "rpg_textual"

    class Config:
        env_file = ".env"


settings = Settings()
