import datetime
import json

from bson.objectid import ObjectId
from typing import Annotated
import uuid
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Cookie, BackgroundTasks, Response, Request, HTTPException
import mariadb
from fastapi_utils.tasks import repeat_every

from .logger import log_info, log_exception, log_warning, log_debug, log_error
from .llm_wrapper import prewarm_characterbuilder
from .models import (
    World,
    Action,
    Chat,
    Character,
    Document,
    Login,
    Register,
    ChatStartingPoint,
    User,
    ChatCopy,
)
from .functions import (
    is_uuid_like,
    mariadb_name,
    mongodb_name,
    to_mongo_compatible,
    user_id_from_jwt,
    set_login_cookie,
)
from .paypal import (
    PayPalWebhookEvent,
    ENABLE_PAYPAL,
    PAYPAL_WEBHOOK_ENDPOINT,
    verify_paypal_signature,
)
from .databases import sql_connection, mongo, qdrant, redis
from .app import app
from .chat_auth_wrapper import wrap
from .chat_endpoint_handlers import (
    chat_delete_success,
    chat_active_success,
    chat_history_success,
    chat_characters_success,
    chat_character_add_success,
    chat_document_add_success,
    chat_document_list_success,
    update_world_internal,
    get_world_internal,
    post_proposals_internal,
    chat_message_internal,
    chat_name_success,
    chat_copy_success,
)


@app.on_event("startup")
@repeat_every(seconds=60)
async def refill_tokens():
    sql_connection.ping()
    now = datetime.datetime.now(datetime.timezone.utc).timestamp().__floor__()
    sql_connection.cursor().execute(
        "UPDATE chat_users.users SET last_incremented=? WHERE remaining_messages >= maximum_remaining_messages",
        [now],
    )
    sql_connection.cursor().execute(
        "UPDATE chat_users.users SET remaining_messages=maximum_remaining_messages WHERE remaining_messages > maximum_remaining_messages"
    )
    sql_connection.cursor().execute(
        "UPDATE chat_users.users SET last_incremented=last_incremented+increment_every_seconds, remaining_messages=remaining_messages+1 WHERE remaining_messages < maximum_remaining_messages AND last_incremented + increment_every_seconds < ?",
        [now],
    )


@app.on_event("startup")
@repeat_every(seconds=60)
async def process_subscriptions():
    if not ENABLE_PAYPAL:
        return
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    sql_connection.ping()
    sql_connection.cursor().execute(
        "UPDATE chat_users.users SET maximum_remaining_messages=(SELECT COUNT(aid)+25 FROM chat_users.subscriptions WHERE subscriptions.user_id=users.user_id AND ? BETWEEN subscriptions.from_datetime AND subscriptions.to_datetime AND subscriptions.product IN('RECHARGELIMIT', 'REWARD_RECHARGELIMIT'))",
        [now],
    )
    sql_connection.cursor().execute(
        "UPDATE chat_users.users SET increment_every_seconds=(SELECT 1800 - COUNT(aid)*180 FROM chat_users.subscriptions WHERE subscriptions.user_id=users.user_id AND ? BETWEEN subscriptions.from_datetime AND subscriptions.to_datetime AND subscriptions.product IN('RECHARGEFREQUENCY', 'REWARD_RECHARGEFREQUENCY'))",
        [now],
    )


@app.get("/")
async def root():
    return "OK"


