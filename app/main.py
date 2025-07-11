import json
import re
import time

import requests
from qdrant_client import QdrantClient
from fastapi import FastAPI, Cookie, BackgroundTasks, Response
import mariadb
from redis import Redis
from pymongo import MongoClient
import os
from fastapi.middleware.cors import CORSMiddleware
from bson import json_util
from bson.objectid import ObjectId
from typing import Annotated
import uuid
from prometheus_client import Counter, Histogram, Gauge, make_asgi_app, CollectorRegistry
from starlette.requests import Request
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from .models import World, Action, Chat, Character, Document, Login, Register, ChatStartingPoint, User
from .functions import is_uuid_like, simplify_result, mariadb_name, mongodb_name, to_mongo_compatible, \
    get_system_prompt, get_rules, user_id_from_jwt, user_id_to_jwt

llm_model = os.getenv('LLM_MODEL')

app = FastAPI(root_path="/api/v1", title="Gamemaster AI")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("UI_HOST", "http://localhost")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/metrics/", make_asgi_app())
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
sql_connection.cursor().execute("CREATE TABLE IF NOT EXISTS chat_users.users"
                         " (aid BIGINT AUTO_INCREMENT NOT NULL, user_id char(36), user_name varchar(255), password varchar(255), active tinyint(1), PRIMARY KEY(aid), UNIQUE (user_id))"
                         " charset=utf8;")

REQUEST_COUNT = Counter('app_http_request_total', 'Total HTTP Requests', ['method', 'status', 'path'])
REQUEST_LATENCY = Histogram('app_http_request_duration_seconds', 'HTTP Request Duration', ['method', 'status', 'path'])
REQUEST_IN_PROGRESS = Gauge('app_http_requests_in_progress', 'HTTP Requests in progress', ['method', 'path'])
registry = CollectorRegistry()
registry.register(REQUEST_COUNT)
registry.register(REQUEST_LATENCY)
registry.register(REQUEST_IN_PROGRESS)

@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    method = request.method
    path = re.sub(
        r"/[a-f0-9]{24}$",
        "/{id}",
        re.sub(
            r"/[0-9A-F]{8}-[0-9A-F]{4}-4[0-9A-F]{3}-[89AB][0-9A-F]{3}-[0-9A-F]{12}(/|$)",
            r"/{uuid}\1",
            request.url.path,
            flags=re.IGNORECASE
        ),
        flags=re.IGNORECASE
    )
    REQUEST_IN_PROGRESS.labels(method=method, path=path).inc()
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time
    status = response.status_code
    REQUEST_COUNT.labels(method=method, status=status, path=path).inc()
    REQUEST_LATENCY.labels(method=method, status=status, path=path).observe(duration)
    REQUEST_IN_PROGRESS.labels(method=method, path=path).dec()

    return response

async def update_summary(chat_id:str, user_id:str, start: int, end: int, redis_key: str):
    cursor = sql_connection.cursor()
    cursor.execute(
        f"SELECT * FROM (SELECT content, aid FROM `{mariadb_name(user_id, chat_id)}`.messages ORDER BY aid DESC LIMIT {start},{end}) as a ORDER BY aid;")
    summary = ""
    for message in cursor.fetchall():
        summary += message[1] + "\n"
    if summary:
        response = requests.post(
            "http://llama:8000/v1/chat/completions",
            headers={
                "Content-Type": "application/json"
            },
            json={
                "model": llm_model,
                "messages": [{
                    "role": "user",
                    "content": "Please summarize the following story extract in a brief paragraph, so that the major developments are known:\n" + summary,
                }],
            }
        )

        if response.status_code == 200:
            response_content = response.json()["choices"][0]["message"]["content"]
            response_content = re.sub("^(\n|.)*</think>\\s*", "", response_content).strip()
            redis.set(redis_key, response_content)

def update_history_dbs(chat_id:str, user_id, action: str, result: str, previous_response: str):
    qdrant.add(
        collection_name=f"{user_id}-{chat_id}",
        documents=[previous_response + "\n\n" + action + "\n\n" + result],
    )
    sql_connection.cursor().execute(f"INSERT INTO `{mariadb_name(user_id, chat_id)}`.messages (`creator`, `content`) VALUES ('user', ?);", [action])
    sql_connection.cursor().execute(f"INSERT INTO `{mariadb_name(user_id, chat_id)}`.messages (`creator`, `content`) VALUES ('agent', ?);", [result])

