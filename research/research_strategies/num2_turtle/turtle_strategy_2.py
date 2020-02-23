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


class TurtleStrategy(CtaTemplate):
    author = "zhanjin"

    entry_length = 3
    exit_length = 10
    atr_length = 20
    stop_multiplier = 1
    fixed_size = 1
    trend_length = 10

    entry_up = 0
    entry_down = 0
    exit_up = 0
    exit_down = 0
    atr_value = 0
    stop_diff_value = 0

    long_entry = 0
    short_entry = 0
    long_stop = 0
    short_stop = 0

    is_new_today = True
    is_trade_today = False

    parameters = ["entry_window", "exit_window", "atr_window", "fixed_size"]
    variables = ["entry_up", "entry_down", "exit_up", "exit_down", "atr_value"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super(TurtleStrategy, self).__init__(
            cta_engine, strategy_name, vt_symbol, setting
        )

        self.bg = BarGenerator(self.on_bar)
        self.am_day = ArrayManager(max(self.entry_length, self.atr_length, ) + 5)
        self.bar_today = SampleBarData()

    def on_init(self):
        self.write_log("策略初始化")
        self.load_bar(max(self.entry_length, self.atr_length) + 6)

    def on_start(self):
        self.write_log("策略启动")

    def on_stop(self):
        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        self.cancel_all()

        is_last_min = time(hour=14, minute=58) <= bar.datetime.time() <= time(hour=15, minute=00)
        if self.is_new_today and not is_last_min:
            self.is_new_today = False
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
            if is_last_min:
                self.is_trade_today = False
                self.is_new_today = True

        if not self.am_day.inited:
            return

        self.exit_up, self.exit_down = self.am_day.donchian(self.exit_length)

        if not self.pos:
            # 过滤：趋势，20日均线
            trend_sma = self.am_day.sma(self.trend_length, True)
            trend = 1 if trend_sma[-1] > trend_sma[-2] else -1

            self.long_entry = 0
            self.short_entry = 0
            self.long_stop = 0
            self.short_stop = 0
            self.stop_diff_value = 0

            self.entry_up, self.entry_down = self.am_day.donchian(self.entry_length)
            self.atr_value = self.am_day.atr(self.atr_length)

            self.buy(self.entry_up, self.fixed_size, stop=True)
            self.short(self.entry_down, self.fixed_size, stop=True)

        elif self.pos > 0:
            """
            止损逻辑：
                >> 止损价没达成本价，吊灯止损
                >> 止损价达或超成本价，使用成本价、出场价较大者作为止损价
            """
            if self.long_stop < self.long_entry:
                self.long_stop = max(self.long_stop,
                                     self.bar_today.high_price - self.stop_diff_value)

            else:
                # self.long_stop = max(self.long_stop, self.exit_down)
                self.long_stop = max(self.long_stop,
                                     self.bar_today.high_price - self.stop_diff_value * 2)

            self.sell(self.long_stop, abs(self.pos), stop=True)

        elif self.pos < 0:
            if self.short_stop > self.short_entry:
                self.short_stop = min(self.short_stop,
                                      self.bar_today.low_price + self.stop_diff_value)
            else:
                # self.short_stop = min(self.short_stop, self.exit_up)
                self.short_stop = min(self.short_stop,
                                      self.bar_today.low_price + self.stop_diff_value * 2)

            self.cover(self.short_stop, abs(self.pos), stop=True)

        self.put_event()

    def on_trade(self, trade: TradeData):
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
