from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.api import deps
from app.core.security import create_access_token, verify_password
from app.crud import user as crud_user
from app.schemas.user import UserCreate

router = APIRouter()


@router.post("/signup")
async def create_user(
    user: UserCreate, db: AsyncIOMotorDatabase = Depends(deps.get_db)
):
    db_user = await crud_user.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )
    created_user = await crud_user.create_user(db=db, user=user)
    return created_user


@router.post("/login")
async def login(
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    db_user = await crud_user.get_user_by_email(db, email=form_data.username)
    if not db_user or not verify_password(
        form_data.password, db_user["hashed_password"]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(subject=db_user["email"])
    return {"access_token": access_token, "token_type": "bearer"}
