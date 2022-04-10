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


def report_percentage_diff(
    df: pd.DataFrame, coin: str, windows=[1, 3, 7, 14, 60]
) -> str:
    """
    Produces verbose and pretty report on latest price
    difference from a given list of windows.

    Args:
        df (_type_): _description_
        coin (_type_): _description_
        windows (:obj:`list` of :obj:`int`, optional): list of windows
            to compute percentage difference. Defaults to [1, 3, 7, 14, 60].

    Returns:
        str: string report
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


def report_stock_gain(df: pd.DataFrame):
    """report stock gain

    Args:
        df (pd.DataFrame): dataframe with single day data with calculations

    Returns:
        str: string report
    """
    df = df[["Symbol", "Stock Gain / (Loss)"]]
    s = ""
    for idx, row in df.iterrows():
        s = (
            s
            + row["Symbol"]
            + " : "
            + "{:.2f}".format(row["Stock Gain / (Loss)"])
            + "\n"
        )
    return s

def report_coinbase_live_value(portfolio):
    """
    Nicely formatted report of accounts portfolio and user total
    balance in EUR.

    Args:
        portfolio (_type_): _descr_

    Returns:
        s (str): text
    """
    s = ""
    tot = 0
    for account in portfolio.coinbase.accounts:
        if float(account.native_balance.amount) > 0:
            s = (
                s
                + str(account.currency)
                + " : "
                + str(account.native_balance)
                + "\n"
            )
            tot += float(account.native_balance.amount)
    s = s + "---\n" + "Portfolio: EUR " + "{:.2f}".format(tot)
    return s