"""
figures built for crypto prices.
"""
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap, Normalize
import matplotlib.dates as mdates
from matplotlib.cm import ScalarMappable
import matplotlib.cm as cm

import pandas as pd
import copy
import calplot
import pyfolio as pf
import dateutil
import datetime
import pytz
from dateutil.relativedelta import relativedelta

from surfingcrypto.ts import TS
from surfingcrypto.portfolio import Portfolio
from surfingcrypto.algotrading.backtesting import BackTest


import surfingcrypto.reporting.plotting as scplot
from surfingcrypto.reporting.plotting import shiftedColorMap


# GLOBAL VARIABLES (?!?) TO SET PLOT STYLE
plt.style.use("dark_background")
mpl.rcParams["font.size"] = 4
plt.rcParams["figure.figsize"] = [15, 5]



class BaseFigure:
    """
    This is the base class object for all figures.

    Arguments:
        object (:class:`surfingcrypto.ts.TS` or :class:`surfingcrypto.portfolio.Portfolio` ) :
            timeseries :obj:`TS` or :obj:`Portfolio` object
        graphstart (str) : date string in d-m-Y format
            (or relative from today eg. 1 month: `1m`,3 month: `3m`) from which
            to start the graph.
    """

    def __init__(
        self, object: TS or Portfolio, graphstart="1-1-2021",
    ):

        self.object = copy.copy(object)  # copy so can be sliced for purpose

        self._set_graphstart(graphstart)
        if isinstance(object, TS):
            self.subset_ts_df(self.graphstart)

    def _set_graphstart(self, graphstart):
        if graphstart.lower() == "3m":
            self.graphstart = datetime.date.today() + relativedelta(months=-3)
        elif graphstart.lower() == "6m":
            self.graphstart = datetime.date.today() + relativedelta(months=-6)
        elif graphstart.lower() == "1m":
            self.graphstart = datetime.date.today() + relativedelta(months=-1)
        elif graphstart.lower() == "1y":
            self.graphstart = datetime.date.today() + relativedelta(years=-1)
        else:
            self.graphstart = dateutil.parser.parse(graphstart).date()
        # localize UTC
        self.graphstart = datetime.datetime.combine(
            self.graphstart, datetime.time.min
        ).replace(tzinfo=pytz.UTC)

    def subset_ts_df(self, first: str, last=None):
        """subsets inplace ts.df to selected interval

        Note:
            The `object` attribute is a TS or Portfolio object and it must have
            a df attribute.

        Args:
            first (str): first date of interval, as string in d-m-Y format
            last (_type_, optional):  last date of interval, as string in d-m-Y format.
                Defaults to None.
        """
        if last is None:
            self.object.df = self.object.df.loc[first:]
        else:
            self.object.df = self.object.df.loc[first:last]

    def save(self, path):
        """
        save fig to specified path.

        Arguments:
            path (str) : path to output file.
        """
        return self.f.savefig(path)

    def set_axes(self):
        """
        set axes look.
        set axes to the specified xlims.
        """
        if hasattr(self, "axes"):
            for iax in self.axes:
                iax.grid(which="major", axis="x", linewidth=0.1)
                iax.grid(which="major", axis="y", linewidth=0.05)
                iax.yaxis.set_label_position("left")
                iax.yaxis.tick_left()
        elif hasattr(self, "ax"):
            self.ax.grid(which="major", axis="x", linewidth=0.1)
            self.ax.grid(which="major", axis="y", linewidth=0.05)
            self.ax.yaxis.set_label_position("left")
            self.ax.yaxis.tick_left()
        else:
            raise NotImplementedError


