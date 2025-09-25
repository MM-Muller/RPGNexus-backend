from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime


class BattleState(BaseModel):
    character_id: str
    battle_id: str
    battle_theme: str
    history: List[Dict[str, str]] = []
    player_health: int
    enemy_health: int
    last_updated: datetime