if PAYPAL_WEBHOOK_ENDPOINT and ENABLE_PAYPAL:

    @app.post(f"/paypal/{PAYPAL_WEBHOOK_ENDPOINT}")
    async def paypal_webhook(request: Request, event: PayPalWebhookEvent):

        log_info(
            f"Received PayPal webhook event. Type: {event.event_type}",
            func_name="paypal_webhook",
        )

        if event.event_type != "PAYMENT.CAPTURE.COMPLETED":

            log_warning(
                f"Unsupported PayPal event type received: {event.event_type}",
                func_name="paypal_webhook",
            )
            raise HTTPException(status_code=400, detail="Unsupported event type")
        transmission_id = request.headers.get("PAYPAL-TRANSMISSION-ID")
        transmission_time = request.headers.get("PAYPAL-TRANSMISSION-TIME")
        cert_url = request.headers.get("PAYPAL-CERT-URL")
        auth_algo = request.headers.get("PAYPAL-AUTH-ALGO")
        transmission_sig = request.headers.get("PAYPAL-TRANSMISSION-SIG")
        if not all([transmission_id, transmission_time, cert_url, auth_algo]):

            log_error("Incomplete PayPal webhook.", func_name="paypal_webhook")
            raise HTTPException(
                status_code=400, detail="PayPal webhook endpoint incomplete"
            )
        if not await verify_paypal_signature(
            transmission_id,
            transmission_time,
            await request.body(),
            cert_url,
            transmission_sig,
            auth_algo,
        ):

            log_error(
                "PayPal event validation failed due to invalid signature.",
                func_name="paypal_webhook",
            )
            raise HTTPException(
                status_code=400, detail="PayPal event validation failed"
            )
        now = event.resource.create_time.timestamp().__floor__()

        log_info(
            f"PayPal payment has been successful. Event ID: {event.id}",
            func_name="paypal_webhook",
        )
        return {"success": True}


@app.post("/login")
async def login(response: Response, login_data: Login):
    log_info(f"Login attempt for user_id: {login_data.user_id}", func_name="login")

    if not is_uuid_like(login_data.user_id):
        log_warning("Login failed: invalid user_id format.", func_name="login")
        return {"error": "Login failed"}
    if not login_data.password:
        log_warning("Login failed: password field is empty.", func_name="login")
        return {"error": "Login failed"}
    try:
        cursor = sql_connection.cursor()
        cursor.execute(
            "SELECT user_id, password FROM `chat_users`.`users` WHERE `user_id` = ?",
            [login_data.user_id],
        )
        chatuser = cursor.fetchone()
        if not chatuser:
            log_warning(
                f"Login failed: user not found with user_id: {login_data.user_id}",
                func_name="login",
            )
            return {"error": "Login failed"}
        try:
            PasswordHasher().verify(chatuser[1], login_data.password)
        except VerifyMismatchError as e:
            log_warning(
                f"Login failed: incorrect password for user_id: {login_data.user_id}",
                func_name="login",
            )
            return {"error": "Login failed"}
        set_login_cookie(response, login_data.user_id)
        log_info(
            f"Login successful for user_id: {login_data.user_id}", func_name="login"
        )
        return {"success": True}
    except mariadb.Error as e:
        log_exception(e, "login")
        return {"error": "Login failed"}


@app.post("/me")
async def me(user: User, user_jwt: Annotated[str | None, Cookie()] = None):
    log_info("Profile update attempt.", func_name="me")
    user_id = user_id_from_jwt(user_jwt)
    if not is_uuid_like(user_id):
        log_warning("Profile update failed: invalid user_id format.", func_name="me")
        return {"error": "Not a valid User"}
    cursor = sql_connection.cursor()
    cursor.execute("SELECT * FROM `chat_users`.`users` WHERE `user_id` = ?", [user_id])
    chatuser = cursor.fetchone()
    if not chatuser:
        log_warning(
            f"Profile update failed: user not found with user_id: {user_id}",
            func_name="me",
        )
        return {"error": "Not a valid User"}
    if user.password and user.username:
        log_info(
            f"Updating password and username for user_id: {user_id}", func_name="me"
        )
        sql_connection.cursor().execute(
            "UPDATE `chat_users`.`users` SET password = ?, user_name= ? WHERE `user_id` = ?",
            [PasswordHasher().hash(user.password), user.username, user_id],
        )
    elif user.password:
        log_info(f"Updating password for user_id: {user_id}", func_name="me")
        sql_connection.cursor().execute(
            "UPDATE `chat_users`.`users` SET password = ? WHERE `user_id` = ?",
            [PasswordHasher().hash(user.password), user_id],
        )
    elif user.username:
        log_info(f"Updating username for user_id: {user_id}", func_name="me")
        sql_connection.cursor().execute(
            "UPDATE `chat_users`.`users` SET user_name = ? WHERE `user_id` = ?",
            [user.username, user_id],
        )
    log_info(
        f"User profile successfully updated for user_id: {user_id}", func_name="me"
    )
    return True


