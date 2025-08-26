from qdrant_client import QdrantClient
import mariadb
from redis import Redis
from pymongo import MongoClient

qdrant = QdrantClient("http://qdrant:6333")
qdrant.set_model(qdrant.DEFAULT_EMBEDDING_MODEL, providers=["CPUExecutionProvider"])
redis = Redis(host="redis", port=6379, db=0, decode_responses=True)
mongo = MongoClient("mongodb://root:example@mongo:27017/")
sql_connection = mariadb.connect(
    user="root",
    password="example",
    host="mariadb",
    port=3306
)
sql_connection.autocommit = True
sql_connection.auto_reconnect = True
