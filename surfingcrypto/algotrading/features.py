"""feature engineering"""

import pandas as pd
import numpy as np
import re

from surfingcrypto.ts import TS
import surfingcrypto.algotrading.signals as surf_signals


class Features:
    def __init__(self, ts: TS, indicators: list):
        self.ts = ts
        self.indicators = self._fmt_indicators(indicators)
        self.x_cols_names = []
        self.df = pd.DataFrame()  # dataframe with  indicators and signals
        self.model_df = pd.DataFrame()  # dataframe with Y and X

    def _fmt_indicators(self, indicators: list) -> dict:
        dicts = {}
        for i in range(len(indicators)):
            dicts["i_" + "{}".format(str(i + 1).zfill(2))] = indicators[i]
        return dicts


class BinaryLaggedLogReturns(Features):
    def __init__(self, lags: list, *args, **kwargs):
        self.lags = lags
        super().__init__(*args, **kwargs)
        self.df = self._compute_signals()
        self.model_df = self._set_binary_lagged_features(self.indicators)

    def _compute_signals(self) -> pd.DataFrame:
        df = self.ts.df

        # SMA
        df["SMA_12_26_Signal"] = surf_signals.sma_signal(df)
        df["SMA_100_200_Signal"] = surf_signals.sma_signal(
            df, colnames=["SMA_100", "SMA_200"]
        )
        # MACD
        df["MACD_12_26_9_Signal"] = surf_signals.macd_signal(df)

        ## BB
        df["BB_20_2_Signal"] = surf_signals.bb_signal(df)

        # RSI
        df["RSI_14_Signal"] = surf_signals.rsi_signal(df)

        return df

    def _set_binary_lagged_features(self, indicatori: dict) -> pd.DataFrame:
        model_df = self.df[["Close"] + list(indicatori.values())].copy()

        model_df.rename(columns={"Close": self.ts.coin}, inplace=True)
        model_df.rename(
            columns={v: k for k, v in indicatori.items()}, inplace=True
        )  # rename cols with reversed dict

        # calculate daily log returns
        model_df["returns"] = np.log(
            model_df[self.ts.coin] / model_df[self.ts.coin].shift(1)
        )
        model_df.dropna(inplace=True)

        # calculate binary direction of market
        model_df["direction"] = np.sign(model_df["returns"]).astype(int)

        # get lagged values of all indicators
        self.x_cols_names = []
        for key in indicatori:
            for lag in self.lags:
                col = f"{key}_lag{str(lag).zfill(2)}"
                model_df[col] = model_df[key].shift(lag)
                self.x_cols_names.append(col)

        model_df.dropna(inplace=True)

        return model_df

    def get_future_x(self) -> pd.Series:
        last = self.model_df.loc[
            self.model_df.iloc[-1].name, self.x_cols_names
        ]
        future = []
        for key in self.indicators:
            iseries = last.loc[last.index.str.contains(key)].shift()
            iseries.iloc[0] = self.model_df.loc[
                self.model_df.iloc[-1].name, key
            ]
            future.append(iseries)

        future = pd.concat(future)
        future.name = self.model_df.index[-1] + pd.Timedelta(days=1)

        return future

    def __repr__(self) -> str:
        return f"BinaryLaggedLogReturns(ts={self.ts.coin},lags={self.lags})"

    def __str__(self) -> str:
        return f"BinaryLaggedLogReturns(ts={self.ts.coin}),lags={self.lags})"
