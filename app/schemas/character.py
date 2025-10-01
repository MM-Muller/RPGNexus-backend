from pydantic import BaseModel, Field
from typing import Optional, Dict, List


class Attributes(BaseModel):
    strength: int
    intelligence: int
    charisma: int
    dexterity: int
    intuition: int


class CharacterCreate(BaseModel):
    name: str
    race: str
    char_class: str = Field(..., alias="class")
    description: Optional[str] = None
    attributes: Attributes
    race_icon: str
    class_icon: str
    level: int = 1
    experience: int = 0
    campaign_progress: Dict[str, bool] = {}
    inventory: List[str] = []

    class Config:
        populate_by_name = True


class CharacterInDB(CharacterCreate):
    id: str = Field(..., alias="_id")
    user_id: str