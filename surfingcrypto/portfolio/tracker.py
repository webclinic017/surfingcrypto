"""
portfolio value traker.
"""
import datetime
import pandas as pd
import numpy as np
import surfingcrypto
from surfingcrypto.ts import TS


# https://towardsdatascience.com/modeling-your-stock-portfolio-performance-with-python-fbba4ef2ef11


class Tracker:
    """Tracker module

    This module tracks the daily portfolio value,
    plus it features a series of portfolio statistics.

    Args:
        df (pd.DataFrame): dataframe with only "buy" or "sell" transaction.
        stocks_start (str, optional): time from which start tracking.
            Defaults to None.
        stocks_end (str, optional): time from which stop tracking.
            Defaults to None.
        benchmark (str, optional): string code of benchmark. Defaults to None.
        configuration (Config, optional): surfingcrypto configuration object.
            Defaults to None.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        stocks_start: str = None,
        stocks_end: str = None,
        benchmark: str = None,
        configuration: surfingcrypto.Config = None,
    ):
        self.configuration = configuration

        # for now, sets time limits to all transactions
        if stocks_start is None:
            self.stocks_start = pd.Timestamp(
                self.portfolio_df["Open date"].min().date(), tz="utc"
            )
        else:
            self.stocks_start = pd.Timestamp(
                datetime.datetime.strptime(stocks_start, "%d-%m-%Y"), tz="utc"
            )

        if stocks_end is None:
            self.stocks_end = pd.Timestamp(
                datetime.datetime.now(datetime.timezone.utc).date()
                + datetime.timedelta(-1),
                tz="utc",
            )
        else:
            self.stocks_end = pd.Timestamp(
                datetime.datetime.strptime(stocks_end, "%d-%m-%Y"), tz="utc"
            )

        self.benchmark = benchmark

        self.portfolio_df = self._format_df(df)
        self.closedata = self._load_data()
        self.active_positions = self._portfolio_start_balance()
        daily_snapshots = self._time_fill(self.active_positions)

        if self.benchmark is not None:
            self._set_benchmark()

        self.daily_calcs = self._per_day_portfolio_calcs(daily_snapshots)

    def _format_df(
        self, df: pd.DataFrame,
    ):
        """
        sets dataframe to required format by traker module.

        Arrguments:
            df (:obj:`pd.DataFrame`):

        Returns:
            portfolio_df (:obj:`pd.DataFrame`): dataframe
                in required format
        """
        portfolio_df = (
            df.reset_index()
            .copy()
            .rename(
                {
                    "datetime": "Open date",
                    "type": "Type",
                    "symbol": "Symbol",
                    "amount": "Qty",
                    "spot_price": "Adj cost per share",
                    "native_amount": "Adj cost",
                },
                axis=1,
            )
        )
        portfolio_df["Open date"] = pd.to_datetime(portfolio_df["Open date"])

        # drop unused columns
        portfolio_df.drop(
            ["transaction_type_id", "nat_symbol", "total", "subtotal", "total_fee"],
            axis=1,
            inplace=True,
        )

        return portfolio_df

    def _load_data(self) -> pd.DataFrame:
        """loads required data from configuration object

        Returns:
            pd.DataFrame: dataframe of close prices
                requested by transactions

        """
        self.error_log = []
        dfs = []

        symbols = self.portfolio_df.Symbol.unique()

        for symbol in symbols:
            try:
                ts = TS(configuration=self.configuration, coin=symbol)

                # considering rebrandings
                rebrandings = [
                    k for k, v in self.configuration.rebrandings.items() if v == ts.coin
                ]
                if rebrandings:
                    ts.coin = rebrandings[0]

                df = self._check_data(
                    ts.df[["Close"]].copy(),
                    pd.Timestamp(self.configuration.coinbase_req[ts.coin]["start"]),
                    pd.Timestamp(self.configuration.coinbase_req[ts.coin]["end_day"]),
                )
                df["symbol"] = symbol
                dfs.append(df)

            except Exception as e:
                self.error_log.append({"symbol": symbol, "error": e})

        closedata = pd.concat(dfs, sort=True)
        closedata.reset_index(inplace=True)
        return closedata

    def _set_benchmark(self) -> pd.DataFrame:
        """sets benchmark
        """
        ts = TS(configuration=self.configuration, coin=self.benchmark)
        self.benchmark_df = self._check_data(
            ts.df[["Close"]].copy(), self.stocks_start, self.stocks_end
        )

    def _check_data(self, df, i: pd.Timestamp, o: pd.Timestamp,) -> pd.DataFrame:
        """_summary_

        Args:
            df (_type_): _description_
            i (pd.Timestamp): _description_
            o (pd.Timestamp): _description_

        Raises:
            ValueError: _description_

        Returns:
            pd.DataFrame: _description_
        """
        if df.index.min() <= i and df.index.max() >= o:
            return df
        else:
            raise ValueError("Local data is not sufficient for purpose.")

    def _position_adjust(
        self, daily_positions: pd.DataFrame, sale: pd.Series
    ) -> pd.DataFrame:
        """adjust daily positions based for given sale

        Given a sale, it adjusts the daily_poisitions dataframe accordingly

        For every buy in buys:
        - If quantity of the oldest buy amount is ≤ the sold quantity
            subtract the amount of the buy position from the sell,
            then set the buy quantity to 0.
        - Else, subtract the sales quantity from the buy position
            subtract that same amount from the sales position

        Args:
            daily_positions (pd.DataFrame): dataframe of positions
            sale (pd.Series): pandas series of sale

        Returns:
            pd.DataFrame: _descr_
        """
        # sorting by ‘Open Date’ to subtract positions using the _fifo method
        stocks_with_sales = pd.DataFrame()
        buys = daily_positions[daily_positions["Type"] == "buy"].sort_values(
            by="Open date"
        )

        # apply correction
        for position in buys[buys["Symbol"] == sale[1]["Symbol"]].iterrows():
            if position[1]["Qty"] <= sale[1]["Qty"]:
                sale[1]["Qty"] -= position[1]["Qty"]
                position[1]["Qty"] = 0
            else:
                position[1]["Qty"] -= sale[1]["Qty"]
                sale[1]["Qty"] -= sale[1]["Qty"]
            stocks_with_sales = stocks_with_sales.append(position[1])
        return stocks_with_sales

    def _portfolio_start_balance(self) -> pd.DataFrame:
        """gets the portfolio start balance

        Gets the portfolio at the given start date,
        updated to its current value by applying
        the `poisition_adjust` method on the positions before
        the start date.

        Returns:
            pd.DataFrame: transactions adjusted to start date
        """
        # create a dataframe of all trades that happened before our start date.
        positions_before_start = self.portfolio_df[
            self.portfolio_df["Open date"] < self.stocks_start
        ]

        # future sales after the start_date since
        future_positions = self.portfolio_df[
            (self.portfolio_df["Open date"] >= self.stocks_start)
        ]

        # get sales of positions before start
        sales = (
            positions_before_start[positions_before_start["Type"] == "sell"]
            .groupby(["Symbol"])["Qty"]
            .sum()
        )
        sales = sales.reset_index()

        # poisitions that didnt change
        positions_no_change = positions_before_start[
            ~positions_before_start["Symbol"].isin(sales["Symbol"].unique())
        ]

        # loop thru the sales adjusting poisitions accordingly
        adj_positions_df = pd.DataFrame()
        for sale in sales.iterrows():
            adj_positions_df = adj_positions_df.append(
                self._position_adjust(positions_before_start, sale)
            )

        # append poisitions and future
        adj_positions_df = adj_positions_df.append(positions_no_change)
        adj_positions_df = adj_positions_df.append(future_positions)

        # filtering out any rows that _position_adjust zeroed out
        adj_positions_df = adj_positions_df[adj_positions_df["Qty"] > 0]

        return adj_positions_df

    def _fifo(self, portfolio, sales, date):

        # Our _fifo function takes your active portfolio positions, the sales
        # dataframe created in _time_fill, and the current date in the
        #  market_cal list.
        # It then filters sales to find any that have occurred on the current
        #  date, and
        # create a dataframe of positions not affected by sales:

        sales = sales[sales["Open date"].dt.date == date]
        daily_positions = portfolio[portfolio["Open date"].dt.date <= date]
        positions_no_change = daily_positions[
            ~daily_positions["Symbol"].isin(sales["Symbol"].unique())
        ]

        # bringing along all future positions
        future_positions = portfolio[portfolio["Open date"].dt.date > date]

        # We’ll then use our trusty _position_adjust function to zero-out any
        #  positions with active sales. If there were no sales for the
        # specific date,
        #   our function will simply append the positions_no_change
        # onto the empty
        #    adj_positions dataframe, leaving you with an accurate
        # daily snapshot of positions:

        adj_positions = pd.DataFrame()
        for sale in sales.iterrows():
            adj_positions = adj_positions.append(
                self._position_adjust(daily_positions, sale)
            )
        adj_positions = adj_positions.append(positions_no_change)
        adj_positions = adj_positions.append(future_positions)
        adj_positions = adj_positions[~np.isclose(adj_positions["Qty"], 0)]
        # adj_positions = adj_positions[adj_positions["Qty"] > 0]
        return adj_positions

    def _time_fill(self, active_df: pd.DataFrame) -> list:
        """adjust active positions of selected time interval

        Providing the dataframe of active positions,
        find the sales, and zero-out sales against buy positions.

        To obtain the positions for each day, this will loop for every day in
        the selected time interval.

        Args:
            active_df (pd.DataFrame) : _descr_

        Returns:
            per_day_balance (:obj:`list` of :obj:`pandas.DataFrame`):
                list of dfs
        """

        portfolio = active_df

        # calendar
        calendar = pd.date_range(
            start=self.stocks_start, end=self.stocks_end, freq="1d"
        )

        # get sales
        sales = (
            portfolio[portfolio["Type"] == "sell"]
            .groupby(["Symbol", pd.Grouper(key="Open date", freq="D")])["Qty"]
            .sum()
        )
        sales = sales.reset_index()

        # sets
        per_day_balance = []
        for date in calendar:
            if (sales["Open date"].dt.date == date).any():
                portfolio = self._fifo(portfolio, sales, date)
            daily_positions = portfolio[portfolio["Open date"].dt.date <= date]
            daily_positions = daily_positions[daily_positions["Type"] == "buy"]
            daily_positions["Date Snapshot"] = date
            per_day_balance.append(daily_positions)
        return per_day_balance

    def _per_day_portfolio_calcs(self, daily_snapshots) -> pd.DataFrame:
        """calculates daily portfolio stats.

        Calculates
            - Modified cost per share
            - Benchmark calculations
            - Returns

        Args:
            daily_snapshots (pandas.DataFrame): portfolio 
                daily snapshots

        Returns:
            pd.DataFrame: _description_
        """
        df = pd.concat(daily_snapshots)

        # modified cost per share
        df = self._modified_cost_per_share(df)

        # benchmark stats
        if self.benchmark is not None:
            df = self._benchmark_portfolio_calcs(df)

        # calc return
        df = self._calc_returns(df)

        return df

    def _modified_cost_per_share(self, portfolio: pd.DataFrame) -> pd.DataFrame:
        """
        matches prices of each asset to open date

        Args:
            portfolio (pd.DataFrame): _description_

        Returns:
            pd.DataFrame: _description_
        """
        df = pd.merge(
            portfolio,
            self.closedata,
            left_on=["Date Snapshot", "Symbol"],
            right_on=["Date", "symbol"],
            how="left",
        )
        df.rename(columns={"Close": "Symbol Adj Close"}, inplace=True)
        df["Adj cost daily"] = df["Symbol Adj Close"] * df["Qty"]
        df = df.drop(["symbol", "Date"], axis=1)
        return df

    # merge portfolio data with latest benchmark data and create several calcs
    def _benchmark_portfolio_calcs(self, portfolio: pd.DataFrame) -> pd.DataFrame:
        """make benchmark calculations

        Args:
            portfolio (pd.DataFrame): portfolio

        Returns:
            pd.DataFrame: portfolio with appended benchmark calcs
        """
        portfolio = pd.merge(
            portfolio,
            self.benchmark_df,
            left_on=["Date Snapshot"],
            right_on=["Date"],
            how="left",
        )
        portfolio.rename(columns={"Close": "Benchmark Close"}, inplace=True)

        portfolio["Open date_temp"] = portfolio["Open date"].dt.floor("d")

        portfolio = pd.merge(
            portfolio,
            self.benchmark_df,
            left_on=["Open date_temp"],
            right_on=["Date"],
            how="left",
        )
        portfolio.drop("Open date_temp", axis=1, inplace=True)
        portfolio.rename(columns={"Close": "Benchmark DayOfBuy Close"}, inplace=True)
        portfolio["Benchmark Equiv Shares"] = (
            portfolio["Adj cost"] / portfolio["Benchmark DayOfBuy Close"]
        )
        portfolio["Benchmark Adj Cost Daily"] = (
            portfolio["Benchmark Equiv Shares"] * portfolio["Benchmark Close"]
        )
        return portfolio

    def _calc_returns(self, portfolio: pd.DataFrame) -> pd.DataFrame:
        """calculate daily returns

        Args:
            portfolio (pd.DataFrame): _description_

        Returns:
            pd.DataFrame: _description_
        """
        # symbol
        portfolio["symbol Return"] = (
            portfolio["Symbol Adj Close"] / portfolio["Adj cost per share"] - 1
        )
        portfolio["Stock Gain / (Loss)"] = (
            portfolio["Adj cost daily"]
            - portfolio["Qty"] * portfolio["Adj cost per share"]
        )
        # #benchmark
        portfolio["Benchmark Return"] = (
            portfolio["Benchmark Close"] / portfolio["Benchmark DayOfBuy Close"] - 1
        )

        portfolio["Benchmark Gain / (Loss)"] = (
            portfolio["Benchmark Adj Cost Daily"] - portfolio["Adj cost"]
        )

        # #others
        # portfolio["Abs Value Compare"] = (
        #     portfolio["Adj cost daily"]
        #     - portfolio["Benchmark DayOfBuy Close"]
        # )
        # portfolio["Abs Value Return"] = (
        #     portfolio["Abs Value Compare"] /
        #   portfolio["Benchmark DayOfBuy Close"]
        # )
        # portfolio["Abs Return Compare"] = (
        #     portfolio["symbol Return"] - portfolio["Benchmark Return"]
        # )
        return portfolio

    def daily_grouped_metrics(self, cols: list, by_symbol=False,) -> pd.DataFrame:
        """_summary_

        Args:
            cols (list): _description_
            by_symbol (bool, optional): _description_. Defaults to False.

        Returns:
            pd.DataFrame: _description_
        """
        idf = self.daily_calcs.copy()
        idf["Date Snapshot"] = idf["Date Snapshot"].dt.date

        if not by_symbol:
            by = ["Date Snapshot"]
        else:
            by = ["Date Snapshot", "Symbol"]

        # group by day
        grouped_metrics = idf.groupby(by)[cols].sum().reset_index()
        grouped_metrics = pd.melt(grouped_metrics, id_vars=by, value_vars=cols,)
        grouped_metrics = (
            grouped_metrics.set_index(by + ["variable"])
            .unstack([x for x in by if x != "Date Snapshot"] + ["variable"])
            .sort_index(axis=1, level=1)
        )
        # eventually fill gaps
        grouped_metrics.reindex(
            pd.date_range(
                grouped_metrics.index.min(), grouped_metrics.index.max(), freq="D",
            )
        )
        # drop first "value" level, unrequired
        grouped_metrics.columns = grouped_metrics.columns.droplevel(0)

        return grouped_metrics

    def daily_snaphost(self, day: str) -> pd.DataFrame:
        """_summary_

        Args:
            day (str): date as string in "Y-m-d" format, or "last" to 
                get last date available

        Returns:
            pd.DataFrame: daily snapshot dataframe
        """
        if day == "last":
            day = self.daily_calcs["Date Snapshot"].unique()[-1]
        return self.daily_calcs.set_index("Date Snapshot").loc[day]
