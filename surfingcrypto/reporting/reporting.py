"""
reporting with text
"""

import pandas as pd


def percentage_diff(df: pd.DataFrame, window=7):
    """
    Percentage difference given a window size.

    Arguments:
        df ()
        window (int): number of days used to computer percentage
            difference.
    """
    return (
        (df.Close[-1] - df.Close[-window - 1]) / (df.Close[-window - 1]) * 100
    )



def report_percentage_diff(df, coin, windows=[1, 3, 7, 14, 60]) -> str:
    """
    Produces verbose and pretty report on latest price
    difference from a given list of windows.

    Args:
        df (_type_): _description_
        coin (_type_): _description_
        windows (:obj:`list` of :obj:`int`, optional): list of windows
            to compute percentage difference. Defaults to [1, 3, 7, 14, 60].

    Returns:
        str: _description_
    """
    s = f"**{coin}**\n"
    for window in windows:
        s = (
            s
            + f"- {window}d: "
            + "{:.2f}".format(percentage_diff(df, window))
            + " %\n"
        )
    return s
