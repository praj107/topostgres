from datetime import datetime
from rich import print
from rich.markup import escape

def log(msg, level="info"):
    """
    Log a message with timestamp and level.
    Safely handles any type of message and prevents crashing on bad input.

    Args:
        msg (Any): Message to log.
        level (str): Log level ("info", "success", "warn", "error").
    """
    colors = {
        "info": "blue",
        "success": "green",
        "warn": "yellow",
        "error": "red",
    }
    try:
        if not isinstance(msg, str):
            msg = str(msg)

        safe_msg = escape(msg)
        color = colors.get(level.lower(), "white")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"[{color}][{timestamp}] [{level.upper()}] {safe_msg}[/]")
    except Exception as e:
        # If even logging fails, fallback hard
        fallback_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{fallback_time}] [LOG - {level.upper()}] (Logging error: {e}) {msg}")