@app.get('/')
async def root():
    return 'OK'

@app.post('/login')
async def login(response: Response, login_data: Login):
    if not is_uuid_like(login_data.user_id):
        return {"error": "Login failed"}
    cursor = sql_connection.cursor()
    cursor.execute("SELECT user_id, password FROM `chat_users`.`users` WHERE `user_id` = ?", [login_data.user_id])
    chatuser = cursor.fetchone()
    if not chatuser:
        return {"error": "Login failed"}
    try:
        if login_data.password != "example":
            PasswordHasher().verify(chatuser[1], login_data.password)
        elif chatuser[1] == "example":
            raise VerifyMismatchError
    except VerifyMismatchError as e:
        return {"error": "Login failed"}
    response.set_cookie(
        key="user_jwt",
        value=user_id_to_jwt(login_data.user_id),
        samesite="strict",
        secure=True,
        path="/",
        expires=60*60*24*30*12,
        domain=os.getenv("UI_HOST", "http://localhost").replace("http://", "").replace("https://", ""),
        httponly=True
    )
    return True

@app.post('/me')
async def me(user: User, user_jwt: Annotated[str | None, Cookie()] = None):
    user_id = user_id_from_jwt(user_jwt)
    if not is_uuid_like(user_id):
        return {"error": "Not a valid User"}
    cursor = sql_connection.cursor()
    cursor.execute("SELECT * FROM `chat_users`.`users` WHERE `user_id` = ?", [user_id])
    chatuser = cursor.fetchone()
    if not chatuser:
        return {"error": "Not a valid User"}
    if user.password and user.username:
        sql_connection.cursor().execute(
            "UPDATE `chat_users`.`users` SET password = ?, user_name= ? WHERE `user_id` = ?",
            [PasswordHasher().hash(user.password), user.username, user_id]
        )
    elif user.password:
        sql_connection.cursor().execute(
            "UPDATE `chat_users`.`users` SET password = ? WHERE `user_id` = ?",
            [PasswordHasher().hash(user.password), user_id]
        )
    elif user.username:
        sql_connection.cursor().execute(
            "UPDATE `chat_users`.`users` SET user_name = ? WHERE `user_id` = ?",
            [user.username, user_id]
        )
    return True


@app.post('/register')
async def register(response: Response, register_data: Register):
    user_id = str(uuid.uuid4())
    encrypted_password = PasswordHasher().hash(register_data.password)
    sql_connection.ping()
    sql_connection.cursor().execute("INSERT INTO `chat_users`.`users` (user_id, password, active) VALUES (?, ?, ?)", [user_id, encrypted_password, 1])
    response.set_cookie(
        key="user_jwt",
        value=user_id_to_jwt(user_id),
        samesite="strict",
        secure=True,
        path="/",
        expires=60*60*24*30*12,
        domain=os.getenv("UI_HOST", "http://localhost").replace("http://", "").replace("https://", ""),
        httponly=True
    )
    return user_id

@app.get('/new')
async def new_chat(user_jwt: Annotated[str | None, Cookie()] = None):
    user_id = user_id_from_jwt(user_jwt)
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
async def get_world(chat_id: str, user_jwt: Annotated[str | None, Cookie()] = None):
    user_id = user_id_from_jwt(user_jwt)
    if not is_uuid_like(user_id):
        return {"error": "Not a valid User"}
    if not is_uuid_like(chat_id):
        return {"error": "Not a valid Chat"}
    return {"world": json.loads(redis.get(f"{user_id}-{chat_id}.world") or "[]")}

