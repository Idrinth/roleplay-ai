from redis import Redis

def chat_is_in_use(redis: Redis, user_id: str, chat_id: str):
    return redis.get(f"{user_id}-{chat_id}.chat_is_active") == "true"

def set_chat_unused(redis: Redis, user_id: str, chat_id: str):
    redis.set(f"{user_id}-{chat_id}.chat_is_active", "false")

def set_chat_in_use(redis: Redis, user_id: str, chat_id: str):
    redis.set(f"{user_id}-{chat_id}.chat_is_active", "true")
