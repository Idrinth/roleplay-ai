from typing import Callable
import mariadb
from fastapi import BackgroundTasks

from .chat_active import chat_is_in_use, set_chat_unused, set_chat_in_use
from .logger import log_exception
from .functions import user_id_from_jwt, is_uuid_like

async def wrap(chat_id: str, user_jwt: str|None, success_callback: Callable, model = None, lock = False, background_tasks: BackgroundTasks = None):
    if not user_jwt:
        return {"error": "Not a valid User"}
    user_id = user_id_from_jwt(user_jwt)
    if not is_uuid_like(user_id):
        return {"error": "Not a valid User"}
    if not is_uuid_like(chat_id):
        return {"error": "Not a valid Chat"}
    if lock and chat_is_in_use(user_id, chat_id):
        return {"error": "Chat already busy"}
    try:
        if lock:
            set_chat_in_use(user_id, chat_id)
        if model and background_tasks:
            result = await success_callback(chat_id, user_id, model, background_tasks)
        elif background_tasks:
            result = await success_callback(chat_id, user_id, background_tasks)
        elif model:
            result = await success_callback(chat_id, user_id, model)
        else:
            result = await success_callback(chat_id, user_id)
        if lock:
            set_chat_unused(user_id, chat_id)
        return result
    except mariadb.Error as e:
        if lock:
            set_chat_unused(user_id, chat_id)
        log_exception(e, "chat_auth_wrapper.wrap")
        return {"error": "An error occurred, please try again later"}
    except Exception as e:
        if lock:
            set_chat_unused(user_id, chat_id)
        log_exception(e, "chat_auth_wrapper.wrap")
        return {"error": "An error occurred, please try again later"}
