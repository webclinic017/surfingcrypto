"""
plotting methods.
"""
import mplfinance as mplf
import matplotlib.pyplot as plt

# warning di mplfinance per too many data in candlestick plot
import warnings

warnings.filterwarnings("ignore")


def candlesticks(ts, ax, volume=False, vol_ax=None, style="candlesticks"):
    """
    plotting candlesticks into a matplotlib.axes.Axes object.

    Args:
        ts (:class:`surfingcrypto.ts.TS`) : `surfingcrypto.ts.TS` object
        ax (:class:`matplotlib.axes.Axes`) : matplotlib ax to plot candlesticks into.
        volume (bool,optional): plot volume histogram data into a another ax specified with `vol_ax`
        vol_ax (:class:`matplotlib.axes.Axes`) : matplotlib ax to plot volume histogram into.
        style (str,optional): style of plotting candlesticks, `candlesticks` is default but `ohlc` style is used in BB bands plotting.
    """
    if style == "candlesticks":
        if volume is False:
            mplf.plot(
                ts.df,
                ax=ax,
                type="candle",
                style="yahoo",
                show_nontrading=True,
                loc="lower left",
            )
        elif volume and vol_ax is None:
            raise ValueError("Must specify ax for volume plot.")
        else:
            mplf.plot(
                ts.df,
                ax=ax,
                volume=vol_ax,
                type="candle",
                style="yahoo",
                show_nontrading=True,
            )
    elif style == "ohlc":
        mplf.plot(
            ts.df, ax=ax, type="ohlc", style="mike", show_nontrading=True
        )
    else:
        raise ValueError("Must specify style.")
    return


def plot_moving_averages(ts, ax, windows=None):
    """
    Plot two simple moving averages.
    Default windows are 12 and 26 days. Can be customized by using lists of window-color pairs.

    Args:
        ts (:class:`surfingcrypto.ts.TS`) : `surfingcrypto.ts.TS` object
        windows (obj:`list` of obj:`int`,optional): list of windows to compute MA 
    """

    colors = ["yellow", "orange"]
    if windows is None:
        windows = [ts.ta_params["sma"]["fast"], ts.ta_params["sma"]["slow"]]
    for window, color in zip(windows, colors):
        ax.plot(
            ts.df["SMA_" + str(window)],
            linestyle="-",
            color=color,
            label="SMA" + str(window),
            alpha=0.3,
            linewidth=1,
        )
        l = ax.legend(loc="upper left", prop={"size": 3})
        l.get_frame().set_linewidth(0.5)


def plot_macd(ts, ax, plot_lines=True):
    """
    plot macd indicator into a matplotlib.axes.Axes object.     


    Args:
        ts (:class:`surfingcrypto.ts.TS`) : `surfingcrypto.ts.TS` object
        ax (:class:`matplotlib.axes.Axes`) : matplotlib ax to plot MACD into.
        plot_lines (bool): plot lines in addition to histogram.

    """

    fast = str(ts.ta_params["macd"]["fast"])
    slow = str(ts.ta_params["macd"]["slow"])
    sign = str(ts.ta_params["macd"]["signal"])

    prices = ts.df["Open"]
    macd = ts.df["MACD_" + fast + "_" + slow + "_" + sign]
    signal = ts.df[f"MACDs_" + fast + "_" + slow + "_" + sign]
    hist = ts.df[f"MACDh_" + fast + "_" + slow + "_" + sign]

    if plot_lines:
        # ax1.plot(prices)
        ax.plot(
            macd,
            color="grey",
            linewidth=1.5,
            label="MACD(" + fast + "-" + slow,
        )
        ax.plot(
            signal,
            color="skyblue",
            linewidth=1.5,
            label="SIGNAL(" + sign + ")",
        )

    for i in range(len(prices)):
        if str(hist[i])[0] == "-":
            ax.bar(prices.index[i], hist[i], color="#ef5350")
        else:
            ax.bar(prices.index[i], hist[i], color="#26a69a")

    if plot_lines:
        l = ax.legend(loc="lower left", prop={"size": 3})
        l.get_frame().set_linewidth(0.5)

    ax.annotate(
        "MACD(" + fast + "-" + slow + ")-S(" + sign + ")",
        xy=(0.99, 0.1),
        xycoords="axes fraction",
        ha="right",
    )
    ax.set_ylabel("MACD")


def plot_bb(ts, iax):
    """
    plot Bollinger bands indicator into a matplotlib.axes.Axes object.

    Args:
        ts (:class:`surfingcrypto.ts.TS`) : `surfingcrypto.ts.TS` object
        ax (:class:`matplotlib.axes.Axes`) : matplotlib ax to plot BB bands into.
    """
    length = str(ts.ta_params["bbands"]["length"])
    std = "{0:.1f}".format(ts.ta_params["bbands"]["std"])

    iax.plot(
        ts.df["BBM_" + length + "_" + std],
        label=f"MA{length}-STD{str(std)}",
        color="dodgerblue",
        alpha=0.35,
    )  # middle band
    iax.plot(
        ts.df["BBU_" + length + "_" + std],
        label="_",
        color="greenyellow",
        alpha=0.35,
    )  # Upper band
    iax.plot(
        ts.df["BBL_" + length + "_" + std],
        label="_",
        color="coral",
        alpha=0.35,
    )  # lower band
    iax.fill_between(
        ts.df.index,
        ts.df["BBL_" + length + "_" + std],
        ts.df["BBU_" + length + "_" + std],
        alpha=0.1,
    )
    l = iax.legend(loc="lower left", prop={"size": 3})
    l.get_frame().set_linewidth(0.5)
    iax.set_ylabel("B Bands")


def plot_RSI(ts, iax):
    """
    plot RSI indicator into a matplotlib.axes.Axes object.

    Args:
        ts (:class:`surfingcrypto.ts.TS`) : `surfingcrypto.ts.TS` object
        ax (:class:`matplotlib.axes.Axes`) : matplotlib ax to plot RSI into.
    """
    timeperiod = str(ts.ta_params["rsi"]["timeperiod"])
    iax.plot(ts.df["RSI_" + timeperiod], color="magenta", alpha=0.5)
    iax.set_ylim([0, 100])
    iax.set_ylabel("RSI")
    iax.axhspan(30, 70, facecolor="white", alpha=0.1)
    iax.axhline(30, color="coral", linewidth=0.5, alpha=0.3)
    iax.axhline(70, color="greenyellow", linewidth=0.5, alpha=0.3)

