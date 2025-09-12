import os
import platform
import json

def clear_screen():
    os.system("cls" if platform.system() == "Windows" else "clear")

def load_config(path="config.json"):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_config(config, path="config.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
