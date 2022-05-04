"""
time-series objects for cryptocurrencies.
"""
import pandas as pd
import os
import pandas_ta as ta


class TS:
    """
    This is an time-series oriented crypto price data object.

    Note:
        Data can be downloaded calling ```surfingcrypto.scraper.Scraper```
        object.

    Arguments:
        configuration (:obj:`surfingcrypto.config.config`): configuration
            object
        coin (str): string representing the crypto coin of choice,
            eg. BTC,ETH

    Attributes:
        df (:obj:`pandas.DataFrame`): dataframe with datetime index
            of ohlc data. Could store also TA indicators if these are
            computed invoking the relative method.
        ta_params (dict): dictionary containing TA parametrization
    """

    def __init__(self, configuration, coin=None):

        self.config = configuration

        if coin is None:
            raise ValueError("Must specify coin.")
        else:
            # rebrandings
            if coin in self.config.rebrandings:
                coin = self.config.rebrandings[coin]
            self.coin = coin
            self.build_ts()

    def build_ts(self):
        """
        reads the data from data stored locally in `data/ts/` and
        saved in .csv format.
        """
        if os.path.isfile(self.config.data_folder + "/ts/" + self.coin + ".csv"):
            self.df = pd.read_csv(self.config.data_folder + "/ts/" + self.coin + ".csv")
            self.df["Date"] = pd.to_datetime(self.df["Date"], utc=True)
            self.df.set_index("Date", inplace=True)
            if any(self.df.index.duplicated()):
                raise ValueError("Data has duplicates.")
        else:
            raise FileNotFoundError(f"{self.coin}.csv not found.")

    # TA INDICATORS SAVED TO DF
    def ta_indicators(self):
        """
        computes the selected TA indicators and appends them to df attribute.
        """
        self.parametrization()

        #all sma 
        for sma in self.ta_params["sma"]:
            self.df.ta.sma(length=sma["slow"], append=True)
            self.df.ta.sma(length=sma["fast"], append=True)
        #macd
        self.df.ta.macd(
            window_slow=self.ta_params["macd"]["slow"],
            window_fast=self.ta_params["macd"]["fast"],
            window_sign=self.ta_params["macd"]["signal"],
            append=True,
        )
        #bollinger bands
        self.df.ta.bbands(
            length=self.ta_params["bbands"]["length"],
            std=self.ta_params["bbands"]["std"],
            append=True,
        )
        self.df.ta.rsi(timeperiod=self.ta_params["rsi"]["timeperiod"], append=True)

    def parametrization(self):
        """
        sets the default parameters if not specified in config.json file.
        """
        # TA parameters
        if (
            self.coin not in self.config.coins.keys()
            or self.config.coins[self.coin] == ""
        ):
            # default if empty or not specified in coins
            self.ta_params = {
                "sma": [{"fast": 12, "slow": 26},{"fast":100,"slow":200}],
                "macd": {"fast": 12, "slow": 26, "signal": 9},
                "bbands": {"length": 20, "std": 2},
                "rsi": {"timeperiod": 14},
            }
        elif isinstance(self.config.coins[self.coin], dict):
            self.ta_params = self.config.coins[self.coin]
        else:
            raise ValueError("Must provide TA parametrization in the correct format.")

    def distance_from_ath(self):
        d = {}
        for idx in self.df.index:
            d[idx] = abs(self.df.loc[idx, "Close"] - self.df[:idx]["Close"].max())
        self.df["distance_ATH"] = pd.Series(d)