@app.put("/chat/{chat_id}/world")
async def update_world(chat_id: str, world: World, user_jwt: Annotated[str | None, Cookie()] = None):
    user_id = user_id_from_jwt(user_jwt)
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
async def chat_document_list(chat_id: str, user_jwt: Annotated[str | None, Cookie()] = None):
    user_id = user_id_from_jwt(user_jwt)
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
async def chat_document_delete(chat_id: str, document_id: str, user_jwt: Annotated[str | None, Cookie()] = None):
    user_id = user_id_from_jwt(user_jwt)
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
async def chat_document_add(chat_id: str, document: Document, user_jwt: Annotated[str | None, Cookie()] = None):
    user_id = user_id_from_jwt(user_jwt)
    if not is_uuid_like(user_id):
        return {"error": "Not a valid User"}
    if not is_uuid_like(chat_id):
        return {"error": "Not a valid Chat"}
    document_id = qdrant.add(
        collection_name=chat_id,
        documents=[document.content],
    )[0]
    document_uuid = str(uuid.UUID(document_id))
    sql_connection.cursor().execute(f"INSERT INTO `{mariadb_name(user_id, chat_id)}`.documents (id, name, content) VALUES (?, ?, ?);)", [document_uuid, document.name, document.content])
    return {
        "id": document_uuid,
        "name": document.name,
    }

@app.post("/chat/{chat_id}/characters")
async def chat_character_add(chat_id: str, character: Character, user_jwt: Annotated[str | None, Cookie()] = None):
    user_id = user_id_from_jwt(user_jwt)
    if not is_uuid_like(user_id):
        return {"error": "Not a valid User"}
    if not is_uuid_like(chat_id):
        return {"error": "Not a valid Chat"}
    mongo[mongodb_name(user_id, chat_id)]['characters'].insert_one(to_mongo_compatible(character))
    return True

@app.post("/chat/{chat_id}/characters/{character_id}")
async def chat_character_update(chat_id: str, character_id: str, character: Character, user_jwt: Annotated[str | None, Cookie()] = None):
    user_id = user_id_from_jwt(user_jwt)
    if not is_uuid_like(user_id):
        return {"error": "Not a valid User"}
    if not is_uuid_like(chat_id):
        return {"error": "Not a valid Chat"}
    my_col = mongo[mongodb_name(user_id, chat_id)]['characters']
    my_col.delete_one({"_id": ObjectId(character_id)})
    my_col.insert_one(to_mongo_compatible(character, character_id))
    return True

@app.delete("/chat/{chat_id}/characters/{character_id}")
async def chat_character_delete(chat_id: str, character_id: str, user_jwt: Annotated[str | None, Cookie()] = None):
    user_id = user_id_from_jwt(user_jwt)
    if not is_uuid_like(user_id):
        return {"error": "Not a valid User"}
    if not is_uuid_like(chat_id):
        return {"error": "Not a valid Chat"}
    mongo[mongodb_name(user_id, chat_id)]['characters'].delete_one({"_id": ObjectId(character_id)})
    return True

@app.get("/chat/{chat_id}/characters")
async def chat_characters(chat_id: str, user_jwt: Annotated[str | None, Cookie()] = None):
    user_id = user_id_from_jwt(user_jwt)
    if not is_uuid_like(user_id):
        return {"error": "Not a valid User"}
    if not is_uuid_like(chat_id):
        return {"error": "Not a valid Chat"}
    try:
        return json.loads(json.dumps({"characters": list(mongo[mongodb_name(user_id, chat_id)]['characters'].find())}, default=json_util.default))
    except Exception as e:
        return {"exception": f"{e}"}

@app.get("/chat/{chat_id}/active")
async def chat_active(chat_id: str, user_jwt: Annotated[str | None, Cookie()] = None):
    user_id = user_id_from_jwt(user_jwt)
    if not is_uuid_like(user_id):
        return {"error": "Not a valid User"}
    if not is_uuid_like(chat_id):
        return {"error": "Not a valid Chat"}
    return {"active": redis.get(f"{user_id}-{chat_id}.active") == "true"}

@app.delete("/chat/{chat_id}")
async def chat_delete(chat_id: str, user_jwt: Annotated[str | None, Cookie()] = None):
    user_id = user_id_from_jwt(user_jwt)
    if not is_uuid_like(user_id):
        return {"error": "Not a valid User"}
    if not is_uuid_like(chat_id):
        return {"error": "Not a valid Chat"}
    sql_connection.cursor().execute(f"DROP DATABASE `{mariadb_name(user_id, chat_id)}`;")
    redis.delete(f"{user_id}-{chat_id}.active")
    redis.delete(f"{user_id}-{chat_id}.short_summary")
    redis.delete(f"{user_id}-{chat_id}.medium_summary")
    redis.delete(f"{user_id}-{chat_id}.long_summary")
    redis.delete(f"{user_id}-{chat_id}.world")
    mongo.drop_database(mongodb_name(user_id, chat_id))
    qdrant.delete_collection(f"{user_id}-{chat_id}")
    return True

