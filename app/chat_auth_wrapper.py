from typing import Callable
import mariadb
from fastapi import BackgroundTasks

from models import Background
from .chat_active import chat_is_in_use, set_chat_unused, set_chat_in_use

from .functions import user_id_from_jwt, is_uuid_like

async def wrap(chat_id: str, user_jwt: str|None, success_callback: Callable, model = None, lock = False, background_tasks: BackgroundTasks = None):
    if not user_jwt:
        return {"error": "Not a valid User"}
    user_id = user_id_from_jwt(user_jwt)
    if not is_uuid_like(user_id):
        return {"error": "Not a valid User"}
    if not is_uuid_like(chat_id):
        return {"error": "Not a valid Chat"}
    if lock and chat_is_in_use(chat_id, user_id):
        return {"error": "Chat already busy"}
    try:
        if lock:
            set_chat_in_use(user_id, chat_id)
        if model and background_tasks:
            return await success_callback(chat_id, user_id, model, background_tasks)
        if background_tasks:
            return await success_callback(chat_id, user_id, background_tasks)
        if model:
            return await success_callback(chat_id, user_id, model)
        return await success_callback(chat_id, user_id)
    except mariadb.Error as e:
        if lock:
            set_chat_unused(user_id, chat_id)
        return {"error": f"{e}"}
    except Exception as e:
        if lock:
            set_chat_unused(user_id, chat_id)
        return {"exception": f"{e}"}
