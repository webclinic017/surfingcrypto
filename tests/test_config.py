"""
test config class.
"""
import pytest
from unittest.mock import patch
import os

from surfingcrypto.config import config

@pytest.mark.parametrize("scrap_req",[(dict,dict)])
@pytest.mark.parametrize('cb_req',[(type(None),dict)])
@pytest.mark.parametrize(
    'temp_test_env',
    [("config.json",),("config.json","coinbase_accounts.json")],
    indirect=True
    )
def test_init_with_datafolder(
    temp_test_env,
    cb_req,
    scrap_req
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
    assert isinstance(c.coinbase_req,cb_req)
    print(c.coinbase_req)
    assert isinstance(c.scraping_req,scrap_req)

@pytest.mark.parametrize("scrap_req",[(dict,dict)])
@pytest.mark.parametrize('cb_req',[(type(None),dict)])
@pytest.mark.parametrize(
    'temp_test_env',
    [("config.json",),("config.json","coinbase_accounts.json")],
    indirect=True
    )
def test_init_without_datafolder(
    temp_test_env,
    cb_req,
    scrap_req
    ):
    """
    test initialization of config class without specifying a data folder
    """
    tmp=temp_test_env
    c=config(str(tmp/"config"))
    assert hasattr(c,"coins")
    assert isinstance(c.data_folder,str)
    assert os.path.isdir(tmp/"data"/"ts")
    assert isinstance(c.coinbase_req,cb_req)
    assert isinstance(c.scraping_req,scrap_req)
