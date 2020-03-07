"""
从tqdata直接同步数据到数据库

注：最多只可获取最近8964条

@parm interval : example 1m 1d
"""
from libs.db.sqlite import DatabaseSqlite
from tqsdk import TqApi

default_settings = {
    "data_length": 8964,
    "duration_seconds": 60,
    "interval": "1m",
}

sync_list = [
    {
        "symbol_tq": "SHFE.ru2005",
        "symbol_db": "ru2005",
        "exchange": "SHFE",
        "interval": "1h",
        "data_length": 50,
        "duration_seconds": 60 * 60,
    },
    {
        "symbol_tq": "SHFE.rb2005",
        "symbol_db": "rb2005",
        "exchange": "SHFE",
        "interval": "1d",
        "data_length": 50,
        "duration_seconds": 60 * 60 * 24,
    },
]


def sync_db():
    api = TqApi()
    queryset = DatabaseSqlite()

    for item in sync_list:
        try:
            df = api.get_kline_serial(
                symbol=item["symbol_tq"],
                duration_seconds=item.get("duration_seconds", default_settings["duration_seconds"]),
                data_length=item.get("data_length", default_settings["data_length"])
            )
            queryset.update_from_df(
                df=df,
                exchange=item["exchange"],
                symbol=item["symbol_db"],
                interval=item.get("interval", default_settings["interval"]),
                time_handler_type="nanometre"
            )
        except Exception as error:
            print(f"{item['symbol_tq']} 导入失败，原因：{error}")

    queryset.close()

    print("\n列表同步完毕！！！")


if __name__ == "__main__":
    sync_db()

