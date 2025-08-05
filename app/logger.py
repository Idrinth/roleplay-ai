from datetime import datetime, timezone
import mariadb
import os

ALLOWED_LOG_TYPES = os.getenv("ALLOWED_LOG_TYPES", default="warning,error").split(",")

def log(message: str, func_name, log_type: str) -> None:
    if log_type not in ALLOWED_LOG_TYPES:
        return
    print(f"[{datetime.now(timezone.utc).isoformat()}][{func_name}] {log_type}: {message.replace("\n", "\\n")}")

def log_exception(ex: Exception|mariadb.Error, func_name: str) -> None:
    log(f"{type(ex)}: {ex}", func_name, "error")

def log_error(message: str, func_name: str) -> None:
    log(message, func_name, "error")

def log_warning(message: str, func_name: str) -> None:
    log(message, func_name, "warning")

def log_info(message: str, func_name: str) -> None:
    log(message, func_name, "info")

def log_debug(message: str, func_name: str) -> None:
    log(message, func_name, "debug")
