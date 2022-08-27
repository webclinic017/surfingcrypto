"""
test scraper module.
"""
import datetime
import pathlib
import pytest
import pandas as pd
from unittest.mock import Mock, patch


from surfingcrypto.scraper import CMCutility, UpdateHandler

######## cmc utility


def test_CMCutility():
    cmc = CMCutility(
        "BTC",
        datetime.datetime(2021, 1, 1),
        datetime.datetime(2022, 1, 1),
        "EUR",
    )
    response = cmc.scrape_data()
    assert isinstance(response, pd.DataFrame)
    print(response)
    assert len(response)>0
    assert str(response["Date"].iloc[-1]) == str(datetime.datetime(2021, 1, 1))
    assert str(response["Date"].iloc[-0]) == str(datetime.datetime(2022, 1, 1))



def test_CMCutility_str_repr():
    cmc = CMCutility(
        "BTC",
        datetime.datetime(2021, 1, 1),
        datetime.datetime(2022, 1, 1),
        "EUR",
    )
    cmc.scrape_data()
    expected = "CmcScraper(BTC, left=01-01-2021, right=01-01-2022, empty_response=False)"
    assert str(cmc) == expected
    assert repr(cmc) == expected


def test_CMCutility_str_repr_empty_response():
    cmc = CMCutility(
        "BTC",
        datetime.datetime(2021, 1, 1),
        datetime.datetime(2022, 1, 1),
        "EUR",
    )
    expected = "CmcScraper(BTC, left=01-01-2021, right=01-01-2022, empty_response=None)"
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
    assert hasattr(uh, "apiwrapper")


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
    """load local csv data"""
    root = temp_test_env
    uh = UpdateHandler(
        "BTC",
        "EUR",
        datetime.datetime(2021, 1, 1),
        datetime.datetime(2022, 1, 1),
        root / "data" / "ts" / "BTC_EUR.csv",
    )
    df, first, last = uh._load_csv()
    assert isinstance(df, pd.DataFrame)
    assert first == datetime.datetime(2021, 1, 1)
    assert last == datetime.datetime(2021, 12, 31)


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
def test_UpdateHandler_get_required_bounds_2(mock, temp_test_env):
    """
    load get required bounds
    start 2021-1-1
    first 2021-1-1
    last  2021-12-31
    end   2022-8-7
    --> get from day after last to end
    """
    root = temp_test_env
    uh = UpdateHandler(
        "BTC",
        "EUR",
        datetime.datetime(2021, 1, 1),
        datetime.datetime(2022, 8, 27),
        root / "data" / "ts" / "BTC_EUR.csv",
    )
    df, first, last = uh._load_csv()
    left, right = uh._get_required_bounds(first, last)
    assert left == datetime.datetime(2022, 1, 1)
    assert right == datetime.datetime(2022, 8, 27)


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
def test_UpdateHandler_get_required_bounds_1(mock, temp_test_env):
    """
    load get required bounds
    start 2019-1-1
    first 2021-1-1
    last  2021-12-31
    end   2021-12-31
    --> get from start to day before the first
    """
    root = temp_test_env
    uh = UpdateHandler(
        "BTC",
        "EUR",
        datetime.datetime(2019, 1, 1),
        datetime.datetime(2021, 12, 31),
        root / "data" / "ts" / "BTC_EUR.csv",
    )
    df, first, last = uh._load_csv()
    left, right = uh._get_required_bounds(first, last)
    assert left == datetime.datetime(2019, 1, 1)
    assert right == datetime.datetime(2020, 12, 31)


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
def test_UpdateHandler_get_required_bounds_3(mock, temp_test_env):
    """
    load get required bounds
    start 2020-1-1
    first 2021-1-1
    last  2021-12-31
    end   2022-08-20

    --> two-sided update, lists of lefts and rights
    """
    root = temp_test_env
    uh = UpdateHandler(
        "BTC",
        "EUR",
        datetime.datetime(2020, 1, 1),
        datetime.datetime(2022, 8, 20),
        root / "data" / "ts" / "BTC_EUR.csv",
    )
    df, first, last = uh._load_csv()
    left, right = uh._get_required_bounds(first, last)
    assert isinstance(left, list)
    assert isinstance(right, list)
    assert left[0] == datetime.datetime(2020, 1, 1)
    assert right[0] == datetime.datetime(2020, 12, 31)
    assert left[1] == datetime.datetime(2022, 1, 1)
    assert right[1] == datetime.datetime(2022, 8, 20)


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
def test_UpdateHandler_get_required_bounds_4(mock, temp_test_env):
    """
    load get required bounds
    first 2021-1-1
    start 2021-2-1
    end   2021-10-31
    last  2021-12-31

    --> already have return None
    """
    root = temp_test_env
    uh = UpdateHandler(
        "BTC",
        "EUR",
        datetime.datetime(2021, 2, 1),
        datetime.datetime(2021, 10, 31),
        root / "data" / "ts" / "BTC_EUR.csv",
    )
    df, first, last = uh._load_csv()
    left, right = uh._get_required_bounds(first, last)
    assert left == None
    assert right == None


@pytest.mark.skip
@patch("surfingcrypto.scraper.UpdateHandler._handle_update")
def test_UpdateHandler_get_updates(mock, temp_test_env):
    """"""
    cmc_mock = Mock(spec=CMCutility)
    cmc_mock.ciao = 2
    cmc_mock.get_data().return_value = pd.DataFrame()
    root = temp_test_env
    uh = UpdateHandler(
        "BTC",
        "EUR",
        datetime.datetime(2021, 1, 1),
        datetime.datetime(2022, 1, 1),
        root / "data" / "ts" / "BTC_EUR.csv",
    )
    uh.left, uh.right = uh.start, uh.end_day

    # uh.apiwrapper=cmc_mock()

    # df = uh._get_updates(None)
    # print()
    # assert isinstance(df,pd.DataFrame)
    # assert cmc_mock.getassert_called_once()



@pytest.mark.skip
@patch("surfingcrypto.scraper.UpdateHandler._handle_update")
def test_UpdateHandler_handle_update(mock, temp_test_env):
    root = temp_test_env
    uh = UpdateHandler(
        "BTC",
        "EUR",
        datetime.datetime(2021, 2, 1),
        datetime.datetime(2021, 10, 31),
        root / "data" / "ts" / "BTC_EUR.csv",
    )
    uh._handle_update()


@pytest.mark.skip
@pytest.mark.parametrize(
    "temp_test_env,result",
    [
        (None, "False"),
        (
            {
                "ts": ("BTC_EUR.csv",),
            },
            "True",
        ),
    ],
    indirect=["temp_test_env"],
)
def test_UpdateHandler_str_repr(temp_test_env, result):
    root = temp_test_env
    uh = UpdateHandler(
        "BTC",
        "EUR",
        datetime.datetime(2021, 2, 1),
        datetime.datetime(2021, 10, 31),
        root / "ts" / "BTC_EUR.csv",
    )
    expected = f"UpdateHandler(BTC, result={result})"
    assert str(uh) == expected
    assert repr(uh) == expected
