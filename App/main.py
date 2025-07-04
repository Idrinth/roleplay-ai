import json
import re
from ollama import ChatResponse, Client
from qdrant_client import QdrantClient
from qdrant_client.http.models import QueryResponse
from fastapi import FastAPI, Cookie, BackgroundTasks, Response
import mariadb
from redis import Redis
from pymongo import MongoClient
from pydantic import BaseModel
import os
from fastapi.middleware.cors import CORSMiddleware
from bson import json_util
from bson.objectid import ObjectId
from enum import Enum, StrEnum
from typing import Annotated
import uuid
from .models import World, Action, Chat, Character, Document

def mariadb_name(user_id: str, chat_id: str):
    # max length 64
    return f"{user_id}{chat_id}".replace("-", "")

def mongodb_name(user_id: str, chat_id: str):
    # max length 63
    return f"{user_id}{chat_id}".replace("-", "")[:-1]

def simplify_result(query_result: QueryResponse):
    return query_result.model_dump(mode="json")

def is_uuid_like(string: str):
    if string is None:
        return False
    if string == "":
        return False
    try:
        uuid.UUID(string)
        return True
    except ValueError:
        return False
app = FastAPI(root_path="/api/v1", title="Gamemaster AI")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("UI_HOST", "http://localhost")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
ollama = Client(host="http://ollama:11434")
qdrant = QdrantClient("http://qdrant:6333")
qdrant.set_model(qdrant.DEFAULT_EMBEDDING_MODEL, providers=["CPUExecutionProvider"])
redis = Redis(host="redis", port=6379, db=0)
mongo = MongoClient("mongodb://root:example@mongo:27017/")
sql_connection = mariadb.connect(
    user="root",
    password="example",
    host="mariadb",
    port=3306
)
sql_connection.autocommit = True
sql_connection.auto_reconnect = True
sql_connection.cursor().execute("CREATE DATABASE IF NOT EXISTS `chat_users`;")
sql_connection.cursor().execute("CREATE TABLE IF NOT EXISTS chat_users.mapping"
                         " (user_id char(36),chat_id char(36), chat_name varchar(255), PRIMARY KEY(user_id, chat_id))"
                         " charset=utf8;")

with open('./app/character-sheet.schema.json', 'r') as schema_file:
    schema = json.dumps(json.load(schema_file))
with open('./app/rules.md', 'r') as md_file:
    rules = md_file.read()

def to_mongo_compatible(obj: BaseModel, object_id: str | None = None):
    dc = obj.dict()
    for k, v in dc.items():
        if isinstance(v, BaseModel):
            dc[k] = to_mongo_compatible(v)
        elif isinstance(v, StrEnum) or isinstance(v, Enum):
            dc[k] = v.value
    if object_id is not None:
        dc["_id"] = ObjectId(object_id)
    return dc

def update_summary(chat_id:str, user_id:str, start: int, end: int, redis_key: str):
    cursor = sql_connection.cursor()
    cursor.execute(
        f"SELECT * FROM (SELECT content, aid FROM `{mariadb_name(user_id, chat_id)}`.messages ORDER BY aid DESC LIMIT {start},{end}) as a ORDER BY aid;")
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

def update_history_dbs(chat_id:str, user_id, action: str, result: str, previous_response: str):
    qdrant.add(
        collection_name=f"{user_id}-{chat_id}",
        documents=[previous_response + "\n\n" + action + "\n\n" + result],
    )
    sql_connection.cursor().execute(f"INSERT INTO `{mariadb_name(user_id, chat_id)}`.messages (`creator`, `content`) VALUES ('user', ?);", [action])
    sql_connection.cursor().execute(f"INSERT INTO `{mariadb_name(user_id, chat_id)}`.messages (`creator`, `content`) VALUES ('agent', ?);", [result])

def get_system_prompt(characters, world: str, short_term_summary: str, medium_term_summary: str, long_term_summary: str, vectordb_results):
    out = ""
    if len(characters) >= 1:
        out += "# Player Characters:\nThe following character sheets are for reference ONLY."\
            " Do not use these to infer motivations or write actions for player characters."\
            "\n```json\n" + json.dumps(characters, default=json_util.default) + "\n```\n"\
            "## Character Sheet Schema:\n```json\n" + schema + "\n```\n"
    if len(world) > 0:
        out += "# World:\n" + ", ".join(world) + "\n"
    if short_term_summary != "":
        out += "# Short Term Summary:\n" + short_term_summary +"\n"
    if medium_term_summary != "":
        out += "# Medium Term Summary:\n" + medium_term_summary +"\n"
    if long_term_summary != "":
        out += "# Long Term Summary:\n" + long_term_summary +"\n"
    if len(vectordb_results) > 0:
        out += "# Potentially Related Information:\n```json\n" + json.dumps(vectordb_results) + "\n```"
    return out.strip()

