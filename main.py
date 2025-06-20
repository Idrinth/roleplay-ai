import json

from ollama import ChatResponse, Client
from qdrant_client import QdrantClient
from qdrant_client.http.models import QueryResponse
from fastapi import FastAPI
import mariadb
from redis import Redis
from pymongo import MongoClient
from pydantic import BaseModel
from fastapi.responses import HTMLResponse, PlainTextResponse
import yaml
import os

def simplify_result(query_result: QueryResponse):
    return query_result.model_dump(mode="json")


app = FastAPI()

ollama = Client(host="http://ollama:11434")
qdrant = QdrantClient("http://qdrant:6333")
qdrant.set_model(qdrant.DEFAULT_EMBEDDING_MODEL, providers=["CPUExecutionProvider"])
redis = Redis(host="redis", port=6379, db=0)
mongo = MongoClient("mongodb://mongo:27017/")
mdbconn = mariadb.connect(
    user="root",
    password="example",
    host="mariadb",
    port=3306
)
mdbconn.autocommit = True



class Action(BaseModel):
    description: str | None = None

class Character(BaseModel):
    sheet: str | None = None


@app.get("/", response_class=HTMLResponse)
def index():
    data = "ERROR!"
    with open('./app/index.html', 'r') as file:
        data = file.read()
    return HTMLResponse(content=data, status_code=200)


@app.get("/showdown.min.js", response_class=PlainTextResponse)
def index():
    data = "ERROR!"
    with open('./app/showdown.min.js', 'r') as file:
        data = file.read()
    return PlainTextResponse(content=data, status_code=200, media_type="application/javascript")


@app.post("/chat/{uuid}/characters")
def chat_character(uuid: str, character: Character):
    mydb = mongo[uuid]

@app.get("/chat/{uuid}/characters")
def chat_character(uuid: str):
    mydb = mongo[uuid]



@app.get("/chat/{uuid}")
def chat_history(uuid: str, action: Action):
    try:
        messages = []
        mdbconn.cursor().execute("CREATE DATABASE IF NOT EXISTS `"+uuid+"`;")
        mdbconn.cursor().execute("USE `"+uuid+"`;")
        mdbconn.cursor().execute(
            "CREATE TABLE IF NOT EXISTS messages (aid BIGINT NOT NULL AUTO_INCREMENT, creator varchar(6),content text, PRIMARY KEY(aid)) charset=utf8;")
        cursor = mdbconn.cursor()
        cursor.execute("SELECT creator, content, aid FROM messages;")
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

