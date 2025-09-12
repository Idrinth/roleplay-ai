import json
import uuid

from bson import json_util
from fastapi import BackgroundTasks
import os
import mariadb

from .logger import log_exception
from .llm_wrapper import ask_characterbuilder, ask_storysummarizer, ask_gamemaster, prewarm_gamemaster, prewarm_storysummarizer
from .models import World, Character, Document, ChatStartingPoint, Action, Chat, ChatCopy
from .databases import sql_connection, mongo, qdrant, redis
from .functions import mariadb_name, mongodb_name, to_mongo_compatible, get_system_prompt, simplify_result, get_from_redis
from .chat_active import chat_is_in_use,remove_chat_from_use

ENABLE_MESSAGE_LIMITS = os.environ.get("ENABLE_MESSAGE_LIMITS") == "true"

async def update_summary(chat_id: str, user_id: str, offset: int, end: int, redis_key: str):
    if offset < 0:
        offset = 0
    if end < offset:
        temp = offset
        offset = end
        end = temp
    count = end - offset
    sql_connection.ping()
    cursor = sql_connection.cursor()
    cursor.execute(
        f"SELECT * FROM (SELECT content, aid FROM `{mariadb_name(user_id, chat_id)}`.messages ORDER BY aid DESC LIMIT {int(offset)},{int(count)}) as a ORDER BY aid;")
    summary = []
    for message in cursor.fetchall():
        summary.append(message[0])
    if summary:
        response = await ask_storysummarizer([
            {
                "role": "user",
                "content": "\n\n".join(summary),
            }
        ])
        redis.set(redis_key, response)

def update_history_dbs(chat_id:str, user_id, action: str, result: str, previous_response: str):
    qdrant.add(
        collection_name=f"{user_id}-{chat_id}",
        documents=[previous_response + "\n\n" + action + "\n\n" + result],
    )
    sql_connection.ping()
    sql_connection.cursor().execute(f"INSERT INTO `{mariadb_name(user_id, chat_id)}`.messages (`creator`, `content`) VALUES ('user', ?);", [action])
    sql_connection.cursor().execute(f"INSERT INTO `{mariadb_name(user_id, chat_id)}`.messages (`creator`, `content`) VALUES ('agent', ?);", [result])

async def get_world_internal(chat_id: str, user_id: str):
    return {"world": json.loads(get_from_redis(user_id, chat_id, "world", "[]"))}

async def update_world_internal(chat_id: str, user_id: str, world: World):
    keywords = []
    for keyword in world.keywords:
        keyword = keyword.strip()
        if keyword not in keywords and keyword != "":
            keywords.append(keyword)
    redis.set(f"{user_id}-{chat_id}.world", json.dumps(keywords))
    return {"success": True}

async def chat_document_list_success(chat_id: str, user_id: str) -> dict[str, list[dict[str, str]]]:
    sql_connection.ping()
    cursor = sql_connection.cursor()
    cursor.execute(f"SELECT id, document_name, content FROM `{mariadb_name(user_id, chat_id)}`.documents;")
    documents = []
    for row in cursor.fetchall():
        documents.append({"id": row[0], "name": row[1], "content": row[2]})
    return {
        "documents": documents,
    }

async def chat_document_add_success(chat_id: str, user_id: str, document: Document):
    document_id = qdrant.add(
        collection_name=f"{user_id}-{chat_id}",
        documents=[document.content],
    )[0]
    document_uuid = str(uuid.UUID(document_id))
    sql_connection.cursor().execute(f"INSERT INTO `{mariadb_name(user_id, chat_id)}`.documents (id, document_name, content) VALUES (?, ?, ?);", [document_uuid, document.name, document.content])
    return {"success": True}

async def chat_character_add_success(chat_id: str, user_id: str, character: Character):
    mongo[mongodb_name(user_id, chat_id)]['characters'].insert_one(to_mongo_compatible(character))
    return {"success": True}

async def chat_characters_success(chat_id, user_id):
    data = json.loads(
        json.dumps(
            list(mongo[mongodb_name(user_id, chat_id)]['characters'].find()),
            default=json_util.default
        )
    )
    fixed_data = []
    for character in data:
        character["id"] = character["_id"]["$oid"]
        del character["_id"]
        fixed_data.append(character)
    return {"characters": fixed_data}

