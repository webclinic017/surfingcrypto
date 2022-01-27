"""
time-series objects for cryptocurrencies.
"""
from numpy import sign
import pandas as pd
import mplfinance as mplf
import matplotlib.pyplot as plt
import pandas_ta as ta
import os

#warning di mplfinance per too many data in candlestick plot
import warnings
warnings.filterwarnings("ignore")

class TS:
    """
    This is an time-series oriented crypto price data object.

    Note:
        Data can be downloaded calling ```surfingcrypto.scraper.Scraper``` object.

    Args:
    	configuration (:obj:`surfingcrypto.config.config`): configuration object
        coin (str): string representing the crypto coin of choice, eg. BTC,ETH

    Attributes:
        df (:obj:`pandas.DataFrame`): dataframe with datetime index of ohlc data. Could store also TA indicators if these are computed invoking the relative method.
        ta_params (dict): dictionary containing TA parametrization
    """

    def __init__(self,configuration,coin=None):

        self.config=configuration
        
        if coin is None:
            raise ValueError("Must specify coin.")
        else:
            self.coin=coin
            self.build_ts()

    def build_ts(self):
        """
        reads the data from data stored locally in `data/ts/` and saved in .csv format.
        """
        if os.path.isfile(self.config.data_folder+"/ts/"+self.coin+".csv"):
            self.df=pd.read_csv(self.config.data_folder+"/ts/"+self.coin+".csv")
            self.df["Date"]=pd.to_datetime(self.df["Date"],utc=True)
            self.df.set_index("Date",inplace=True)
        else:
            raise FileNotFoundError(f"{self.coin}.csv not found.")

    def percentage_diff(self,window=7):
        """
        Percentage difference given a window size.

        Arguments:
            window (int): number of days used to computer percentage difference.
        """
        return (self.df.Close[-1]-self.df.Close[-window-1])/(self.df.Close[-window-1])*100

    def report_percentage_diff(self,windows=[1,3,7,14,60]):
        """
        Produces verbose and pretty report on latest price difference from a given list of windows.

        Arguments:
            windows (:obj:`list` of :obj:`int`): list of windows to compute percentage difference.

        """
        s=f"**{self.coin}**\n"
        for window in windows:
            s=s+f"- {window}d: "+"{:.2f}".format(self.percentage_diff(window))+" %\n"
        return s
    
#TA INDICATORS SAVED TO DF       
    def ta_indicators(self):
        """
        computes the selected TA indicators and appends them to df attribute.
        """
        self.parametrization()

        self.df.ta.sma(length=self.ta_params["sma"]["slow"],append=True)
        self.df.ta.sma(length=self.ta_params["sma"]["fast"],append=True)
        self.df.ta.macd(
            window_slow=self.ta_params["macd"]["slow"],
            window_fast=self.ta_params["macd"]["fast"],
            window_sign=self.ta_params["macd"]["signal"],
            append=True
            )
        self.df.ta.bbands(
            length=self.ta_params["bbands"]["length"],
            std=self.ta_params["bbands"]["std"],
            append=True)
        self.df.ta.rsi(
            timeperiod=self.ta_params["rsi"]["timeperiod"],
            append=True)

    def parametrization(self):
        """
        sets the default parameters if not specified in config.json file.
        """
        #TA parameters
        if self.config.config["coins"][self.coin]=="":
            #default if empty
            self.ta_params={
                "sma":{"fast":12,"slow":26},
                "macd":{"fast":12,"slow":26,"signal":9},
                "bbands":{"length":20,"std":2},
                "rsi":{"timeperiod":14}
            }
        elif isinstance(self.config["coins"][self.coin],dict):
            self.ta_params=self.config["coins"][self.coin]
        else:
            raise ValueError ("Must provide TA parametrization in the correct format.")

