from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, characters, campaign

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(characters.router, prefix="/characters", tags=["characters"])
api_router.include_router(campaign.router, prefix="/campaign", tags=["campaign"])
