from motor.motor_asyncio import AsyncIOMotorDatabase
from app.schemas.character import CharacterCreate
from bson import ObjectId
from typing import Dict, Any


async def get_character_by_id(db: AsyncIOMotorDatabase, character_id: str):
    return await db.characters.find_one({"_id": ObjectId(character_id)})


async def update_character(
    db: AsyncIOMotorDatabase, character_id: str, data: Dict[str, Any]
):
    await db.characters.update_one({"_id": ObjectId(character_id)}, {"$set": data})
    return await get_character_by_id(db, character_id)


async def create_character(
    db: AsyncIOMotorDatabase, user_id: str, character: CharacterCreate
):
    character_data = character.model_dump(by_alias=True)
    character_data["user_id"] = user_id
    result = await db.characters.insert_one(character_data)
    created_character = await db.characters.find_one({"_id": result.inserted_id})
    return created_character


async def get_characters_by_user(db: AsyncIOMotorDatabase, user_id: str):
    characters = await db.characters.find({"user_id": user_id}).to_list(100)
    return characters


async def delete_character(db: AsyncIOMotorDatabase, character_id: str, user_id: str):
    delete_result = await db.characters.delete_one(
        {"_id": ObjectId(character_id), "user_id": user_id}
    )
    return delete_result.deleted_count > 0
