"""
test scraper module.
"""
import datetime
import pytest
import pandas as pd
from unittest.mock import patch


from surfingcrypto.scraper import CMCutility, UpdateHandler

######## cmc utility

def test_CMCutility():
    cmc = CMCutility(
        "BTC",
        datetime.datetime(2021, 1, 1),
        datetime.datetime(2022, 1, 1),
        "EUR",
    )
    assert isinstance(cmc.get_data(), pd.DataFrame)


def test_CMCutility_str_repr():
    cmc = CMCutility(
        "BTC",
        datetime.datetime(2021, 1, 1),
        datetime.datetime(2022, 1, 1),
        "EUR",
    )
    expected = "CmcScraper(BTC, left=01-01-2021, right=01-01-2022)"
    assert str(cmc) == expected
    assert repr(cmc) == expected


############  updatehandler

# @patch.object(UpdateHandler,"_handle_update") #both works
@patch("surfingcrypto.scraper.UpdateHandler._handle_update")
def test_UpdateHandler(mock, temp_test_env):
    """base test for UpdateHandler"""
    root = temp_test_env
    uh = UpdateHandler(
        "BTC",
        "EUR",
        datetime.datetime(2021, 1, 1),
        datetime.datetime(2022, 1, 1),
        root,
    )
    assert uh.coin == "BTC"
    assert not hasattr(uh, "df")

@pytest.mark.parametrize(
    "temp_test_env",
    [
        {
            "ts": ("BTC_EUR.csv",),
        },
    ],
    indirect=["temp_test_env"],
)
@patch("surfingcrypto.scraper.UpdateHandler._handle_update")
def test_UpdateHandler_load_csv(mock, temp_test_env):
    """load local csv data """
    root = temp_test_env
    uh = UpdateHandler(
        "BTC",
        "EUR",
        datetime.datetime(2021, 1, 1),
        datetime.datetime(2022, 1, 1),
        root/"data"/"ts"/"BTC_EUR.csv",
    )
    df, first, last = uh._load_csv()
    assert isinstance(df,pd.DataFrame)
    assert isinstance(first,datetime.datetime)
    assert isinstance(last,datetime.datetime)

