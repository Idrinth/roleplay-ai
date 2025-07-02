import json
import re

from ollama import ChatResponse, Client
from qdrant_client import QdrantClient
from qdrant_client.http.models import QueryResponse
from fastapi import FastAPI, Cookie, BackgroundTasks
import mariadb
from redis import Redis
from pymongo import MongoClient
from pydantic import BaseModel, Field
import os
import enum
from fastapi.middleware.cors import CORSMiddleware
from bson import json_util
from enum import Enum, StrEnum
from typing import Dict, List, Optional
import uuid

def simplify_result(query_result: QueryResponse):
    return query_result.model_dump(mode="json")

def is_uuid_like(string: str):
    try:
        uuid.UUID(string)
        return True
    except ValueError:
        return False
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost', 'http://127.0.0.1', 'http://92.205.177.104:8080'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
ollama = Client(host="http://ollama:11434")
qdrant = QdrantClient("http://qdrant:6333")
qdrant.set_model(qdrant.DEFAULT_EMBEDDING_MODEL, providers=["CPUExecutionProvider"])
redis = Redis(host="redis", port=6379, db=0)
mongo = MongoClient("mongodb://root:example@mongo:27017/")
mdbconn = mariadb.connect(
    user="root",
    password="example",
    host="mariadb",
    port=3306
)
mdbconn.autocommit = True
mdbconn.auto_reconnect = True
with open('./app/character-sheet.schema.json', 'r') as schemafile:
    schema = json.dumps(json.load(schemafile))
with open('./app/rules.md', 'r') as mdfile:
    rules = mdfile.read()


class Action(BaseModel):
    description: str | None = None

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
    titles: List[str] = Field(min_length=1)

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
    high_magic_ritual_tongues: Optional[LanguageLevel] = Field(
        default=None,
        alias="High Magic ritual tongues"
    )

    class Config:
        allow_population_by_field_name = True

class Background(BaseModel):
    former_occupation: str = Field(alias="former occupation")
    while_alive: WhileAlive = Field(alias="while alive")
    description: str
    personality: List[str] = Field(min_length=1)
    place_of_birth: str = Field(alias="place of birth")
    favorite_weapon: List[str] = Field(min_length=1, alias="favorite weapon")
    combat_style: str = Field(alias="combat style")
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
    Athel_Loren: MagicLevel = Field(alias="Athel Loren")
    High_Magic: MagicLevel = Field(alias="High Magic")
    Dark_Magic: MagicLevel = Field(alias="Dark Magic")

    class Config:
        allow_population_by_field_name = True

class Magic(BaseModel):
    capacity: int = Field(ge=0)
    wind_strength_increase: int = Field(ge=0, alias="wind strength increase")
    lores: MagicLores

    class Config:
        allow_population_by_field_name = True

class Statblock(BaseModel):
    strength: int = Field(ge=1)
    movement_speed: int = Field(ge=1, alias="movement speed")
    reaction_speed: int = Field(ge=1, alias="reaction speed")
    weapon_skill: int = Field(ge=1, alias="weapon skill")
    ballistic_skill: int = Field(ge=1, alias="ballistic skill")
    toughness: int = Field(ge=1)
    fatigue: int = Field(ge=0)

    class Config:
        allow_population_by_field_name = True

class Age(BaseModel):
    physical: int = Field(ge=0)
    human_equivalent: int = Field(ge=0, alias="human-equivalent")

    class Config:
        allow_population_by_field_name = True

class YearsAgo(BaseModel):
    born: int = Field(ge=0)
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
    years_ago: YearsAgo = Field(alias="years ago")
    roles: Roles
    Sex: Sex

    class Config:
        allow_population_by_field_name = True
        use_enum_values = True

def to_mongo_compatible(obj:BaseModel, id: str|None = None):
    dc = obj.dict()
    for k, v in dc.items():
        if isinstance(v, BaseModel):
            dc[k] = to_mongo_compatible(v)
        elif isinstance(v, StrEnum) or isinstance(v, Enum):
            dc[k] = v.value
    if id is not None:
        dc["_id"] = id
    return dc

def update_summary(start: int, end: int, redis_key: str):
    cursor = mdbconn.cursor()
    cursor.execute(
        f"SELECT * FROM (SELECT content, aid FROM messages ORDER BY aid DESC LIMIT {start},{end}) as a ORDER BY aid;")
    summary = ""
    for message in cursor.fetchall():
        summary += message[1] + "\n"
    if summary:
        response: ChatResponse = ollama.chat(
            model=os.getenv("LLM_MODEL_SUMMARY"),
            messages=[{
                "role": "user",
                "content": \
                    "Please summarize the following story extract in a brief paragraph, so that the major developments are known:\n"
                    + summary,
            }]
        )
        response_content = re.sub("^(\n|.)*</think>\\s*", "", response["message"]["content"]).strip()
        redis.set(redis_key, response_content)

def update_history_dbs(chat_id:str, action: str, result: str, previous_response: str):
    qdrant.add(
        collection_name=chat_id,
        documents=[previous_response + "\n\n" + action + "\n\n" + result],
    )
    mdbconn.cursor().execute("INSERT INTO `"+chat_id+"`.messages (`creator`, `content`) VALUES ('user', ?);", [action])
    mdbconn.cursor().execute("INSERT INTO `"+chat_id+"`.messages (`creator`, `content`) VALUES ('agent', ?);", [result])



@app.get('/')
async def root():
    return 'OK'