@app.get('/')
async def root():
    return 'OK'

@app.get('/new')
async def new_chat(user_id: Annotated[str | None, Cookie()] = None):
    if not is_uuid_like(user_id):
        return {"error": "Not a valid User"}
    chat_id = str(uuid.uuid4())
    sql_connection.ping()
    sql_connection.cursor().execute(
        f"CREATE DATABASE IF NOT EXISTS `{mariadb_name(user_id, chat_id)}`;"
    )
    sql_connection.cursor().execute(
        f"CREATE TABLE IF NOT EXISTS `{mariadb_name(user_id, chat_id)}`.messages (aid BIGINT NOT NULL AUTO_INCREMENT, creator varchar(6),"
        "content text, PRIMARY KEY(aid)) charset=utf8;"
    )
    sql_connection.cursor().execute(
        f"CREATE TABLE IF NOT EXISTS {mariadb_name(user_id, chat_id)}.documents (id char(36) NOT NULL, document_name varchar(255),"
        "content text, PRIMARY KEY(id)) charset=utf8;"
    )
    sql_connection.cursor().execute(
        f"INSERT INTO chat_users.mapping (chat_id, user_id, chat_name) VALUES (?, ?, ?)",
        [chat_id, user_id, chat_id]
    )
    redis.set(f"{user_id}-{chat_id}.world", json.dumps(["fantasy", "high magic"]))
    return {"chat": chat_id}

@app.get("/chat/{chat_id}/world")
async def get_world(chat_id: str, user_id: Annotated[str | None, Cookie()] = None):
    if not is_uuid_like(user_id):
        return {"error": "Not a valid User"}
    if not is_uuid_like(chat_id):
        return {"error": "Not a valid Chat"}
    return {"world": json.loads(redis.get(f"{user_id}-{chat_id}.world") or "[]")}

@app.put("/chat/{chat_id}/world")
async def update_world(chat_id: str, world: World, user_id: Annotated[str | None, Cookie()] = None):
    if not is_uuid_like(user_id):
        return {"error": "Not a valid User"}
    if not is_uuid_like(chat_id):
        return {"error": "Not a valid Chat"}
    keywords = []
    for keyword in world.keywords:
        keyword = keyword.strip()
        if keyword not in keywords and keyword != "":
            keywords.append(keyword)
    redis.set(f"{user_id}-{chat_id}.world", json.dumps(keywords))
    return True

@app.get("/chat/{chat_id}/documents")
async def chat_document_list(chat_id: str, user_id: Annotated[str | None, Cookie()] = None):
    if not is_uuid_like(user_id):
        return {"error": "Not a valid User"}
    if not is_uuid_like(chat_id):
        return {"error": "Not a valid Chat"}
    cursor = sql_connection.cursor()
    cursor.execute(f"SELECT id, name FROM `{mariadb_name(user_id, chat_id)}`.documents;")
    documents = []
    for row in cursor.fetchall():
        documents.append({"id": row[0], "name": row[1]})
    return {
        "documents": documents,
    }

@app.get("/chat/{chat_id}/documents/{document_id}")
async def chat_document_delete(chat_id: str, document_id: str, user_id: Annotated[str | None, Cookie()] = None):
    if not is_uuid_like(user_id):
        return {"error": "Not a valid User"}
    if not is_uuid_like(chat_id):
        return {"error": "Not a valid Chat"}
    if not is_uuid_like(document_id):
        return {"error": "Not a valid Document"}
    sql_connection.cursor().execute(f"DELETE FROM `{mariadb_name(user_id, chat_id)}`.documents WHERE id='{document_id}';")
    qdrant.delete(
        collection_name=chat_id,
        points_selector=[document_id],
        wait=True,
    )
    return True

@app.post("/chat/{chat_id}/documents")
async def chat_document_add(chat_id: str, document: Document, user_id: Annotated[str | None, Cookie()] = None):
    if not is_uuid_like(user_id):
        return {"error": "Not a valid User"}
    if not is_uuid_like(chat_id):
        return {"error": "Not a valid Chat"}
    document_id = qdrant.add(
        collection_name=chat_id,
        documents=[document.content],
    )[0]
    id_uuided = str(uuid.UUID(document_id))
    sql_connection.cursor().execute(f"INSERT INTO `{mariadb_name(user_id, chat_id)}`.documents (id, name, content) VALUES (?, ?, ?);)", [id_uuided, document.name, document.content])
    return {
        "id": id_uuided,
        "name": document.name,
    }

