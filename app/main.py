import json
from bson import json_util
from bson.objectid import ObjectId
from typing import Annotated
import uuid
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Cookie, BackgroundTasks, Response
import mariadb

from .logger import log_exception
from .llm_wrapper import prewarm_characterbuilder
from .models import World, Action, Chat, Character, Document, Login, Register, ChatStartingPoint, User
from .functions import is_uuid_like, mariadb_name, mongodb_name, to_mongo_compatible, user_id_from_jwt, set_login_cookie
from .databases import sql_connection, mongo, qdrant, redis
from .app import app
from .chat_auth_wrapper import wrap
from .chat_endpoint_handlers import chat_delete_success, chat_active_success, chat_history_success, \
    chat_characters_success, chat_character_add_success, chat_document_add_success, chat_document_list_success, \
    update_world_internal, get_world_internal, post_proposals_internal, chat_message_internal, chat_name_success

@app.get('/')
async def root():
    return 'OK'

@app.post('/login')
async def login(response: Response, login_data: Login):
    if not is_uuid_like(login_data.user_id):
        return {"error": "Login failed"}
    if not login_data.password:
        return {"error": "Login failed"}
    try:
        cursor = sql_connection.cursor()
        cursor.execute("SELECT user_id, password FROM `chat_users`.`users` WHERE `user_id` = ?", [login_data.user_id])
        chatuser = cursor.fetchone()
        if not chatuser:
            return {"error": "Login failed"}
        try:
            PasswordHasher().verify(chatuser[1], login_data.password)
        except VerifyMismatchError as e:
            return {"error": "Login failed"}
        set_login_cookie(response, login_data.user_id)
        return {"success": True}
    except mariadb.Error as e:
        log_exception(e, "login")
        return {"error": "Login failed"}

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
    if not register_data.password:
        return {"error": "Registration failed"}
    try:
        user_id = str(uuid.uuid4())
        encrypted_password = PasswordHasher().hash(register_data.password)
        sql_connection.ping()
        sql_connection.cursor().execute(
            "INSERT INTO `chat_users`.`users` (user_id, password, active) VALUES (?, ?, ?);",
            [user_id, encrypted_password, 1]
        )
        set_login_cookie(response, user_id)
        return {"user": user_id}
    except mariadb.Error as e:
        log_exception(e, "register")
        return {"error": "Registration failed"}

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
        f"CREATE TABLE IF NOT EXISTS `{mariadb_name(user_id, chat_id)}`.documents (id char(36) NOT NULL, document_name varchar(255),"
        "content text, PRIMARY KEY(id)) charset=utf8;"
    )
    sql_connection.cursor().execute(
        f"INSERT INTO chat_users.mapping (chat_id, user_id, chat_name) VALUES (?, ?, ?);",
        [chat_id, user_id, chat_id]
    )
    redis.set(f"{user_id}-{chat_id}.world", json.dumps(["fantasy", "high magic"]))
    await prewarm_characterbuilder()
    return {"chat": chat_id}

@app.get("/chat/{chat_id}/world")
async def get_world(chat_id: str, user_jwt: Annotated[str | None, Cookie()] = None):
    return await wrap(chat_id, user_jwt, get_world_internal)

@app.put("/chat/{chat_id}/world")
async def update_world(chat_id: str, world: World, user_jwt: Annotated[str | None, Cookie()] = None):
    return wrap(chat_id, user_jwt, update_world_internal, world)

@app.get("/chat/{chat_id}/documents")
async def chat_document_list(chat_id: str, user_jwt: Annotated[str | None, Cookie()] = None):
    return await wrap(chat_id, user_jwt, chat_document_list_success)

@app.post("/chat/{chat_id}/documents/{document_id}/delete")
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
    return await wrap(chat_id, user_jwt, chat_document_add_success, document)

@app.post("/chat/{chat_id}/characters")
async def chat_character_add(chat_id: str, character: Character, user_jwt: Annotated[str | None, Cookie()] = None):
    return await wrap(chat_id, user_jwt, chat_character_add_success, character)

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

@app.post("/chat/{chat_id}/characters/{character_id}/delete")
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
    return await wrap(chat_id, user_jwt, chat_characters_success)

@app.get("/chat/{chat_id}/active")
async def chat_active(chat_id: str, user_jwt: Annotated[str | None, Cookie()] = None):
    return await wrap(chat_id, user_jwt, chat_active_success)

@app.post("/chat/{chat_id}/delete")
async def chat_delete(chat_id: str, user_jwt: Annotated[str | None, Cookie()] = None):
    return await wrap(chat_id, user_jwt, chat_delete_success)

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
    return await wrap(chat_id, user_jwt, chat_history_success)

@app.post("/chat/{chat_id}/name")
async def chat_name(chat_id: str, chat_data: Chat, user_jwt: Annotated[str | None, Cookie()] = None):
    return await wrap(chat_id, user_jwt, chat_name_success, chat_data)

@app.post("/chat/{chat_id}")
async def chat(chat_id: str, action: Action, background_tasks: BackgroundTasks, user_jwt: Annotated[str | None, Cookie()] = None):
    return await wrap(chat_id, user_jwt, chat_message_internal, action, True, background_tasks)

@app.post("/chat/{chat_id}/starting-point-proposal")
async def post_proposals(starting_point: ChatStartingPoint, chat_id: str, user_jwt: Annotated[str | None, Cookie()] = None):
    return await wrap(chat_id, user_jwt, post_proposals_internal, starting_point, True)