@app.get('/new')
async def new_chat():
    local_uuid = uuid.uuid4()
    mdbconn.ping()
    mdbconn.cursor().execute("CREATE DATABASE IF NOT EXISTS `"+local_uuid+"`;")
    mdbconn.cursor().execute(
        f"CREATE TABLE IF NOT EXISTS `{local_uuid}`.messages (aid BIGINT NOT NULL AUTO_INCREMENT, creator varchar(6),"
        "content text, PRIMARY KEY(aid)) charset=utf8;")
    return {'chat': local_uuid}

@app.post("/chat/{chat_id}/characters")
def chat_character(chat_id: str, character: Character):
    if not is_uuid_like(chat_id):
        return False
    mydb = mongo[chat_id]
    mydb['characters'].insert_one(to_mongo_compatible(character))
    return True

@app.put("/chat/{chat_id}/characters/{id}")
def chat_character(chat_id: str, id: str, character: Character):
    if not is_uuid_like(chat_id):
        return False
    mydb = mongo[chat_id]
    mydb['characters'].delete_one({"_id": id})
    mydb['characters'].insert_one(to_mongo_compatible(character, id))
    return True

@app.delete("/chat/{chat_id}/characters/{id}")
def chat_character(chat_id: str, id: str):
    if not is_uuid_like(chat_id):
        return False
    mydb = mongo[chat_id]
    mydb['characters'].delete_one({"_id": id})
    return True

@app.get("/chat/{chat_id}/characters")
def chat_character(chat_id: str):
    if not is_uuid_like(chat_id):
        return {"error": "Not a valid UUID"}
    try:
        return json.loads(json.dumps({"characters": list(mongo[chat_id]['characters'].find())}, default=json_util.default))
    except Exception as e:
        return {"exception": f"{e}"}

@app.get("/chat/{chat_id}")
def chat_history(chat_id: str):
    if not is_uuid_like(chat_id):
        return {"error": "Not a valid UUID"}
    try:
        messages = []
        mdbconn.ping()
        cursor = mdbconn.cursor()
        cursor.execute(f"SELECT creator, content, aid FROM `{chat_id}`.messages;")
        old_messages = cursor.fetchall()
        for message in old_messages:
            messages.append({
                "role": message[0],
                "content": message[1],
            })
        return {"messages": messages}
    except mariadb.Error as e:
        return {"error": f"{e}"}
    except Exception as e:
        return {"exception": e}

@app.post("/chat/{chat_id}")
def chat(chat_id: str, action: Action, background_tasks: BackgroundTasks):
    if not is_uuid_like(chat_id):
        return {"error": "Not a valid UUID"}
    if not os.getenv("LLM_MODEL_SUMMARY"):
        return {"error": "A model for the summary is needed."}
    if not os.getenv("LLM_MODEL_PLAY"):
        return {"error": "A model for playing is needed."}
    if not action.description:
        return {"error": "A description is required."}
    long_term_summary = redis.get(chat_id + ".long_text_summary") or "Nothing happened yet."
    medium_term_summary = redis.get(chat_id + ".medium_text_summary") or "Nothing happened yet."
    short_term_summary = redis.get(chat_id + ".short_text_summary") or "Nothing happened yet."
    characters = []
    try:
        mydb = mongo[chat_id]
        mycol = mydb["characters"]
        characters = list(mycol.find())
    except Exception as e:
        print(f"{e}")
    world = "dark fantasy, Warhammer Fantasy"
    messages = []
    try:
        mdbconn.ping()
        cursor = mdbconn.cursor()
        cursor.execute(f"SELECT * FROM (SELECT creator, content, aid FROM `{chat_id}`.messages ORDER BY aid DESC LIMIT 20) as a ORDER BY aid;")
        old_messages = cursor.fetchall()
        previous_response = ""
        for message in old_messages:
            messages.append({
                "role": message[0],
                "content": message[1],
            })
            previous_response = message[1]
        messages.append({
            "role": "system",
            "content": rules
        })
        vectordb_results = []
        if qdrant.collection_exists(chat_id):
            search_result = qdrant.query(
                collection_name=chat_id,
                query_text=previous_response + "\n" + action.description,
                limit=10
            )
            for res in search_result:
                vectordb_results.append(simplify_result(res))
        messages.append({
            "role": "system",
            "content": "# Player Characters:\nThe following character sheets are for reference ONLY."
                " Do not use these to infer motivations or write actions for player characters."
                "\n```json\n" + json.dumps(characters, default=json_util.default) +
                "\n```\n"
                "## Character Sheet Schema:\n```json\n" + schema +
                "\n```\n"
                "# World:\n" + world +
                "\n"
                "# Short Term Summary:\n" + short_term_summary +
                "\n"
                "# Medium Term Summary:\n" + medium_term_summary +
                "\n"
                "# Long Term Summary:\n" + long_term_summary +
                "\n"
                "# Potentially Related Information:\n```json\n" + json.dumps(vectordb_results) + "\n```"
        })
        messages.append({
            "role": "user",
            "content": action.description,
        })
        response: ChatResponse = ollama.chat(
            model=os.getenv("LLM_MODEL_PLAY"),
            messages=messages
        )
        response_content = re.sub("^(\n|.)*</think>\\s*", "", response["message"]["content"]).strip()
        background_tasks.add_task(update_history_dbs, chat_id, action.description, response_content, previous_response)
        background_tasks.add_task(update_summary, 20, 40, chat_id + ".short_text_summary")
        background_tasks.add_task(update_summary, 40, 80, chat_id + ".medium_text_summary")
        background_tasks.add_task(update_summary, 80, 160, chat_id + ".long_text_summary")
        background_tasks.add_task(update_summary, 80, 160, chat_id + ".long_text_summary")
        return {"message": response_content, "request": messages}
    except mariadb.Error as e:
        return {"error": f"{e}"}
    except Exception as e:
        return {"exception": f"{e}", "data": e}
