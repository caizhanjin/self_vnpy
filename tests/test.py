# -*- coding:utf-8 -*-
from datetime import datetime, date
from os import path
from configs.main_configs import FUTURES

import json


def test_import_json():
    json_path = "C:\\self_vnpy\\configs\\json\\settings.json"
    with open(json_path, "r") as f:
        data = json.load(f)
        print(date)


if __name__ == "__main__":
    print(FUTURES)
    print(FUTURES["BU"])

    print("Finish test!")
