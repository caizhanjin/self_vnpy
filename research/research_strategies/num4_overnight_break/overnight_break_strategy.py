from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
    SampleBarData,
)
from datetime import time


class OvernightBreakStrategy(CtaTemplate):
    """
    有点类似日内突破策略的隔夜版
    """
    author = "zhanjin"

    fixed_size = 1

    tend_length = 20
    break_length = 5
    # stop_length = 2  # 有疑问？包不包含今天
    stop_rate = 0.4

    break_up = 0
    break_down = 0
    stop_up = 0
    stop_down = 0
    long_stop = 0
    short_stop = 0

    is_new_today = False

    parameters = ["fixed_size", "tend_length", "break_length", "stop_length"]
    variables = ["break_up", "break_down", "stop_up", "stop_down"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        super(OvernightBreakStrategy, self).__init__(
            cta_engine, strategy_name, vt_symbol, setting
        )

        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()

        self.am_day = ArrayManager(self.tend_length + 2)
        self.bar_today = SampleBarData()

    def on_init(self):
        self.write_log("策略初始化")
        self.load_bar(40)

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

        is_exit_time = time(hour=14, minute=55) <= bar.datetime.time() <= time(hour=15, minute=00)
        if not self.is_new_today and (bar.datetime.hour > 20 or bar.datetime.hour < 10):
            # 更新新一天数据前更新变量
            self.break_up, self.break_down = self.am_day.donchian(self.break_length)
            self.stop_up, self.stop_down = self.bar_today.high_price, self.bar_today.low_price

            self.is_new_today = True
            # 新的一天，更新昨天数据到 am_day
            if self.bar_today.open_price:
                self.am_day.update_bar(self.bar_today)

            self.bar_today.open_price = bar.open_price
            self.bar_today.high_price = bar.high_price
            self.bar_today.low_price = bar.low_price
            self.bar_today.close_price = bar.close_price
        else:
            self.bar_today.high_price = max(bar.high_price, self.bar_today.high_price)
            self.bar_today.low_price = min(bar.low_price, self.bar_today.low_price)
            self.bar_today.close_price = bar.close_price
            # 初始化每天状态
            if is_exit_time:
                self.is_new_today = False

        if not am.inited:
            return
        if not self.am_day.inited:
            return

        if not is_exit_time:
            if self.pos == 0:
                is_fit_trade = True
                # # 过滤：下午14点后不交易
                # if 14 <= bar.datetime.hour <= 15:
                #     is_fit_trade = False
                # 过滤：趋势，20日均线
                trend_am = self.am_day.sma(self.tend_length, True)
                long_or_short = 1 if trend_am[-1] > trend_am[-2] else -1

                if is_fit_trade:
                    if long_or_short == 1:
                        self.buy(self.break_up, self.fixed_size, stop=True)

                    if long_or_short == -1:
                        self.short(self.break_down, self.fixed_size, stop=True)

            elif self.pos > 0:
                self.long_stop = self.bar_today.high_price * (1 - self.stop_rate / 100)
                self.sell(max(self.long_stop, self.stop_down), abs(self.pos), stop=True)

            elif self.pos < 0:
                self.short_stop = self.bar_today.low_price * (1 + self.stop_rate / 100)
                self.cover(min(self.short_stop, self.stop_up), abs(self.pos), stop=True)

        self.put_event()

    def on_order(self, order: OrderData):
        pass

    def on_trade(self, trade: TradeData):
        if self.pos != 0:
            if self.pos > 0:
                self.break_up = max(self.break_up, self.bar_today.high_price)
            else:
                self.break_down = min(self.break_down, self.bar_today.low_price)

        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        pass
