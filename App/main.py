import json
import re

from ollama import ChatResponse, Client
from qdrant_client import QdrantClient
from qdrant_client.http.models import QueryResponse
from fastapi import FastAPI
import mariadb
from redis import Redis
from pymongo import MongoClient
from pydantic import BaseModel
import os
from fastapi.middleware.cors import CORSMiddleware
from bson import json_util

def simplify_result(query_result: QueryResponse):
    return query_result.model_dump(mode="json")


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost', 'http://127.0.0.1'],
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

@app.post("/chat/{uuid}/characters")
def chat_character(uuid: str, character: BaseModel):
    mydb = mongo[uuid]
    return mydb['characters'].insert_one(character)

@app.put("/chat/{uuid}/characters/{id}")
def chat_character(uuid: str, id: str, character: BaseModel):
    mydb = mongo[uuid]
    mydb['characters'].delete_one({"_id": id})
    mydb['characters'].insert_one(character)
    return True

@app.delete("/chat/{uuid}/characters/{id}")
def chat_character(uuid: str, id: str):
    mydb = mongo[uuid]
    mydb['characters'].delete_one({"_id": id})
    return True

@app.get("/chat/{uuid}/characters")
def chat_character(uuid: str):
    try:
        return json.loads(json.dumps({"characters": list(mongo[uuid]['characters'].find())}, default=json_util.default))
    except Exception as e:
        return {"exception": f"{e}"}

@app.get("/chat/{uuid}")
def chat_history(uuid: str):
    try:
        messages = []
        mdbconn.ping()
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

@app.post("/chat/{uuid}")
def chat(uuid: str, action: Action):
    if not os.getenv("LLM_MODEL"):
        return {"error": "A model is needed."}
    if not action.description:
        return {"error": "A description is required."}
    long_term_summary = redis.get(uuid + ".long_text_summary") or "Nothing happened yet."
    medium_term_summary = redis.get(uuid + ".medium_text_summary") or "Nothing happened yet."
    short_term_summary = redis.get(uuid + ".short_text_summary") or "Nothing happened yet."
    characters = []
    try:
        mydb = mongo[uuid]
        mycol = mydb["characters"]
        characters = list(mycol.find())
    except Exception as e:
        print(f"{e}")
    world = "dark fantasy, Warhammer Fantasy"
    messages = []
    try:
        mdbconn.ping()
        mdbconn.cursor().execute("CREATE DATABASE IF NOT EXISTS `"+uuid+"`;")
        mdbconn.cursor().execute("USE `"+uuid+"`;")
        mdbconn.cursor().execute(
            "CREATE TABLE IF NOT EXISTS messages (aid BIGINT NOT NULL AUTO_INCREMENT, creator varchar(6),"
            "content text, PRIMARY KEY(aid)) charset=utf8;")
        cursor = mdbconn.cursor()
        cursor.execute("SELECT * FROM (SELECT creator, content, aid FROM messages ORDER BY aid DESC LIMIT 20) as a ORDER BY aid;")
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
        if qdrant.collection_exists(uuid):
            search_result = qdrant.query(
                collection_name=uuid,
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
        mdbconn.cursor().execute("INSERT INTO messages (`creator`, `content`) VALUES ('user', ?);", [action.description])
        messages.append({
            "role": "user",
            "content": action.description,
        })
        response: ChatResponse = ollama.chat(
            model=os.getenv("LLM_MODEL"),
            messages=messages
        )
        response_content = re.sub("^(\n|.)*</think>\\s*", "", response["message"]["content"]).strip()
        qdrant.add(
            collection_name=uuid,
            documents=[previous_response + "\n\n" + action.description + "\n\n" + response_content],
        )
        mdbconn.cursor().execute("INSERT INTO messages (`creator`, `content`) VALUES ('agent', ?);", [response_content])
        return {"message": response_content}
    except mariadb.Error as e:
        return {"error": f"{e}"}
    except Exception as e:
        return {"exception": f"{e}", "data": e}
