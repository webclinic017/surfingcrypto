"""feature engineering"""

import pandas as pd
import numpy as np
import re

from surfingcrypto.ts import TS
import surfingcrypto.algotrading.signals as surf_signals


class BinaryLaggedFeatures:
    def __init__(self, ts: TS, indicators:list,lags: list):
        self.ts = ts
        self.indicators= self._fmt_indicators(indicators)
        self.lags = lags
        self.df = self._compute_signals()
        self.model_df = self.get_model_dataframe(self.indicators)

    def _fmt_indicators(self,indicators:list)-> dict:
        dicts = {}
        for i in range(len(indicators)):
            dicts["i_" + "{}".format(str(i + 1).zfill(2))] = indicators[i]
        return dicts


    def _compute_signals(self) -> pd.DataFrame:
        df = self.ts.df

        # SMA
        df["SMA_12_26_Signal"] = df.apply(surf_signals.sma_signal, axis=1)
        df["SMA_100_200_Signal"] = df.apply(
            surf_signals.sma_signal, args=(["SMA_100", "SMA_200"],), axis=1
        )

        # MACD
        df["MACD_12_26_9_Signal"] = df.apply(surf_signals.macd_signal, axis=1)

        ## BB
        df["PREV_STOCK"] = df["Close"].shift(1)
        df["PREV_LOWERBB"] = df["BBL_20_2.0"].shift(1)
        df["PREV_UPPERBB"] = df["BBU_20_2.0"].shift(1)
        df["BBL_20_2_Signal"] = df.apply(
            surf_signals.bb_signal, args=(0,), axis=1
        )
        df["BBL_20_2_Signal"] = df["BBL_20_2_Signal"].fillna(method="bfill")
        df["BBL_20_2_Signal"] = df["BBL_20_2_Signal"].fillna(method="ffill")

        # RSI
        df["PREV_RSI"] = df["RSI_14"].shift(1)
        df["RSI_14_Signal"] = df.apply(surf_signals.rsi_signal, axis=1)
        df["RSI_14_Signal"] = df["RSI_14_Signal"].fillna(method="bfill")
        df["RSI_14_Signal"] = df["RSI_14_Signal"].fillna(method="ffill")

        return df

    def get_model_dataframe(self, indicatori: dict) -> pd.DataFrame:
        model_df = self.df[["Close"] + list(indicatori.values())]

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

        # get lagged values
        cols = []
        for key in indicatori:
            for lag in self.lags:
                col = f"{key}_lag{str(lag).zfill(2)}"
                model_df[col] = model_df[key].shift(lag)
                cols.append(col)

        model_df.dropna(inplace=True)

        # get colun names columns
        self.x_cols_names = []
        for col in model_df.columns:
            if col[:2] == "i_":
                if re.match(r"(i_[0-9]{2})_(lag[0-9]{2})", col):
                    self.x_cols_names.append(col)

        model_df.tail(2)

        return model_df

    def __repr__(self) -> str:
        return f"BinaryLaggedFeatures(ts={self.ts.coin},lags={self.lags})"

    def __str__(self) -> str:
        return f"BinaryLaggedFeatures(ts={self.ts.coin}),lags={self.lags})"