@app.get("/statistics")
def statistics():
    log_info("Fetching application statistics.", func_name="statistics")
    try:
        sql_connection.ping()
        cursor = sql_connection.cursor()
        cursor.execute("SELECT `label`, `value` FROM `chat_users`.`statistics`")
        data = {label: value for (label, value) in cursor}
        cursor.execute("SELECT `word`, `count` FROM `chat_users`.`keywords`")
        data["keywords"] = {word: count for (word, count) in cursor}
        log_info("Statistics data retrieved successfully.", func_name="statistics")
        return data
    except mariadb.Error as e:
        log_exception(e, "statistics")
    return {}


@app.get("/ratelimits")
async def remaining_messages(user_jwt: Annotated[str | None, Cookie()] = None):
    user_id = user_id_from_jwt(user_jwt)
    if not is_uuid_like(user_id):
        return {
            "remainingMessages": 0,
            "lastIncremented": 0,
            "incrementEverySeconds": 0,
            "maximumRemainingMessages": 0,
            "additionalRemainingMessages": 0,
        }
    try:
        cursor = sql_connection.cursor()
        cursor.execute(
            "SELECT remaining_messages, last_incremented, increment_every_seconds, maximum_remaining_messages, additional_remaining_messages FROM chat_users.users WHERE user_id=?;",
            [user_id],
        )
        for user_row in list(cursor.fetchall()):
            last_incremented_raw = user_row[1]
            if hasattr(last_incremented_raw, "timestamp"):
                last_incremented = int(last_incremented_raw.timestamp())
            else:
                last_incremented = int(last_incremented_raw)
            increment_every_seconds = int(user_row[2])
            maximum_remaining_messages = int(user_row[3])
            remaining_message_count = int(user_row[0])
            additional_remaining_messages = int(user_row[4])
            return {
                "remainingMessages": remaining_message_count,
                "lastIncremented": last_incremented,
                "incrementEverySeconds": increment_every_seconds,
                "maximumRemainingMessages": maximum_remaining_messages,
                "additionalRemainingMessages": additional_remaining_messages,
            }
    except mariadb.Error as e:
        log_exception(e, "remaining_messages")

    return {
        "remainingMessages": 0,
        "lastIncremented": 0,
        "incrementEverySeconds": 0,
        "maximumRemainingMessages": 0,
        "additionalRemainingMessages": 0,
    }


@app.post("/register")
async def register(response: Response, register_data: Register):
    if not register_data.password:
        return {"error": "Registration failed"}
    try:
        user_id = str(uuid.uuid4())
        encrypted_password = PasswordHasher().hash(register_data.password)
        sql_connection.ping()
        sql_connection.cursor().execute(
            "INSERT INTO `chat_users`.`users` (user_id, password, active) VALUES (?, ?, ?);",
            [user_id, encrypted_password, 1],
        )
        try:
            sql_connection.cursor().execute(
                "INSERT INTO `chat_users`.`statistics` (label, value) VALUES (?, 1) ON DUPLICATE KEY UPDATE value = value +1;",
                ["Registrations"],
            )
        except mariadb.Error as error:
            pass
        set_login_cookie(response, user_id)
        return {"user": user_id}
    except mariadb.Error as e:
        log_exception(e, "register")
        return {"error": "Registration failed"}


@app.get("/new")
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
        [chat_id, user_id, chat_id],
    )
    redis.set(f"{user_id}-{chat_id}.world", json.dumps(["fantasy", "high magic"]))
    try:
        sql_connection.cursor().execute(
            "INSERT INTO `chat_users`.`statistics` (label, value) VALUES (?, 1) ON DUPLICATE KEY UPDATE value = value +1;",
            ["Chats"],
        )
    except mariadb.Error as error:
        pass
    await prewarm_characterbuilder()
    return {"chat": chat_id}


@app.get("/chat/{chat_id}/world")
async def get_world(chat_id: str, user_jwt: Annotated[str | None, Cookie()] = None):
    return await wrap(chat_id, user_jwt, get_world_internal)


