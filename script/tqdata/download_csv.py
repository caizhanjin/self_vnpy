# -*- coding:utf-8 -*-
"""
从tqdata下载数据到本地：
需要安装天勤包：pip install tqsdk -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com

只需将要下载的数据填入：download_list即可
default_settings是默认设置，当然也可以在download_list中个性化


SHFE 上海期货交易所
DCE 大连商品交易所
CZCE 郑州商品交易所
CFFEX 中国金融交易所
INE 上海能源中心(原油在这里)
KQ 快期 (所有主连合约, 指数都归属在这里)
SSWE 上期所仓单
SSE 上海证券交易所(尚未上线)
SZSE 深圳证券交易所(尚未上线)


一些合约代码示例:
SHFE.cu1901 - 上期所 cu1901 期货合约
DCE.m1901 - 大商所 m1901 期货合约
CZCE.SR901 - 郑商所 SR901 期货合约
CFFEX.IF1901 - 中金所 IF1901 期货合约

CZCE.SPD SR901&SR903 - 郑商所 SR901&SR903 跨期合约
DCE.SP a1709&a1801 - 大商所 a1709&a1801 跨期合约

DCE.m1807-C-2450 - 大商所豆粕期权
CZCE.CF003C11000 - 郑商所棉花期权
SHFE.au2004C308 - 上期所黄金期权
CFFEX.IO2002-C-3550 - 中金所沪深300股指期权


KQ.m@CFFEX.IF - 中金所IF品种主连合约
KQ.i@SHFE.bu - 上期所bu品种指数
"""
from datetime import date
from contextlib import closing
from tqsdk import TqApi, TqSim
from tqsdk.tools import DataDownloader
from os import path

from configs.main_configs import load_settings

SETTINGS = load_settings()

default_settings = {
    "save_path": SETTINGS["tqdata_save_path"],
    "cycle": 1 * 60,  # 1min
    "start_dt": date(2019, 9, 1),
    "end_dt": date(2019, 9, 4),
}

download_list = [
    {
        "symbol": "KQ.i@SHFE.bu",
        "save_name": "BU_99_SHFE.csv",
    },
    {
        "symbol": "KQ.i@SHFE.cu",
        "save_name": "CU_99_SHFE.csv",
    },
]


def download():
    api = TqApi(TqSim())

    download_tasks = {}

    for item in download_list:
        save_path = item.get("save_path", default_settings["save_path"])
        download_tasks[item["symbol"]] = DataDownloader(
            api,
            symbol_list=item["symbol"],
            dur_sec=item.get("cycle", default_settings["cycle"]),
            start_dt=item.get("start_dt", default_settings["start_dt"]),
            end_dt=item.get("end_dt", default_settings["end_dt"]),
            csv_file_name=path.join(save_path, item["save_name"])
        )

    with closing(api):
        while not all([v.is_finished() for v in download_tasks.values()]):
            api.wait_update()
            print("progress: ", {k: ("%.2f%%" % v.get_progress()) for k, v in download_tasks.items()})


if __name__ == "__main__":
    download()
