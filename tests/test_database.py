# -*- coding:utf-8 -*-
import unittest

from libs.db.sqlite import DatabaseSqlite


class TestDatabase(unittest.TestCase):

    def setUp(self):
        self.DatabaseSqlite = DatabaseSqlite()

    def tearDown(self):
        self.DatabaseSqlite.close()

    # def test_query_future_data(self):
    #     result = self.DatabaseSqlite.query_future(symbol='rb2001', begin_date='2019-11-11', end_date='2019-11-11')
    #     print(len(result))

    def test_import_csv_single(self):
        csv_file_path = ".\\data\\RB99_SHFE.csv"
        self.DatabaseSqlite.import_csv_single(
            csv_file_path=csv_file_path,
            symbol="RB99",
            exchange="SHFE",
            interval="1m"
        )


if __name__ == "__main__":
    unittest.main()
