from fastapi import Depends, HTTPException, status, WebSocket
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import chromadb
from typing import Optional

from app.core.config import settings
from app.crud import user as crud_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

mongo_client = AsyncIOMotorClient(settings.MONGODB_URL)
db = mongo_client[settings.DB_NAME]

chroma_client = chromadb.HttpClient(
    host=settings.CHROMA_HOST, port=settings.CHROMA_PORT
)


async def get_db() -> AsyncIOMotorDatabase:
    return db


def get_chroma_client() -> chromadb.Client:
    return chroma_client


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncIOMotorDatabase = Depends(get_db)
):
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


async def get_current_user_ws(
    websocket: WebSocket, db: AsyncIOMotorDatabase = Depends(get_db)
) -> Optional[dict]:
    """
    Decodifica o token JWT do WebSocket para obter o usuário atual.
    Retorna o usuário ou None se a autenticação falhar.
    """
    token: Optional[str] = websocket.query_params.get("token")
    if token is None:
        return None

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            return None
    except JWTError:
        return None

    user = await crud_user.get_user_by_email(db, email=email)
    if user is None:
        return None
    return user
