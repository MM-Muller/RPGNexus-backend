from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.api import deps
from app.schemas.character import CharacterCreate
from app.crud import character as crud_character
from app.core.leveling import get_xp_for_next_level
from typing import Dict

router = APIRouter()


class ExperiencePayload(BaseModel):
    experience_points: int


class ProgressPayload(BaseModel):
    progress: Dict[str, bool]


def character_helper(character) -> dict:
    """
    Converte um personagem do formato do banco de dados para um dicionário,
    garantindo que os campos de nível e experiência tenham valores padrão.
    """
    return {
        "id": str(character["_id"]),
        "name": character["name"],
        "race": character["race"],
        "char_class": character["class"],
        "description": character.get("description"),
        "attributes": character["attributes"],
        "race_icon": character["race_icon"],
        "class_icon": character["class_icon"],
        "user_id": character["user_id"],
        "level": character.get("level", 1),
        "experience": character.get("experience", 0),
        "campaign_progress": character.get("campaign_progress", {}),
    }


@router.post("/{character_id}/add-xp", response_model=dict)
async def add_experience(
    character_id: str,
    payload: ExperiencePayload,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    char_from_db = await crud_character.get_character_by_id(db, character_id)

    if not char_from_db or str(char_from_db.get("user_id")) != str(current_user["_id"]):
        raise HTTPException(status_code=404, detail="Character not found")

    current_experience = char_from_db.get("experience", 0)
    current_level = char_from_db.get("level", 1)

    char_from_db["experience"] = current_experience + payload.experience_points
    char_from_db["level"] = current_level

    leveled_up = False
    xp_needed = get_xp_for_next_level(char_from_db["level"])

    while char_from_db["experience"] >= xp_needed:
        leveled_up = True
        char_from_db["experience"] -= xp_needed
        char_from_db["level"] += 1

        char_from_db["attributes"]["strength"] += 1
        char_from_db["attributes"]["intelligence"] += 1

        xp_needed = get_xp_for_next_level(char_from_db["level"])

    updated_char = await crud_character.update_character(db, character_id, char_from_db)

    return {
        "message": (
            f"Leveled up to {updated_char['level']}!"
            if leveled_up
            else "Experience gained."
        ),
        "character": character_helper(updated_char),
        "leveled_up": leveled_up,
    }


@router.post("/")
async def create_character(
    character: CharacterCreate,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    user_id = str(current_user["_id"])
    created_character = await crud_character.create_character(
        db=db, user_id=user_id, character=character
    )
    return character_helper(created_character)


@router.get("/")
async def get_characters(
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    user_id = str(current_user["_id"])
    characters = await crud_character.get_characters_by_user(db, user_id=user_id)
    return [character_helper(char) for char in characters]


@router.delete("/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_character(
    character_id: str,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    user_id = str(current_user["_id"])
    deleted_count = await crud_character.delete_character(
        db, character_id=character_id, user_id=user_id
    )
    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="Character not found")
    return


@router.get("/{character_id}/progress")
async def get_character_progress(
    character_id: str,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    character = await crud_character.get_character_by_id(db, character_id)
    if not character or character["user_id"] != str(current_user["_id"]):
        raise HTTPException(status_code=404, detail="Character not found")
    return {"campaign_progress": character.get("campaign_progress", {})}


@router.put("/{character_id}/progress")
async def update_character_progress(
    character_id: str,
    payload: ProgressPayload,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    character = await crud_character.get_character_by_id(db, character_id)
    if not character or character["user_id"] != str(current_user["_id"]):
        raise HTTPException(status_code=404, detail="Character not found")

    updated_character = await crud_character.update_character(
        db, character_id, {"campaign_progress": payload.progress}
    )
    return character_helper(updated_character)
