"""
test telegram bot
"""
from debugpy import configure
import pandas as pd
import time
import pytest
from surfingcrypto.telegram_bot import Tg_notifications 
from surfingcrypto import Config

@pytest.mark.parametrize(
    "temp_test_env",
    [("config.json",)],
    indirect=["temp_test_env"]
    )
def test_missing_configuration(temp_test_env):
    """test ValueError when no telegram is specified in config"""
    root=temp_test_env
    c=Config(str(root/"config"))
    with pytest.raises(ValueError):
        assert Tg_notifications(c)

@pytest.mark.skip
@pytest.mark.parametrize(
    "temp_test_env",
    [("config_telegram.json",)],
    indirect=["temp_test_env"]
    )
def test_init_testbot(temp_test_env):
    """initialize class with testbot"""
    root=temp_test_env
    c=Config(str(root/"config"))
    t=Tg_notifications(c)
    assert isinstance(t.configuration,Config)
    assert t.token==c.telegram["token"]
    assert t.channel_mode is False