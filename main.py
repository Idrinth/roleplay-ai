import json

from ollama import ChatResponse, Client
from qdrant_client import QdrantClient
from qdrant_client.http.models import QueryResponse
from fastapi import FastAPI
import mariadb
from redis import Redis
from pymongo import MongoClient


def simplify_result(query_result: QueryResponse):
    return query_result.model_dump(mode="json")


app = FastAPI()

ollama = Client(host="http://ollama:11434")
qdrant = QdrantClient("http://quadrant:6333")
qdrant.set_model(qdrant.DEFAULT_EMBEDDING_MODEL, providers=["CPUExecutionProvider"])
redis = Redis(host="redis", port=6379, db=0)
mongo = MongoClient("mongodb://mongo:27017/")
mdbconn = mariadb.connect(
    user="root",
    password="example",
    host="mariadb",
    port=3306
)

@app.get("/")
def index():
    return {"message": "Hello, World!"}


@app.put("/chat/{uuid}")
def chat(uuid: str, body: str):
    search_result = qdrant.query(
        collection_name=uuid,
        query_text=body,
        limit=25
    )
    result = []
    for res in search_result:
        result.append(simplify_result(res))
    #mydb = myclient["mydatabase"]
    long_term_summary = redis.get(uuid + ".long_text_summary") or ""
    medium_term_summary = redis.get(uuid + ".medium_text_summary") or ""
    short_term_summary = redis.get(uuid + ".short_text_summary") or ""
    try:
        cursor = mdbconn.cursor()
        cursor.execute("CREATE DATABASE `"+uuid+"` IF NOT EXISTS")
        cursor.execute("USE DATABASE `"+uuid+"`")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS  messages {aid BIGINT NOT NULL autoincrement, creator char(5),content text, PRIMARY KEY aid} charset=utf8;")
        messages = cursor.execute("SELECT creator, content FROM messages LIMIT 20 SORT BY aid DESC").fetchall()
    except Exception as e:
        print(e)
    response: ChatResponse = ollama.chat(
        model="gemma3",
        messages=[
            {
                "role": "agent",
                "content": "Personality:\n\nYou are a game master. React to provided texts with in character responses and try to progress the story appropriately taking the provided context into account."
                           "\n\n"
                           "Short Term Summary:\n\n" + short_term_summary +
                           "\n\n"
                           "Medium Term Summary:\n\n" + medium_term_summary +
                           "\n\n"
                           "Long Term Summary:\n\n" + long_term_summary +
                           "\n\n"
                           "Further Information:\n\n" + json.dumps(result),
            },
            {
                "role": "user",
                "content": "Action:\n\n" + body,
            },
        ]
    )
    return {"message": response["message"]["content"]}
