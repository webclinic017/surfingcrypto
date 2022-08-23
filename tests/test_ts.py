"""
test ts class
"""
from xml.dom import InvalidCharacterErr
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


def test_valuerror(temp_test_env):
    """test ValueError when no coin is specified"""
    root = temp_test_env
    c = Config(COINS, root / "data")
    with pytest.raises(ValueError):
        TS(c, coin=None)



def test_failed_load_data(temp_test_env):
    """test FileNotFoundError"""
    root = temp_test_env
    c = Config(COINS, root / "data")
    with pytest.raises(FileNotFoundError):
        TS(c, coin="BTC")


@pytest.mark.parametrize(
    "temp_test_env",     
    [
        ("BTC.csv",),
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
    ts._parametrize(None)
    assert hasattr(ts, "ta_params")
    assert ts.ta_params == DEFAULT_TA
