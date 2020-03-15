# -*- coding: utf-8 -*-
"""
@author : caizhanjin
@date   : 2019-11-28
@detail : tools for strategy
"""


class SampleBarData(object):
    """简单记录bar数据使用"""
    symbol: str
    open_price: float = 0
    high_price: float = 0
    low_price: float = 0
    close_price: float = 0
    volume: float = 0
    open_interest: float = 0
