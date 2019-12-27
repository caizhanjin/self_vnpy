from datetime import time
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


class RBreakStrategy(CtaTemplate):
    """
    r_break修改版：简化了逻辑，核心 突破+小止损/止盈
    第一版：
    """
    author = "zhanjin"

    break_rate = 0.4
    stop_rate = 0.4
    tend_length = 20

    fixed_size = 1

    middle_line = 0  # 中轴
    sell_break = 0  # 突破卖出价
    buy_break = 0  # 突破买入价

    long_stop = 0
    short_stop = 0

    is_new_today = False

    parameters = ["break_rate", "stop_rate", "tend_length", "fixed_size"]
    variables = ["buy_break", "sell_break", "middle_line", "long_stop", "short_stop"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        super(RBreakStrategy, self).__init__(
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
            self.is_new_today = True
            # 新的一天，更新昨天数据到 am_day
            if self.bar_today.open_price:
                self.am_day.update_bar(self.bar_today)

                # 更新交易价格（每天只需计算一次）
                self.middle_line = (self.bar_today.close_price + self.bar_today.low_price + self.bar_today.high_price) / 3
                self.buy_break = self.middle_line + self.break_rate * (self.bar_today.high_price - self.bar_today.low_price)
                self.sell_break = self.middle_line - self.break_rate * (self.bar_today.high_price - self.bar_today.low_price)

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
        if not self.middle_line:
            return

        if not is_exit_time:
            if self.pos == 0:
                self.long_stop = 0
                self.short_stop = 0

                # 过滤：下午14点后不交易
                is_fit_trade = True
                if 14 <= bar.datetime.hour <= 15:
                    is_fit_trade = False
                # 过滤：趋势，20日均线
                trend_am = self.am_day.sma(self.tend_length, True)
                trend = 1 if trend_am[-1] > trend_am[-2] else -1

                if is_fit_trade:
                    long_entry = max(self.buy_break, self.bar_today.high_price)
                    # self.buy(long_entry, self.fixed_size, stop=True)
                    if trend == 1:
                        self.buy(long_entry, self.fixed_size, stop=True)

                    short_entry = min(self.sell_break, self.bar_today.low_price)
                    # self.short(short_entry, self.fixed_size, stop=True)
                    if trend == -1:
                        self.short(short_entry, self.fixed_size, stop=True)

            elif self.pos > 0:
                self.long_stop = self.bar_today.high_price * (1 - self.stop_rate / 100)
                self.sell(self.long_stop, abs(self.pos), stop=True)

            elif self.pos < 0:
                self.short_stop = self.bar_today.low_price * (1 + self.stop_rate / 100)
                self.cover(self.short_stop, abs(self.pos), stop=True)

        else:
            if self.pos > 0:
                self.sell(bar.close_price * 0.99, abs(self.pos))
            elif self.pos < 0:
                self.cover(bar.close_price * 1.01, abs(self.pos))

        self.put_event()

    def on_order(self, order: OrderData):
        pass

    def on_trade(self, trade: TradeData):
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        pass
