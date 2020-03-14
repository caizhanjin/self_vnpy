import json
import os

BASE_PATH = os.path.dirname(__file__)
ROOT_PATH = os.path.dirname(BASE_PATH)
JSON_PATH = os.path.join(BASE_PATH, "json")


def load_settings():
    SETTINGS_PATH = os.path.join(JSON_PATH, "settings.json")
    with open(SETTINGS_PATH, "r", encoding="utf8") as f:
        SETTINGS = json.load(f)

    return SETTINGS


def load_futures():
    FUTURES_PATH = os.path.join(JSON_PATH, "futures.json")
    with open(FUTURES_PATH, "r", encoding="utf8") as f:
        FUTURES = json.load(f)
    return FUTURES




