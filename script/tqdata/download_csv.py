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
from libs.db.sqlite import DatabaseSqlite


SETTINGS = load_settings()

default_settings = {
    "save_path": SETTINGS["tqdata_save_path"],
    "cycle": 1 * 60,  # 1min
    "interval": "1m",
    "start_dt": date(2020, 3, 5),
    "end_dt": date(2020, 3, 8),

}

download_list = [
    {
        "symbol": "KQ.i@SHFE.bu",
    },
    {
        "symbol": "KQ.i@SHFE.cu",
    },
    {
        "symbol": "SHFE.cu2005",
    },
]


def download(return_paths=False):
    api = TqApi(TqSim())

    download_tasks = {}
    csv_paths = []

    for item in download_list:
        save_path = item.get("save_path", default_settings["save_path"])
        symbol = item["symbol"]
        start_dt = item.get("start_dt", default_settings["start_dt"])
        end_dt = item.get("end_dt", default_settings["end_dt"])
        interval = item.get("interval", default_settings["interval"])
        csv_file_name = symbol + "_" + interval + "_" + \
                        start_dt.strftime("%Y%m%d") + "_" + end_dt.strftime("%Y%m%d") + ".csv"
        csv_file_path = path.join(save_path, csv_file_name)
        if return_paths:
            csv_paths.append(csv_file_path)
        download_tasks[item["symbol"]] = DataDownloader(
            api,
            symbol_list=symbol,
            dur_sec=item.get("cycle", default_settings["cycle"]),
            start_dt=start_dt,
            end_dt=end_dt,
            csv_file_name=csv_file_path
        )

    with closing(api):
        while not all([v.is_finished() for v in download_tasks.values()]):
            api.wait_update()
            print("progress: ", {k: ("%.2f%%" % v.get_progress()) for k, v in download_tasks.items()})

    if return_paths:
        return csv_paths


def sync_db(csv_paths: list):
    """同步下载csv数据库
    @:param csv_path_list 同步csv文件列表，注：必须是天勤下载的csv格式，如KQ.i@SHFE.cu_20200305_20200308.csv
    """
    queryset = DatabaseSqlite()

    for item in csv_paths:
        csv_name = path.basename(item)
        csv_name_split1 = csv_name.split("@")
        index_name = ""
        if len(csv_name_split1) == 1:
            csv_name_split2 = csv_name_split1[0].split("_")
        else:
            csv_name_split2 = csv_name_split1[1].split("_")
            if csv_name_split1[0] == "KQ.i":
                index_name = "99"
            elif csv_name_split1[0] == "KQ.m":
                index_name = "88"

        csv_name_split3 = csv_name_split2[0].split(".")
        exchange = csv_name_split3[0]
        symbol = csv_name_split3[1] if not index_name else csv_name_split3[1] + index_name
        interval = csv_name_split2[1]
        head_prefix = csv_name.split("_")[0]

        queryset.import_csv_single(
            csv_file_path=item,
            symbol=symbol,
            exchange=exchange,
            interval=interval,
            datetime="datetime",
            open=head_prefix + ".open",
            high=head_prefix + ".high",
            low=head_prefix + ".low",
            close=head_prefix + ".close",
            volume=head_prefix + ".volume"
        )

    queryset.close()


def download_and_sync():
    """下载并同步数据库"""
    csv_path_list = download(return_paths=True)
    sync_db(csv_path_list)


if __name__ == "__main__":
    # download()

    # csv_path_list = [
    #     "C:\\self_vnpy\\history_data\\tq\\KQ.i@SHFE.bu_1m_20200305_20200308.csv",
    #     "C:\\self_vnpy\\history_data\\tq\\SHFE.cu2005_1m_20200305_20200308.csv",
    #     "C:\\self_vnpy\\history_data\\tq\\KQ.i@SHFE.cu_1m_20200305_20200308.csv"
    # ]
    # sync_db(csv_path_list)

    download_and_sync()