class SimplePlot(BaseFigure):
    """
    This is the basic price plot.
    Candlesticks + volume.

    Arguments:
        ts (:class:`surfingcrypto.ts.TS`) : `surfingcrypto.ts.TS` object
        graphstart (str) : date string in d-m-Y format 
            (or relative from today eg. 1 month: `1m`,3 month: `3m`) from which to start the graph.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_plot()

    def default_plot(self):
        """
        default plotting.
        """
        # figure
        self.f, self.axes = plt.subplots(
            2, 1, sharex=True, gridspec_kw={"height_ratios": [4, 1]}, dpi=200,
        )
        # plot
        scplot.candlesticks(
            self.object,
            ax=self.axes[0],
            volume=True,
            vol_ax=self.axes[1],
            style="candlesticks",
        )
        # axes look
        self.set_axes()
        self.axes[0].set_title(
            self.object.coin, fontsize=10, va="center", ha="center", pad=20
        )
        # log
        print(f"{self.object.coin} plotted.")


class TaPlot(BaseFigure):
    """
    this is the Technical Analysis plot.
    It shows (at current time): candlesticks,
    volume and 3 TA Indicators (MACD, BB bands and RSI)
    Can be easily modified to fit other and/or more indicators.

    Arguments:
        trendlines (bool) : UNDER DEVELOPEMENT! - plot also trendlines 
            calculated with `src.trend_line` class.
        ts (:class:`surfingcrypto.ts.TS`) : `surfingcrypto.ts.TS` object
        graphstart (str) : date string in d-m-Y format 
            (or relative from today eg. 1 month: `1m`,3 month: `3m`) from
            which to start the graph.
 
    """

    def __init__(self, trendlines=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ta_plot(trendlines)

    def ta_plot(self, trendlines):
        """
        plotting function.
        """

        if not hasattr(self.object, "ta_params"):
            raise AttributeError("Object myust have `ta_params`")
        # figure
        self.f, self.axes = plt.subplots(
            5,
            1,
            sharex=True,
            gridspec_kw={"height_ratios": [2, 1, 1, 1, 1]},
            dpi=200,
            figsize=(7.5, 7.5),
        )
        # plots
        scplot.candlesticks(
            self.object,
            ax=self.axes[0],
            volume=True,
            vol_ax=self.axes[1],
            style="candlesticks",
        )
        scplot.plot_moving_averages(self.object, ax=self.axes[0])
        # scplot.plot_macd(self.object, self.axes[2], plot_lines=False)
        scplot.candlesticks(self.object, self.axes[3], style="ohlc")
        scplot.plot_bb(self.object, self.axes[3])
        scplot.plot_RSI(self.object, self.axes[4])

        # axes look
        self.set_axes()
        self.axes[0].set_title(
            self.object.coin, fontsize=10, va="center", ha="center", pad=20
        )
        # log
        print(f"{self.object.coin} plotted.")


class ATHPlot(BaseFigure):
    """
    distance from ATH plot.

    Arguments:
        ts (:class:`surfingcrypto.ts.TS`) : `surfingcrypto.ts.TS` object
        graphstart (str) : date string in d-m-Y format 
            (or relative from today eg. 1 month: `1m`,3 month: `3m`) from which to start the graph.

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.plot()

    def plot(self):
        """
        plot distance from ath points.

        Note:
            ATM it its a zoomed-in view.
        """
        # figure
        self.f, self.ax = plt.subplots(dpi=200,)
        # compute distance

        # normalizzato su tutto intervallo
        vmin = self.object.df["distance_ATH"].min()
        vmax = self.object.df["distance_ATH"].max()
        norm = Normalize(vmin=vmin, vmax=vmax)

        cmap = LinearSegmentedColormap.from_list(
            "colorbar", ["green", "orange", "red", "magenta",]
        )
        colors = [cmap(norm(x)) for x in self.object.df["distance_ATH"]]

        # points
        self.ax.scatter(
            self.object.df.index, self.object.df.Close, c=colors, s=2
        )
        # colorbar
        cmappable = ScalarMappable(norm=norm, cmap=cmap)
        self.f.colorbar(cmappable)

        # axes look
        self.set_axes()
        self.ax.set_title(
            "Distance from All Time High: " + self.object.coin,
            fontsize=10,
            va="center",
            ha="center",
            pad=20,
        )
        # log
        print(f"{self.object.coin} ATH plotted.")


class PortfolioPlot(BaseFigure):
    """
    Portfolio plots

    Arguments:
        variables (list): list of variables to plot
        by_symbol (bool, optional): _description_. Defaults to False.
        zero_line (bool, optional): _description_. Defaults to False.
        portfolio (:class:`surfingcrypto.portfolio.portfolio`) :
            `surfingcrypto.portfolio.portfolio` object
        graphstart (str) : date string in d-m-Y format
            (or relative from today eg. 1 month: `1m`,3 month: `3m`)
            from which to start the graph.

    """

    def __init__(
        self,
        variables: list,
        by_symbol=False,
        zero_line=False,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.plot(variables, by_symbol, zero_line)

    def plot(self, variables: list, by_symbol: bool, zero_line: bool):
        # figure
        self.f, self.ax = plt.subplots(dpi=200,)
        df = self.object.tracker.daily_grouped_metrics(
            variables, by_symbol=by_symbol
        )
        df = df.loc[self.graphstart.date() :].dropna(axis=1, how="all")
        df.plot(ax=self.ax)
        if zero_line:
            self.ax.axhline(0, color="r")

        self.ax.legend(bbox_to_anchor=(1, 1))


class CalendarPlot:
    """calendar plot

    This object is a good visualisation of a variable in a calendar style.

    Args:
        values (pd.Series): variable to plot
    """

    def __init__(self, values: pd.Series):
        norm = Normalize(
            vmin=values["Stock Gain / (Loss)"].min(),
            vmax=values["Stock Gain / (Loss)"].max(),
        )
        cmap = shiftedColorMap(
            LinearSegmentedColormap.from_list(
                "colorbar",
                [
                    "darkred",
                    "red",
                    "orange",
                    "grey",
                    "lightgreen",
                    "green",
                    "darkgreen",
                ],
            ),
            midpoint=norm(0),
        )
        self.calplot = calplot.calplot(
            values["Stock Gain / (Loss)"], cmap=cmap
        )


class BacktestPerformancePlot:
    def __init__(self, bt: BackTest):
        self.bt = bt
        self.plot()

    def plot(self):
        fig, ax = plt.subplots(
            nrows=2, ncols=2, figsize=(16, 9), constrained_layout=True
        )
        axes = ax.flatten()

        pf.plot_drawdown_periods(returns=self.bt.returns, ax=axes[0])
        axes[0].grid(True)
        pf.plot_rolling_returns(
            returns=self.bt.returns,
            factor_returns=self.bt.benchmark_returns,
            ax=axes[1],
            title="Strategy vs Buy&Hold",
        )
        axes[1].grid(True)
        pf.plot_drawdown_underwater(returns=self.bt.returns, ax=axes[2])
        axes[2].grid(True)
        pf.plot_rolling_sharpe(returns=self.bt.returns, ax=axes[3])
        axes[3].grid(True)

        # plt.grid(True)
        # plt.legend()
