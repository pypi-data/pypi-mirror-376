from datetime import datetime
from typing import Any

def _ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log(message: Any, level: str = "INFO") -> None:
    colors = {
        "INFO": "\033[94m",
        "WARN": "\033[93m",
        "ERROR": "\033[91m",
        "DEBUG": "\033[90m",
    }
    reset = "\033[0m"
    prefix = f"[{_ts()}] {level}:"
    color = colors.get(level, "")
    try:
        print(f"{color}{prefix} {message}{reset}")
    except Exception:
        print(f"{prefix} {message}")
