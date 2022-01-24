"""
test config class.
"""
import pytest
from unittest.mock import patch
import os
import datetime

from surfingcrypto.config import config

scenarios=[
    (("config.json",),dict,type(None)),
    (("config.json","coinbase_accounts.json"),dict,dict),
]

@pytest.mark.parametrize(
    'temp_test_env,scrp_req,cb_req',
    scenarios,
    indirect=["temp_test_env"]
    )
def test_init_with_datafolder(
    temp_test_env,
    scrp_req,
    cb_req
    ):
    """
    test initialization of config class without specifying a data folder
    """
    tmp=temp_test_env
    os.mkdir(tmp/"data")
    c=config(str(tmp/"config"),str(tmp/"data"))
    assert hasattr(c,"coins")
    assert isinstance(c.data_folder,str)
    assert os.path.isdir(tmp/"data"/"ts")
    print(scrp_req,cb_req)
    assert isinstance(c.scraping_req,scrp_req)
    assert "BTC" in c.scraping_req.keys()
    assert isinstance(c.coinbase_req,cb_req)
    if isinstance(cb_req,dict):
        assert "SOL" in c.coinbase_req.keys()
        assert isinstance(c.coinbase_req["start"],datetime)
        assert isinstance(c.coinbase_req["end_day"],datetime)
        assert c.coinbase_req["end_day"] > c.coinbase_req["start"]

@pytest.mark.parametrize(
    'temp_test_env,scrp_req,cb_req',
    scenarios,
    indirect=["temp_test_env"]
    )
def test_init_with_datafolder(
    temp_test_env,
    scrp_req,
    cb_req
    ):
    """
    test initialization of config class without specifying a data folder
    """
    tmp=temp_test_env
    c=config(str(tmp/"config"))
    assert hasattr(c,"coins")
    assert isinstance(c.data_folder,str)
    assert os.path.isdir(tmp/"data"/"ts")
    print(scrp_req,cb_req)
    assert isinstance(c.scraping_req,scrp_req)
    assert "BTC" in c.scraping_req.keys()
    assert isinstance(c.coinbase_req,cb_req)
    if isinstance(cb_req,dict):
        assert "SOL" in c.coinbase_req.keys()
        assert isinstance(c.coinbase_req["start"],datetime)
        assert isinstance(c.coinbase_req["end_day"],datetime)
        assert c.coinbase_req["end_day"] > c.coinbase_req["start"]