@app.put("/chat/{chat_id}/world")
async def update_world(
    chat_id: str, world: World, user_jwt: Annotated[str | None, Cookie()] = None
):
    return await wrap(chat_id, user_jwt, update_world_internal, world)


@app.get("/chat/{chat_id}/documents")
async def chat_document_list(
    chat_id: str, user_jwt: Annotated[str | None, Cookie()] = None
):
    log_info(
        f"Listing documents for chat_id: {chat_id}", func_name="chat_document_list"
    )
    return await wrap(chat_id, user_jwt, chat_document_list_success)


@app.post("/chat/{chat_id}/documents/{document_id}/delete")
async def chat_document_delete(
    chat_id: str, document_id: str, user_jwt: Annotated[str | None, Cookie()] = None
):
    user_id = user_id_from_jwt(user_jwt)
    if not is_uuid_like(user_id):
        return {"error": "Not a valid User"}
    if not is_uuid_like(chat_id):
        return {"error": "Not a valid Chat"}
    if not is_uuid_like(document_id):
        return {"error": "Not a valid Document"}
    sql_connection.cursor().execute(
        f"DELETE FROM `{mariadb_name(user_id, chat_id)}`.documents WHERE id=?;",
        [document_id],
    )
    qdrant.delete(
        collection_name=f"{user_id}-{chat_id}",
        points_selector=[document_id],
        wait=True,
    )
    return True


@app.post("/chat/{chat_id}/documents")
async def chat_document_add(
    chat_id: str, document: Document, user_jwt: Annotated[str | None, Cookie()] = None
):
    document = await wrap(chat_id, user_jwt, chat_document_add_success, document)
    if document and "success" in document:
        try:
            sql_connection.cursor().execute(
                "INSERT INTO `chat_users`.`statistics` (label, value) VALUES (?, 1) ON DUPLICATE KEY UPDATE value = value +1;",
                ["Documents"],
            )
        except mariadb.Error as error:
            pass
    return document


@app.post("/chat/{chat_id}/characters")
async def chat_character_add(
    chat_id: str, character: Character, user_jwt: Annotated[str | None, Cookie()] = None
):
    character_sheet = await wrap(
        chat_id, user_jwt, chat_character_add_success, character
    )
    if character_sheet and "success" in character_sheet:
        try:
            sql_connection.cursor().execute(
                "INSERT INTO `chat_users`.`statistics` (label, value) VALUES (?, 1) ON DUPLICATE KEY UPDATE value = value +1;",
                ["Character Sheets"],
            )
        except mariadb.Error:
            pass
    return character_sheet


@app.post("/chat/{chat_id}/characters/{character_id}")
async def chat_character_update(
    chat_id: str,
    character_id: str,
    character: Character,
    user_jwt: Annotated[str | None, Cookie()] = None,
):
    user_id = user_id_from_jwt(user_jwt)
    if not is_uuid_like(user_id):
        return {"error": "Not a valid User"}
    if not is_uuid_like(chat_id):
        return {"error": "Not a valid Chat"}
    my_col = mongo[mongodb_name(user_id, chat_id)]["characters"]
    my_col.delete_one({"_id": ObjectId(character_id)})
    my_col.insert_one(to_mongo_compatible(character, character_id))
    return True


@app.post("/chat/{chat_id}/characters/{character_id}/delete")
async def chat_character_delete(
    chat_id: str, character_id: str, user_jwt: Annotated[str | None, Cookie()] = None
):
    log_info(
        f"Attempting to delete character '{character_id}' from chat '{chat_id}'",
        func_name="chat_character_delete",
    )
    user_id = user_id_from_jwt(user_jwt)
    if not is_uuid_like(user_id):
        log_warning(
            "Character deletion failed: Not a valid user_id.",
            func_name="chat_character_delete",
        )
        return {"error": "Not a valid User"}
    if not is_uuid_like(chat_id):
        log_warning(
            "Character deletion failed: Not a valid chat_id.",
            func_name="chat_character_delete",
        )
        return {"error": "Not a valid Chat"}
    mongo[mongodb_name(user_id, chat_id)]["characters"].delete_one(
        {"_id": ObjectId(character_id)}
    )
    log_info(
        f"Successfully deleted character_id: {character_id} from chat_id: {chat_id}",
        func_name="chat_character_delete",
    )
    return True


