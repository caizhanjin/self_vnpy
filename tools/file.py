# -*- coding:utf8 -*-
import csv
import os
import time

from configs import load_settings

SETTINGS = load_settings()


class DealCsv(object):
    """通达信数据源处理"""

    @classmethod
    def clean_csv_file(cls, file_path, save_path, csv_type="tq"):
        """批量处理文件夹下csv文件"""
        for file_name in os.listdir(file_path):
            if ".csv" in file_name:
                csv_file_path = os.path.join(file_path, file_name)
                save_file_path = os.path.join(save_path, file_name)
                if csv_type == "tq":
                    cls.clean_csv_tq(csv_file_path, save_file_path)
                elif csv_type == "tdx":
                    cls.clean_csv_tdx(csv_file_path, save_file_path)

    @staticmethod
    def clean_csv_tdx(csv_file_path, save_file_path):
        """处理下载csv文件，针对tdx数据处理"""
        header = ['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']
        csv_list = []

        with open(csv_file_path) as csv_file:
            csv_reader = csv.reader(csv_file)
            for row in csv_reader:
                csv_list.append(row)

        csv_list = csv_list[:-1]
        csv_list = [
            [
                item[0].replace('/', '-') + ' ' + item[1][:-2] + ':' + item[1][-2:],
                item[2],
                item[3],
                item[4],
                item[5],
                item[6],
            ]
            for item in csv_list
        ]

        with open(save_file_path, mode="wt", encoding="utf8", newline="") as f:
            writer = csv.writer(f)
            writer.writerows([header])
            writer.writerows(csv_list)

    @staticmethod
    def clean_csv_tq(csv_file_path, save_file_path):
        """处理下载csv文件，针对tq数据处理"""
        header = ['datetime', 'open', 'high', 'low', 'close', 'volume']
        csv_list = []

        with open(csv_file_path) as csv_file:
            csv_reader = csv.reader(csv_file)
            for row in csv_reader:
                csv_list.append(row)

        csv_list = csv_list[1:]
        csv_list = [
            [
                item[0].split(".")[0],
                item[1],
                item[2],
                item[3],
                item[4],
                item[5],
            ]
            for item in csv_list
        ]

        with open(save_file_path, mode="wt", encoding="utf8", newline="") as f:
            writer = csv.writer(f)
            writer.writerows([header])
            writer.writerows(csv_list)


if __name__ == "__main__":
    source_path = SETTINGS["tq_99_save"]
    deal_path = SETTINGS["tq_99"]

    DealCsv.clean_csv_file(source_path, deal_path)
