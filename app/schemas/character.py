from pydantic import BaseModel, Field
from typing import Optional


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

    class Config:
        populate_by_name = True


class CharacterInDB(CharacterCreate):
    id: str = Field(..., alias="_id")
    user_id: str
