import talib

from vnpy.trader.utility import ArrayManager


class ArrayManagerExtend(ArrayManager):

    def __init__(self, size=100):
        super().__init__(size)

    def sar(self, array=False):
        """
        sar指标
        """
        result = talib.SAR(self.high, self.low)
        if array:
            return result
        return result[-1]