@app.post("/chat/{chat_id}/characters")
async def chat_character_add(chat_id: str, character: Character, user_id: Annotated[str | None, Cookie()] = None):
    if not is_uuid_like(user_id):
        return {"error": "Not a valid User"}
    if not is_uuid_like(chat_id):
        return {"error": "Not a valid Chat"}
    mongo[mongodb_name(user_id, chat_id)]['characters'].insert_one(to_mongo_compatible(character))
    return True

@app.put("/chat/{chat_id}/characters/{character_id}")
async def chat_character_update(chat_id: str, character_id: str, character: Character, user_id: Annotated[str | None, Cookie()] = None):
    if not is_uuid_like(user_id):
        return {"error": "Not a valid User"}
    if not is_uuid_like(chat_id):
        return {"error": "Not a valid Chat"}
    my_col = mongo[mongodb_name(user_id, chat_id)]['characters']
    my_col.delete_one({"_id": ObjectId(character_id)})
    my_col.insert_one(to_mongo_compatible(character, character_id))
    return True

@app.delete("/chat/{chat_id}/characters/{character_id}")
async def chat_character_delete(chat_id: str, character_id: str, user_id: Annotated[str | None, Cookie()] = None):
    if not is_uuid_like(user_id):
        return {"error": "Not a valid User"}
    if not is_uuid_like(chat_id):
        return {"error": "Not a valid Chat"}
    mongo[mongodb_name(user_id, chat_id)]['characters'].delete_one({"_id": ObjectId(character_id)})
    return True

@app.get("/chat/{chat_id}/characters")
async def chat_characters(chat_id: str, user_id: Annotated[str | None, Cookie()] = None):
    if not is_uuid_like(user_id):
        return {"error": "Not a valid User"}
    if not is_uuid_like(chat_id):
        return {"error": "Not a valid Chat"}
    try:
        return json.loads(json.dumps({"characters": list(mongo[mongodb_name(user_id, chat_id)]['characters'].find())}, default=json_util.default))
    except Exception as e:
        return {"exception": f"{e}"}

@app.get("/chat/{chat_id}/active")
async def chat_active(chat_id: str, user_id: Annotated[str | None, Cookie()] = None):
    if not is_uuid_like(user_id):
        return {"error": "Not a valid User"}
    if not is_uuid_like(chat_id):
        return {"error": "Not a valid Chat"}
    return {"active": redis.get(f"{user_id}-{chat_id}.active") == "true"}

@app.delete("/chat/{chat_id}")
async def chat_delete(chat_id: str, user_id: Annotated[str | None, Cookie()] = None):
    if not is_uuid_like(user_id):
        return {"error": "Not a valid User"}
    if not is_uuid_like(chat_id):
        return {"error": "Not a valid Chat"}
    sql_connection.cursor().execute(f"DROP DATABASE `{mariadb_name(user_id, chat_id)}`;")
    await redis.delete(f"{user_id}-{chat_id}.active")
    await redis.delete(f"{user_id}-{chat_id}.short_summary")
    await redis.delete(f"{user_id}-{chat_id}.medium_summary")
    await redis.delete(f"{user_id}-{chat_id}.long_summary")
    await redis.delete(f"{user_id}-{chat_id}.world")
    mongo.drop_database(mongodb_name(user_id, chat_id))
    qdrant.delete_collection(f"{user_id}-{chat_id}")
    return True

@app.get("/whoami")
async def whoami(response: Response, user_id: Annotated[str | None, Cookie()] = None):
    if not user_id:
        user_id = str(uuid.uuid4())
    if not is_uuid_like(user_id):
        user_id = str(uuid.uuid4())
    response.set_cookie(
        key="user_id",
        value=user_id,
        samesite="strict",
        path="/",
        expires=60*60*24*30*12,
        domain=os.getenv("UI_HOST", "http://localhost").replace("http://", "").replace("https://", ""),
        httponly=True
    )
    user = {
        "id": user_id,
        "name": "User " + user_id,
        "chats": [],
    }
    sql_connection.ping()
    cursor = sql_connection.cursor()
    cursor.execute(f"SELECT chat_id, chat_name FROM chat_users.mapping WHERE user_id='{user_id}';")
    for chat_row in cursor.fetchall():
        user["chats"].append({
            "id": chat_row[0],
            "name": chat_row[1],
        })
    return user

