"""custom objects for backtraading"""

import backtrader as bt
import pandas as pd

import pyfolio as pf  # install with pip install git+ssh://git@github.com/giocaizzi/pyfolio.git

from surfingcrypto.algotrading.strategies import MLStrategy


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
    """ commission info for crypto"""
    params = (
        ("commission", 1), # percentage
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

class BackTest:
    """backtest istance"""
    def __init__(self, data: pd.DataFrame, name: str, verbose=False,):
        self.verbose=verbose
        self.name=name
        # instantiate Cerebro, add strategy, data, initial cash, commission and pyfolio for performance analysis
        self.cerebro = bt.Cerebro(stdstats=True, cheat_on_open=False)
        # cerebro.broker = bt.brokers.BackBroker(slip_open=True)  # consider market slippage
        self.cerebro.broker.setcash(1250.0)  #  cash value
        self.cerebro.adddata(CryptoPandasData(dataname=data), name=self.name)
        self.cerebro.addsizer(CryptoSizer)
        self.cerebro.addstrategy(MLStrategy,verbose=self.verbose)  # strategy
        self.cerebro.broker.addcommissioninfo(
            CryptoComissionInfo(),
        )  # fractional prices and commissions scheme
        self.cerebro.addanalyzer(
            bt.analyzers.PyFolio, _name="pyfolio"
        )  # analyizer

    def run(self):
        # run the backtest
        self.start_value = self.cerebro.broker.getvalue()
        self.backtest_result = self.cerebro.run()
        self.end_value = self.cerebro.broker.getvalue()
        if self.verbose:
            print("Starting Portfolio Value: %.2f" % self.start_value)
            print("Final Portfolio Value: %.2f" % self.end_value)

    def performance_stats(self) -> pd.Series:
        # Extract inputs for pyfolio
        strat = self.backtest_result[0]
        pyfoliozer = strat.analyzers.getbyname("pyfolio")
        (
            self.returns,
            positions,
            transactions,
            gross_lev,
        ) = pyfoliozer.get_pf_items()
        self.returns.name = "Strategy"
        return pf.timeseries.perf_stats(self.returns)

    def print_log(self):
        if len(self.backtest_result)==1:
            print(self.backtest_result[0].log_text)
        else:
            raise NotImplementedError

class CryptoSizer(bt.Sizer):
    """sizer for getting proper sizing"""
    params = (('prop', 1),)

    def _getsizing(self, comminfo, cash, data, isbuy):
        """Returns the proper sizing"""

        if isbuy:    # Buying
            target = self.broker.getvalue() * self.params.prop    # Ideal total value of the position
            price = data.close[0]
            size_net = target / price    # How many shares are needed to get target
            size = size_net * 0.99

            if size * price > cash:
                return 0    # Not enough money for this trade
            else:
                return size

        else:    # Selling
            return self.broker.getposition(data).size    # Clear the position
