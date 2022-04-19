"""
get google search trend data
"""
from pytrends.request import TrendReq
import pandas as pd


class GTrends:
    """
    Interface with Google Trends by unofficial API.

    Arguments:
        kw_list (:obj:`list` of :obj:`str`): list of keywords to look for.

    Note:
        Gets data, but the data is "relative".
        1 : day of highest interaction
        0 : day of lowest interaction
    """

    def __init__(self, kw_list=None):
        self.kw_list = kw_list
        pass

    def trends(self):
        df_list = []
        for kw in self.kw_list:
            pytrends = TrendReq(hl="en-US", tz=360)
            pytrends.build_payload([kw], cat=0, timeframe="today 5-y", geo="", gprop="")
            df_list.append(pytrends.interest_over_time())

        df = df_list[0].copy()
        for idf in range(len(df_list) - 1):
            df_list[idf].drop("isPartial", axis=1, inplace=True)
            df = pd.concat([df, df_list[idf + 1]])

        if len(df_list) == 1:
            df.drop("isPartial", axis=1, inplace=True)

        if df.index.duplicated().any():
            df = df.groupby(df.index).sum()

        x2 = pd.date_range(df.index.min(), df.index.max(), freq="1D")
        df2 = df.reindex(x2)
        for column in df2.columns.tolist():
            df2[column] = df2[column].interpolate("time")

        return df2
