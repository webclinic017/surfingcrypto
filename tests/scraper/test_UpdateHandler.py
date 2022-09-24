"""
test UpdateHandler class.
"""
import datetime
from logging import root
import pytest
import pandas as pd
from pandas.testing import assert_frame_equal

import os
from unittest.mock import patch

from surfingcrypto.scraper import CMCutility, UpdateHandler

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
    assert uh.apiwrapper == CMCutility


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
    """load local csv data, with first and last being datetime"""
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
    assert isinstance(first, datetime.datetime)
    assert isinstance(last, datetime.datetime)
    # range index
    assert isinstance(df.index, pd.RangeIndex)
    # ascending order
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


@patch("surfingcrypto.scraper.UpdateHandler._handle_update")
def test_UpdateHandler_get_updates_onesided(mock, temp_test_env):
    """get updates in basic version, one side update is required"""
    root = temp_test_env
    uh = UpdateHandler(
        "BTC",
        "EUR",
        datetime.datetime(2021, 1, 1),
        datetime.datetime(2022, 1, 1),
        root / "data" / "ts" / "BTC_EUR.csv",
    )
    uh.left, uh.right = uh.start, uh.end_day
    assert not hasattr(uh, "df")
    uh.df = uh._get_updates(None)
    assert hasattr(uh, "df")
    assert len(uh.df) == 366


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
def test_UpdateHandler_get_updates_twosided(mock, temp_test_env):
    """get updates in a basic version, patching handle update verify that
    the two way update is recognized"""
    root = temp_test_env
    uh = UpdateHandler(
        "BTC",
        "EUR",
        datetime.datetime(2018, 1, 1),
        datetime.datetime(2022, 5, 30),
        root / "data" / "ts" / "BTC_EUR.csv",
    )
    df, left, right = uh._load_csv()
    uh.left, uh.right = uh._get_required_bounds(left, right)
    uh.df = uh._get_updates(df)
    uh.df["Date"] = pd.to_datetime(uh.df["Date"])

    assert not any(uh.df["Date"].duplicated())
    assert str(uh.df["Date"].iloc[0]) == str(
        datetime.datetime(2018, 1, 1),
    )
    assert str(uh.df["Date"].iloc[-1]) == str(
        datetime.datetime(2022, 5, 30),
    )


@pytest.mark.parametrize(
    "temp_test_env",
    [
        {
            "ts": ("BTC_EUR.csv",),
        },
    ],
    indirect=["temp_test_env"],
)
def test_UpdateHandler_handle_update_already_up_to_date(temp_test_env):
    """test when local data is already up to date"""
    root = temp_test_env
    uh = UpdateHandler(
        "BTC",
        "EUR",
        datetime.datetime(2021, 1, 1),
        datetime.datetime(2021, 12, 31),
        root / "data" / "ts" / "BTC_EUR.csv",
    )
    assert uh.description == "BTC in EUR, already up to date."
    assert uh.result == True


@pytest.mark.parametrize(
    "temp_test_env",
    [
        {
            "ts": (),
        },
    ],
    indirect=["temp_test_env"],
)
def test_UpdateHandler_handle_update_nolocaldata(temp_test_env):
    """test when there is no local data

    empty tuple so that folder struct is created by fixture

    """
    root = temp_test_env
    uh = UpdateHandler(
        "BTC",
        "EUR",
        datetime.datetime(2021, 1, 1),
        datetime.datetime(2021, 12, 31),
        root / "data" / "ts" / "BTC_EUR.csv",
    )
    assert uh.description == "BTC in EUR, successfully downloaded."
    assert os.path.isfile(root / "data" / "ts" / "BTC_EUR.csv")
    assert uh.result == True
    df = pd.read_csv("tests/fixtures/BTC_EUR.csv")
    df["Date"] = pd.to_datetime(df["Date"])
    # quick fix for compraing rangeindex e int index
    df.index = df.index.to_list()
    assert_frame_equal(df, uh.df)


@pytest.mark.parametrize(
    "temp_test_env",
    [
        {
            "ts": ("BTC_EUR.csv",),
        },
    ],
    indirect=["temp_test_env"],
)
def test_UpdateHandler_handle_update_oneside_endside(temp_test_env):
    """test oneside update (append to end) of df"""
    root = temp_test_env

    # split df for test
    df = pd.read_csv(root / "data" / "ts" / "BTC_EUR.csv")
    df[:31].to_csv(root / "data" / "ts" / "BTC_EUR.csv", index=False)
    df["Date"] = pd.to_datetime(df["Date"])

    uh = UpdateHandler(
        "BTC",
        "EUR",
        datetime.datetime(2021, 1, 1),
        datetime.datetime(2021, 12, 31),
        root / "data" / "ts" / "BTC_EUR.csv",
    )
    assert uh.description == "BTC in EUR, successfully updated."
    assert_frame_equal(df, uh.df)


@pytest.mark.skip
def test_UpdateHandler_handle_update_oneside_frontside():
    pass


@pytest.mark.skip
def test_UpdateHandler_handle_update_twoside():
    pass

@pytest.mark.wip
@pytest.mark.parametrize(
    "temp_test_env",
    [
        {
            "ts": (),
        },
    ],
    indirect=["temp_test_env"],
)
def test_UpdateHandler_handle_update_save_csv(temp_test_env,):
    """
    test if data is saved locally correctly

    eg. pandas int index is ignored
    """
    root = temp_test_env
    UpdateHandler(
        "BTC",
        "EUR",
        datetime.datetime(2021, 1, 1),
        datetime.datetime(2021, 12, 31),
        root / "data" / "ts" / "BTC_EUR.csv",
    )
    df = pd.read_csv(root / "data" / "ts" / "BTC_EUR.csv",)

    assert any([True for col in df.columns if "Unnamed" in col]) == False

@pytest.mark.parametrize(
    "temp_test_env,descr",
    [
        (
            {
                "ts": ("BTC_EUR.csv",),
            },
            "BTC in EUR, already up to date.",
        ),
        (
            {
                "ts": (),
            },
            "BTC in EUR, successfully downloaded.",
        ),
    ],
    indirect=["temp_test_env"],
)
def test_UpdateHandler_str_repr(temp_test_env, descr):
    """str and repr magic methods"""
    root = temp_test_env
    uh = UpdateHandler(
        "BTC",
        "EUR",
        datetime.datetime(2021, 2, 1),
        datetime.datetime(2021, 10, 31),
        root / "data" / "ts" / "BTC_EUR.csv",
    )
    expected = f"UpdateHandler(BTC-EUR: {descr})"
    assert str(uh) == expected
    assert repr(uh) == expected