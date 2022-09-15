"""
test CMCUtility class.
"""
import datetime
import pandas as pd

from surfingcrypto.scraper import CMCutility

#######################################################################
#
#  cmc utility


def test_CMCutility_scrape_data():
    """test that scrape data returns the expected result

    dataframe
    newest to oldest order
    """
    cmc = CMCutility(
        "BTC",
        datetime.datetime(2021, 1, 1),
        datetime.datetime(2022, 1, 1),
        "EUR",
    )
    response = cmc.scrape_data()
    assert isinstance(response, pd.DataFrame)
    assert len(response) > 0
    # response is in descending order
    assert str(response["Date"].iloc[0]) == str(datetime.datetime(2022, 1, 1))
    assert str(response["Date"].iloc[-1]) == str(datetime.datetime(2021, 1, 1))


def test_CMCutility_str_repr_before_scraping():
    cmc = CMCutility(
        "BTC",
        datetime.datetime(2021, 1, 1),
        datetime.datetime(2022, 1, 1),
        "EUR",
    )
    expected = (
        "CmcScraper(BTC, left=01-01-2021, right=01-01-2022, response=None)"
    )
    assert str(cmc) == expected
    assert repr(cmc) == expected


def test_CMCutility_str_repr_with_good_response():
    cmc = CMCutility(
        "BTC",
        datetime.datetime(2021, 1, 1),
        datetime.datetime(2022, 1, 1),
        "EUR",
    )
    cmc.scrape_data()
    expected = (
        "CmcScraper(BTC, left=01-01-2021, right=01-01-2022, response=True)"
    )
    assert str(cmc) == expected
    assert repr(cmc) == expected


def test_CMCutility_str_repr_with_bad_response():
    """there are no data for this range"""
    cmc = CMCutility(
        "SOL",
        datetime.datetime(2017, 1, 1),
        datetime.datetime(2018, 1, 1),
        "EUR",
    )
    cmc.scrape_data()
    expected = (
        "CmcScraper(SOL, left=01-01-2017, right=01-01-2018, response=False)"
    )
    assert str(cmc) == expected
    assert repr(cmc) == expected