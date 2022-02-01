"""
test config class.
"""
import pytest
import os
import datetime

from surfingcrypto import Config

scenarios = [
    (("config.json",), dict, type(None)),
    (("config.json", "coinbase_accounts.json"), dict, dict),
]


@pytest.mark.parametrize(
    "temp_test_env,scrp_req,cb_req", scenarios, indirect=["temp_test_env"]
)
def test_init_with_datafolder(temp_test_env, scrp_req, cb_req):
    """
    test initialization of config class without specifying a data folder
    """
    root = temp_test_env
    os.mkdir(root / "data")
    c = Config(str(root / "config"), str(root / "data"))
    assert hasattr(c, "coins")
    assert isinstance(c.data_folder, str)
    assert os.path.isdir(root / "data" / "ts")
    assert os.path.isdir(root / "data"/"temp")
    print(scrp_req, cb_req)
    assert isinstance(c.scraping_req, scrp_req)
    assert "BTC" in c.scraping_req.keys()
    assert isinstance(c.coinbase_req, cb_req)
    if isinstance(cb_req, dict):
        assert "SOL" in c.coinbase_req.keys()
        assert isinstance(c.coinbase_req["start"], datetime)
        assert isinstance(c.coinbase_req["end_day"], datetime)
        assert c.coinbase_req["end_day"] > c.coinbase_req["start"]


@pytest.mark.parametrize(
    "temp_test_env,scrp_req,cb_req", scenarios, indirect=["temp_test_env"]
)
def test_init_with_datafolder(temp_test_env, scrp_req, cb_req):
    """
    test initialization of config class without specifying a data folder
    """
    root = temp_test_env
    c = Config(str(root / "config"))
    assert hasattr(c, "coins")
    assert isinstance(c.data_folder, str)
    assert os.path.isdir(root / "data" / "ts")
    assert os.path.isdir(root / "data"/"temp")
    print(scrp_req, cb_req)
    assert isinstance(c.scraping_req, scrp_req)
    assert "BTC" in c.scraping_req.keys()
    assert isinstance(c.coinbase_req, cb_req)
    if isinstance(cb_req, dict):
        assert "SOL" in c.coinbase_req.keys()
        assert isinstance(c.coinbase_req["start"], datetime)
        assert isinstance(c.coinbase_req["end_day"], datetime)
        assert c.coinbase_req["end_day"] > c.coinbase_req["start"]


@pytest.mark.parametrize("temp_test_env", [()], indirect=["temp_test_env"])
def test_fail_init(temp_test_env):
    root = temp_test_env
    with pytest.raises(FileNotFoundError):
        c = Config(str(root / "config"))

@pytest.mark.parametrize(
    "temp_test_env", [("config.json",)], indirect=["temp_test_env"]
)
def test_temp_folder(temp_test_env):
    root = temp_test_env
    #first run to create folder struct
    c = Config(str(root / "config"))
    #create file
    with open(root/"data"/"temp"/"test.txt","wb") as f:
        f.close()
    #calling again the init should empty the temp dir
    c = Config(str(root / "config"))
    #directory exits
    assert os.path.isdir(root / "data"/"temp")
    #but all temp files from previous run are removed with init
    assert not os.listdir(root / "data"/"temp")

