from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.api import deps
from app.schemas.character import CharacterCreate
from app.crud import character as crud_character

router = APIRouter()


def character_helper(character) -> dict:
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
        raise HTTPException(
            status_code=404,
            detail="Character not found or you don't have permission to delete it",
        )
    return
