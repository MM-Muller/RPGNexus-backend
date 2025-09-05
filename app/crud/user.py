from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.security import get_password_hash
from app.schemas.user import UserCreate


async def get_user_by_email(db: AsyncIOMotorDatabase, email: str):
    return await db.users.find_one({"email": email})


async def create_user(db: AsyncIOMotorDatabase, user: UserCreate):
    hashed_password = get_password_hash(user.password)

    # CORREÇÃO: Use model_dump() em vez de dict() para Pydantic v2
    user_data = user.model_dump()

    user_data["hashed_password"] = hashed_password
    del user_data["password"]

    result = await db.users.insert_one(user_data)

    created_user = await db.users.find_one({"_id": result.inserted_id})

    return created_user
