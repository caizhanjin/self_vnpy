import json
import os

from .log_config import initialize_logging

BASE_PATH = os.path.dirname(__file__)
ROOT_PATH = os.path.dirname(BASE_PATH)
JSON_PATH = os.path.join(BASE_PATH, "json")


def load_settings():
    SETTINGS_PATH = os.path.join(JSON_PATH, "settings.json")
    with open(SETTINGS_PATH, "r", encoding="utf8") as f:
        SETTINGS = json.load(f)

    if not os.path.exists(SETTINGS["tqdata_save_path"]):
        os.makedirs(SETTINGS["tqdata_save_path"])

    return SETTINGS


def load_futures():
    FUTURES_PATH = os.path.join(JSON_PATH, "futures.json")
    with open(FUTURES_PATH, "r", encoding="utf8") as f:
        FUTURES = json.load(f)
    return FUTURES


def init_logging():
    """初始化log配置"""
    initialize_logging(ROOT_PATH)
