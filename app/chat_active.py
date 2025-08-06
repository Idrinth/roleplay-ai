from .databases import redis

ACTIVE_KEY="chat_is_active"

def chat_is_in_use(user_id: str, chat_id: str):
    value = redis.get(f"{user_id}-{chat_id}.{ACTIVE_KEY}")
    return value and (value == b"true" or value.decode() == "true")

def set_chat_unused(user_id: str, chat_id: str):
    redis.set(f"{user_id}-{chat_id}.{ACTIVE_KEY}", "false")
    redis.expire(f"{user_id}-{chat_id}.{ACTIVE_KEY}", 600)

def set_chat_in_use(user_id: str, chat_id: str):
    redis.set(f"{user_id}-{chat_id}.{ACTIVE_KEY}", "true")
    redis.expire(f"{user_id}-{chat_id}.{ACTIVE_KEY}", 600)

def remove_chat_from_use(user_id: str, chat_id: str):
    redis.delete(f"{user_id}-{chat_id}.{ACTIVE_KEY}")
