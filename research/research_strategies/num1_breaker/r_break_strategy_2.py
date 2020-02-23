from datetime import time
from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager
)


class RBreakStrategy(CtaTemplate):
    """
    基于break，尝试了一下简化，效果并没有原版好，
    该策略还没完全完善
    """
    author = "jin"

    fixed_size = 1

    atr_ma_len = 3
    atr_break_per = 0.5
    atr_stop_per = 0.3
    sma_len = 20

    pivot = 0       # 枢纽轴
    buy_break = 0   # 突破买入价
    sell_break = 0  # 突破卖出价

    day_high = 0
    day_open = 0
    day_close = 0
    day_low = 0

    is_new_today = False
    atr_ma = 0
    long_stop_price = 0
    short_stop_price = 0

    parameters = ["atr_ma_len", "atr_break_per", "atr_stop_per", "fixed_size"]
    variables = ["buy_break", "sell_break", 'atr_ma']

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        super(RBreakStrategy, self).__init__(
            cta_engine, strategy_name, vt_symbol, setting
        )

        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()
        self.am_day = ArrayManager(30)

    def on_init(self):
        self.write_log("策略初始化")
        self.load_bar(30)

    def on_start(self):
        self.write_log("策略启动")

    def on_stop(self):
        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        self.cancel_all()

        am = self.am
        am.update_bar(bar)

        # New Day 有夜盘的写法
        if bar.datetime.hour > 15 and not self.is_new_today:
            self.is_new_today = True
            if self.day_open:
                am_day = self.am_day
                am_day.update_bar(BarData(
                    open_price=self.day_open,
                    high_price=self.day_high,
                    low_price=self.day_low,
                    close_price=self.day_close,
                    volume=bar.volume,
                    gateway_name=bar.gateway_name,
                    symbol=bar.symbol,
                    exchange=bar.exchange,
                    datetime=bar.datetime,
                ))

                # 每天开盘计算好成交价
                if am_day.inited:
                    self.atr_ma = self.am_day.atr(self.atr_ma_len)

                    self.pivot = (self.day_open + self.day_high + self.day_close) / 3

                    self.buy_break = max((self.pivot + self.atr_ma * self.atr_break_per), self.day_high)
                    self.sell_break = min((self.pivot - self.atr_ma * self.atr_break_per), self.day_low)

            self.day_open = bar.open_price
            self.day_high = bar.high_price
            self.day_close = bar.close_price
            self.day_low = bar.low_price

        # Today
        else:
            self.day_high = max(self.day_high, bar.high_price)
            self.day_low = min(self.day_low, bar.low_price)
            self.day_close = bar.close_price

        # 收盘前初始化变量
        if time(hour=14, minute=59) <= bar.datetime.time() <= time(hour=15, minute=00):
            self.is_new_today = False

        if not am.inited:
            return
        if not self.buy_break:
            return

        if time(hour=14, minute=55) < bar.datetime.time() <= time(hour=15, minute=00):
            if self.pos > 0:
                self.sell(bar.close_price * 0.99, abs(self.pos))
            elif self.pos < 0:
                self.cover(bar.close_price * 1.01, abs(self.pos))
        else:
            if self.pos == 0:
                # 过滤：下午13点后不交易
                is_fit_trade = True
                if 14 <= bar.datetime.hour <= 15:
                    is_fit_trade = False
                # 过滤：每天只交易一次
                # if self.is_long_traded or self.is_short_traded:
                #     is_fit_trade = False
                # 过滤：趋势，20日均线
                trend_am = self.am_day.sma(self.sma_len, True)
                trend = 1 if trend_am[-1] > trend_am[-2] else -1

                if is_fit_trade:
                    if trend == 1:
                        self.buy(self.buy_break, self.fixed_size, stop=True)
                    elif trend == -1:
                        self.short(self.sell_break, self.fixed_size, stop=True)

            elif self.pos > 0:
                self.long_stop_price = self.day_high - self.atr_ma * self.atr_stop_per
                self.sell(self.long_stop_price, abs(self.pos), stop=True)

            elif self.pos < 0:
                self.short_stop_price = self.day_low + self.atr_ma * self.atr_stop_per
                self.cover(self.short_stop_price, abs(self.pos), stop=True)

        self.put_event()

    def on_order(self, order: OrderData):
        pass

    def on_trade(self, trade: TradeData):
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        pass
