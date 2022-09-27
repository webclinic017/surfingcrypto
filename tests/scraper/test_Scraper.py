"""
test Scraper Class.
"""
import pytest
import pandas as pd
from pandas.testing import assert_frame_equal

import os
from unittest.mock import patch

from surfingcrypto.config import Config
from surfingcrypto.scraper import UpdateHandler, Scraper

COINS = {"BTC": "", "ETH": ""}


def test_Scraper(temp_test_env):
    """
    test basic Scraper with full download of data
    """
    root = temp_test_env
    c = Config(COINS, root / "data")
    s = Scraper(
        c,
    )
    s.run()
    assert isinstance(s.runs, list)
    for run in s.runs:
        assert isinstance(run, UpdateHandler)
    print(s.runs)
    print(type(s.runs[0].left))
    print(type(s.runs[0].right))
    assert os.path.isfile(root / "data" / "ts" / "BTC_EUR.csv")
    assert os.path.isfile(root / "data" / "ts" / "ETH_EUR.csv")


@pytest.mark.parametrize(
    "error,output",
    [
        (None, True),
        ("str", False),
    ],
)
@patch("surfingcrypto.scraper.UpdateHandler", autospec=True)
def test_Scraper_output(mock, error, output, temp_test_env):
    """
    test Scraper output when no errors and when there is
    """
    mock.return_value.error = error

    root = temp_test_env
    c = Config(COINS, root / "data")
    s = Scraper(
        c,
    )
    s.run()
    print(s.runs)
    assert len(s.runs) == 2
    assert s.output == output


@pytest.mark.skip
@patch("surfingcrypto.scraper.UpdateHandler", autospec=True)
def test_Scraper_output_mixed(mock, temp_test_env):
    """
    test output verbose when partly failed.
    """
    ## cant do this, having a different value each time
    mock.return_value.error = [None, "str"]

    root = temp_test_env
    c = Config(COINS, root / "data")
    s = Scraper(
        c,
    )
    s.run()
    print(s.runs)
    assert len(s.runs) == 2
    assert s.output == False
    assert s.output_verbose == ("Update failed." f" There are (1/2) errors.")
