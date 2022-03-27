"""
portfolio objects.
"""
from surfingcrypto.portfolio import MyCoinbase


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

        # exclude fiat deposit and withdrawals AND SEND
        self.std_df = self.std_df[
            self.std_df["type"].isin(["buy", "sell", "trade", "send"])
        ]

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

        #split trades fees among the two
        for trade in self.std_df.trade_id.unique():
            if trade is not None:
                t = self.std_df[self.std_df["trade_id"] == trade]
                if len(t) == 2:
                    fee = t["native_amount"].diff()
                    self.std_df.loc[
                        (self.std_df["trade_id"] == trade), "total_fee"
                    ] = (fee[-1] / 2)

                elif len(t) > 2:
                    raise ValueError("More than 2 trades found.")
                else:
                    raise ValueError(
                        "Did not find 2 trades with matching trade_id"
                    )

    def _init_log(self):
        """
        prints log of initialization status.
        """
        print("####### PORTFOLIO ")
        print("")
        print(self.coinbase)
        print("")

        if len(self.std_df) != len(self.coinbase.history.df):
            n = len(self.coinbase.history.df) - len(self.std_df)
            print("")
            print(
                f"Warning! There are {n} transactions"
                "that were EXCLUDED in std_df."
            )
        if not self.coinbase.history.executed_without_errors():
            print("")
            print("Warning! Errors while handling transactions:")
            print(self.coinbase.history)

    def total_fees(self):
        """
        total fees paid for handled transactions.
        """
        return self.std_df.total_fee.sum()
