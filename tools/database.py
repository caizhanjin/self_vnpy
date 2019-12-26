# -*- coding:utf-8 -*-
import sqlite3


class DatabaseSqlite(object):
    """sqlite 数据库操作类"""
    database_path = "C:\\self_vnpy\\.vntrader\\database.db"
    db_connect = object
    cursor = object

    def __init__(self, database_path=""):
        if database_path:
            self.database_path = database_path
        self.connect()

    def query_future(self, symbol='', interval='1m', begin_date='', end_date='', used_close=False, fields=None):
        """
        @param: interval ('1m', 'd')
        """
        if fields is None:
            fields = ['symbol', 'datetime', 'interval', 'volume', 'open_price', 'high_price', 'close_price']
        fields_str = '' if len(fields) == 0 else ', '.join(fields)

        sql_base = f"SELECT {fields_str} FROM dbbardata"
        sql_order = " ORDER BY datetime ASC"
        sql_filter = f" WHERE interval='{interval}'"
        if symbol:
            sql_filter += f" AND symbol='{symbol}'"
        if begin_date:
            sql_filter += f" AND datetime>='{begin_date}'"
        if end_date:
            end_date += ' 23:59:59'
            sql_filter += f" AND datetime<='{end_date}'"

        self.cursor.execute(sql_base + sql_filter + sql_order)
        result = self.cursor.fetchall()

        if used_close:
            self.close()

        return result

    def connect(self):
        self.db_connect = sqlite3.connect(self.database_path)
        self.cursor = self.db_connect.cursor()

    def close(self):
        self.cursor.close()
        self.db_connect.close()