@app.get("/chat/{chat_id}")
async def chat_history(chat_id: str, user_id: Annotated[str | None, Cookie()] = None):
    if not is_uuid_like(user_id):
        return {"error": "Not a valid User"}
    if not is_uuid_like(chat_id):
        return {"error": "Not a valid Chat"}
    try:
        messages = []
        sql_connection.ping()
        cursor = sql_connection.cursor()
        cursor.execute(f"SELECT creator, content, aid FROM `{mariadb_name(user_id, chat_id)}`.messages;")
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

@app.patch("/chat/{chat_id}")
async def chat(chat_id: str, chat_data: Chat, user_id: Annotated[str | None, Cookie()] = None):
    if not is_uuid_like(user_id):
        return {"error": "Not a valid User"}
    if not is_uuid_like(chat_id):
        return {"error": "Not a valid Chat"}
    if not chat_data.name:
        return {"error": "Chat name must be filled."}
    sql_connection.cursor().execute("UPDATE chat_users.mapping SET chat_name=? WHERE user_id=? AND chat_id=?;", [chat_data.name, user_id, chat_id])
    return True

@app.post("/chat/{chat_id}")
async def chat(chat_id: str, action: Action, background_tasks: BackgroundTasks, user_id: Annotated[str | None, Cookie()] = None):
    if not is_uuid_like(user_id):
        return {"error": "Not a valid User"}
    if not is_uuid_like(chat_id):
        return {"error": "Not a valid Chat"}
    if not os.getenv("LLM_MODEL_SUMMARY"):
        return {"error": "A model for the summary is needed."}
    if not os.getenv("LLM_MODEL_PLAY"):
        return {"error": "A model for playing is needed."}
    if not action.description:
        return {"error": "A description is required."}
    if redis.get(chat_id + ".chat_is_active") == "true":
        return {"error": "Chat is already active."}
    redis.set(f"{user_id}-{chat_id}.chat_is_active", "true")
    long_term_summary = redis.get(f"{user_id}-{chat_id}.long_text_summary") or ""
    medium_term_summary = redis.get(f"{user_id}-{chat_id}.medium_text_summary") or ""
    short_term_summary = redis.get(f"{user_id}-{chat_id}.short_text_summary") or ""
    world = ", ".join(json.loads(redis.get(f"{user_id}-{chat_id}.world") or "[]"))
    characters = []
    try:
        characters = list(mongo[mongodb_name(user_id, chat_id)]["characters"].find())
    except Exception as e:
        print(f"{e}")
    messages = []
    try:
        sql_connection.ping()
        cursor = sql_connection.cursor()
        cursor.execute(f"SELECT * FROM (SELECT creator, content, aid FROM `{mariadb_name(user_id, chat_id)}`.messages ORDER BY aid DESC LIMIT 20) as a ORDER BY aid;")
        old_messages = cursor.fetchall()
        previous_response = ""
        old_message_count = 0
        for message in old_messages:
            messages.append({
                "role": message[0],
                "content": message[1],
            })
            old_message_count += 1
            previous_response = message[1]
        messages.append({
            "role": "system",
            "content": rules
        })
        vectordb_results = []
        if qdrant.collection_exists(chat_id):
            search_result = qdrant.query(
                collection_name=f"{user_id}-{chat_id}",
                query_text=previous_response + "\n" + action.description,
                limit=10
            )
            for res in search_result:
                vectordb_results.append(simplify_result(res))
        system_prompt = get_system_prompt(characters, world, short_term_summary, medium_term_summary, long_term_summary, vectordb_results)
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
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
        background_tasks.add_task(update_history_dbs, chat_id, user_id, action.description, response_content, previous_response)
        background_tasks.add_task(update_summary, chat_id, user_id, 20, 40, f"{user_id}-{chat_id}.short_text_summary")
        background_tasks.add_task(update_summary, chat_id, user_id, 40, 80, f"{user_id}-{chat_id}.medium_text_summary")
        background_tasks.add_task(update_summary, chat_id, user_id, 80, 160, f"{user_id}-{chat_id}.long_text_summary")
        background_tasks.add_task(redis.set, f"{user_id}-{chat_id}.is-active", "false")
        return {"message": response_content, "request": messages}
    except mariadb.Error as e:
        background_tasks.add_task(redis.set, f"{user_id}-{chat_id}.chat_is-active", "false")
        return {"error": f"{e}"}
    except Exception as e:
        background_tasks.add_task(redis.set, f"{user_id}-{chat_id}.chat_is_active", "false")
        return {"exception": f"{e}", "data": e}
