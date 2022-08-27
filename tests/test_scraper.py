"""
test scraper module.
"""
import datetime
import pytest
import pandas as pd
from unittest.mock import patch


from surfingcrypto.scraper import CMCutility, UpdateHandler


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
# @patch.object(UpdateHandler,"_handle_update") #both works
@patch("surfingcrypto.scraper.UpdateHandler._handle_update")
def test_UpdateHandler(mock,temp_test_env):
    root = temp_test_env
    uh = UpdateHandler(
        "BTC",
        "EUR",
        datetime.datetime(2021, 1, 1),
        datetime.datetime(2022, 1, 1),
        str(root),
    )
    assert uh.coin == "BTC"
    assert not hasattr(uh,"df")


# scenarios = [
#     # load config without running
#     (None, False, []),
#     # load config and run
#     (None, True, ["BTC_EUR.csv"]),
#     # load config, data to be updated and run.
#     # one is updated and the other is downloaded entirely
#     ({"ts" : ("BTC_EUR.csv",),}, True, ["SOL_EUR.csv", "BTC_EUR.csv"]),
# ]

# COINS = {"BTC": "","SOL":""}


# @pytest.mark.parametrize(
#     "temp_test_env,run,check_files", scenarios, indirect=["temp_test_env"]
# )
# def test_scraping_without_coinbase(temp_test_env, run, check_files):
#     """
#     test scraping the only coins specified in config.
#     """
#     root = temp_test_env

#     c = Config(COINS, root / "data")
#     s = Scraper(c)
#     assert isinstance(s.config, Config)
#     if run:
#         s.run()
#         for file in check_files:
#             assert os.path.isfile(root / "data" / "ts" / file)
#             df = pd.read_csv(root / "data" / "ts" / file)
#             df["Date"] = pd.to_datetime(df["Date"])
#             if file == "BTC_EUR.csv":
#                 # check price is downloaded in EUR by checking known values
#                 assert (
#                     df.set_index("Date").loc["2021-12-31", "Close"] == 40712.7200439697
#                 )
#                 assert (
#                     df.set_index("Date").loc["2022-01-25,", "Close"]
#                     == 32693.35339746429
#                 )
#             # sorted
#             assert df["Date"].is_monotonic_increasing is True
#             # test no duplicates
#             assert any(df["Date"].duplicated()) is False
#             # test continuous index
#             assert len(
#                 pd.date_range(df["Date"].iat[0], df["Date"].iat[-1], freq="D")
#             ) == len(df)
#             # test last of df is last price available
#             assert df["Date"].iat[
#                 -1
#             ].date() == datetime.datetime.utcnow().date() + datetime.timedelta(-1)


# scenarios = [
#     # scrape data from config with the addtional coibase requirements
#     (
#         ("config.json", "coinbase_accounts.json"),
#         ["BTC.csv", "SOL.csv", "AAVE.csv"],
#     ),
#     (
#         (("config.json", "coinbase_accounts.json"), ("BTC.csv",)),
#         ["BTC.csv", "SOL.csv", "AAVE.csv"],
#     ),
# ]


# @pytest.mark.parametrize(
#     "temp_test_env,check_files", scenarios, indirect=["temp_test_env"]
# )
# def test_scraping_with_coinbase(temp_test_env, check_files):
#     """
#     test scraping when there is additional data required by the coinbase module.
#     """
#     root = temp_test_env

#     c = Config(COINS, str(root / "config"))
#     s = Scraper(c)
#     assert isinstance(s.config, Config)
#     s.run()
#     for file in check_files:
#         assert os.path.isfile(root / "data" / "ts" / file)
#         df = pd.read_csv(root / "data" / "ts" / file)
#         df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(pytz.utc)
#         # sorted
#         assert df["Date"].is_monotonic_increasing is True
#         # test no duplicates
#         assert any(df["Date"].duplicated()) is False
#         # test continuous index
#         assert len(
#             pd.date_range(df["Date"].iat[0], df["Date"].iat[-1], freq="D")
#         ) == len(df)
#         assert df["Date"].iat[-1] == pd.Timestamp(c.scraping_req[file[:-4]]["end_day"])
