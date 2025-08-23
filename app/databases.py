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
sql_connection.cursor().execute("CREATE DATABASE IF NOT EXISTS `chat_users`;")
sql_connection.cursor().execute("CREATE TABLE IF NOT EXISTS chat_users.mapping"
                         " (user_id char(36),chat_id char(36), chat_name varchar(255), PRIMARY KEY(user_id, chat_id))"
                         " charset=utf8;")
sql_connection.cursor().execute("CREATE TABLE IF NOT EXISTS chat_users.users"
                         " (aid BIGINT AUTO_INCREMENT NOT NULL, user_id char(36), user_name varchar(255), password varchar(255), active tinyint(1), PRIMARY KEY(aid), UNIQUE (user_id))"
                         " charset=utf8;")
try:
    sql_connection.cursor().execute("ALTER TABLE chat_users.users"
                                    " ADD COLUMN email text default NULL,"
                                    " ADD COLUMN remaining_messages INT(10) unsigned DEFAULT 10,"
                                    " ADD COLUMN last_incremented INT(10) unsigned DEFAULT UNIX_TIMESTAMP(),"
                                    " ADD COLUMN increment_every_seconds INT(10) unsigned DEFAULT 1800,"
                                    " ADD COLUMN maximum_remaining_messages INT(10) unsigned DEFAULT 25"
                                    ";")
except mariadb.Error as e:
    pass

sql_connection.cursor().execute("CREATE TABLE IF NOT EXISTS chat_users.statistics"
                         " (label varchar(255), value DECIMAL UNSIGNED NOT NULL DEFAULT 0, PRIMARY KEY(label))"
                         " charset=utf8;")

sql_connection.cursor().execute("CREATE TABLE IF NOT EXISTS chat_users.keywords "
    "(word varchar(255), count DECIMAL UNSIGNED NOT NULL DEFAULT 0, PRIMARY KEY(word)) "
    "charset=utf8;")