async def chat_active_success(chat_id: str, user_id: str):
    return {"active": chat_is_in_use(user_id, chat_id)}

async def chat_delete_success(chat_id, user_id):
    sql_connection.ping()
    sql_connection.cursor().execute("DELETE FROM chat_users.mapping WHERE user_id=? and chat_id=?;", [user_id, chat_id])
    sql_connection.cursor().execute(f"DROP DATABASE IF EXISTS  `{mariadb_name(user_id, chat_id)}`;")
    remove_chat_from_use(user_id, chat_id)
    redis.delete(f"{user_id}-{chat_id}.short_summary")
    redis.delete(f"{user_id}-{chat_id}.medium_summary")
    redis.delete(f"{user_id}-{chat_id}.long_summary")
    redis.delete(f"{user_id}-{chat_id}.world")
    mongo.drop_database(mongodb_name(user_id, chat_id))
    qdrant.delete_collection(f"{user_id}-{chat_id}")
    return {"success": True}

async def chat_history_success(chat_id, user_id):
    messages = []
    sql_connection.ping()
    cursor = sql_connection.cursor()
    cursor.execute(
        f"SELECT creator, content, aid FROM `{mariadb_name(user_id, chat_id)}`.messages ORDER BY aid;"
    )
    old_messages = cursor.fetchall()
    for message in old_messages:
        messages.append({
            "role": message[0],
            "content": message[1],
        })
    await prewarm_gamemaster()
    return {"messages": messages}

async def post_proposals_internal(chat_id: str, user_id: str, starting_point: ChatStartingPoint):
    if ENABLE_MESSAGE_LIMITS:
        cursor = sql_connection.cursor()
        cursor.execute(
            "SELECT remaining_messages, additional_remaining_messages FROM chat_users.users WHERE user_id=?;",
            [user_id]
        )
        remaining_messages = 0
        additional_remaining_messages = 0
        try:
            for user_row in list(cursor.fetchall()):
                remaining_messages = int(user_row[0])
                additional_remaining_messages = int(user_row[1])
        except mariadb.Error as e:
            log_exception(e, "post_proposals_internal")
        if remaining_messages < 1 and additional_remaining_messages < 1:
            return {"success": False}
        if remaining_messages < 1:
            sql_connection.cursor().execute(
                "UPDATE chat_users.users SET additional_remaining_messages=IF(additional_remaining_messages < 1, 0, additional_remaining_messages - 1) WHERE user_id=?;",
                [user_id]
            )
        else:
            sql_connection.cursor().execute(
                "UPDATE chat_users.users SET remaining_messages=IF(remaining_messages < 1, 0, remaining_messages - 1) WHERE user_id=?;",
                [user_id]
            )
    gender = (starting_point.gender or "").strip().casefold()
    sex_map = {
        "m": "male", "male": "male", "man": "male", "boy": "male",
        "f": "female", "female": "female", "woman": "female", "girl": "female",
        "none": "none", "n/a": "none", "na": "none", "unspecified": "none",
        "non-binary": "other", "nonbinary": "other", "nb": "other", "other": "other", "intersex": "other",
    }
    sex = sex_map.get(gender, "other")

    mongo[mongodb_name(user_id, chat_id)]["characters"].insert_one({
        "name": starting_point.name,
        "heritage": starting_point.heritage,
        "description": starting_point.wear,
        "profession": starting_point.profession,
        "languages": {},
        "sex": sex,
        "facts": {},
        "relationships": {}
    })

    response = await ask_characterbuilder([
        {
            "role": "user",
            "content": f"Name: {starting_point.name}\n"
                f"Gender: {starting_point.gender}\n"
                f"Heritage: {starting_point.heritage}\n"
                f"Wear/Clothing: {starting_point.wear}\n"
                f"Profession: {starting_point.profession}\n"
                f"location: {starting_point.location}\n"
                f"Purpose/Goal: {starting_point.purpose}\n"
                f"Mood/Feeling: {starting_point.mood}\n"
                f"Genre: {starting_point.genre}\n"
                f"World: {starting_point.world}\n"
                f"Weather: {starting_point.weather}\n",
        },
    ],)
    await prewarm_gamemaster()
    return {"message": response}

