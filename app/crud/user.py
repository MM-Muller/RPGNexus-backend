from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.security import get_password_hash
from app.schemas.user import UserCreate


async def get_user_by_email(db: AsyncIOMotorDatabase, email: str):
    return await db.users.find_one({"email": email})


async def create_user(db: AsyncIOMotorDatabase, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    user_data = user.dict()
    user_data["hashed_password"] = hashed_password
    del user_data["password"]

    await db.users.insert_one(user_data)

    # Após a inserção, podemos retornar o objeto sem a senha hashada
    del user_data["hashed_password"]
    return user_data
