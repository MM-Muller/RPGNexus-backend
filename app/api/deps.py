from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import chromadb

from app.core.config import settings
from app.crud import user as crud_user

# Esta URL informa ao FastAPI qual endpoint o cliente deve usar para obter o token.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

# --- Conexão com o MongoDB ---
# Mantemos uma única instância do cliente para reutilização
mongo_client = AsyncIOMotorClient(settings.MONGODB_URL)
db = mongo_client[settings.DB_NAME]

# --- Conexão com o ChromaDB ---
# Cliente para o banco de dados vetorial
chroma_client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)


async def get_db() -> AsyncIOMotorDatabase:
    """
    Dependência para obter a instância do banco de dados MongoDB.
    """
    return db

def get_chroma_client() -> chromadb.Client:
    """
    Dependência para obter a instância do cliente do ChromaDB.
    """
    return chroma_client


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Decodifica o token JWT para obter o usuário atual.
    Levanta uma exceção HTTPException 401 se as credenciais não forem válidas.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await crud_user.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user