@app.put("/chat/{uuid}")
def chat(uuid: str, action: Action):
    results = []
    if qdrant.collection_exists(uuid):
        search_result = qdrant.query(
            collection_name=uuid,
            query_text=action.description,
            limit=10
        )
        for res in search_result:
            results.append(simplify_result(res))
    #mydb = myclient["mydatabase"]
    long_term_summary = redis.get(uuid + ".long_text_summary") or "Nothing happened yet."
    medium_term_summary = redis.get(uuid + ".medium_text_summary") or "Nothing happened yet."
    short_term_summary = redis.get(uuid + ".short_text_summary") or "Nothing happened yet."
    characters = []
    schema = "{}";
    with open('./app/idrinth.character-sheet.yaml', 'r') as file:
        characters.append(yaml.safe_load(file))
    with open('./app/lienne.character-sheet.yaml', 'r') as file:
        characters.append(yaml.safe_load(file))
    with open('./app/character-sheet.schema.json', 'r') as file:
        schema = file.read()
    world = "dark fantasy, Warhammer Fantasy"
    location = "Warhammer Fantasy, Ulthuan, Lothern, Gate"
    messages = [
        {
            "role": "system",
            "content": "# Rules:"
                "\n\n"
                "- You are NOT a co-author.\n"
                "- You are NOT the narrator.\n"
                "- You are the world reacting to the players, nothing more.\n"
                "- You only control the world and NPCs. You never describe player intent or motivation.\n"
                "- If uncertain, wait. Do not assume.\n"
                "- NEVER speak for player characters.\n"
                "- NEVER act for player characters.\n"
                "- NEVER define player character motivation.\n"
                "- DO NOT resolve narrative tensions.\n"
                "- DO NOT change character names.\n"
                "- DO play NPCs.\n"
                "- DO NOT assume what the player is thinking.\n"
                "- DO NOT speculate on relationships.\n"
                "- DO NOT describe PC inner state.\n"
                "- DO NOT mirror or echo player phrasing or emotions.\n"
                "- FOCUS on immediate consequences and reactions to player actions.\n"
                "- DO describe environmental changes.\n"
                "- DO add dialogue, sensory details and atmosphere.\n"
                "- DO keep the core situation intact for players to resolve.\n"
                "- DO NOT invent details, unless they are minor.\n"
                "- DO NOT contradict previously established facts.\n"
                "- NEVER exceed 500 characters in your response.\n"
                "- TRY to stay below 250 characters in your response.\n"
                "- DO NOT rewrite the player's actions.\n"
                "- ASSUME characters don't know each other if no information exists.\n"
                "\n\n"
                "# Personality:"
                "\n\n"
                "You are a GAME MASTER. React to provided actions with in character responses of NPCs."
                "\n\n"
                "# Player Characters:\n\nThe following character sheets are for reference ONLY. Do not use these to infer motivations or write actions for player characters..\n```json\n" + json.dumps(characters) +
                "\n```\n\n"
                "## Character Sheet Schema:\n\n```json\n" + schema +
                "\n```\n\n"
                "# World:\n\n" + world +
                "\n\n"
                "# Starting Location:\n\n" + location +
                "\n\n"
                "# Short Term Summary:\n\n" + short_term_summary +
                "\n\n"
                "# Medium Term Summary:\n\n" + medium_term_summary +
                "\n\n"
                "# Long Term Summary:\n\n" + long_term_summary +
                "\n\n"
                "# Potentially Related Information:\n\n```json\n" + json.dumps(results) + "\n```"
                "\n\n"
                "# Validation:"
                "\n\n"
                "- If you accidentally describe a player character’s thoughts or resolve tension, stop immediately and issue a correction in-world. Do not continue the mistake.\n"
                "- If you accidentally write more than 250 characters, shorten the response if possible."
        },
    ]
    try:
        mdbconn.cursor().execute("CREATE DATABASE IF NOT EXISTS `"+uuid+"`;")
        mdbconn.cursor().execute("USE `"+uuid+"`;")
        mdbconn.cursor().execute(
            "CREATE TABLE IF NOT EXISTS messages (aid BIGINT NOT NULL AUTO_INCREMENT, creator varchar(6),content text, PRIMARY KEY(aid)) charset=utf8;")
        cursor = mdbconn.cursor()
        cursor.execute("SELECT * FROM (SELECT creator, content, aid FROM messages ORDER BY aid DESC LIMIT 20) as a ORDER BY aid ASC;")
        old_messages = cursor.fetchall()
        previous_response = ""
        for message in old_messages:
            messages.append({
                "role": message[0],
                "content": message[1],
            })
            previous_response = message[1]
        mdbconn.cursor().execute("INSERT INTO messages (`creator`, `content`) VALUES ('user', ?);", [action.description])
        messages.append({
            "role": "user",
            "content": action.description,
        })
        response: ChatResponse = ollama.chat(
            model=os.getenv("LLM_MODEL"),
            messages=messages
        )
        response_content = response["message"]["content"]
        qdrant.add(
            collection_name=uuid,
            documents=[previous_response + "\n\n" + action.description + "\n\n" + response_content],
        )
        mdbconn.cursor().execute("INSERT INTO messages (`creator`, `content`) VALUES ('agent', ?);", [response_content])
        return {"message": response_content, "prompt": messages}
    except mariadb.Error as e:
        return {"error": f"{e}"}
    except Exception as e:
        return {"exception": e}
