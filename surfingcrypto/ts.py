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

    def __init__(self, configuration, coin=None):

        self.config = configuration
        self.fiat = self.config.fiat

        if coin is None:
            raise ValueError("Must specify coin.")
        else:
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
            self.config.data_folder
            / "ts"
            / (self.coin + "_" + self.fiat + ".csv")
        ):
            self.df = pd.read_csv(
                self.config.data_folder
                / "ts"
                / (self.coin + "_" + self.fiat + ".csv")
            )
            self.df["Date"] = pd.to_datetime(self.df["Date"], utc=True)
            self.df.set_index("Date", inplace=True)
            if any(self.df.index.duplicated()):
                raise ValueError("Data has duplicates.")
        else:
            raise FileNotFoundError(f"{self.coin}.csv not found.")

    # TA INDICATORS SAVED TO DF
    def ta_indicators(self, params=None):
        """computes the selected TA indicators and appends them to df attribute

        It supports:
            - SMA
            - MACD
            - Bolinger bands
            - RSI
        """
        self._parametrize(params)

        for key in self.ta_params:
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

    def _parametrize(self, params: dict or None):
        """sets the TA parameters

        first sets package defaults, then overrides with condfiguration default
        if present and finally ovverrides once again with method argument

        """

        # default if empty or not specified in coins
        self.ta_params = {
            "sma": [{"fast": 12, "slow": 26}, {"fast": 100, "slow": 200}],
            "macd": {"fast": 12, "slow": 26, "signal": 9},
            "bbands": {"length": 20, "std": 2},
            "rsi": {"timeperiod": 14},
        }
        # if provided in config, override default
        if isinstance(self.config.coins[self.coin], dict):
            self.ta_params = self.config.coins[self.coin]
        # if provided via the method, overide previous
        if params is not None:
            self.ta_params = params

    def distance_from_ath(self):
        d = {}
        for idx in self.df.index:
            d[idx] = abs(
                self.df.loc[idx, "Close"] - self.df[:idx]["Close"].max()
            )
        self.df["distance_ATH"] = pd.Series(d)
