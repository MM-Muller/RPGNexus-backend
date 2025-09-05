from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.security import get_password_hash
from app.schemas.user import UserCreate, UserUpdate
from bson import ObjectId


async def get_user_by_email(db: AsyncIOMotorDatabase, email: str):
    return await db.users.find_one({"email": email})


async def create_user(db: AsyncIOMotorDatabase, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    user_data = user.model_dump()
    user_data["hashed_password"] = hashed_password
    del user_data["password"]
    result = await db.users.insert_one(user_data)
    created_user = await db.users.find_one({"_id": result.inserted_id})
    return created_user


async def update_user(db: AsyncIOMotorDatabase, user_id: str, user_update: UserUpdate):
    update_data = user_update.model_dump(exclude_unset=True)
    if "password" in update_data and update_data["password"]:
        update_data["hashed_password"] = get_password_hash(update_data["password"])
        del update_data["password"]
    if update_data:
        await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
    updated_user = await db.users.find_one({"_id": ObjectId(user_id)})
    return updated_user


async def delete_user(db: AsyncIOMotorDatabase, user_id: str):
    delete_result = await db.users.delete_one({"_id": ObjectId(user_id)})
    return delete_result.deleted_count > 0