@app.get("/chat/{chat_id}/characters")
async def chat_characters(
    chat_id: str, user_jwt: Annotated[str | None, Cookie()] = None
):
    log_info(f"Fetching characters for chat_id: {chat_id}", func_name="chat_characters")
    return await wrap(chat_id, user_jwt, chat_characters_success)


@app.get("/chat/{chat_id}/active")
async def chat_active(chat_id: str, user_jwt: Annotated[str | None, Cookie()] = None):
    log_info(
        f"Checking if chat is active for chat_id: {chat_id}", func_name="chat_active"
    )
    return await wrap(chat_id, user_jwt, chat_active_success)


@app.post("/chat/{chat_id}/delete")
async def chat_delete(chat_id: str, user_jwt: Annotated[str | None, Cookie()] = None):
    log_info(f"Deleting chat with ID: {chat_id}", func_name="chat_delete")
    return await wrap(chat_id, user_jwt, chat_delete_success)


@app.post("/chat/{chat_id}/copy")
async def chat_copy(
    chat_id: str, copy: ChatCopy, user_jwt: Annotated[str | None, Cookie()] = None
):
    return await wrap(chat_id, user_jwt, chat_copy_success, copy)


@app.get("/whoami")
async def whoami(user_jwt: Annotated[str | None, Cookie()] = None):
    if not user_jwt:
        return {"error": "Login Required"}
    user_id = user_id_from_jwt(user_jwt)
    if not is_uuid_like(user_id):
        return {"error": "Login Required"}
    cursor = sql_connection.cursor()
    cursor.execute(
        "SELECT user_id, user_name FROM `chat_users`.`users` WHERE `user_id` = ?",
        [user_id],
    )
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
    cursor.execute(
        f"SELECT chat_id, chat_name FROM chat_users.mapping WHERE user_id='{user_id}';"
    )
    for chat_row in cursor.fetchall():
        user["chats"].append(
            {
                "id": chat_row[0],
                "name": chat_row[1],
            }
        )
    return user


@app.get("/chat/{chat_id}")
async def chat_history(chat_id: str, user_jwt: Annotated[str | None, Cookie()] = None):
    log_info(
        f"Fetching chat history for chat_id: {chat_id}, user_jwt: {user_jwt}",
        func_name="chat_history",
    )
    return await wrap(chat_id, user_jwt, chat_history_success)


@app.post("/chat/{chat_id}/name")
async def chat_name(
    chat_id: str, chat_data: Chat, user_jwt: Annotated[str | None, Cookie()] = None
):
    log_info(
        f"Chat name updated for chat_id: {chat_id}, new name: {chat_data.name}",
        func_name="chat_name",
    )
    return await wrap(chat_id, user_jwt, chat_name_success, chat_data)


@app.post("/chat/{chat_id}")
async def chat(
    chat_id: str,
    action: Action,
    background_tasks: BackgroundTasks,
    user_jwt: Annotated[str | None, Cookie()] = None,
):
    chat_message = await wrap(
        chat_id, user_jwt, chat_message_internal, action, True, background_tasks
    )
    if chat_message and "message" in chat_message:
        try:
            sql_connection.cursor().execute(
                "INSERT INTO `chat_users`.`statistics` (label, value) VALUES (?, 1) ON DUPLICATE KEY UPDATE value = value +1;",
                ["Chat Replies"],
            )
        except mariadb.Error as error:
            pass
    return chat_message


@app.post("/chat/{chat_id}/starting-point-proposal")
async def post_proposals(
    starting_point: ChatStartingPoint,
    chat_id: str,
    user_jwt: Annotated[str | None, Cookie()] = None,
):
    proposal = await wrap(
        chat_id, user_jwt, post_proposals_internal, starting_point, True
    )
    if proposal and "message" in proposal:
        try:
            sql_connection.cursor().execute(
                "INSERT INTO `chat_users`.`statistics` (label, value) VALUES (?, 1) ON DUPLICATE KEY UPDATE value = value + 1;",
                ["Starting-Point Proposals"],
            )
        except mariadb.Error as error:
            pass
    return proposal