CHAT_SUMMARY_WINDOWS = {
    "short_summary": [20, 40],
    "medium_summary": [40, 80],
    "long_summary": [80, 160],
}

async def chat_message_internal(chat_id: str, user_id: str, action: Action, background_tasks: BackgroundTasks):
    await prewarm_gamemaster()
    if ENABLE_MESSAGE_LIMITS:
        cursor = sql_connection.cursor()
        cursor.execute(
            "SELECT remaining_messages, additional_remaining_messages FROM chat_users.users WHERE user_id=?;",
            [user_id]
        )
        remaining_messages = 0
        additional_remaining_messages = 0
        try:
            for user_row in list(cursor.fetchall()):
                remaining_messages = int(user_row[0])
                additional_remaining_messages = int(user_row[1])
        except mariadb.Error as e:
            log_exception(e, "chat_message_internal")
        if remaining_messages < 1 and additional_remaining_messages < 1:
            return {"success": False}
        if remaining_messages < 1:
            sql_connection.cursor().execute(
                "UPDATE chat_users.users SET additional_remaining_messages=IF(additional_remaining_messages < 1, 0, additional_remaining_messages - 1) WHERE user_id=?;",
                [user_id]
            )
        else:
            sql_connection.cursor().execute(
                "UPDATE chat_users.users SET remaining_messages=IF(remaining_messages < 1, 0, remaining_messages - 1) WHERE user_id=?;",
                [user_id]
            )
    long_term_summary = get_from_redis(user_id,chat_id, "long_summary")
    medium_term_summary = get_from_redis(user_id,chat_id, "medium_summary")
    short_term_summary = get_from_redis(user_id,chat_id, "short_summary")
    world = json.loads(get_from_redis(user_id, chat_id, "world", "[]"))
    try:
        for keyword in world:
            sql_connection.cursor().execute(
                "INSERT INTO `chat_users`.`keywords` (word, count) VALUES (?, 1) "
                "ON DUPLICATE KEY UPDATE count = count + 1;",
                [keyword.lower()]
            )
    except Exception as e:
        log_exception(e, "chat_message_internal.keywords")
    world = ", ".join(world)
    characters = []
    try:
        characters = list(mongo[mongodb_name(user_id, chat_id)]["characters"].find())
    except Exception as e:
        log_exception(e, "chat_endpoint_handlers.chat_message_internal")
    messages = [{
        "role": "system",
        "content": ""
    }]
    sql_connection.ping()
    cursor = sql_connection.cursor()
    cursor.execute(
        f"SELECT * FROM (SELECT creator, content, aid FROM `{mariadb_name(user_id, chat_id)}`.messages ORDER BY aid DESC LIMIT 20) as a ORDER BY aid;")
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
    vectordb_results = []
    if qdrant.collection_exists(f"{user_id}-{chat_id}"):
        search_result = qdrant.query(
            collection_name=f"{user_id}-{chat_id}",
            query_text=previous_response + "\n" + action.description,
            limit=10
        )
        for res in search_result:
            vectordb_results.append(simplify_result(res))
    system_prompt = get_system_prompt(characters, world, short_term_summary, medium_term_summary, long_term_summary,
                                      vectordb_results)
    if system_prompt:
        messages[0]["content"] += "\n\n" + system_prompt
    messages.append({
        "role": "user",
        "content": action.description,
    })
    response = await ask_gamemaster(messages)
    await prewarm_storysummarizer()
    background_tasks.add_task(update_history_dbs, chat_id, user_id, action.description, response, previous_response)
    for window in CHAT_SUMMARY_WINDOWS:
        background_tasks.add_task(
            update_summary,
            chat_id,
            user_id,
            CHAT_SUMMARY_WINDOWS[window][0],
            CHAT_SUMMARY_WINDOWS[window][1],
            f"{user_id}-{chat_id}.{window}"
        )
    return {"message": response}

async def chat_name_success(chat_id: str, user_id: str, chat_data: Chat):
    if not chat_data.name:
        return {"error": "Chat name must be filled."}
    sql_connection.cursor().execute("UPDATE chat_users.mapping SET chat_name=? WHERE user_id=? AND chat_id=?;", [chat_data.name, user_id, chat_id])
    return {"success": True}

