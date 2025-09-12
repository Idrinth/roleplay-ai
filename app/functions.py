import os
import uuid
import json
import base64
from qdrant_client.http.models import QueryResponse
from bson.objectid import ObjectId
from enum import StrEnum
from pydantic import BaseModel
from bson import json_util
from datetime import datetime, UTC, timedelta
from jwt import encode, decode
from .databases import redis

from .logger import log_exception

with open('./app/charactersheet.schema.json', 'r') as schema_file:
    schema = json.dumps(json.load(schema_file))

def b64(s: str)->str:
    return base64.b64encode(s.encode("ascii")).decode("ascii")

def mariadb_name(user_id: str, chat_id: str):
    if not is_uuid_like(user_id):
        raise TypeError('user_id is not a uuid')
    if not is_uuid_like(chat_id):
        raise TypeError('chat_id is not a uuid')
    # max length 64
    return f"{user_id}{chat_id}".replace("-", "")

def mongodb_name(user_id: str, chat_id: str):
    if not is_uuid_like(user_id):
        raise TypeError('user_id is not a uuid')
    if not is_uuid_like(chat_id):
        raise TypeError('chat_id is not a uuid')
    # max length 63
    return f"{user_id}{chat_id}".replace("-", "")[:-1]

def simplify_result(query_result: QueryResponse):
    return query_result.model_dump(mode="json")

def is_uuid_like(string: str):
    if string is None:
        return False
    if string == "":
        return False
    try:
        uuid.UUID(string)
        return True
    except ValueError:
        return False

def to_mongo_compatible(obj: BaseModel, object_id: str | None = None):
    dc = obj.model_dump()
    for k, v in dc.items():
        if isinstance(v, BaseModel):
            dc[k] = to_mongo_compatible(v)
        elif isinstance(v, StrEnum):
            dc[k] = v.value
    if object_id is not None:
        dc["_id"] = ObjectId(object_id)
    return dc

def get_system_prompt(characters, world: str, short_term_summary: str, medium_term_summary: str, long_term_summary: str, vectordb_results):
    out = ""
    if len(characters) > 0:
        out += "# Player Characters:\nThe following character sheets are for reference ONLY."\
            " Do not use these to infer motivations or write actions for player characters."\
            "\n```json\n" + json.dumps(characters, default=json_util.default) + "\n```\n"\
            "## Character Sheet Schema:\n```json\n" + schema + "\n```\n"
    if len(world) > 0:
        out += "# World:\n" + world + "\n"
    if short_term_summary != "":
        out += "# Short Term Summary:\n" + short_term_summary +"\n"
    if medium_term_summary != "":
        out += "# Medium Term Summary:\n" + medium_term_summary +"\n"
    if long_term_summary != "":
        out += "# Long Term Summary:\n" + long_term_summary +"\n"
    if len(vectordb_results) > 0:
        out += "# Potentially Related Information:\n```json\n" + json.dumps(vectordb_results) + "\n```"
    return out.strip()

def user_id_from_jwt(encoded_jwt: str) -> str|None:
    try:
        payload = decode(encoded_jwt, os.getenv('PUBLIC_KEY_PEM'), algorithms=["RS256"])
        if payload['iss'] != os.getenv("UI_HOST", "http://localhost"):
            return None
        return payload["sub"]
    except Exception as e:
        log_exception(e, "functions.user_id_from_jwt")
        return None

def user_id_to_jwt(user_id: str):
    return encode(
        {
            'iss': os.getenv("UI_HOST", "http://localhost"),
            'sub': user_id,
            'exp': datetime.now(UTC) + timedelta(days=360),
            'nbf': datetime.now(UTC),
        },
        os.getenv('PRIVATE_KEY_PEM'),
        algorithm='RS256'
    )

def set_login_cookie(response, user_id: str):
    response.set_cookie(
        key="user_jwt",
        value=user_id_to_jwt(user_id),
        samesite="strict",
        secure=True,
        path="/",
        expires=60*60*24*30*12,
        domain=os.getenv("UI_HOST", "http://localhost").replace("http://", "").replace("https://", ""),
        httponly=True
    )

def get_from_redis(user_id: str, chat_id: str, key: str, default: str=""):
    data = redis.get(f"{user_id}-{chat_id}.{key}")
    if data is None:
        return default
    if isinstance(data, bytes):
        data = data.decode()
    return data or default
