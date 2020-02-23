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


class SingleTrendStrategy(CtaTemplate):
    """
    """
    author = "zhanjin"

    fixed_size = 1

    long_length = 30
    short_length = 10
    short_stop_rate = 1
    long_stop_rate = 4

    trend = 0  # 多空方向：1多 -1空 0未知
    stop_type = "short"  # 止损类型：short long
    trade_price = 0

    is_new_today = False

    parameters = []
    variables = []

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        super(SingleTrendStrategy, self).__init__(
            cta_engine, strategy_name, vt_symbol, setting
        )

        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()

        self.am_day = ArrayManager(self.long_length + 2)
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

        current_price = bar.close_price
        long_price = self.am_day.sma(self.long_length)
        short_price = self.am_day.sma(self.short_length)
        # trend = 1 if trend_sma[-1] > trend_sma[-2] else -1

        # 长周期判断多空
        if current_price > long_price:
            self.trend = 1
        elif current_price < long_price:
            self.trend = -1
        else:
            self.trend = 0

        if not is_exit_time:
            if self.pos == 0:
                if self.trend == 1 and current_price > short_price:
                    self.buy(current_price, self.fixed_size)
                elif self.trend == -1 and current_price < short_price:
                    self.short(current_price, self.fixed_size)

            elif self.pos > 0:
                if self.stop_type == "short":
                    if current_price < short_price:
                        self.sell(current_price, abs(self.pos))
                    else:
                        self.sell(self.trade_price * (1 - self.short_stop_rate / 100), abs(self.pos), True)
                    if current_price > self.trade_price * (1 + self.short_stop_rate / 100):
                        self.stop_type = "long"
                else:
                    stop_price = max(self.trade_price,
                                     self.trade_price * (1 - self.long_stop_rate / 100),
                                     long_price)
                    self.sell(stop_price, abs(self.pos), True)

            elif self.pos < 0:
                if self.stop_type == "short":
                    if current_price > short_price:
                        self.cover(current_price, abs(self.pos))
                    else:
                        self.cover(self.trade_price * (1 + self.short_stop_rate / 100), abs(self.pos), True)
                    if current_price < self.trade_price * (1 - self.short_stop_rate / 100):
                        self.stop_type = "long"
                else:
                    stop_price = min(self.trade_price,
                                     self.trade_price * (1 + self.long_stop_rate / 100),
                                     long_price)
                    self.cover(stop_price, abs(self.pos), True)

        self.put_event()

    def on_order(self, order: OrderData):
        pass

    def on_trade(self, trade: TradeData):
        self.stop_type = "short"
        self.trade_price = trade.price

        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        pass
