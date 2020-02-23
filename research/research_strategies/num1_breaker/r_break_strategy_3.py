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
from datetime import time


class RBreakStrategy(CtaTemplate):
    """论坛原版突破策略：
    简单添加了过滤器优化，比较忠实于原版
    """
    author = "zhanjin"

    setup_coef = 0.25
    break_coef = 0.2
    enter_coef_1 = 1.07
    enter_coef_2 = 0.07
    fixed_size = 1
    donchian_window = 30

    trailing_long = 0.4
    trailing_short = 0.4
    multiplier = 1

    buy_break = 0   # 突破买入价
    sell_setup = 0  # 观察卖出价
    sell_enter = 0  # 反转卖出价
    buy_enter = 0   # 反转买入价
    buy_setup = 0   # 观察买入价
    sell_break = 0  # 突破卖出价

    intra_trade_high = 0
    intra_trade_low = 0

    tend_high = 0
    tend_low = 0

    is_new_today = False

    parameters = ["setup_coef", "break_coef", "enter_coef_1", "enter_coef_2", "fixed_size", "donchian_window"]
    variables = ["buy_break", "sell_setup", "sell_enter", "buy_enter", "buy_setup", "sell_break"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        super(RBreakStrategy, self).__init__(
            cta_engine, strategy_name, vt_symbol, setting
        )

        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()
        self.bars = []

        self.am_day = ArrayManager(25)
        self.bar_today = SampleBarData()

    def on_init(self):
        self.write_log("策略初始化")
        self.load_bar(10)

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
        if not self.is_new_today and (bar.datetime.hour > 15 or bar.datetime.hour < 10):
            self.is_new_today = True
            # 新的一天，更新昨天数据到 am_day
            if self.bar_today.open_price:
                self.am_day.update_bar(self.bar_today)

                # 更新交易价格（每天只需计算一次）
                self.buy_setup = self.bar_today.low_price - \
                    self.setup_coef * (self.bar_today.high_price - self.bar_today.close_price)  # 观察买入价
                self.sell_setup = self.bar_today.high_price + \
                    self.setup_coef * (self.bar_today.close_price - self.bar_today.low_price)  # 观察卖出价

                self.buy_enter = (self.enter_coef_1 / 2) * (self.bar_today.high_price + self.bar_today.low_price) - \
                    self.enter_coef_2 * self.bar_today.high_price  # 反转买入价
                self.sell_enter = (self.enter_coef_1 / 2) * (self.bar_today.high_price + self.bar_today.low_price) - \
                    self.enter_coef_2 * self.bar_today.low_price  # 反转卖出价

                self.buy_break = self.buy_setup + self.break_coef * (self.sell_setup - self.buy_setup)  # 突破买入价
                self.sell_break = self.sell_setup - self.break_coef * (self.sell_setup - self.buy_setup)  # 突破卖出价

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
        if not self.sell_setup:
            return

        # 过滤：分钟级别趋势，入场
        self.tend_high, self.tend_low = am.donchian(self.donchian_window)

        if not is_exit_time:
            if self.pos == 0:
                self.intra_trade_low = bar.low_price
                self.intra_trade_high = bar.high_price

                # 过滤：下午14点后不交易
                is_fit_trade = True
                if 14 <= bar.datetime.hour <= 15:
                    is_fit_trade = False
                # 过滤：趋势，20日均线
                trend_am = self.am_day.sma(20, True)
                trend = 1 if trend_am[-1] > trend_am[-2] else -1

                if is_fit_trade:
                    if self.tend_high > self.sell_setup:
                        long_entry = max(self.buy_break, self.bar_today.high_price)
                        if trend == 1:
                            self.buy(long_entry, self.fixed_size, stop=True)
                        # self.short(self.sell_enter, self.multiplier * self.fixed_size, stop=True)
                        # if trend == 1:
                        #     self.buy(long_entry, self.fixed_size, stop=True)
                        # else:
                        #     self.short(self.sell_enter, self.multiplier * self.fixed_size, stop=True)

                    elif self.tend_low < self.buy_setup:
                        short_entry = min(self.sell_break, self.bar_today.low_price)
                        # self.buy(self.buy_enter, self.multiplier * self.fixed_size, stop=True)
                        if trend == -1:
                            self.short(short_entry, self.fixed_size, stop=True)
                        # if trend == -1:
                        #     self.short(short_entry, self.fixed_size, stop=True)
                        # else:
                        #     self.buy(self.buy_enter, self.multiplier * self.fixed_size, stop=True)

            elif self.pos > 0:
                self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
                long_stop = self.intra_trade_high * (1 - self.trailing_long / 100)
                self.sell(long_stop, abs(self.pos), stop=True)

            elif self.pos < 0:
                self.intra_trade_low = min(self.intra_trade_low, bar.low_price)
                short_stop = self.intra_trade_low * (1 + self.trailing_short / 100)
                self.cover(short_stop, abs(self.pos), stop=True)

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
