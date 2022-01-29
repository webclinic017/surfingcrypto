"""
test telegram bot
"""
import pandas as pd
import time
import pytest
from surfingcrypto.telegram_bot import Tg_notifications 
from surfingcrypto import config

@pytest.mark.parametrize(
    "temp_test_env",
    [("config.json",)],
    indirect=["temp_test_env"]
    )
def test_missing_configuration(temp_test_env):
    root=temp_test_env
    c=config(str(root/"config"))
    with pytest.raises(ValueError):
        assert Tg_notifications(c)