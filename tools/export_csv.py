# -*- coding:utf8 -*-
import sqlite3
import os
import csv
import time


if __name__ == "__main__":
    start_time = time.time()
    # csv本地保存路径
    save_path = ".\\history_data"
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    # 连接数据库
    database_path = "C:\\self_vnpy\\.vntrader\\database.db"
    db_connect = sqlite3.connect(database_path)
    cursor = db_connect.cursor()

    symbol_sql = "SELECT DISTINCT symbol, exchange, interval FROM dbbardata"
    cursor.execute(symbol_sql)
    symbol_results = cursor.fetchall()

    # csv头
    header = ['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']
    for symbol_item in symbol_results:
        print(f"开始导出 {symbol_item[0]} ")

        query_sql = """
            SELECT 
                symbol, datetime, interval, volume, open_price, high_price, close_price 
            FROM dbbardata
                WHERE symbol='%s' AND interval='%s'
                ORDER BY datetime ASC
        """ % (symbol_item[0], symbol_item[2])

        cursor.execute(query_sql)
        query_results = cursor.fetchall()

        save_file_path = os.path.join(save_path, symbol_item[0] + ".csv")
        with open(save_file_path, mode="wt", encoding="utf8", newline="") as f:
            writer = csv.writer(f)
            writer.writerows([header])
            writer.writerows(query_results)

    cursor.close()
    db_connect.close()

    print(f"导出完成，共导出表格{len(symbol_results)}个，耗时：{time.time() - start_time}s")
