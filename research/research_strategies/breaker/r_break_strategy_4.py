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
    基于空中花园策略
    试图简化，r_break 策略，
    19/12/22 表现没有r_break好，对比差异，可能原因：1小百分比止损，2不断调高或低开仓位置(防止横盘)，3小周期趋势过滤
    """
    author = "zhanjin"

    fixed_size = 1
    donchian_window = 30
    trailing_long = 0.4
    trailing_short = 0.4

    art_length = 3  # art取值
    open_break_percent = -0.1  # 开盘突破百分比
    trade_break_percent = 0.1  # 突破art百分比
    lowest_percent = 0.1  # 下影线控制

    long_or_short = 0  # 多空方向，1多 0不交易 -1空
    art_value = 0
    long_break_price = 0
    short_break_price = 0
    long_lowest_price = 0
    short_lowest_price = 0

    intra_trade_high = 0
    intra_trade_low = 0

    tend_high = 0
    tend_low = 0

    is_new_today = False

    parameters = ["fixed_size", "donchian_window"]
    variables = ["long_break_price", "short_break_price"]

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

        self.am.update_bar(bar)

        is_exit_time = time(hour=14, minute=55) <= bar.datetime.time() <= time(hour=15, minute=00)
        if not self.is_new_today and (bar.datetime.hour > 20 or bar.datetime.hour < 10):
            self.is_new_today = True
            # 新的一天，更新昨天数据到 am_day
            self.long_or_short = 0
            if self.bar_today.open_price:
                self.am_day.update_bar(self.bar_today)
                if self.am_day.inited:
                    self.art_value = self.am_day.atr(self.art_length)
                    if bar.open_price > (self.bar_today.close_price + self.art_value * self.open_break_percent):
                        self.long_or_short = 1
                    elif bar.open_price < (self.bar_today.close_price - self.art_value * self.open_break_percent):
                        self.long_or_short = -1
                    self.long_break_price = bar.open_price + self.art_value * self.trade_break_percent
                    self.short_break_price = bar.open_price - self.art_value * self.trade_break_percent
                    self.long_lowest_price = bar.open_price - self.art_value * self.lowest_percent
                    self.short_lowest_price = bar.open_price + self.art_value * self.lowest_percent

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

        if not self.am.inited:
            return
        if not self.am_day.inited:
            return
        if not self.art_value:
            return

        # 过滤：分钟级别趋势，入场
        # self.tend_high, self.tend_low = am.donchian(self.donchian_window)

        if not is_exit_time:
            if self.pos == 0:
                # 过滤：下午14点后不交易
                is_fit_trade = True
                if 14 <= bar.datetime.hour <= 15:
                    is_fit_trade = False
                # 过滤：趋势，20日均线
                trend_am = self.am_day.sma(20, True)
                trend = 1 if trend_am[-1] > trend_am[-2] else -1

                if is_fit_trade:
                    if self.long_or_short == 1 and \
                            self.bar_today.close_price > self.long_break_price and \
                            self.bar_today.low_price > self.long_lowest_price:
                        long_entry = max(self.long_break_price, self.bar_today.high_price)
                        # self.buy(long_entry, self.fixed_size, stop=True)
                        if trend == 1:
                            self.buy(long_entry, self.fixed_size, stop=True)

                    elif self.long_or_short == -1 and \
                            self.bar_today.close_price < self.short_break_price and \
                            self.bar_today.high_price < self.short_lowest_price:
                        short_entry = min(self.short_break_price, self.bar_today.low_price)
                        # self.short(short_entry, self.fixed_size, stop=True)
                        if trend == -1:
                            self.short(short_entry, self.fixed_size, stop=True)

            elif self.pos > 0:
                long_stop = self.bar_today.high_price * (1 - self.trailing_long / 100)
                self.sell(long_stop, abs(self.pos), stop=True)

            elif self.pos < 0:
                short_stop = self.bar_today.low_price * (1 + self.trailing_short / 100)
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
