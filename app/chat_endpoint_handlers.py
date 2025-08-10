import json
import uuid

from bson import json_util
from fastapi import BackgroundTasks

from .logger import log_exception
from .llm_wrapper import ask_characterbuilder, ask_storysummarizer, ask_gamemaster, prewarm_gamemaster, prewarm_storysummarizer
from .models import World, Character, Document, ChatStartingPoint, Action, Chat
from .databases import sql_connection, mongo, qdrant, redis
from .functions import mariadb_name, mongodb_name, to_mongo_compatible, get_system_prompt, simplify_result
from .chat_active import chat_is_in_use,remove_chat_from_use

async def update_summary(chat_id:str, user_id:str, start: int, end: int, redis_key: str):
    cursor = sql_connection.cursor()
    cursor.execute(
        f"SELECT * FROM (SELECT content, aid FROM `{mariadb_name(user_id, chat_id)}`.messages ORDER BY aid DESC LIMIT {start},{end}) as a ORDER BY aid;")
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
    sql_connection.cursor().execute(f"INSERT INTO `{mariadb_name(user_id, chat_id)}`.messages (`creator`, `content`) VALUES ('user', ?);", [action])
    sql_connection.cursor().execute(f"INSERT INTO `{mariadb_name(user_id, chat_id)}`.messages (`creator`, `content`) VALUES ('agent', ?);", [result])

async def get_world_internal(chat_id: str, user_id: str):
    return {"world": json.loads(redis.get(f"{user_id}-{chat_id}.world") or "[]")}

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
    cursor.execute(f"SELECT creator, content, aid FROM `{mariadb_name(user_id, chat_id)}`.messages;")
    old_messages = cursor.fetchall()
    for message in old_messages:
        messages.append({
            "role": message[0],
            "content": message[1],
        })
    await prewarm_gamemaster()
    return {"messages": messages}

async def post_proposals_internal(chat_id: str, user_id: str, starting_point: ChatStartingPoint):
    response = await ask_characterbuilder([
        {
            "role": "user",
            "content": f"Name: {starting_point.name}\n"
                f"Gender: {starting_point.gender}\n"
                f"Race: {starting_point.race}\n"
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

async def chat_message_internal(chat_id: str, user_id: str, action: Action, background_tasks: BackgroundTasks):
    await prewarm_gamemaster()
    long_term_summary = redis.get(f"{user_id}-{chat_id}.long_summary") or ""
    medium_term_summary = redis.get(f"{user_id}-{chat_id}.medium_summary") or ""
    short_term_summary = redis.get(f"{user_id}-{chat_id}.short_summary") or ""
    world = ", ".join(json.loads(redis.get(f"{user_id}-{chat_id}.world") or "[]"))
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
    background_tasks.add_task(update_summary, chat_id, user_id, 20, 40, f"{user_id}-{chat_id}.short_summary")
    background_tasks.add_task(update_summary, chat_id, user_id, 40, 80, f"{user_id}-{chat_id}.medium_summary")
    background_tasks.add_task(update_summary, chat_id, user_id, 80, 160, f"{user_id}-{chat_id}.long_summary")
    return {"message": response}

async def chat_name_success(chat_id: str, user_id: str, chat_data: Chat):
    if not chat_data.name:
        return {"error": "Chat name must be filled."}
    sql_connection.cursor().execute("UPDATE chat_users.mapping SET chat_name=? WHERE user_id=? AND chat_id=?;", [chat_data.name, user_id, chat_id])
    return {"success": True}
