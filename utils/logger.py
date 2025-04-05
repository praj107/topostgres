from rich import print

def log(msg, level="info"):
    """
    Log a message with a specific level.
    This function prints the message to the console with a color based on the log level.

    Args:
        msg (str): The message to log.
        level (str): The log level. Can be "info", "success", "warn", or "error". Defaults to "info".
    """
    colors = {
        "info": "blue",
        "success": "green",
        "warn": "yellow",
        "error": "red",
    }
    print(f"[{colors.get(level, 'white')}][LOG] {msg}[/]")