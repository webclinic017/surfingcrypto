"""methods for price signals"""

import pandas as pd
import numpy as np


def sma_signal(df: pd.DataFrame, colnames=["SMA_12", "SMA_26"]) -> pd.Series:
    def sma(serie: pd.Series, colnames: list) -> int or np.nan:
        """Simple Moving Average signal

        Args:
            serie (pd.Series): _description_
            colnames (list): _description_

        Returns:
            int or np.nan: _description_
        """
        if not pd.isna(serie[colnames[0]]) and not pd.isna(serie[colnames[1]]):
            if serie[colnames[0]] < serie[colnames[1]]:
                return 0
            else:
                return 1
        else:
            np.nan

    return df.apply(sma, args=(colnames,), axis=1)


def macd_signal(df: pd.DataFrame) -> pd.Series:
    def macd(serie: pd.Series) -> int or np.nan:
        """MACD signal

        Args:
            serie (pd.Series): _description_

        Returns:
            int or np.nan: _description_
        """
        if not pd.isna(serie["MACDh_12_26_9"]):
            if serie["MACDh_12_26_9"] > 0:
                return 1
            else:
                return 0
        else:
            return np.nan

    return df.copy().apply(macd, axis=1)


def bb_signal(df: pd.DataFrame, buffer=0.1) -> pd.Series:
    df["PREV_STOCK"] = df["Close"].shift(1)
    df["PREV_LOWERBB"] = df["BBL_20_2.0"].shift(1)
    df["PREV_UPPERBB"] = df["BBU_20_2.0"].shift(1)

    # IF PREV_STOCK > PREV_LOWERBB & CUR_STOCK < CUR_LOWER_BB => BUY
    # IF PREV_STOCK < PREV_UPPERBB & CUR_STOCK > CUR_UPPER_BB => SELL
    def bb(serie: pd.Series, buffer: float) -> int or np.nan:
        """Bollinger Bands signal

        Args:
            serie (pd.Series): _description_
            buffer (float): _description_

        Returns:
            int or np.nan: _description_
        """
        if (
            not pd.isna(serie["PREV_STOCK"])
            and not pd.isna(serie["PREV_LOWERBB"])
            and not pd.isna(serie["PREV_UPPERBB"])
        ):
            if (
                serie["PREV_STOCK"]
                > serie["PREV_LOWERBB"] + serie["PREV_LOWERBB"] * buffer
                and serie["Close"]
                < serie["BBL_20_2.0"] + serie["BBL_20_2.0"] * buffer
            ):
                return 1
            elif (
                serie["PREV_STOCK"]
                < serie["PREV_UPPERBB"] - serie["PREV_UPPERBB"] * buffer
                and serie["Close"]
                > serie["BBU_20_2.0"] - serie["BBU_20_2.0"] * buffer
            ):
                return 0
        else:
            return np.nan

    df["BBL_20_2_Signal"] = df.apply(bb, args=(buffer,), axis=1)
    df["BBL_20_2_Signal"] = df["BBL_20_2_Signal"].fillna(method="bfill")
    df["BBL_20_2_Signal"] = df["BBL_20_2_Signal"].fillna(method="ffill")
    return df["BBL_20_2_Signal"].copy()


def rsi_signal(df: pd.DataFrame, lower=30, upper=70) -> pd.Series:
    df["PREV_RSI"] = df["RSI_14"].shift(1)
    # IF PREVIOUS RSI > 30 AND CURRENT RSI < 30 ==> BUY SIGNAL
    # IF PREVIOUS RSI < 70 AND CURRENT RSI > 70 ==> SELL SIGNAL
    def rsi(serie: pd.Series, lower: int, upper: int) -> int or np.nan:
        """RSI signal

        Args:
            serie (pd.Series): _description_
            lower (int, optional): _description_. Defaults to 30.
            upper (int, optional): _description_. Defaults to 70.

        Returns:
            int or np.nan: _description_
        """
        if not pd.isna(serie["PREV_RSI"]):
            if serie["PREV_RSI"] > lower and serie["RSI_14"] < lower:
                return 1
            elif serie["PREV_RSI"] < upper and serie["RSI_14"] > upper:
                return 0
        else:
            return np.nan

    df["RSI_14_Signal"] = df.apply(
        rsi,
        args=(
            lower,
            upper,
        ),
        axis=1,
    )
    df["RSI_14_Signal"] = df["RSI_14_Signal"].fillna(method="bfill")
    df["RSI_14_Signal"] = df["RSI_14_Signal"].fillna(method="ffill")

    return df["RSI_14_Signal"].copy()
