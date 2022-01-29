"""
figures built for crypto prices.
"""
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.dates as mdates
import dateutil
import datetime
from dateutil.relativedelta import relativedelta

from surfingcrypto.ts import TS
import surfingcrypto.reporting.plotting as scplot
from surfingcrypto.reporting.trend_line import trend_line


##GLOBAL VARIABLES (?!?) TO SET PLOT STYLE
plt.style.use("dark_background")
mpl.rcParams["font.size"] = 5


class CoinFigure:
    """
    This objects are complex matplotlib figures predisponed to fit OHLC + TA indicators data.

    Note:
        There are two styles implemented at the moment: `default` that is candlestick + volume
        and `ta` that is candlecticks, volume + technical indicators.

    Arguments:
        ts (:class:`surfingcrypto.ts.TS`) : `surfingcrypto.ts.TS`object
        kind (str) : string representing desired style of plot.
        trendlines (bool) : UNDER DEVELOPEMENT! - plot also trendlines calculated with `src.trend_line` class.
        graphstart (str) : date string in d-m-Y format (or relative from today eg. 1 month: `1m`,3 month: `3m`) from which to start the graph.
        \*\*kwargs : Keyword arguments to `TS` module.


    """

    def __init__(
        self,
        ts,
        kind="default",
        trendlines=False,
        graphstart="1-1-2021",
        *args,
        **kwargs,
    ):

        self.ts = ts

        if graphstart.lower() == "3m":
            self.graphstart = datetime.date.today() + relativedelta(months=-3)
        elif graphstart.lower() == "6m":
            self.graphstart = datetime.date.today() + relativedelta(months=-6)
        elif graphstart.lower() == "1m":
            self.graphstart = datetime.date.today() + relativedelta(months=-1)
        elif graphstart.lower() == "1y":
            self.graphstart = datetime.date.today() + relativedelta(years=-1)
        else:
            self.graphstart = dateutil.parser.parse(graphstart)

        if kind == "default":
            self.default_plot()
        elif kind == "ta":
            self.ta_plot(trendlines=trendlines)
        else:
            raise ValueError("Kind not implemented.")

    def save(self, path):
        """
        save fig to specified path.

        Arguments:
            path (str) : path to output file.
        """
        return self.f.savefig(path)

    def center_series(self, ax, on="Close"):
        """
        centers the active series in the graph.
        
        Arguments:
            ax (:obj:`matplotlib.axes.Axes`) object is 
            on (str): `Close` or TA indicator name
        """
        xlim = mdates.num2date(ax.get_xlim())
        if on.lower() == "close":
            max = self.ts.df.loc[xlim[0] : xlim[1], "Close"].max()
            min = self.ts.df.loc[xlim[0] : xlim[1], "Close"].min()
        elif on.lower() == "macd":
            pass
        else:
            raise ValueError("Error: `on` parameter not known.")
        ax.set_ylim((min - 0.1 * min, max + 0.1 * max))

    def set_axes(self, xlims):
        """
        set all axes to the specified xlims.

        Arguments:
            xlims(:obj:`tuple`): tuple of xlims as datetime objects.
        """

        for iax in self.axes:
            iax.grid(which="major", axis="x", linewidth=0.1)
            iax.grid(which="major", axis="y", linewidth=0.05)
            iax.set_xlim(xlims)
            iax.yaxis.set_label_position("left")
            iax.yaxis.tick_left()

    def default_plot(self):
        """
        this is the default plot. It shows candlesticks and volume data.

        Arguments:
            graphstart 
        """

        self.f, self.axes = plt.subplots(
            2,
            1,
            sharex=True,
            gridspec_kw={"height_ratios": [3, 1]},
            dpi=200,
            figsize=(7.5, 7.5),
        )
        self.axes[0].set_title(
            self.ts.coin, fontsize=10, va="center", ha="center", pad=20
        )

        scplot.candlesticks(
            self.ts,
            ax=self.axes[0],
            volume=True,
            vol_ax=self.axes[1],
            style="candlesticks",
        )

        self.set_axes(
            (self.graphstart, self.ts.df.index[-1] + datetime.timedelta(days=5))
        )
        print(f"{self.ts.coin} plotted.")

    def ta_plot(self, trendlines):
        """
        this is the Technical Analysis plot.
        It shows (at current time): candlesticks, volume and 3 TA Indicators (MACD, BB bands and RSI)
        Can be easily modified to fit other and/or more indicators.
        """

        self.f, self.axes = plt.subplots(
            5,
            1,
            sharex=True,
            gridspec_kw={"height_ratios": [2, 1, 1, 1, 1]},
            dpi=200,
            figsize=(7.5, 7.5),
        )
        self.axes[0].set_title(
            self.ts.coin, fontsize=10, va="center", ha="center", pad=20
        )

        self.ts.ta_indicators()

        scplot.candlesticks(
            self.ts,
            ax=self.axes[0],
            volume=True,
            vol_ax=self.axes[1],
            style="candlesticks",
        )
        scplot.plot_moving_averages(self.ts, ax=self.axes[0])
        scplot.plot_macd(self.ts, self.axes[2], plot_lines=False)
        scplot.candlesticks(self.ts, self.axes[3], style="ohlc")
        scplot.plot_bb(self.ts, self.axes[3])
        scplot.plot_RSI(self.ts, self.axes[4])

        if trendlines:
            pass
            # trend=trend_line(self,trendln_start="01-01-2021")
            # trend.build(compute=True,
            #     method="NCUBED",
            #     window=125,
            #     save_output=False
            # )
            # trend.plot_trend(ax=self.axes[0],
            #     extend=False,
            #     nbest=2,
            #     show_min_maxs=False
            #     )

        self.set_axes(
            (self.graphstart, self.ts.df.index[-1] + datetime.timedelta(days=5))
        )

        print(f"{self.ts.coin} plotted.")
        self.center_series(self.axes[0], on="Close")

