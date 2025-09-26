from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from typing import Dict, Any, Optional
from datetime import datetime


async def get_battle_state(
    db: AsyncIOMotorDatabase, character_id: str, battle_id: str
) -> Optional[Dict[str, Any]]:
    return await db.battle_states.find_one(
        {"character_id": character_id, "battle_id": battle_id}
    )


async def get_battle_state_by_id(
    db: AsyncIOMotorDatabase, battle_id: str
) -> Optional[Dict[str, Any]]:
    return await db.battle_states.find_one({"_id": ObjectId(battle_id)})


async def get_battle_state_by_character_and_user(
    db: AsyncIOMotorDatabase, character_id: str, battle_id: str, user_id: str
) -> Optional[Dict[str, Any]]:
    return await db.battle_states.find_one(
        {"character_id": character_id, "battle_id": battle_id, "user_id": user_id}
    )


async def get_most_recent_battle_state(
    db: AsyncIOMotorDatabase, character_id: str, user_id: str
) -> Optional[Dict[str, Any]]:
    return await db.battle_states.find_one(
        {"character_id": character_id, "user_id": user_id}, sort=[("last_updated", -1)]
    )


async def save_battle_state(db: AsyncIOMotorDatabase, battle_state: Dict[str, Any]):
    # Atualiza se existir, ou insere um novo documento
    await db.battle_states.update_one(
        {
            "character_id": battle_state["character_id"],
            "battle_id": battle_state["battle_id"],
        },
        {"$set": battle_state},
        upsert=True,
    )


async def delete_battle_state(
    db: AsyncIOMotorDatabase, character_id: str, battle_id: str
):
    await db.battle_states.delete_one(
        {"character_id": character_id, "battle_id": battle_id}
    )


async def delete_battle_state_by_id(db: AsyncIOMotorDatabase, battle_id: str):
    await db.battle_states.delete_one({"_id": ObjectId(battle_id)})
