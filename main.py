import json

from ollama import ChatResponse, Client
from qdrant_client import QdrantClient
from qdrant_client.http.models import QueryResponse
from fastapi import FastAPI
import mariadb
from redis import Redis
from pymongo import MongoClient
from pydantic import BaseModel
from fastapi.responses import HTMLResponse


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


@app.post("/chat/{uuid}/characters")
def chat_character(uuid: str, character: Character):
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
            limit=25
        )
        for res in search_result:
            results.append(simplify_result(res))
    #mydb = myclient["mydatabase"]
    long_term_summary = redis.get(uuid + ".long_text_summary") or ""
    medium_term_summary = redis.get(uuid + ".medium_text_summary") or ""
    short_term_summary = redis.get(uuid + ".short_text_summary") or ""
    messages = [
        {
            "role": "system",
            "content": "Personality:\n\nYou are a game master. React to provided actions with in character responses. Try to progress the story in small steps. Take the provided context into account. The player character's/characters' action(s) are not yours to define. Do keep your responses below 1000 characters."
                       "\n\n"
                       "Rules: DO NOT resolve narrative tensions. DO NOT change character names. DO play NPCs. FOCUS on immediate consequences and reactions to player actions. DO describe enviromental changes. DO add dialogue, sensory details and atmosphere. DO keep the core situation intact for players to resolve. DO NOT invent details, ask for clarification insted."
                       "\n\n"
                       "Player Character(s): Idrinth Thalui, Lienne Thalui"
                       "\n\n"
                       "World: dark fantasy, Warhammer Fantasy inspired"
                       "\n\n"
                       "Short Term Summary:\n\n" + short_term_summary +
                       "\n\n"
                       "Medium Term Summary:\n\n" + medium_term_summary +
                       "\n\n"
                       "Long Term Summary:\n\n" + long_term_summary +
                       "\n\n"
                       "Related Information:\n\n" + json.dumps(results),
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
        for message in old_messages:
            messages.append({
                "role": message[0],
                "content": message[1],
            })
        mdbconn.cursor().execute("INSERT INTO messages (`creator`, `content`) VALUES ('user', ?);", [action.description])
        messages.append({
            "role": "user",
            "content": action.description,
        })
        response: ChatResponse = ollama.chat(
            model="Tohur/natsumura-storytelling-rp-llama-3.1",
            messages=messages
        )
        response_content = response["message"]["content"]
        qdrant.add(
            collection_name=uuid,
            documents=[action.description + "\n\n" + response_content],
        )
        mdbconn.cursor().execute("INSERT INTO messages (`creator`, `content`) VALUES ('agent', ?);", [response_content])
        return {"message": response_content}
    except mariadb.Error as e:
        return {"error": f"{e}"}
    except Exception as e:
        return {"exception": e}