### PLOTTING METHODS

    def candlesticks(self,ax,volume=False,vol_ax=None,style="candlesticks"):
        """
        plotting candlesticks into a matplotlib.axes.Axes object.

        Args:
            ax (:class:`matplotlib.axes.Axes`) : matplotlib ax to plot candlesticks into.
            volume (bool,optional): plot volume histogram data into a another ax specified with `vol_ax`
            vol_ax (:class:`matplotlib.axes.Axes`) : matplotlib ax to plot volume histogram into.
            style (str,optional): style of plotting candlesticks, `candlesticks` is default but `ohlc` style is used in BB bands plotting.
        """
        if style=="candlesticks":
            if volume is False:
                mplf.plot(self.df,
                    ax=ax,
                    type='candle',
                    style='yahoo',
                    show_nontrading=True,loc="lower left"
                    )
            elif volume and vol_ax is None:
                raise ValueError("Must specify ax for volume plot.")
            else: 
                mplf.plot(self.df,ax=ax,volume=vol_ax,type='candle',style='yahoo',show_nontrading=True)
        elif style=="ohlc":
            mplf.plot(self.df,
                ax=ax,
                type="ohlc",
                style="mike",
                show_nontrading=True
            )
        else:
            raise ValueError("Must specify style.")       
        return

    def plot_moving_averages(self,ax,windows=None):
        """
        Plot two simple moving averages.
        Default windows are 12 and 26 days. Can be customized by using lists of window-color pairs.

        Args:
            windows (obj:`list` of obj:`int`,optional): list of windows to compute MA 
        """

        colors=["yellow","orange"]
        if windows is None:
            windows=[
                self.ta_params["sma"]["fast"],
                self.ta_params["sma"]["slow"]
            ]
        for window,color in zip(windows,colors):
            ax.plot(self.df["SMA_"+str(window)],linestyle="-",color=color,label="SMA"+str(window),alpha=0.3,linewidth=1)
            l=ax.legend(loc="upper left",prop={"size":3})
            l.get_frame().set_linewidth(0.5)

    def plot_macd(self,ax,plot_lines=True):
        """
        plot macd indicator into a matplotlib.axes.Axes object.     


        Args:
            ax (:class:`matplotlib.axes.Axes`) : matplotlib ax to plot MACD into.
            plot_lines (bool): plot lines in addition to histogram.

        """

        fast=str(self.ta_params["macd"]["fast"])
        slow=str(self.ta_params["macd"]["slow"])
        sign=str(self.ta_params["macd"]["signal"])

        prices=self.df["Open"]
        macd=self.df["MACD_"+fast+"_"+slow+"_"+sign]
        signal=self.df[f"MACDs_"+fast+"_"+slow+"_"+sign]
        hist=self.df[f"MACDh_"+fast+"_"+slow+"_"+sign]

        if plot_lines:
            #ax1.plot(prices)
            ax.plot(macd, color = 'grey', linewidth = 1.5, label = "MACD("+fast+"-"+slow)
            ax.plot(signal, color = 'skyblue', linewidth = 1.5, label = "SIGNAL("+sign+")")

        for i in range(len(prices)):
            if str(hist[i])[0] == '-':
                ax.bar(prices.index[i], hist[i], color = '#ef5350')
            else:
                ax.bar(prices.index[i], hist[i], color = '#26a69a')

        if plot_lines:
            l=ax.legend(loc = 'lower left',prop={"size":3})
            l.get_frame().set_linewidth(0.5)

        ax.annotate("MACD("+fast+"-"+slow+")-S("+sign+")",xy=(0.99,0.1),xycoords="axes fraction",ha="right")
        ax.set_ylabel("MACD")

    
    def plot_bb(self,iax):
        """
        plot Bollinger bands indicator into a matplotlib.axes.Axes object.

        Args:
            ax (:class:`matplotlib.axes.Axes`) : matplotlib ax to plot BB bands into.
        """
        length=str(self.ta_params["bbands"]["length"])
        std="{0:.1f}".format(self.ta_params["bbands"]["std"])


        iax.plot(self.df['BBM_'+length+"_"+std], label=f'MA{length}-STD{str(std)}',color='dodgerblue', alpha=0.35) #middle band
        iax.plot(self.df['BBU_'+length+"_"+std], label='_', color='greenyellow', alpha=0.35) #Upper band
        iax.plot(self.df['BBL_'+length+"_"+std], label='_', color='coral', alpha=0.35) #lower band
        iax.fill_between(self.df.index, self.df['BBL_'+length+"_"+std], self.df['BBU_'+length+"_"+std], alpha=0.1)
        l=iax.legend(loc='lower left',prop={"size":3})
        l.get_frame().set_linewidth(0.5)
        iax.set_ylabel("B Bands")

    def plot_RSI(self,iax):
        """
        plot RSI indicator into a matplotlib.axes.Axes object.

        Args:
            ax (:class:`matplotlib.axes.Axes`) : matplotlib ax to plot RSI into.
        """
        timeperiod=str(self.ta_params["rsi"]["timeperiod"])
        iax.plot(self.df["RSI_"+timeperiod],color="magenta",alpha=0.5)
        iax.set_ylim([0,100])
        iax.set_ylabel("RSI")
        iax.axhspan(30, 70, facecolor="white", alpha=0.1)
        iax.axhline(30,color="coral",linewidth=0.5, alpha=0.3)
        iax.axhline(70,color="greenyellow",linewidth=0.5, alpha=0.3)