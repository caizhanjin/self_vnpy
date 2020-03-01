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
    Direction,
    Offset,
)
from datetime import time


class BreakStrategy(CtaTemplate):
    """
    """
    author = "zhanjin"

    fixed_size = 1

    tend_length = 20
    long_length = 10
    short_length = 1
    fixed_stop_rate = 0.2
    move_stop_rate = 0.4

    long_up = 0
    long_down = 0
    short_up = 0
    short_down = 0
    long_stop = 0
    short_stop = 0
    trade_days = 0
    is_trade_today = False

    is_new_today = False

    parameters = ["fixed_size", "long_length", "short_length", "stop_rate"]
    variables = ["trade_days", "long_stop", "short_stop"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        super(BreakStrategy, self).__init__(
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

            self.long_up, self.long_down = self.am_day.donchian(self.long_length)
            if self.short_length == 1:
                self.short_up, self.short_down = self.bar_today.high_price, self.bar_today.low_price
            else:
                self.short_up, self.short_down = self.am_day.donchian(self.short_length)
            self.is_trade_today = False
            if self.trade_days > 0:
                self.trade_days += 1

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
                # 过滤：下午14点后不交易
                is_fit_trade = True
                if 14 <= bar.datetime.hour <= 15:
                    is_fit_trade = False
                # 过滤：趋势，20日均线
                trend_am = self.am_day.sma(self.tend_length, True)
                trend = 1 if trend_am[-1] > trend_am[-2] else -1

                if is_fit_trade and not self.is_trade_today:
                    if trend == 1:
                        self.buy(self.long_up, self.fixed_size, stop=True)
                    elif trend == -1:
                        self.short(self.long_down, self.fixed_size, stop=True)

            elif self.pos > 0:
                self.long_stop = max(self.long_stop,
                                     self.bar_today.high_price * (1 - self.move_stop_rate),
                                     self.short_down)
                self.sell(self.long_stop, abs(self.pos), stop=True)

            elif self.pos < 0:
                self.short_stop = min(self.short_stop,
                                      self.bar_today.high_price * (1 + self.move_stop_rate),
                                      self.short_up)
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
        # 开多
        if trade.direction == Direction.LONG and trade.offset == Offset.OPEN:
            self.is_trade_today = True
            self.trade_days = 1
            self.long_stop = trade.price * (1 - self.fixed_stop_rate)

        # 开空
        elif trade.direction == Direction.SHORT and trade.offset == Offset.OPEN:
            self.is_trade_today = True
            self.trade_days = 1
            self.short_stop = trade.price * (1 + self.fixed_stop_rate)

        # 平仓
        else:
            self.trade_days = 0

        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        pass
