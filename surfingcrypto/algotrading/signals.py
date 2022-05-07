"""methods for price signals"""

import pandas as pd
import numpy as np


def sma_signal(
    serie: pd.Series, colnames=["SMA_12", "SMA_26"]
) -> int or np.nan:
    """Simple Moving Average signal

    Args:
        serie (pd.Series): _description_
        colnames (list, optional): _description_. Defaults to ["SMA_12", "SMA_26"].

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


def macd_signal(serie: pd.Series) -> int or np.nan:
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


# IF PREV_STOCK > PREV_LOWERBB & CUR_STOCK < CUR_LOWER_BB => BUY
# IF PREV_STOCK < PREV_UPPERBB & CUR_STOCK > CUR_UPPER_BB => SELL
def bb_signal(serie: pd.Series, buffer=0.1) -> int or np.nan:
    """Bollinger Bands signal

    Args:
        serie (pd.Series): _description_
        buffer (float, optional): _description_. Defaults to 0.1.

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


# IF PREVIOUS RSI > 30 AND CURRENT RSI < 30 ==> BUY SIGNAL
# IF PREVIOUS RSI < 70 AND CURRENT RSI > 70 ==> SELL SIGNAL
def rsi_signal(serie: pd.Series, lower=30, upper=70) -> int or np.nan:
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
