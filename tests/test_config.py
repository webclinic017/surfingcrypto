"""
test config class.
"""
import pytest
import os
import datetime
from pathlib import Path
import datetime
from freezegun import freeze_time

from surfingcrypto.config import Config

COINS = {"BTC": "", "ETH": ""}


@freeze_time("2022-09-22")
def test_default_init(temp_test_env):
    """
    test initialization of config class

    must have data from the first day posssible or at least 2017-10-1
    until last available price
    """
    root = temp_test_env
    c = Config(COINS, root / "data")

    assert c.coins == COINS
    assert c.fiat == "EUR"
    assert isinstance(c.data_folder, Path)

    # default dirs
    assert os.path.isdir(root / "data" / "ts")
    assert os.path.isdir(root / "data" / "temp")
    assert os.path.isdir(root / "data" / "cache")

    # default scraping parameters, as datetime UTC AWARE
    assert c.scraping_req["ETH"]["start"] == datetime.datetime(
        2017, 10, 1, tzinfo=datetime.timezone.utc
    )
    # end_day must be one day before today, UTC
    assert c.scraping_req["ETH"]["end_day"] == datetime.datetime(
        2022, 9, 21, tzinfo=datetime.timezone.utc
    )


def test_clear_temp_files(temp_test_env):
    root = temp_test_env
    # first run to create folder struct
    c = Config(COINS, root / "data")
    # create file
    with open(root / "data" / "temp" / "test.txt", "wb") as f:
        f.close()
    # calling again the init should empty the temp dir
    c = Config(COINS, root / "data")
    # directory exits
    assert os.path.isdir(root / "data" / "temp")
    # but all temp files from previous run are removed with init
    assert not os.listdir(root / "data" / "temp")


@freeze_time("2022-09-22")
@pytest.mark.parametrize(
    "temp_test_env",
    [
        {
            "cache": ("coinbase_accounts.json",),
        },
    ],
    indirect=["temp_test_env"],
)
def test_init_with_coinbase_req(temp_test_env):
    root = temp_test_env
    c = Config(COINS, root / "data")

    # should be parsing strings cached by coinbase
    # from coinbase_accounts.json
    # as datetime UTC AWARE
    assert c.coinbase_req["SOL"]["start"].replace(
        hour=0, minute=0, second=0, microsecond=0
    ) == datetime.datetime(2021, 11, 29, tzinfo=datetime.timezone.utc)
    # end_day must be one day before today, UTC
    assert c.coinbase_req["SOL"]["end_day"].replace(
        hour=0, minute=0, second=0, microsecond=0
    ) == datetime.datetime(2022, 9, 21, tzinfo=datetime.timezone.utc)


def test_storage_of_secrets(temp_test_env):
    root = temp_test_env
    secrets = {"foo": {}, "baz": "baz"}
    c = Config(COINS, root / "data", secrets)

    assert hasattr(c, "foo")
    assert hasattr(c, "baz")


@freeze_time("2022-09-22")
def test_add_coin(temp_test_env):
    # test adding a coin that is not already in c.coins
    # no coinbase req
    root = temp_test_env
    c = Config(COINS, root / "data")
    c.add_coins(["SOL"])

    # default scraping parameters, as datetime UTC AWARE
    assert c.scraping_req["SOL"]["start"] == datetime.datetime(
        2017, 10, 1, tzinfo=datetime.timezone.utc
    )
    # end_day must be one day before today, UTC
    assert c.scraping_req["SOL"]["end_day"] == datetime.datetime(
        2022, 9, 21, tzinfo=datetime.timezone.utc
    )
