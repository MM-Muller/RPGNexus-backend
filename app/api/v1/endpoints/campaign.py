import json
import asyncio
import re
import random
from datetime import datetime
from bson import ObjectId

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api import deps
from app.crud import character as crud_character
from app.crud import battle as crud_battle
from app.services import llm_service
from app.api.v1.endpoints.characters import character_helper

router = APIRouter()


# Função auxiliar para serializar ObjectId
def serialize_object_id(obj: Any) -> Any:
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, dict):
        return {k: serialize_object_id(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serialize_object_id(i) for i in obj]
    return obj


# Modelos Pydantic para as payloads
class BattleStartPayload(BaseModel):
    character_id: str
    battle_theme: str


class ActionPayload(BaseModel):
    character_id: str
    battle_theme: str
    action: str
    history: List[str]


class SuggestionsPayload(BaseModel):
    character_id: str
    battle_theme: str
    history: List[str]


class BattleStatePayload(BaseModel):
    character_id: str
    battle_id: str
    battle_theme: str
    history: List[Dict[str, str]]
    player_health: int
    enemy_health: int
    last_updated: str


def parse_llm_response(response_str: str):
    narrative = response_str
    event = {"tipo": "dialogo", "danoRecebido": 0, "danoCausado": 0, "vitoria": False}

    match = re.search(r"\[DANO_CAUSADO:(\d+),DANO_RECEBIDO:(\d+)\]", response_str)
    if match:
        narrative = response_str.split("[")[0].strip()
        event = {
            "tipo": "combate",
            "danoCausado": int(match.group(1)),
            "danoRecebido": int(match.group(2)),
            "vitoria": False,  
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


@router.post("/suggestions", summary="Obtém sugestões de ação da LLM")
async def get_action_suggestions(
    payload: SuggestionsPayload,
    current_user=Depends(deps.get_current_user),
):
    try:
        suggestions_str = await llm_service.generate_action_suggestions(
            payload.battle_theme, payload.history
        )
        # Usa regex para encontrar uma lista de sugestões separadas por '|' ou em formato de lista
        match = re.search(r"([^\n]+)\|([^\n]+)\|([^\n]+)", suggestions_str)
        if match:
            suggestions = [
                match.group(1).strip(),
                match.group(2).strip(),
                match.group(3).strip(),
            ]
        else:
            suggestions = [s.strip() for s in suggestions_str.split("\n") if s.strip()][
                :3
            ]

        return {"suggestions": suggestions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/battle/{character_id}/{battle_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    character_id: str,
    battle_id: str,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: Optional[dict] = Depends(deps.get_current_user_ws),
):
    await websocket.accept()

    if not current_user:
        await websocket.close(
            code=status.HTTP_401_UNAUTHORIZED, reason="Token de autenticação inválido."
        )
        return

    try:
        battle_state_doc = await crud_battle.get_battle_state_by_character_and_user(
            db, character_id, battle_id, str(current_user["_id"])
        )
        if battle_state_doc:
            serialized_doc = serialize_object_id(battle_state_doc)
            await websocket.send_json({"type": "load_state", "payload": serialized_doc})
        else:
            battle_theme = "Conflito na Nebulosa Primordial"
            char_from_db = await crud_character.get_character_by_id(db, character_id)
            if not char_from_db or char_from_db.get("user_id") != str(
                current_user.get("_id")
            ):
                await websocket.close(code=status.HTTP_404_NOT_FOUND)
                return

            character = character_helper(char_from_db)
            memory = llm_service.retrieve_memory(character_id, battle_theme)
            narrative = await llm_service.generate_initial_narrative(
                character, battle_theme, memory
            )

            await websocket.send_json({"type": "narrative_start"})
            await asyncio.sleep(0.5)
            for line in narrative.split("\n"):
                if line.strip():
                    await websocket.send_json(
                        {"type": "narrative_chunk", "payload": line + "\n"}
                    )
                    await asyncio.sleep(0.05)

            initial_state = {
                "character_id": character_id,
                "battle_id": battle_id,
                "battle_theme": battle_theme,
                "history": [{"speaker": "Narrador", "text": narrative}],
                "player_health": 200,
                "enemy_health": 450,
                "last_updated": datetime.utcnow().isoformat(),
            }
            await crud_battle.save_battle_state(
                db, {**initial_state, "user_id": str(current_user["_id"])}
            )

            await websocket.send_json(
                {"type": "narrative_end", "payload": {"event": {}}}
            )

        while True:
            message = await websocket.receive_json()

            if message["type"] == "player_action":
                player_action = message["payload"]["action"]
                history = message["payload"]["history"]

                char_from_db = await crud_character.get_character_by_id(
                    db, character_id
                )
                if not char_from_db:
                    await websocket.close(code=status.HTTP_404_NOT_FOUND)
                    return
                char = character_helper(char_from_db)

                current_state_doc = await crud_battle.get_battle_state(
                    db, character_id, battle_id
                )
                if not current_state_doc:
                    await websocket.close(code=status.HTTP_404_NOT_FOUND)
                    return

                context_query = f"Tema: {current_state_doc.get('battle_theme', '')}. Ação do jogador: {player_action}"
                memory = llm_service.retrieve_memory(
                    character_id=character_id, query=context_query
                )

                response_str = await llm_service.continue_narrative(
                    char,
                    current_state_doc.get("battle_theme", ""),
                    history,
                    player_action,
                    memory,
                )

                narrative, event = parse_llm_response(response_str)

                llm_service.save_interaction(
                    character_id, f"{char['name']}: {player_action}"
                )
                llm_service.save_interaction(character_id, f"Narrador: {narrative}")

                updated_history = current_state_doc["history"]
                updated_history.append({"speaker": char["name"], "text": player_action})
                updated_history.append({"speaker": "Narrador", "text": narrative})

                updated_state = {
                    "history": updated_history,
                    "player_health": current_state_doc["player_health"]
                    - event.get("danoRecebido", 0),
                    "enemy_health": current_state_doc["enemy_health"]
                    - event.get("danoCausado", 0),
                    "last_updated": datetime.utcnow().isoformat(),
                }
                if updated_state["enemy_health"] <= 0 or updated_state["player_health"] <= 0:
                    event["vitoria"] = updated_state["enemy_health"] <= 0
                
                await crud_battle.save_battle_state(
                    db, {**current_state_doc, **updated_state}
                )

                # Avisa o frontend que uma nova resposta do narrador está começando
                await websocket.send_json({"type": "narrator_turn_start"})
                await asyncio.sleep(0.1) # Um pequeno delay para garantir a ordem

                sentences = re.split(r'(?<=[.!?])\s+', narrative.strip())
                for i, sentence in enumerate(sentences):
                    payload = sentence + " " if i < len(sentences) - 1 else sentence
                    if payload:
                        await websocket.send_json(
                            {"type": "narrative_chunk", "payload": payload}
                        )
                        await asyncio.sleep(min(len(payload) * 0.02, 1.5))

                # Envia a mensagem de finalização com o evento da rodada
                await websocket.send_json(
                    {"type": "narrative_end", "payload": {"event": event}}
                )

            elif message["type"] == "exit_battle":
                await crud_battle.delete_battle_state(db, character_id, battle_id)
                await websocket.close()
                break

    except WebSocketDisconnect:
        print(f"WebSocket desconectado para o personagem {character_id}")
    except Exception as e:
        print(f"Erro no WebSocket: {e}")
        await websocket.close(code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get(
    "/most-recent-state/{character_id}",
    summary="Retorna o estado de batalha mais recente de um personagem.",
)
async def get_most_recent_battle_state(
    character_id: str,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    char_from_db = await crud_character.get_character_by_id(db, character_id)
    if not char_from_db or str(char_from_db["user_id"]) != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Acesso negado.")

    battle_state = await crud_battle.get_most_recent_battle_state(
        db, character_id, str(current_user["_id"])
    )
    if not battle_state:
        raise HTTPException(
            status_code=404, detail="Nenhum estado de batalha encontrado."
        )

    return serialize_object_id(battle_state)
