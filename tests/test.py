# -*- coding:utf-8 -*-
from datetime import datetime, date
from os import path
# from configs.main_configs import FUTURES
import time
import json


def test_import_json():
    json_path = "C:\\self_vnpy\\configs\\json\\settings.json"
    with open(json_path, "r") as f:
        data = json.load(f)
        print(data)


if __name__ == "__main__":
    print("2020-03-05 09:00:00.998885"[:19])
    print(len('2020-03-05 09:00:00'))

    print("Finish test!")
