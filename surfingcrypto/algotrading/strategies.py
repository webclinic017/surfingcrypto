"""backtrading strategies"""

import backtrader as bt


# define backtesting strategy class
class MLStrategy(bt.Strategy):
    params = (
        ("verbose",False),
    )

    def __init__(self):

        self.log_text=""

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
        s=f"{dt}, {txt}"
        if self.params.verbose:
            print(s)
        self.log_text+=(s+"\n")

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # order already submitted/accepted - no action required
            return

        # report executed order
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f"BUY EXECUTED --- Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f},Commission: {order.executed.comm:.2f}"
                )
                self.price = order.executed.price
                self.comm = order.executed.comm
            else:
                self.log(
                    f"SELL EXECUTED --- Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f},Commission: {order.executed.comm:.2f}"
                )
        elif order.status in [order.Canceled]:
            self.log(f"Order Canceled")
        elif order.status in [order.Rejected]:
            self.log(f"Order Rejected")
        elif order.status in [order.Margin]:
            self.log(f"Order Failed: Margin --- Price: {order.created.price:.3f}")

        # set no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log(
            f"OPERATION RESULT --- Gross: {trade.pnl:.2f}, Net: {trade.pnlcomm:.2f}"
        )

    def next(self):
        # self.log("------")
        # self.log(f"Open: {self.data_open[0]}, Close: {self.data_close[0]}")
        # Check if we are in the market
        if not self.position:
            if self.data_predicted > 0:
                # calculate the max number of shares ('all-in')
                # size = int(self.broker.getcash() / self.datas[0].open) #   this is for stocks
                size = (
                    self.broker.getcash() / self.datas[0].open
                )  #  fractional
                # buy order
                self.log(
                    f"BUY CREATED --- Size: {size}, Cost: {self.broker.getcash():.2f}"
                )
                self.buy(size=size)
        else:
            # Already in the market ... we might sell
            if self.data_predicted < 0:
                # sell order
                self.log(f"SELL CREATED --- Size: {self.position.size}")
                self.sell(size=self.position.size)
