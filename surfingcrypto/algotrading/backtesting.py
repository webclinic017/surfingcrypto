"""custom objects for backtesting"""

import backtrader as bt
import pandas as pd
import pyfolio as pf  # install with pip install git+ssh://git@github.com/giocaizzi/pyfolio.git
import matplotlib.pyplot as plt

from surfingcrypto.algotrading.model import Model


# class to define the columns we will provide
class CryptoPandasData(bt.feeds.PandasData):
    """pandas df structure"""

    cols = ["open", "high", "low", "close", "volume"] + ["predicted"]

    # create lines
    lines = tuple(cols)

    # define parameters
    params = {c: -1 for c in cols}
    params.update({"datetime": None})
    params = tuple(params.items())


class CryptoComissionInfo(bt.CommissionInfo):
    """commission info for crypto"""

    params = (
        ("commission", 1),  # percentage
        ("mult", 1.0),
        ("margin", None),
        ("commtype", None),
        ("stocklike", False),
        ("percabs", False),
        ("interest", 0.0),
        ("interest_long", False),
        ("leverage", 1.0),
        ("automargin", False),
    )

    def getsize(self, price, cash):
        """Returns fractional size for cash operation @price"""
        return self.p.leverage * (cash / price)


class CryptoSizer(bt.Sizer):
    """sizer for getting proper sizing"""

    params = (("prop", 1),)

    def _getsizing(self, comminfo, cash, data, isbuy):
        """Returns the proper sizing"""

        if isbuy:  # Buying
            target = (
                self.broker.getvalue() * self.params.prop
            )  # Ideal total value of the position
            price = data.close[0]
            size_net = target / price  # How many shares are needed to get target
            size = size_net * 0.99

            if size * price > cash:
                return 0  # Not enough money for this trade
            else:
                return size

        else:  # Selling
            return self.broker.getposition(data).size  # Clear the position


class BackTest:
    """backtest istance"""

    def __init__(
        self,
        m: Model,
        start: str,
        verbose=False,
    ):
        self.model = m
        self.start = start
        self.name = self.model.feature.ts.coin
        self.verbose = verbose

        # benchmark buy&hold returns
        self.benchmark_returns = self._get_benchmark_returns()

        # backtrader data
        data = self._fmt_dataframe()

        # instantiate Cerebro, add strategy, data, initial cash, commission and pyfolio for performance analysis
        self.cerebro = bt.Cerebro(stdstats=True, cheat_on_open=False)
        # cerebro.broker = bt.brokers.BackBroker(slip_open=True)  # consider market slippage
        self.cerebro.broker.setcash(1250.0)  #  cash value
        self.cerebro.adddata(CryptoPandasData(dataname=data), name=self.name)
        self.cerebro.addsizer(CryptoSizer)
        self.cerebro.addstrategy(MLStrategy, verbose=self.verbose)  # strategy
        self.cerebro.broker.addcommissioninfo(
            CryptoComissionInfo(),
        )  # fractional prices and commissions scheme
        self.cerebro.addanalyzer(bt.analyzers.PyFolio, _name="pyfolio")  # analyizer

    def _fmt_dataframe(self) -> pd.DataFrame:
        prices = self.model.feature.df[["Open", "High", "Low", "Close", "Volume"]]
        prices = prices.loc[self.start :]
        prices.rename(
            columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            },
            inplace=True,
        )

        backtestdata = self.model.estimated.join(prices, how="right").dropna()

        return backtestdata

    def run(self):
        # run the backtest
        self.start_value = self.cerebro.broker.getvalue()
        if self.verbose:
            print("Starting Portfolio Value: %.2f" % self.start_value)
        self.backtest_result = self.cerebro.run()
        self.returns = self._get_backtest_returns()
        self.end_value = self.cerebro.broker.getvalue()
        if self.verbose:
            print("Final Portfolio Value: %.2f" % self.end_value)

    def _get_benchmark_returns(self) -> pd.Series:
        # get benchmark returns # just buy and hold
        benchmark_rets = self.model.feature.model_df.loc[self.start :, "returns"]
        benchmark_rets.name = "Buy&Hold"
        return benchmark_rets

    def _get_backtest_returns(self) -> pd.Series:
        pyfoliozer = self.backtest_result[0].analyzers.getbyname("pyfolio")
        (
            returns,
            positions,
            transactions,
            gross_lev,
        ) = pyfoliozer.get_pf_items()
        returns.name = "Backtest returns"

        return returns

    def performance_stats(self) -> pd.Series:
        # Extract inputs for pyfolio
        performance = pf.timeseries.perf_stats(self.returns)
        performance = performance.append(
            pd.Series([self.end_value], index=["End Value"])
        )

        return performance

    def print_log(self):
        if len(self.backtest_result) == 1:
            print(self.backtest_result[0].log_text)
        else:
            raise NotImplementedError


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
                    f"Open: {self.data_open[0]:.3f}, Close: {self.data_close[0]:.3f}"
                )
                cost = order.created.size * order.created.price
                self.log(
                    "    "
                    f"BUY CREATED --- Size: {order.created.size:.3f}, "
                    f"Price: {order.created.price:.3f}, Cost: {cost:.3f}"
                )
            if order.issell():
                self.log(
                    f"Open: {self.data_open[0]:.3f}, Close: {self.data_close[0]:.3f}"
                )
                cost = order.created.size * order.created.price
                self.log(
                    "    "
                    f"SELL CREATED --- Size: {order.created.size:.3f}, "
                    f"Price: {order.created.price:.3f}, Cost: {cost:.3f}"
                )
            return

        # report executed order
        if order.status in [order.Completed]:
            if order.isbuy():
                cost = order.executed.size * order.executed.price
                self.log(
                    "    "
                    f"BUY EXECUTED --- Size: {order.executed.size:.3f}, "
                    f"Price: {order.executed.price:.3f}, "
                    f"Cost: {cost:.3f}, Commission: {order.executed.comm:.3f}"
                )
                self.price = order.executed.price
                self.comm = order.executed.comm
            else:
                cost = order.executed.size * order.executed.price
                self.log(
                    "    "
                    f"SELL EXECUTED --- Size: {order.executed.size:.3f}, "
                    f"Price: {order.executed.price:.3f}, "
                    f"Cost: {cost:.3f}, Commission: {order.executed.comm:.3f}"
                )
        elif order.status in [order.Canceled]:
            self.log("    " f"Order Canceled")
        elif order.status in [order.Rejected]:
            self.log("    " f"Order Rejected")
        elif order.status in [order.Margin]:
            self.log("    " f"Order Failed: Margin")

        # set no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log(
            "        "
            f" -> OPERATION RESULT --- Gross: {trade.pnl:.3f}, Net: {trade.pnlcomm:.3f}"
        )

    def next(self):
        # Check if we are in the market
        if not self.position:
            if self.data_predicted > 0:
                self.buy()
        else:
            # Already in the market ... we might sell
            if self.data_predicted < 0:
                self.sell()
