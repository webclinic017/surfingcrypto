"""
portfolio value traker.
"""
import datetime
import pandas as pd
import numpy as np
import plotly.express as px
import surfingcrypto
from surfingcrypto.ts import TS

from plotly.offline import iplot

# init_notebook_mode(connected=True)


class Tracker:
    """Tracker module

    This module tracks the daily portfolio value, 
    plus it features a series of portfolio statistics.

    Args:
        df (pd.DataFrame): _description_
        stocks_start (str, optional): time from which start tracking.
            Defaults to None.
        stocks_end (str, optional): time from which stop tracking.
            Defaults to None.
        configuration (Config, optional): surfingcrypto configuration object.
            Defaults to None.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        stocks_start: str = None,
        stocks_end: str = None,
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

        self.portfolio_df = self._format_df(df)

    def _format_df(self, df: pd.DataFrame,):
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
            ["trade_id", "nat_symbol", "total", "subtotal", "total_fee"],
            axis=1,
            inplace=True,
        )

        # exclude double transactions coin-fiat for the tracking purpose.
        portfolio_df = portfolio_df[~(portfolio_df["Symbol"] == "EUR")]

        # subset dataframe
        portfolio_df = (
            portfolio_df.set_index("Open date")
            .loc[self.stocks_start : self.stocks_end, :]
            .reset_index()
        )

        return portfolio_df

    def load_data(self):
        """
        loads required data from configuration object
        """
        self.error_log = []
        dfs = []

        symbols = self.portfolio_df.Symbol.unique()

        for symbol in symbols:
            try:
                ts = TS(configuration=self.configuration, coin=symbol)
                df = ts.df.loc[self.stocks_start :, ["Close"]]
                df["symbol"] = symbol
                dfs.append(df)

            except Exception as e:
                self.error_log.append({"symbol": symbol, "error": e})

        closedata = pd.concat(dfs, sort=True)
        closedata.reset_index(inplace=True)
        return closedata

    def set_benchmark(self, benchmark:str) -> pd.DataFrame:
        """_summary_

        Args:
            benchmark (str): string code of benchmark

        Raises:
            ValueError: _description_

        Returns:
            pd.DataFrame: dataframe of benchmark
        """
        ts = TS(configuration=self.configuration, coin=benchmark)
        df = ts.df.copy()
        if (
            df.index.min() <= self.stocks_start
            and df.index.max() >= self.stocks_end
        ):
            df = df.loc[self.stocks_start : self.stocks_end, ["Close"]]
            df.reset_index(inplace=True)
            return df
        else:
            raise ValueError("Local data is not sufficient for purpose.")

    def portfolio_start_balance(self)-> pd.DataFrame:
        positions_before_start = self.portfolio_df[
            self.portfolio_df["Open date"] <= self.stocks_start
        ]
        future_positions = self.portfolio_df[
            self.portfolio_df["Open date"] >= self.stocks_start
        ]
        sales = (
            positions_before_start[positions_before_start["Type"] == "sell"]
            .groupby(["Symbol"])["Qty"]
            .sum()
        )
        sales = sales.reset_index()
        positions_no_change = positions_before_start[
            ~positions_before_start["Symbol"].isin(sales["Symbol"].unique())
        ]
        adj_positions_df = pd.DataFrame()
        for sale in sales.iterrows():
            adj_positions = position_adjust(positions_before_start, sale)
            adj_positions_df = adj_positions_df.append(adj_positions)
        adj_positions_df = adj_positions_df.append(positions_no_change)
        adj_positions_df = adj_positions_df.append(future_positions)
        adj_positions_df = adj_positions_df[adj_positions_df["Qty"] > 0]
        return adj_positions_df

    def time_fill(self)-> list:
        """_summary_

        Returns:
            per_day_balance (:obj:`list` of :obj:`pandas.DataFrame`):
                list of dfs
        """
        calendar = pd.date_range(
            start=self.stocks_start, end=self.stocks_end, freq="1d"
        )
        portfolio = self.portfolio_df
        sales = (
            portfolio[portfolio["Type"] == "sell"]
            .groupby(["Symbol", "Open date"])["Qty"]
            .sum()
        )
        sales = sales.reset_index()
        per_day_balance = []
        for date in calendar:
            if (sales["Open date"] == date).any():
                portfolio = fifo(portfolio, sales, date)
            daily_positions = portfolio[portfolio["Open date"] <= date]
            daily_positions = daily_positions[daily_positions["Type"] == "buy"]
            daily_positions["Date Snapshot"] = date
            per_day_balance.append(daily_positions)
        return per_day_balance

    def per_day_portfolio_calcs(
        self, per_day_holdings, daily_benchmark, daily_adj_close, stocks_start
    ):
        df = pd.concat(per_day_holdings, sort=True)
        mcps = modified_cost_per_share(df, daily_adj_close, stocks_start)
        bpc = benchmark_portfolio_calcs(mcps, daily_benchmark)
        pes = portfolio_end_of_year_stats(bpc, daily_adj_close)
        pss = portfolio_start_of_year_stats(pes, daily_adj_close)
        returns = calc_returns(pss)
        return returns

    def plot(self, combined_df):
        self.line_facets(combined_df, "symbol Return", "Benchmark Return")
        self.line(
            combined_df, "Stock Gain / (Loss)", "Benchmark Gain / (Loss)"
        )

    def line_facets(self, df, val_1, val_2):
        grouped_metrics = (
            df.groupby(["Symbol", "Date Snapshot"])[[val_1, val_2]]
            .sum()
            .reset_index()
        )
        grouped_metrics = pd.melt(
            grouped_metrics,
            id_vars=["Symbol", "Date Snapshot"],
            value_vars=[val_1, val_2],
        )
        fig = px.line(
            grouped_metrics,
            x="Date Snapshot",
            y="value",
            color="variable",
            facet_col="Symbol",
            facet_col_wrap=5,
        )
        iplot(fig)

    def line(self, df:pd.DataFrame, vals: list):
        """plotly lines

        Args:
            df (pd.DataFrame): dataframe to plot
            vals (list): list of columns to plot
        """
        # group by day
        grouped_metrics = (
            df.groupby([df["Date Snapshot"].dt.date])[vals].sum().reset_index()
        )
        grouped_metrics = pd.melt(
            grouped_metrics, id_vars=["Date Snapshot"], value_vars=vals,
        )
        fig = px.line(
            grouped_metrics, x="Date Snapshot", y="value", color="variable"
        )
        iplot(fig)


def position_adjust(daily_positions, sale):
    stocks_with_sales = pd.DataFrame()
    buys_before_start = daily_positions[
        daily_positions["Type"] == "buy"
    ].sort_values(by="Open date")
    for position in buys_before_start[
        buys_before_start["Symbol"] == sale[1]["Symbol"]
    ].iterrows():
        if position[1]["Qty"] <= sale[1]["Qty"]:
            sale[1]["Qty"] -= position[1]["Qty"]
            position[1]["Qty"] = 0
        else:
            position[1]["Qty"] -= sale[1]["Qty"]
            sale[1]["Qty"] -= sale[1]["Qty"]
        stocks_with_sales = stocks_with_sales.append(position[1])
    return stocks_with_sales


def fifo(daily_positions, sales, date):
    sales = sales[sales["Open date"] == date]
    daily_positions = daily_positions[daily_positions["Open date"] <= date]
    positions_no_change = daily_positions[
        ~daily_positions["Symbol"].isin(sales["Symbol"].unique())
    ]
    adj_positions = pd.DataFrame()
    for sale in sales.iterrows():
        adj_positions = adj_positions.append(
            position_adjust(daily_positions, sale)
        )
    adj_positions = adj_positions.append(positions_no_change)
    adj_positions = adj_positions[adj_positions["Qty"] > 0]
    return adj_positions


# matches prices of each asset to open date, then adjusts for  cps of dates
def modified_cost_per_share(portfolio, adj_close, start_date):
    df = pd.merge(
        portfolio,
        adj_close,
        left_on=["Date Snapshot", "Symbol"],
        right_on=["Date", "symbol"],
        how="left",
    )
    df.rename(columns={"Close": "Symbol Adj Close"}, inplace=True)
    df["Adj cost daily"] = df["Symbol Adj Close"] * df["Qty"]
    df = df.drop(["symbol", "Date"], axis=1)
    return df


# merge portfolio data with latest benchmark data and create several calcs
def benchmark_portfolio_calcs(portfolio, benchmark):
    portfolio = pd.merge(
        portfolio,
        benchmark,
        left_on=["Date Snapshot"],
        right_on=["Date"],
        how="left",
    )
    portfolio = portfolio.drop(["Date"], axis=1)
    portfolio.rename(columns={"Close": "Benchmark Close"}, inplace=True)
    benchmark_max = benchmark[benchmark["Date"] == benchmark["Date"].max()]
    portfolio["Benchmark End Date Close"] = portfolio.apply(
        lambda x: benchmark_max["Close"], axis=1
    )
    benchmark_min = benchmark[benchmark["Date"] == benchmark["Date"].min()]
    portfolio["Benchmark Start Date Close"] = portfolio.apply(
        lambda x: benchmark_min["Close"], axis=1
    )
    return portfolio


def portfolio_end_of_year_stats(portfolio, adj_close_end):
    adj_close_end = adj_close_end[
        adj_close_end["Date"] == adj_close_end["Date"].max()
    ]
    portfolio_end_data = pd.merge(
        portfolio, adj_close_end, left_on="Symbol", right_on="symbol"
    )
    portfolio_end_data.rename(
        columns={"Close": "symbol End Date Close"}, inplace=True
    )
    portfolio_end_data = portfolio_end_data.drop(["symbol", "Date"], axis=1)
    return portfolio_end_data


def portfolio_start_of_year_stats(portfolio, adj_close_start):
    adj_close_start = adj_close_start[
        adj_close_start["Date"] == adj_close_start["Date"].min()
    ]

    portfolio.Symbol = portfolio.Symbol.astype("string")
    adj_close_start.symbol = adj_close_start.symbol.astype("string")

    portfolio_start = portfolio.merge(
        adj_close_start, left_on="Symbol", right_on="symbol",
    )
    portfolio_start.rename(
        columns={"Close": "symbol Start Date Close"}, inplace=True
    )
    portfolio_start["Adj cost per share"] = np.where(
        portfolio_start["Open date"] <= portfolio_start["Date"],
        portfolio_start["symbol Start Date Close"],
        portfolio_start["Adj cost per share"],
    )
    portfolio_start["Adj cost"] = (
        portfolio_start["Adj cost per share"] * portfolio_start["Qty"]
    )
    portfolio_start = portfolio_start.drop(["symbol", "Date"], axis=1)
    portfolio_start["Equiv Benchmark Shares"] = (
        portfolio_start["Adj cost"]
        / portfolio_start["Benchmark Start Date Close"]
    )
    portfolio_start["Benchmark Start Date Cost"] = (
        portfolio_start["Equiv Benchmark Shares"]
        * portfolio_start["Benchmark Start Date Close"]
    )
    return portfolio_start


def calc_returns(portfolio):
    portfolio["Benchmark Return"] = (
        portfolio["Benchmark Close"] / portfolio["Benchmark Start Date Close"]
        - 1
    )
    portfolio["symbol Return"] = (
        portfolio["Symbol Adj Close"] / portfolio["Adj cost per share"] - 1
    )
    portfolio["symbol Share Value"] = (
        portfolio["Qty"] * portfolio["Symbol Adj Close"]
    )
    portfolio["Benchmark Share Value"] = (
        portfolio["Equiv Benchmark Shares"] * portfolio["Benchmark Close"]
    )
    portfolio["Stock Gain / (Loss)"] = (
        portfolio["symbol Share Value"] - portfolio["Adj cost"]
    )
    portfolio["Benchmark Gain / (Loss)"] = (
        portfolio["Benchmark Share Value"] - portfolio["Adj cost"]
    )
    portfolio["Abs Value Compare"] = (
        portfolio["symbol Share Value"]
        - portfolio["Benchmark Start Date Cost"]
    )
    portfolio["Abs Value Return"] = (
        portfolio["Abs Value Compare"] / portfolio["Benchmark Start Date Cost"]
    )
    portfolio["Abs. Return Compare"] = (
        portfolio["symbol Return"] - portfolio["Benchmark Return"]
    )
    return portfolio

