from rich import print

def log(msg, level="info"):
    colors = {
        "info": "blue",
        "success": "green",
        "warn": "yellow",
        "error": "red",
    }
    print(f"[{colors.get(level, 'white')}][LOG] {msg}[/]")