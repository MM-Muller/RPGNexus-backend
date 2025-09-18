from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase
import re

from app.api import deps
from app.crud import character as crud_character
from app.services import llm_service

from app.api.v1.endpoints.characters import character_helper

router = APIRouter()


class BattleStartPayload(BaseModel):
    character_id: str
    battle_theme: str


class ActionPayload(BaseModel):
    character_id: str
    battle_theme: str
    action: str
    history: List[str]


def parse_llm_response(response_str: str):
    narrative = response_str
    event = {"tipo": "dialogo", "danoRecebido": 0, "danoCausado": 0, "vitoria": False}

    match = re.search(
        r"\[DANO_CAUSADO:(\d+),DANO_RECEBIDO:(\d+),VITORIA:(true|false)\]", response_str
    )
    if match:
        narrative = response_str.split("[")[0].strip()
        event = {
            "tipo": "combate",
            "danoCausado": int(match.group(1)),
            "danoRecebido": int(match.group(2)),
            "vitoria": match.group(3).lower() == "true",
        }

    return narrative, event


@router.post("/start_battle", summary="Inicia uma nova batalha com IA")
async def start_battle(
    payload: BattleStartPayload,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    char_from_db = await crud_character.get_character_by_id(db, payload.character_id)
    if not char_from_db or char_from_db.get("user_id") != str(current_user.get("_id")):
        raise HTTPException(status_code=404, detail="Personagem não encontrado.")

    char = character_helper(char_from_db)

    memory = llm_service.retrieve_memory(
        character_id=payload.character_id, query=payload.battle_theme
    )

    narrative = await llm_service.generate_initial_narrative(
        char, payload.battle_theme, memory
    )

    llm_service.save_interaction(
        payload.character_id,
        f"Narrador (Início da Batalha: {payload.battle_theme}): {narrative}",
    )

    initial_event = {
        "tipo": "inicio",
        "danoRecebido": 0,
        "danoCausado": 0,
        "vitoria": False,
    }

    return {"narrativa": narrative, "evento": initial_event}


@router.post("/action", summary="Envia uma ação do jogador para a IA")
async def take_action(
    payload: ActionPayload,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    char_from_db = await crud_character.get_character_by_id(db, payload.character_id)
    if not char_from_db or char_from_db.get("user_id") != str(current_user.get("_id")):
        raise HTTPException(status_code=404, detail="Personagem não encontrado.")

    char = character_helper(char_from_db)

    context_query = f"Tema: {payload.battle_theme}. Ação do jogador: {payload.action}"
    memory = llm_service.retrieve_memory(
        character_id=payload.character_id, query=context_query
    )

    response_str = await llm_service.continue_narrative(
        char, payload.battle_theme, payload.history, payload.action, memory
    )

    narrative, event = parse_llm_response(response_str)

    llm_service.save_interaction(payload.character_id, f"Jogador: {payload.action}")
    llm_service.save_interaction(payload.character_id, f"Narrador: {narrative}")

    return {"narrativa": narrative, "evento": event}
