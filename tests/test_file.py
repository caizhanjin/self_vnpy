# -*- coding:utf-8 -*-
import unittest

from tools.file import TDXData


class TestTDXData(unittest.TestCase):

    def setUp(self):
        self.TDXData = TDXData()

    # def tearDown(self):

    def test_clean_csv_single(self):
        csv_file_path = 'C:\\self_vnpy\\research\\csv\\28#MAL9.csv'
        save_file_path = 'C:\\self_vnpy\\research\\csv\\test\\28#MAL9.csv'

        self.TDXData.clean_csv_single(csv_file_path, save_file_path)

    @classmethod
    def test_clean_csv_file(cls):
        file_path = "C:\\self_vnpy\\history_data\\99_source"
        save_path = "C:\\self_vnpy\\history_data\\99_deal"

        TDXData.clean_csv_file(file_path, save_path)


if __name__ == "__main__":
    # unittest.main()
    TestTDXData.test_clean_csv_file()
