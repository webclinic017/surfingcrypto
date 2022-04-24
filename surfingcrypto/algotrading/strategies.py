"""backtrading strategies"""

import backtrader as bt


# define backtesting strategy class
class MLStrategy(bt.Strategy):
    params = (("verbose", False),)

    def __init__(self):

        self.log_text = ""

        # keep track of open, close prices and predicted value in the series
        self.data_predicted = self.datas[0].predicted
        self.data_open = self.datas[0].open
        self.data_close = self.datas[0].close

        # keep track of pending orders/buy price/buy commission
        self.order = None
        self.price = None
        self.comm = None

    # logging function
    def log(self, txt):
        """Logging function"""
        dt = self.datas[0].datetime.date(0).isoformat()
        s = f"{dt}, {txt}"
        if self.params.verbose:
            print(s)
        self.log_text += s + "\n"

    def notify_order(self, order):
        if order.status in [order.Accepted]:
            # order already submitted/accepted - no action required
            return
        if order.status in [order.Submitted]:
            if order.isbuy():
                self.log(
                    "                 "
                    f"Open: {self.data_open[0]:.3f}, Close: {self.data_close[0]:.3f}"
                )
                cost = order.created.size * order.created.price
                self.log(
                    f"BUY CREATED --- Size: {order.created.size:.3f}, "
                    f"Price: {order.created.price:.3f}, Cost: {cost:.3f}"
                )
            if order.issell():
                self.log(
                    "                 "
                    f"Open: {self.data_open[0]:.3f}, Close: {self.data_close[0]:.3f}"
                )
                cost = order.created.size * order.created.price
                self.log(
                    f"SELL CREATED --- Size: {order.created.size:.3f}, "
                    f"Price: {order.created.price:.3f}, Cost: {cost:.3f}"
                )
            return

        # report executed order
        if order.status in [order.Completed]:
            if order.isbuy():
                cost=order.executed.size * order.executed.price
                self.log(
                    f"BUY EXECUTED --- Size: {order.executed.size:.3f}, "
                    f"Price: {order.executed.price:.3f}, "
                    f"Cost: {cost:.3f}, Commission: {order.executed.comm:.3f}"
                )
                self.price = order.executed.price
                self.comm = order.executed.comm
            else:
                cost=order.executed.size * order.executed.price
                self.log(
                    f"SELL EXECUTED --- Size: {order.executed.size:.3f}, "
                    f"Price: {order.executed.price:.3f}, "
                    f"Cost: {cost:.3f}, Commission: {order.executed.comm:.3f}"
                )
        elif order.status in [order.Canceled]:
            self.log(f"Order Canceled")
        elif order.status in [order.Rejected]:
            self.log(f"Order Rejected")
        elif order.status in [order.Margin]:
            self.log(f"Order Failed: Margin")

        # set no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log(
            f" ---> OPERATION RESULT --- Gross: {trade.pnl:.3f}, Net: {trade.pnlcomm:.3f}"
        )

    def next(self):
        # self.log("------")
        # self.log(f"Open: {self.data_open[0]}, Close: {self.data_close[0]}")
        # Check if we are in the market
        if not self.position:
            if self.data_predicted > 0:
                # calculate the max number of shares ('all-in')
                # size = int(self.broker.getcash() / self.datas[0].open) #   this is for stocks
                # size = (
                #     self.broker.getcash() / self.datas[0].open
                # )  #  fractional
                # # buy order
                # self.log(
                #     f"BUY CREATED --- Size: {size}, Cost: {self.broker.getcash():.3f}"
                # )
                # self.buy(size=size)
                self.buy()
        else:
            # Already in the market ... we might sell
            if self.data_predicted < 0:
                # sell order
                # self.log(f"SELL CREATED --- Size: {self.position.size}")
                # self.sell(size=self.position.size)
                self.sell()
