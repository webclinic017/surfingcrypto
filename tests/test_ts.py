"""
test ts class
"""
import pytest 

from surfingcrypto.ts import TS 
from surfingcrypto.config import config


@pytest.mark.parametrize(
    "temp_test_env",
    [("config.json",)],
    indirect=["temp_test_env"]
    )
def test_failed_load_data(temp_test_env):
    root=temp_test_env
    c=config(str(root/"config"))
    with pytest.raises(FileNotFoundError):
        assert TS(c,coin="BTC")
