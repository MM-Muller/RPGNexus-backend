from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api import deps
from app.crud import character as crud_character
from app.services import llm_service

router = APIRouter()


class BattleStartPayload(BaseModel):
    character_id: str
    battle_theme: str


class ActionPayload(BaseModel):
    character_id: str
    battle_theme: str
    action: str
    history: List[str]  # Histórico da batalha atual


@router.post("/start_battle", summary="Inicia uma nova batalha com IA")
async def start_battle(
    payload: BattleStartPayload,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """
    Inicia uma nova batalha. A LLM gera a narrativa inicial com base no tema
    e nas memórias passadas do personagem.
    """
    char = await crud_character.get_character_by_id(db, payload.character_id)
    if not char or char.get("user_id") != str(current_user.get("_id")):
        raise HTTPException(status_code=404, detail="Personagem não encontrado.")

    # Busca memórias relevantes no ChromaDB para dar contexto à LLM
    memory = llm_service.retrieve_memory(
        character_id=payload.character_id, query=payload.battle_theme
    )

    narrative = await llm_service.generate_initial_narrative(
        char, payload.battle_theme, memory
    )

    # Salva a narrativa inicial como a primeira memória desta batalha
    llm_service.save_interaction(
        payload.character_id,
        f"Narrador (Início da Batalha: {payload.battle_theme}): {narrative}",
    )

    return {"narrative": narrative}


@router.post("/action", summary="Envia uma ação do jogador para a IA")
async def take_action(
    payload: ActionPayload,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """
    Processa a ação de um jogador, continua a narrativa com a LLM e salva
    a interação no histórico de memória.
    """
    char = await crud_character.get_character_by_id(db, payload.character_id)
    if not char or char.get("user_id") != str(current_user.get("_id")):
        raise HTTPException(status_code=404, detail="Personagem não encontrado.")

    # Busca memórias relevantes para a ação atual
    context_query = f"Tema: {payload.battle_theme}. Ação do jogador: {payload.action}"
    memory = llm_service.retrieve_memory(
        character_id=payload.character_id, query=context_query
    )

    narrative = await llm_service.continue_narrative(
        char, payload.battle_theme, payload.history, payload.action, memory
    )

    # Salva a ação do jogador e a resposta da LLM na memória (ChromaDB)
    llm_service.save_interaction(payload.character_id, f"Jogador: {payload.action}")
    llm_service.save_interaction(payload.character_id, f"Narrador: {narrative}")

    return {"narrative": narrative}
