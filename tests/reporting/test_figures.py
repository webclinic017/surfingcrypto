"""test figures module"""
import datetime
import pytest
from freezegun import freeze_time
import pytz
from unittest.mock import patch
from matplotlib.dates import date2num,num2date

from surfingcrypto.reporting.figures import BaseFigure, SimplePlot
from surfingcrypto.ts import TS
from surfingcrypto.config import Config

COINS = {
    "BTC": "",
}

########### BASE FIGURE ########################################################

@pytest.mark.parametrize(
    "temp_test_env",
    [
        {
            "ts": ("BTC_EUR.csv",),
        },
    ],
    indirect=["temp_test_env"],
)
def test_TS_BaseFigure_default_init(temp_test_env):
    """test _set_graphstart """
    root = temp_test_env
    c = Config(COINS, root / "data")
    ts = TS(c, coin="BTC")
    fig = BaseFigure(ts)
    assert isinstance(fig.object,TS)
    assert fig.graphstart == datetime.datetime(2021,1,1).replace(tzinfo=pytz.UTC)
    assert fig.graphend == None

@freeze_time("2022-1-1")
@pytest.mark.parametrize(
    "temp_test_env,graphstart,y,m,d",
    [
        ({"ts": ("BTC_EUR.csv",),},"1y",2021,1,1),
        ({"ts": ("BTC_EUR.csv",),},"1m",2021,12,1),
        ({"ts": ("BTC_EUR.csv",),},"6m",2021,7,1),
        ({"ts": ("BTC_EUR.csv",),},"3m",2021,10,1),
    ],
    indirect=["temp_test_env"],
)
def test_TS_BaseFigure_relative_graphstart(temp_test_env,graphstart,y,m,d):
    """test _set_graphstart """
    root = temp_test_env
    c = Config(COINS, root / "data")
    ts = TS(c, coin="BTC")
    fig = BaseFigure(ts,graphstart)
    assert isinstance(fig.object,TS)
    assert fig.graphstart == datetime.datetime(y,m,d).replace(tzinfo=pytz.UTC)
    assert fig.graphend == None


########### SIMPLE PLOT ########################################################

@freeze_time("2022-1-1")
@pytest.mark.wip
@pytest.mark.parametrize(
    "temp_test_env",
    [
        {
            "ts": ("BTC_EUR.csv",),
        },
    ],
    indirect=["temp_test_env"],
)
def test_SimplePlot(temp_test_env):
    """test _set_graphstart """
    root = temp_test_env
    c = Config(COINS, root / "data")
    ts = TS(c, coin="BTC")
    fig = SimplePlot(ts,"6m")
    assert hasattr(fig,"axes") # must have two axes, candlesticks and volume
    print(num2date(fig.axes[0].get_xticks()[0]))
    print(num2date(fig.axes[0].get_xticks()[1]))
    print(num2date(fig.axes[0].get_xticks()[-1]))

    assert fig.axes[0].get_xticks()[1] == date2num(datetime.datetime(2021,7,1).replace(tzinfo=pytz.UTC))