async def chat_copy_success(chat_id: str, user_id: str, copy: ChatCopy):
    sql_connection.ping()
    cursor = sql_connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM chat_users.mapping WHERE user_id = ? AND chat_id = ?", [user_id, chat_id])
    if cursor.fetchone()[0] == "0" :
        return {"error": "Not a valid Chat"}
    new_chat_id = str(uuid.uuid4())
    sql_connection.cursor().execute(
        f"CREATE DATABASE IF NOT EXISTS `{mariadb_name(user_id, new_chat_id)}`;"
    )
    sql_connection.cursor().execute(
        f"CREATE TABLE IF NOT EXISTS `{mariadb_name(user_id, new_chat_id)}`.messages (aid BIGINT NOT NULL AUTO_INCREMENT, creator varchar(6),"
        "content text, PRIMARY KEY(aid)) charset=utf8;"
    )
    sql_connection.cursor().execute(
        f"CREATE TABLE IF NOT EXISTS `{mariadb_name(user_id, new_chat_id)}`.documents (id char(36) NOT NULL, document_name varchar(255),"
        "content text, PRIMARY KEY(id)) charset=utf8;"
    )
    sql_connection.cursor().execute(
        f"INSERT INTO chat_users.mapping (chat_id, user_id, chat_name) VALUES (?, ?, ?);",
        [new_chat_id, user_id, new_chat_id]
    )
    cursor2 = sql_connection.cursor()
    cursor2.execute(f"SELECT document_name, content FROM `{mariadb_name(user_id, chat_id)}`.documents")
    for (document_name, content) in cursor2.fetchall():
        document_id = qdrant.add(
            collection_name=f"{user_id}-{new_chat_id}",
            documents=[content],
        )[0]
        document_uuid = str(uuid.UUID(document_id))
        sql_connection.cursor().execute(
            f"INSERT INTO `{mariadb_name(user_id, new_chat_id)}`.documents (id, document_name, content) VALUES (?, ?, ?);",
            [document_uuid, document_name, content])
        try:
            sql_connection.cursor().execute(
                "INSERT INTO `chat_users`.`statistics` (label, value) VALUES (?, 1) ON DUPLICATE KEY UPDATE value = value +1;",
                ['Documents']
            )
        except mariadb.Error as error:
            pass
    cursor3 = sql_connection.cursor()
    cursor3.execute(f"SELECT content, creator FROM `{mariadb_name(user_id, chat_id)}`.messages ORDER BY aid ASC LIMIT {copy.num_messages * 2};")
    replies = 0
    for (content, creator) in cursor3.fetchall():
        sql_connection.cursor().execute(f"INSERT INTO `{mariadb_name(user_id, new_chat_id)}`.messages (content, creator) VALUES (?, ?);", [content, creator])
        replies += 1
    try:
        sql_connection.cursor().execute(
            "INSERT INTO `chat_users`.`statistics` (label, value) VALUES (?, ?) ON DUPLICATE KEY UPDATE value = value + ?;",
            ['Chat Replies', replies/2, replies/2]
        )
    except mariadb.Error as error:
        pass
    for character in mongo[mongodb_name(user_id, chat_id)]['characters'].find():
        mongo[mongodb_name(user_id, new_chat_id)]['characters'].insert_one(character)
        try:
            sql_connection.cursor().execute(
                "INSERT INTO `chat_users`.`statistics` (label, value) VALUES (?, 1) ON DUPLICATE KEY UPDATE value = value +1;",
                ['Character Sheets']
            )
        except mariadb.Error as error:
            pass
    for window in CHAT_SUMMARY_WINDOWS:
        await update_summary(
            new_chat_id,
            user_id,
            CHAT_SUMMARY_WINDOWS[window][0],
            CHAT_SUMMARY_WINDOWS[window][1],
            f"{user_id}-{chat_id}.{window}"
        )
    world_data = redis.get(f"{user_id}-{chat_id}.world")
    if world_data:
        redis.set(f"{user_id}-{new_chat_id}.world", world_data)
    try:
        sql_connection.cursor().execute(
            "INSERT INTO `chat_users`.`statistics` (label, value) VALUES (?, 1) ON DUPLICATE KEY UPDATE value = value +1;",
            ['Chats']
        )
    except mariadb.Error as error:
        pass
    await prewarm_gamemaster()
    return {"chat": new_chat_id}
