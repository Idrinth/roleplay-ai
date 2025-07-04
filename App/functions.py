import uuid
import json
from qdrant_client.http.models import QueryResponse
from bson.objectid import ObjectId
from enum import StrEnum
from pydantic import BaseModel
from bson import json_util

with open('./app/character-sheet.schema.json', 'r') as schema_file:
    schema = json.dumps(json.load(schema_file))

def mariadb_name(user_id: str, chat_id: str):
    # max length 64
    return f"{user_id}{chat_id}".replace("-", "")

def mongodb_name(user_id: str, chat_id: str):
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
    if len(characters) >= 1:
        out += "# Player Characters:\nThe following character sheets are for reference ONLY."\
            " Do not use these to infer motivations or write actions for player characters."\
            "\n```json\n" + json.dumps(characters, default=json_util.default) + "\n```\n"\
            "## Character Sheet Schema:\n```json\n" + schema + "\n```\n"
    if len(world) > 0:
        out += "# World:\n" + ", ".join(world) + "\n"
    if short_term_summary != "":
        out += "# Short Term Summary:\n" + short_term_summary +"\n"
    if medium_term_summary != "":
        out += "# Medium Term Summary:\n" + medium_term_summary +"\n"
    if long_term_summary != "":
        out += "# Long Term Summary:\n" + long_term_summary +"\n"
    if len(vectordb_results) > 0:
        out += "# Potentially Related Information:\n```json\n" + json.dumps(vectordb_results) + "\n```"
    return out.strip()