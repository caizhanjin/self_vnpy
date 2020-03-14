"""
@Author : caizhanjin
@Time : 2020-3-14
@detail : 文件操作方法
"""
import os


def list_current_paths(path, include=None):
    """查找当前文件夹下文件"""
    list_paths = []
    for item in os.listdir(path):
        if not include or (include and include in item):
            list_paths.append(os.path.join(path, item))

    return list_paths


def list_all_paths(path, include=None):
    """查找文件夹内所有内容"""
    list_paths = []
    for item in os.listdir(path):
        file_path = os.path.join(path, item)
        if os.path.isdir(file_path):
            list_paths.extend(list_all_paths(file_path, include))
        else:
            if not include or (include and include in item):
                list_paths.append(file_path)

    return list_paths


if __name__ == "__main__":
    # print(os.walk())
    file = "C:\\self_vnpy\\history_data\\tq"
    print(list_all_paths("C:\\self_vnpy", ".py"))


