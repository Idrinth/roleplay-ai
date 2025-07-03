from pydantic import BaseModel, Field
from enum import StrEnum
from typing import Dict, List, Optional

class Action(BaseModel):
    description: str | None = None

class Chat(BaseModel):
    name: str | None = None

class World(BaseModel):
    keywords: List[str]

class Document(BaseModel):
    name: str
    content: str

class OathType(StrEnum):
    THALUI = "Thalui"

class ElvenRace(StrEnum):
    ASUR = "Asur"
    ASRAI = "Asrai"
    DRUCHII = "Druchii"

class VampireBloodline(StrEnum):
    BLOOD_DRAGON = "Blood Dragon"
    LAHMIAN = "Lahmian"
    VON_CARSTEIN = "von Carstein"
    NECRARCH = "Necrarch"
    STRIGOI = "Strigoi"
    VAMPIRE_COAST = "Vampire Coast"

class LanguageLevel(StrEnum):
    NONE = "none"
    BASIC = "basic"
    ADVANCED = "advanced"
    NATIVE = "native"

class MagicLevel(StrEnum):
    NONE = "none"
    NOVICE = "novice"
    APPRENTICE = "apprentice"
    JOURNEYMAN = "journeyman"
    EXPERT = "expert"
    MASTER = "master"

class Sex(StrEnum):
    MALE = "male"
    FEMALE = "female"

class Name(BaseModel):
    taken: str
    given: str
    oath: OathType
    family: str
    titles: List[str] = Field(min_length=0)

class Heritage(BaseModel):
    race: ElvenRace
    bloodline: VampireBloodline

class WhileAlive(BaseModel):
    haircolor: str
    eyecolor: str

class Eltharin(BaseModel):
    Old: Optional[LanguageLevel] = None
    Asur: Optional[LanguageLevel] = None
    Asrai: Optional[LanguageLevel] = None
    Druchii: Optional[LanguageLevel] = None

class Human(BaseModel):
    Classical: Optional[LanguageLevel] = None
    Nehekharan: Optional[LanguageLevel] = None
    Reikspiel: Optional[LanguageLevel] = None
    Bretonnian: Optional[LanguageLevel] = None

class Languages(BaseModel):
    Eltharin: Eltharin
    Human: Human
    high_magic_ritual_tongues: Optional[LanguageLevel] = Field(default=LanguageLevel.NONE)

    class Config:
        allow_population_by_field_name = True

class Background(BaseModel):
    former_occupation: str
    while_alive: WhileAlive
    description: str
    personality: List[str] = Field(min_length=1)
    place_of_birth: str
    favorite_weapon: List[str] = Field(min_length=1, max_length=2)
    combat_style: str
    siblings: Dict[str, str]
    parents: Optional[Dict[str, str]] = None
    connections: Optional[Dict[str, str]] = None

    class Config:
        allow_population_by_field_name = True

class MagicLores(BaseModel):
    Death: MagicLevel
    Shadow: MagicLevel
    Vampire: MagicLevel
    Depth: MagicLevel
    Life: MagicLevel
    Athel_Loren: MagicLevel
    High_Magic: MagicLevel
    Dark_Magic: MagicLevel

    class Config:
        allow_population_by_field_name = True

class Magic(BaseModel):
    capacity: int = Field(ge=0)
    wind_strength_increase: int = Field(ge=0)
    lores: MagicLores

    class Config:
        allow_population_by_field_name = True

class Statblock(BaseModel):
    strength: int = Field(ge=1)
    movement_speed: int = Field(ge=1)
    reaction_speed: int = Field(ge=1)
    weapon_skill: int = Field(ge=1)
    ballistic_skill: int = Field(ge=1)
    toughness: int = Field(ge=1)
    fatigue: int = Field(ge=0)

    class Config:
        allow_population_by_field_name = True

class Age(BaseModel):
    physical: int = Field(ge=0)
    human_equivalent: int = Field(ge=0)

    class Config:
        allow_population_by_field_name = True

class YearsAgo(BaseModel):
    born: int = Field(ge=18)
    turned: int = Field(ge=0)

class Roles(BaseModel):
    combat: str
    diplomacy: str
    civil: str

class Character(BaseModel):
    name: Name
    heritage: Heritage
    background: Background
    languages: Languages
    magic: Magic
    statblock: Statblock
    age: Age
    years_ago: YearsAgo
    roles: Roles
    Sex: Sex

    class Config:
        allow_population_by_field_name = True
        use_enum_values = True