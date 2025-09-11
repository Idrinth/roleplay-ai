from pydantic import BaseModel, Field
from enum import StrEnum
from typing import Dict, List, Optional

class Action(BaseModel):
    description: str | None = None

class Login(BaseModel):
    user_id: str | None = None
    password: str | None = None

class Register(BaseModel):
    password: str | None = None

class Chat(BaseModel):
    name: str | None = None

class World(BaseModel):
    keywords: List[str]

class Document(BaseModel):
    name: str
    content: str

class ChatStartingPoint(BaseModel):
    name: str
    location: str
    purpose: str
    weather: str
    mood: str
    wear: str
    gender: str
    heritage: str
    profession: str
    world: str
    genre: str

class User(BaseModel):
    username: str | None = None
    password: str | None = None

class Sex(StrEnum):
    MALE = "male"
    FEMALE = "female"
    NONE = "none"
    OTHER = "other"

class Language(BaseModel):
    speak: bool
    read: bool
    write: bool

    class Config:
        validate_by_name = True

class Relationship(BaseModel):
    description: str
    events: List[str]

    class Config:
        validate_by_name = True

class Character(BaseModel):
    name: str
    heritage: str
    description: str
    profession: str
    languages: Dict[str, Language]
    sex: Sex
    facts: Dict[str, str]
    relationships: Dict[str, Relationship]

    class Config:
        validate_by_name = True
        use_enum_values = True

class ChatCopy(BaseModel):
    num_messages: int = Field(ge=0)
