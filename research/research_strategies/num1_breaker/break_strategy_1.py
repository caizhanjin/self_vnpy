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


class BreakStrategy(CtaTemplate):
    """
    日内atr突破策略
    """
    author = "jin"

    fixed_size = 50

    atr_length = 20
    break_rate = 0.8
    move_stop_rate = 0.4
    fixed_stop_rate = 0.2
    tend_length = 20

    atr_value = 0
    sell_break = 0  # 突破卖出价
    buy_break = 0  # 突破买入价

    long_stop = 0
    short_stop = 0
    is_trade_today = False

    is_new_today = False

    parameters = ["fixed_size", "break_rate", "move_stop_rate", "fixed_stop_rate"]
    variables = []

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        super(BreakStrategy, self).__init__(
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

            # 更新交易价格
            self.is_trade_today = False
            self.atr_value = self.am_day.atr(self.atr_length)
            self.buy_break = bar.open_price + self.break_rate * self.atr_value
            self.sell_break = bar.open_price - self.break_rate * self.atr_value

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
                # trend_am = self.am_day.sma(self.tend_length, True)
                # trend = 1 if trend_am[-1] > trend_am[-2] else -1

                if is_fit_trade:
                    long_trade_price = max(self.bar_today.high_price, self.buy_break)
                    self.long_stop = long_trade_price - self.fixed_stop_rate * self.atr_value
                    self.buy(long_trade_price, self.fixed_size, stop=True)
                    # if trend == 1:
                    #     self.buy(long_entry, self.fixed_size, stop=True)

                    short_trade_price = min(self.bar_today.low_price, self.sell_break)
                    self.short_stop = short_trade_price + self.fixed_stop_rate * self.atr_value
                    self.short(short_trade_price, self.fixed_size, stop=True)
                    # if trend == -1:
                    #     self.short(short_entry, self.fixed_size, stop=True)

            elif self.pos > 0:
                long_move_stop = self.bar_today.high_price - self.move_stop_rate * self.atr_value
                self.sell(max(self.long_stop, long_move_stop), abs(self.pos), stop=True)

            elif self.pos < 0:
                short_move_stop = self.bar_today.low_price + self.move_stop_rate * self.atr_value
                self.cover(min(self.short_stop, short_move_stop), abs(self.pos), stop=True)

        else:
            if self.pos > 0:
                self.sell(bar.close_price * 0.99, abs(self.pos))
            elif self.pos < 0:
                self.cover(bar.close_price * 1.01, abs(self.pos))

        self.put_event()

    def on_order(self, order: OrderData):
        pass

    def on_trade(self, trade: TradeData):
        self.is_trade_today = True

        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        pass