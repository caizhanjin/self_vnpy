# -*- coding: utf-8 -*-
"""
@author : caizhanjin
@date   : 2019-11-28
@detail : tools for strategy
"""
from vnpy.trader.constant import Interval


class SampleBarData(object):
    """简单记录bar数据使用"""
    symbol: str
    open_price: float = 0
    high_price: float = 0
    low_price: float = 0
    close_price: float = 0
    volume: float = 0
    open_interest: float = 0


def get_cycle_list():
    cycle_list = {
        1: {"cycle": 2, "interval": Interval.MINUTE},
        2: {"cycle": 3, "interval": Interval.MINUTE},
        3: {"cycle": 5, "interval": Interval.MINUTE},
        4: {"cycle": 6, "interval": Interval.MINUTE},
        5: {"cycle": 10, "interval": Interval.MINUTE},
        6: {"cycle": 15, "interval": Interval.MINUTE},
        7: {"cycle": 20, "interval": Interval.MINUTE},
        8: {"cycle": 30, "interval": Interval.MINUTE},

        9: {"cycle": 1, "interval": Interval.HOUR},
        10: {"cycle": 2, "interval": Interval.HOUR},
        11: {"cycle": 3, "interval": Interval.HOUR},
        12: {"cycle": 4, "interval": Interval.HOUR},
        13: {"cycle": 5, "interval": Interval.HOUR},
        14: {"cycle": 6, "interval": Interval.HOUR},
        15: {"cycle": 7, "interval": Interval.HOUR},
        16: {"cycle": 8, "interval": Interval.HOUR},
    }

    return cycle_list
