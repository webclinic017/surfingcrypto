"""
test ts class
"""
import pytest
import pandas as pd
from surfingcrypto import Config, TS

DEFAULT_TA = {
    "sma": [{"fast": 12, "slow": 26}, {"fast": 100, "slow": 200}],
    "macd": {"fast": 12, "slow": 26, "signal": 9},
    "bbands": {"length": 20, "std": 2},
    "rsi": {"timeperiod": 14},
}

COINS = {"BTC": "", "ETH": "",}



def test_failed_load_data(temp_test_env):
    """test FileNotFoundError when no local data is found"""
    root = temp_test_env
    c = Config(COINS, root / "data")
    with pytest.raises(FileNotFoundError):
        TS(c, coin="BTC")

#########

@pytest.mark.parametrize(
    "temp_test_env",     
    [
        {
            "ts" : ("BTC_EUR.csv",),
        },
    ],
    indirect=["temp_test_env"]
)

def test_load_data_and_default_parametrization(temp_test_env):
    """test loading pandas df and setting default ta params"""
    root = temp_test_env
    c = Config(COINS, root / "data")
    ts = TS(c, coin="BTC")
    # load dataframe
    assert isinstance(ts.df, pd.DataFrame)
    assert hasattr(ts, "ta_params")
    assert ts.ta_params == DEFAULT_TA

###########

@pytest.mark.parametrize(
    "temp_test_env",     
    [
        {
            "ts" : ("CELO_EUR.csv",),
        },
    ],
    indirect=["temp_test_env"]
)

def test_load_data_rebranded_coin(temp_test_env):
    """
    test loading the pandas df of a rebranded 
    coin, by calling its old name, and setting default ta params
    CGLD->CELO
    """
    root = temp_test_env
    c = Config(COINS, root / "data")
    ts = TS(c, coin="CGLD")
    # load dataframe
    assert isinstance(ts.df, pd.DataFrame)
    assert hasattr(ts, "ta_params")
    assert ts.ta_params == DEFAULT_TA

##########

@pytest.mark.parametrize(
    "temp_test_env",     
    [
        {"ts" : ("BTC_EUR.csv",),},
    ],
    indirect=["temp_test_env"]
)

def test_set_ta_params(temp_test_env):
    """
    test set new ta params with a dict,
    overriding defaults or adding new if not present
    """
    root = temp_test_env
    c = Config(COINS, root / "data")
    ts = TS(c, coin="BTC")
    ts.set_ta_params(
        {
            "macd":{"fast": 7, "slow": 12, "signal": 9},
            "foo": {"bar":1}
        })
    assert ts.ta_params["macd"]["fast"]== 7
    assert ts.ta_params["foo"]["bar"]== 1

##########

@pytest.mark.parametrize(
    "temp_test_env",     
    [
        {
            "ts" : ("BTC_EUR.csv",),
        },
    ],
    indirect=["temp_test_env"]
)

def test_compute_ta_indicators(temp_test_env):
    """
    test compute_ta_indicators with default parametrization
    """
    root = temp_test_env
    c = Config(COINS, root / "data")
    ts = TS(c, coin="BTC")
    ts.compute_ta_indicators()
    assert set(["MACD_12_26_9","RSI_14","BBU_20_2.0"]).issubset(list(ts.df.columns))

@pytest.mark.wip
@pytest.mark.parametrize(
    "temp_test_env",     
    [
        {
            "ts" : ("BTC_EUR.csv",),
        },
    ],
    indirect=["temp_test_env"]
)

def test_compute_custom_ta_indicators(temp_test_env):
    """
    test compute_ta_indicators with custom parametrization
    """
    root = temp_test_env
    c = Config(COINS, root / "data")
    ts = TS(c, coin="BTC")
    ts.set_ta_params(
        {
            "sma":[{"fast": 3, "slow": 7},],
        })
    ts.compute_ta_indicators()
    print(ts.df.columns)
    print(ts.ta_params)
    assert ("SMA_3" in ts.df.columns)

@pytest.mark.wip
@pytest.mark.parametrize(
    "temp_test_env",     
    [
        {
            "ts" : ("BTC_EUR.csv",),
        },
    ],
    indirect=["temp_test_env"]
)

def test_compute_custom_invalid_ta_indicators(temp_test_env):
    """
    test compute_ta_indicators with custom invalid parametrization
    """
    root = temp_test_env
    c = Config(COINS, root / "data")
    ts = TS(c, coin="BTC")
    ts.set_ta_params(
        {
            "foo": {"bar":1}
        })
    with pytest.raises(NotImplementedError):
        ts.compute_ta_indicators()