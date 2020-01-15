# -*- coding:utf-8 -*-
# vnpy同步两个数据库表
import sqlite3
import time


if __name__ == "__main__":
    start_time = time.time()

    database_path = "C:\\self_vnpy\\.vntrader\\database.db"

    # 原始/数据源数据库
    read_db_connect = sqlite3.connect(database_path)
    read_cursor = read_db_connect.cursor()
    # 本地/同步数据库
    write_db_connect = sqlite3.connect(database_path)
    write_cursor = write_db_connect.cursor()

    write_cursor.execute("select max(id) from dbbardata_copy1")
    id_result = write_cursor.fetchone()
    max_id = 0 if not id_result else id_result

    query_sql = """
    select 
        symbol, exchange, datetime, interval, volume, open_interest, open_price, high_price, low_price, close_price
    from dbbardata 
        where id > %s 
        order by id
    """ % max_id

    print(query_sql)

    read_cursor.execute(query_sql)
    results = read_cursor.fetchall()

    print("开始导入数据...")

    for row in results:
        insert_sql = """
        insert into 
            dbbardata_copy1(symbol, exchange, datetime, interval, volume, open_interest, open_price, high_price, low_price, close_price)
            values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')
        """ % row
        write_cursor.execute(insert_sql)
    write_db_connect.commit()

    read_cursor.close()
    write_cursor.close()
    read_db_connect.close()
    write_db_connect.close()

    print(f"数据导入成功，导入行数{len(results)}，耗时{time.time()-start_time}s")

