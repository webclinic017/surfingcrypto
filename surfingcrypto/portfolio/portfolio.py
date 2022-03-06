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
        if portfolio_type.lower() == "coinbase":
            self.coinbase = MyCoinbase(active_accounts=False, **kwargs)
            self.coinbase.get_history()
            self._standardize()
            self._init_log()
        else:
            raise NotImplementedError

    def total_fees(self):
        """
        total fees paid by user for th
        """
        return self.coinbase.history.df["total_fee"].sum()

    def total_by_type(self):
        """
        total EUR by transaction type.

        Return:
            :obj:`pandas.DataFrame`
        """
        return self.coinbase.history.df.groupby("type")[
            ["native_amount"]
        ].sum()

    def live_value(self, client, amount, currency):
        """
        gets live value of given currency and amount.

        Arguments:
            client (:obj:`surfingcrypto.coinbase.CB.client`) : client
                to coinbase account.
            amount (float): amount of currency
            currency (str): symbol of currency
        """
        change = client.get_spot_price(currency_pair=currency + "-EUR")
        change = float(change["amount"])
        return amount * change

    def portfolio_value(self, client):
        """
        gets live value of portfolio.

        Arguments:
            client (:obj:`surfingcrypto.coinbase.CB.client`) : client to
                coinbase account.
        """
        balance = (
            self.coinbase.history.df[
                self.coinbase.history.df["type"].isin(
                    ["buy", "sell", "trade", "send"]
                )
            ]
            .groupby("symbol")[["amount"]]
            .sum()
        )
        balance = balance.loc[
            ~(balance.round(10) == 0.0).all(axis=1)
        ].reset_index()
        balance["live_value"] = balance.apply(
            lambda x: self.live_value(client, x["amount"], x["symbol"]), axis=1
        )
        print(balance)
        print(
            "Total portfolio balance: "
            + "{:.2f}".format(balance["live_value"].sum())
            + " EUR"
        )

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
            self.std_df["type"].isin(["buy", "sell", "trade"])
        ]
        # set trades as buy or sell transactions
        m = (self.std_df["type"] == "trade") & (self.std_df["amount"] < 0)
        self.std_df.loc[m, "type"] = "sell"
        m = (self.std_df["type"] == "trade") & (self.std_df["amount"] > 0)
        self.std_df.loc[m, "type"] = "buy"
        # make all floats positive
        self.std_df["amount"] = self.std_df["amount"].abs()
        self.std_df["native_amount"] = self.std_df["native_amount"].abs()

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
        if len(self.std_df) != len(self.coinbase.history.df):
            n = len(self.coinbase.history.df) - len(self.std_df)
            print(
                f"Warning! There are {n} transactions"\
                "that were EXCLUDED in std_df."
                )
        if not self.coinbase.history.executed_without_errors():
            print(self.coinbase.history)
