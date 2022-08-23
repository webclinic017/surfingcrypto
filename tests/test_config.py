"""
test config class.
"""
import pytest
import os
import datetime

from surfingcrypto import Config

COINS = {"BTC": "", "ETH": ""}

def test_init_without_datafolder(temp_test_env):
    """
    test initialization of config class without specifying a data folder
    """
    root = temp_test_env
    c = Config(COINS, root / "data")
    assert hasattr(c, "coins")
    assert os.path.isdir(root / "data" / "ts")
    assert os.path.isdir(root / "data" / "temp")
    assert "BTC" in c.scraping_req.keys()

def test_empty_folder(temp_test_env):
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
