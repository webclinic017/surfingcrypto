"""
time-series objects for cryptocurrencies.
"""
import pandas as pd
import os
import pandas_ta as ta
from surfingcrypto.config import Config


class TS:
    """
    This is an time-series oriented crypto price data object.

    Note:
        Data can be downloaded calling ```surfingcrypto.scraper.Scraper```
        object.

    Arguments:
        config (:obj:`surfingcrypto.config.config`): configuration
            object
        coin (str): string representing the crypto coin of choice,
            eg. BTC,ETH

    Attributes:
        config (:obj:`surfingcrypto.config.config`): package
            configuration object
        coin (str): string representing the crypto coin of choice,
            eg. BTC,ETH
        fiat (str): fiat currency in which the prices are represented
        df (:obj:`pandas.DataFrame`): dataframe with datetime index
            of ohlc data. Could store also TA indicators if these are
            computed invoking the relative method.
        ta_params (dict): dictionary containing TA parametrization
    """

    def __init__(self, configuration: Config, coin: str):

        self.config = configuration
        self.fiat = self.config.fiat

        # default ta params
        self.ta_params = {
            "sma": [{"fast": 12, "slow": 26}, {"fast": 100, "slow": 200}],
            "macd": {"fast": 12, "slow": 26, "signal": 9},
            "bbands": {"length": 20, "std": 2},
            "rsi": {"timeperiod": 14},
        }
        # rebrandings
        if coin in self.config.rebrandings:
            coin = self.config.rebrandings[coin]

        self.coin = coin

        self._build_ts()

    def _build_ts(self):
        """
        reads the data from data stored locally in `data/ts/` and
        saved in .csv format.
        """
        if os.path.isfile(
            self.config.data_folder / "ts" / (self.coin + "_" + self.fiat + ".csv")
        ):
            self.df = pd.read_csv(
                self.config.data_folder / "ts" / (self.coin + "_" + self.fiat + ".csv")
            )
            self.df["Date"] = pd.to_datetime(self.df["Date"], utc=True)
            self.df.set_index("Date", inplace=True)
            self._validity_checks()
        else:
            raise FileNotFoundError(f"{self.coin}.csv not found.")

    def _validity_checks(self):
        """
        validity check to avoid errors later on

        Raises:
            AttributeError: _description_
            ValueError: _description_
        """
        # minimum columns
        if not set(
            [
                "Open",
                "High",
                "Low",
                "Close",
            ]
        ).issubset(self.df.columns):
            raise AttributeError(
                "df must have at least columns named: " "Open, High, Low, Close"
            )
        # duplicates
        if any(self.df.index.duplicated()):
            raise ValueError("Data has duplicates.")

    def set_ta_params(self, params: dict):
        """sets new TA parameters
        ```
        self.ta_params = {
            "sma": [
                {"fast": 12, "slow": 26},
                {"fast": 100, "slow": 200}
                ],
            "macd": {"fast": 12, "slow": 26, "signal": 9},
            "bbands": {"length": 20, "std": 2},
            "rsi": {"timeperiod": 14},
        }
        ````
        """
        for param in params:
            # dictionary
            self.ta_params[param] = params[param]

    ########## COLUMNS FOR INDICATORS SAVED TO THE DF INPLACE

    def compute_ta_indicators(self):
        """computes the selected TA indicators and appends them to df attribute
        using `pandas_ta` module.

        It supports:
            - SMA
            - MACD
            - Bolinger bands
            - RSI
        """
        for key in self.ta_params:
            # sma can also be a list,
            if key == "sma":
                # all sma
                for sma in self.ta_params["sma"]:
                    self.df.ta.sma(length=sma["slow"], append=True)
                    self.df.ta.sma(length=sma["fast"], append=True)
            elif key == "macd":
                # macd
                self.df.ta.macd(
                    window_slow=self.ta_params["macd"]["slow"],
                    window_fast=self.ta_params["macd"]["fast"],
                    window_sign=self.ta_params["macd"]["signal"],
                    append=True,
                )
            elif key == "bbands":
                # bollinger bands
                self.df.ta.bbands(
                    length=self.ta_params["bbands"]["length"],
                    std=self.ta_params["bbands"]["std"],
                    append=True,
                )
            elif key == "rsi":
                self.df.ta.rsi(
                    timeperiod=self.ta_params["rsi"]["timeperiod"], append=True
                )
            else:
                raise NotImplementedError

    def distance_from_ath(self):
        d = {}
        for idx in self.df.index:
            d[idx] = abs(self.df.loc[idx, "Close"] - self.df[:idx]["Close"].max())
        self.df["distance_ATH"] = pd.Series(d)
