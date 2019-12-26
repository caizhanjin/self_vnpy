# -*- coding:utf-8 -*-
import unittest

from tools.database import DatabaseSqlite


class TestDatabase(unittest.TestCase):

    def setUp(self):
        self.DatabaseSqlite = DatabaseSqlite()

    def tearDown(self):
        self.DatabaseSqlite.close()

    def test_query_future_data(self):
        # result = self.DatabaseSqlite.query_future_data(symbol='rb2001')
        result = self.DatabaseSqlite.query_future(symbol='rb2001', begin_date='2019-11-11', end_date='2019-11-11')

        print(len(result))

        return


if __name__ == "__main__":
    unittest.main()
