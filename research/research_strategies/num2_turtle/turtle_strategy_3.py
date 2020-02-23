from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    Direction,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
    SampleBarData,
)
from datetime import time


class DonAnData(object):
    """唐奇安通道 data"""
    entry_up: float = 0
    entry_down: float = 0

    exit_up: float = 0
    exit_down: float = 0

    # 趋势 1上升 0震荡 -1下降
    trend_status: int = 0

    def __init__(self, entry_length=20, exit_length=10):
        self.entry_length = entry_length
        self.exit_length = exit_length

    def update_bar_data(self, bar_data):
        self.entry_up, self.entry_down = bar_data.donchian(self.entry_length)
        self.exit_up, self.exit_down = bar_data.donchian(self.exit_length)

    def update_close_price(self, close_price):
        if close_price > self.entry_up:
            self.trend_status = 1
        elif close_price < self.entry_down:
            self.trend_status = -1

        if (self.trend_status == 1 and close_price < self.exit_down) or \
           (self.trend_status == -1 and close_price > self.exit_up):
            self.trend_status = 0


class TurtleStrategy(CtaTemplate):
    """海龟+日内 >> 增强版：
    效果一般般，没有break好
    """
    author = "zhanjin"

    trend_entry_length = 5
    trend_exit_length = 5
    trade_length = 5
    atr_length = 10
    stop_multiplier = 0.5
    fixed_size = 1

    trend_status = 0  # 1上升 0震荡 -1下降
    trade_up = 0
    trade_down = 0

    atr_value = 0
    stop_diff_value = 0

    long_entry = 0
    short_entry = 0
    long_stop = 0
    short_stop = 0

    is_new_today = True
    is_trade_today = False

    parameters = ["fixed_size"]
    variables = ["atr_value"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        super(TurtleStrategy, self).__init__(
            cta_engine, strategy_name, vt_symbol, setting
        )

        self.bg = BarGenerator(self.on_bar)
        self.am_day = ArrayManager(max(self.trend_entry_length, self.atr_length, ) + 5)
        self.bar_today = SampleBarData()
        self.trend_obj = DonAnData(self.trend_entry_length, self.trend_exit_length)

    def on_init(self):
        self.write_log("策略初始化")
        self.load_bar(max(self.trend_entry_length, self.atr_length) + 6)

    def on_start(self):
        self.write_log("策略启动")

    def on_stop(self):
        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        self.cancel_all()

        is_exit_time = time(hour=14, minute=55) <= bar.datetime.time() <= time(hour=15, minute=00)
        if not self.is_new_today and bar.datetime.hour > 15:
            # 开盘更新数据
            self.is_new_today = True
            if self.bar_today.open_price:
                self.am_day.update_bar(self.bar_today)

            self.bar_today.open_price = bar.open_price
            self.bar_today.high_price = bar.high_price
            self.bar_today.low_price = bar.low_price
            self.bar_today.close_price = bar.close_price

            # 更新唐奇安日趋势数据
            self.trend_obj.update_bar_data(self.am_day)
        else:
            self.bar_today.high_price = max(bar.high_price, self.bar_today.high_price)
            self.bar_today.low_price = min(bar.low_price, self.bar_today.low_price)
            self.bar_today.close_price = bar.close_price
            # 收盘初始化状态
            if is_exit_time:
                self.is_trade_today = True
                self.is_new_today = False

        if not self.am_day.inited:
            return

        self.trend_obj.update_close_price(bar.close_price)
        self.trend_status = self.trend_obj.trend_status

        if not is_exit_time:
            if self.pos == 0:
                # 过滤：下午14点后不交易
                is_fit_trade = True
                if 14 <= bar.datetime.hour <= 15:
                    is_fit_trade = False
                # 过滤：每天只交易一次
                # if self.is_long_traded or self.is_short_traded:
                #     is_fit_trade = False

                if self.trend_status != 0 and is_fit_trade:
                    self.long_entry = 0
                    self.short_entry = 0
                    self.long_stop = 0
                    self.short_stop = 0
                    self.stop_diff_value = 0

                    self.trade_up, self.trade_down = self.am_day.donchian(self.trade_length)

                    if self.trend_status == 1:
                        self.buy(self.trade_up, self.fixed_size, stop=True)
                    elif self.trend_status == -1:
                        self.short(self.trade_down, self.fixed_size, stop=True)

            elif self.pos > 0:
                self.long_stop = max(self.long_stop,
                                     self.bar_today.high_price - self.stop_diff_value)

                self.sell(self.long_stop, abs(self.pos), stop=True)

            elif self.pos < 0:
                self.short_stop = min(self.short_stop,
                                      self.bar_today.low_price + self.stop_diff_value)

                self.cover(self.short_stop, abs(self.pos), stop=True)

        else:
            if self.pos > 0:
                self.sell(bar.close_price * 0.99, abs(self.pos))
            elif self.pos < 0:
                self.cover(bar.close_price * 1.01, abs(self.pos))

        self.put_event()

    def on_trade(self, trade: TradeData):
        self.atr_value = self.am_day.atr(self.atr_length)
        self.stop_diff_value = self.atr_value * self.stop_multiplier

        if trade.direction == Direction.LONG:
            self.long_entry = trade.price
            self.long_stop = self.long_entry - self.stop_diff_value

        else:
            self.short_entry = trade.price
            self.short_stop = self.short_entry + self.stop_diff_value

        self.put_event()

    def on_order(self, order: OrderData):
        pass

    def on_stop_order(self, stop_order: StopOrder):
        pass
