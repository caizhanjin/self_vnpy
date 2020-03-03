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
    Interval,
    Direction,
    Offset,
)
from datetime import time


class BreakStrategy(CtaTemplate):
    """
    """
    author = "zhanjin"
    fixed_size = 1

    atr_length = 14
    atr_break_rate = 1
    fixed_stop_rate = 0.4

    sar_price = 0
    long_direction = ""
    short_direction = ""
    long_stop = 0
    short_stop = 0

    is_trade_today = False
    is_break_today = False
    is_new_today = False

    parameters = ["fixed_size"]
    variables = []

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        super(BreakStrategy, self).__init__(
            cta_engine, strategy_name, vt_symbol, setting
        )

        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()

        self.bg_hour = BarGenerator(self.on_bar, 1, self.on_1hour_bar, Interval.HOUR)
        self.am_hour = ArrayManager(20)

        self.bar_today = SampleBarData()
        self.am_day = ArrayManager(20)

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

        self.am.update_bar(bar)
        self.bg_hour.update_bar(bar)

        is_exit_time = time(hour=14, minute=55) <= bar.datetime.time() <= time(hour=15, minute=00)
        if not self.is_new_today and (bar.datetime.hour > 20 or bar.datetime.hour < 10):
            self.is_new_today = True
            self.is_break_today = False
            self.is_trade_today = False
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

        if not self.am.inited:
            return
        if not self.am_hour.inited:
            return
        if not self.am_day.inited:
            return

        atr_value = self.am_day.atr(self.atr_length)
        atr_today = self.bar_today.high_price - self.bar_today.low_price
        if atr_today > atr_value * self.atr_break_rate:
            self.is_break_today = True

        if not is_exit_time:
            if self.pos == 0 and self.is_break_today and not self.is_trade_today:
                if self.short_direction == "多" and self.long_direction == "多":
                    self.buy(bar.close_price, self.fixed_size)
                elif self.short_direction == "空" and self.long_direction == "空":
                    self.short(bar.close_price, self.fixed_size)

            elif self.pos > 0:
                self.sell(self.long_stop, abs(self.pos), stop=True)

            elif self.pos < 0:
                self.cover(self.short_stop, abs(self.pos), stop=True)
        else:
            if self.pos > 0:
                self.sell(bar.close_price * 0.99, abs(self.pos))
            elif self.pos < 0:
                self.cover(bar.close_price * 1.01, abs(self.pos))
        self.put_event()

    def on_1hour_bar(self, bar: BarData):
        self.am_hour.update_bar(bar)
        if not self.am_hour.inited:
            return
        if not self.am_day.inited:
            return

        short_sar_price = self.am_hour.sar()
        long_sar_price = self.am_day.sar()

        self.short_direction = "多" if bar.close_price > short_sar_price else "空"
        self.long_direction = "多" if bar.close_price > long_sar_price else "空"

        if self.short_direction == "多" and self.long_direction == "多":
            self.long_stop = max(short_sar_price, long_sar_price)
        elif self.short_direction == "空" and self.long_direction == "空":
            self.short_stop = min(short_sar_price, long_sar_price)

        self.put_event()

    def on_order(self, order: OrderData):
        pass

    def on_trade(self, trade: TradeData):
        # 开多
        if trade.direction == Direction.LONG and trade.offset == Offset.OPEN:
            self.is_trade_today = True
            # self.long_stop = trade.price * (1 - self.fixed_stop_rate)

        # 开空
        elif trade.direction == Direction.SHORT and trade.offset == Offset.OPEN:
            self.is_trade_today = True
            # self.short_stop = trade.price * (1 + self.fixed_stop_rate)

        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        pass
