# -*- utf-8 -*-
import time


def run_time(func):
    """计算函数运行时间"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f'Function:{func.__name__} runtime is {end_time-start_time}s')
        return result
    return wrapper


@run_time
def test_func():
    print('Hello, wrapper.')
    time.sleep(2)


if __name__ == '__main__':
    test_func()
