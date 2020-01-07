# -*- coding:utf8 -*-
import csv
import os


class TDXData(object):
    """通达信数据源处理"""

    @classmethod
    def clean_csv_file(cls, file_path, save_path):
        """批量处理文件夹下csv文件"""
        for file_name in os.listdir(file_path):
            if ".csv" in file_name:
                csv_file_path = os.path.join(file_path, file_name)
                save_file_path = os.path.join(save_path, file_name)
                cls.clean_csv_single(csv_file_path, save_file_path)

    @staticmethod
    def clean_csv_single(csv_file_path, save_file_path):
        """处理下载csv文件"""
        # save_file_path = os.path.join(save_path, os.path.basename(csv_file_path))
        header = ['datetime', 'open', 'high', 'low', 'close', 'volume']
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

