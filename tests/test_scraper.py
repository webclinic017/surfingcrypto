"""
test scraper module.
"""
import datetime
import pytest
import pandas as pd
import os

from surfingcrypto.scraper import Scraper
from surfingcrypto import Config

scenarios = [
    # load config without running
    (("config.json",), False, []),
    # load config and run
    (("config.json",), True, ["BTC.csv"]),
    # load config, data to be updated and run.
    # one is updated and the other is downloaded entirely
    ((("config.json",), ("BTC.csv",)), True, ["SOL.csv", "BTC.csv"]),
]


@pytest.mark.parametrize(
    "temp_test_env,run,check_files", scenarios, indirect=["temp_test_env"]
)
def test_scraping_without_coinbase(temp_test_env, run, check_files):
    """
    test scraping the only coins specified in config.
    """
    root = temp_test_env

    c = Config(str(root / "config"))
    s = Scraper(c)
    assert isinstance(s.config, Config)
    if run:
        s.run()
        for file in check_files:
            assert os.path.isfile(root / "data" / "ts" / file)
            df = pd.read_csv(root / "data" / "ts" / file)
            df["Date"] = pd.to_datetime(df["Date"])
            # sorted
            assert df["Date"].is_monotonic_increasing is True
            # test no duplicates
            assert any(df["Date"].duplicated()) is False
            # test continuous index
            assert len(
                pd.date_range(df["Date"].iat[0], df["Date"].iat[-1], freq="D")
            ) == len(df)
            # test last of df is last price available
            assert df["Date"].iat[
                -1
            ].date() == datetime.datetime.utcnow().date() + datetime.timedelta(-1)


scenarios = [
    # scrape data from config with the addtional coibase requirements
    (("config.json", "coinbase_accounts.json"), ["BTC.csv", "SOL.csv", "AAVE.csv"]),
    (
        (("config.json", "coinbase_accounts.json"), ("BTC.csv",)),
        ["BTC.csv", "SOL.csv", "AAVE.csv"],
    ),
]


@pytest.mark.parametrize(
    "temp_test_env,check_files", scenarios, indirect=["temp_test_env"]
)
def test_scraping_with_coinbase(temp_test_env, check_files):
    """
    test scraping when there is additional data required by the coinbase module.
    """
    root = temp_test_env

    c = Config(str(root / "config"))
    s = Scraper(c)
    assert isinstance(s.config, Config)
    s.run()
    for file in check_files:
        assert os.path.isfile(root / "data" / "ts" / file)
        df = pd.read_csv(root / "data" / "ts" / file)
        df["Date"] = pd.to_datetime(df["Date"])
        # sorted
        assert df["Date"].is_monotonic_increasing is True
        # test no duplicates
        assert any(df["Date"].duplicated()) is False
        # test continuous index
        assert len(
            pd.date_range(df["Date"].iat[0], df["Date"].iat[-1], freq="D")
        ) == len(df)
        assert df["Date"].iat[-1].date() == c.scraping_req[file[:-4]]["end_day"]

