"""
portfolio objects.
"""
import pandas as pd
from surfingcrypto.portfolio import MyCoinbase
from surfingcrypto.portfolio.tracker import Tracker


class Portfolio:
    """
    User portfolio.

    At the moment the only supported :obj:`portfolio_type` is Coinbase, via
    the :obj:`surfingcrypto.portfolio.coinbase` submodule.

    Has methods for assessing portfolio values, grouping transactions by type,
    calculate total fees, etc.

    With `Portfolio.Analysis._standardize()` it is possible to adapt
    the `surfingcrypto.coinbase.MyCoinbase` object to a standard form
    where there are only `buy` or `sell` trades
    and the amounts are always positive.

    This standard portfolio allows to reconstruct easily the timeline
    of the portfolio value, at each given instant in time.

    Arguments:

    Attributes:
        portfolio_type (string): type of portfolio
        df (:obj:`pandas.DataFrame`): coinbase transaction
            history as from the `surfingcrypto.coinbase.MyCoinbase` output
        std_df (:obj:`pandas.DataFrame`): standardized transaction history,
             contains only `buy` or `sell`
    """

    def __init__(self, portfolio_type, **kwargs):
        self.portfolio_type = portfolio_type
        if self.portfolio_type.lower() == "coinbase":
            self.coinbase = MyCoinbase(active_accounts=False, **kwargs)
            self.coinbase.get_history()
            self.errors = []
            self._standardize()
            self._init_log()
        else:
            raise NotImplementedError

    def _standardize(self):
        """
        creates a dataframe of only `buy` and `sell` orders,
        for easier portfolio analysis.

        It calculates missing fee information of `trade` transactions.

        Note:
            At the moment does not include `send`,`deposit`
            or `withdrawal` transactions

        """
        self.std_df = self.coinbase.history.df.copy()

        # exclude fiat deposit and withdrawals
        self.std_df = self.std_df[
            self.std_df["type"].isin(["buy", "sell", "trade", "send"])
        ]

        # get unique transaction-ids for trades

        trades_trans_id = self.std_df[self.std_df["type"] == "trade"][
            "transaction_type_id"
        ].unique()

        # set trades as buy or sell transactions
        m = (self.std_df["type"] == "trade") & (self.std_df["amount"] < 0)
        self.std_df.loc[m, "type"] = "sell"
        m = (self.std_df["type"] == "trade") & (self.std_df["amount"] > 0)
        self.std_df.loc[m, "type"] = "buy"

        # set sends as buy and sells
        m = (self.std_df["type"] == "send") & (self.std_df["amount"] < 0)
        self.std_df.loc[m, "type"] = "sell"
        m = (self.std_df["type"] == "send") & (self.std_df["amount"] > 0)
        self.std_df.loc[m, "type"] = "buy"

        # make all amounts positive
        self.std_df["amount"] = self.std_df["amount"].abs()
        self.std_df["native_amount"] = self.std_df["native_amount"].abs()

        # exclude double transactions coin-fiat for the tracking purpose.
        self.std_df = self.std_df[~(self.std_df["symbol"] == "EUR")]

        # split trades fees among the two
        for trade in trades_trans_id:
            if trade is not None:
                t = self.std_df[self.std_df["transaction_type_id"] == trade]
                if len(t) == 2:
                    fee = t["native_amount"].diff()
                    self.std_df.loc[
                        (self.std_df["transaction_type_id"] == trade),
                        "total_fee",
                    ] = (fee[-1] / 2)

                else:
                    self.errors.append(
                        {
                            "descr": "Can't split trade because not found 2 trades with matching transaction_type_id",
                            "t": trade,
                        }
                    )

    def total_fees(self) -> float:
        """total fees paid

        Returns:
            float: total fees paid for handled transactions.

        """
        return self.std_df.total_fee.sum()

    def total_investment(self) -> pd.DataFrame:
        """get total investment

        Returns:
            pd.DataFrame: dataframe resuming investment
        """
        investment = (
            self.coinbase.history.df[
                self.coinbase.history.df.type.isin(
                    ["fiat_deposit", "fiat_withdrawal"]
                )
            ]
            .groupby("type")[["amount"]]
            .sum()
        )
        return investment

    def start_tracker(self, stocks_start="1-1-2021", benchmark=None):
        self.tracker = Tracker(
            self.std_df,
            stocks_start=stocks_start,
            benchmark=benchmark,
            configuration=self.coinbase.configuration,
        )

    def live_snapshot(self)-> pd.DataFrame:
        last=self.tracker.daily_snaphost("last")
        
        def update_price(series):
            string=f'{series["Symbol"]}-EUR'
            return float(self.coinbase.client.get_spot_price(currency_pair = string)["amount"])

        last["Symbol Adj Close"]=last.apply(update_price,axis=1)

        # for the moment does not consider benchmark
        to_drop=[x for x in last.columns if "benchmark" in x.lower()]
        last.drop(to_drop,axis=1,inplace=True)

        # update calcs to live price
        last["Adj cost daily"]=last["Symbol Adj Close"]*last["Qty"]
        last["symbol Return"] = (
            last["Symbol Adj Close"] / last["Adj cost per share"] - 1
        )
        last["Stock Gain / (Loss)"] = (
            last["Adj cost daily"]
            - last["Qty"] * last["Adj cost per share"]
        )

        return last

    def _init_log(self):
        """
        prints log of initialization status.
        """
        print("### PORTFOLIO ")
        print(self.coinbase)
        if len(self.std_df) != len(self.coinbase.history.df):
            n = len(self.coinbase.history.df) - len(self.std_df)
            print(
                f"Warning! There are {n} transactions"
                "that were EXCLUDED in std_df."
            )
        if not self.coinbase.history.executed_without_errors():
            print("Warning! Errors while handling transactions:")
            print(self.coinbase.history)
