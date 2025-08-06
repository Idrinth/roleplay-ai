from .databases import redis

ACTIVE_KEY="chat_is_active"

def chat_is_in_use(user_id: str, chat_id: str):
    return redis.get(f"{user_id}-{chat_id}.{ACTIVE_KEY}") == "true"

async def set_chat_unused(user_id: str, chat_id: str):
    await redis.set(f"{user_id}-{chat_id}.{ACTIVE_KEY}", "false")

async def set_chat_in_use(user_id: str, chat_id: str):
    await redis.set(f"{user_id}-{chat_id}.{ACTIVE_KEY}", "true")