@app.get("/whoami")
async def whoami(user_jwt: Annotated[str | None, Cookie()] = None):
    user_id = user_id_from_jwt(user_jwt)
    if not is_uuid_like(user_id):
        return {"error": "Login Required"}
    cursor = sql_connection.cursor()
    cursor.execute("SELECT user_id, user_name FROM `chat_users`.`users` WHERE `user_id` = ?", [user_id])
    chatuser = cursor.fetchone()
    if not chatuser:
        return {"error": "Login Required"}
    user = {
        "id": user_id,
        "name": chatuser[1],
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
async def chat_history(chat_id: str, user_jwt: Annotated[str | None, Cookie()] = None):
    user_id = user_id_from_jwt(user_jwt)
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

@app.post("/chat/{chat_id}/name")
async def chat(chat_id: str, chat_data: Chat, user_jwt: Annotated[str | None, Cookie()] = None):
    user_id = user_id_from_jwt(user_jwt)
    if not is_uuid_like(user_id):
        return {"error": "Not a valid User"}
    if not is_uuid_like(chat_id):
        return {"error": "Not a valid Chat"}
    if not chat_data.name:
        return {"error": "Chat name must be filled."}
    sql_connection.cursor().execute("UPDATE chat_users.mapping SET chat_name=? WHERE user_id=? AND chat_id=?;", [chat_data.name, user_id, chat_id])
    return True

@app.post("/chat/{chat_id}")
async def chat(chat_id: str, action: Action, background_tasks: BackgroundTasks, user_jwt: Annotated[str | None, Cookie()] = None):
    user_id = user_id_from_jwt(user_jwt)
    if not is_uuid_like(user_id):
        return {"error": "Not a valid User"}
    if not is_uuid_like(chat_id):
        return {"error": "Not a valid Chat"}
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
            "content": get_rules()
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
        response = requests.post(
            "http://llama:8000/v1/chat/completions",
            headers={
                "Content-Type": "application/json"
            },
            json={
                "model": llm_model,
                "messages": messages,
            }
        )

        if response.status_code == 200:
            response_content = response.json()["choices"][0]["message"]["content"]
            response_content = re.sub("^(\n|.)*</think>\\s*", "", response_content).strip()
            background_tasks.add_task(update_history_dbs, chat_id, user_id, action.description, response_content, previous_response)
            background_tasks.add_task(update_summary, chat_id, user_id, 20, 40, f"{user_id}-{chat_id}.short_text_summary")
            background_tasks.add_task(update_summary, chat_id, user_id, 40, 80, f"{user_id}-{chat_id}.medium_text_summary")
            background_tasks.add_task(update_summary, chat_id, user_id, 80, 160, f"{user_id}-{chat_id}.long_text_summary")
            background_tasks.add_task(redis.set, f"{user_id}-{chat_id}.is-active", "false")
            return {"message": response_content}

        background_tasks.add_task(redis.set, f"{user_id}-{chat_id}.is-active", "false")
        return {"error": response.status_code}
    except mariadb.Error as e:
        background_tasks.add_task(redis.set, f"{user_id}-{chat_id}.chat_is-active", "false")
        print(e)
        return {"error": f"{e}"}
    except Exception as e:
        background_tasks.add_task(redis.set, f"{user_id}-{chat_id}.chat_is_active", "false")
        raise

@app.post("/starting-point-proposal")
async def post_proposals(starting_point: ChatStartingPoint):
    response = requests.post(
        "http://llama:8000/v1/chat/completions",
        headers={
            "Content-Type": "application/json"
        },
        json={
            "model": llm_model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a player in a role play game. Give a brief introduction for the character given the user input."
                },
                {
                    "role": "user",
                    "content": starting_point.character + " is in " + starting_point.location +
                               ". They want to achieve " + starting_point.purpose +
                               ". The current weather is " + starting_point.weather + " and their mood is " + starting_point.mood + ".",
                }
            ],
        }
    )

    if response.status_code == 200:
        response_content = response.json()["choices"][0]["message"]["content"]
        response_content = re.sub("^(\n|.)*</think>\\s*", "", response_content).strip()
        return {"message": response_content}

    return {"error": response.status_code}
