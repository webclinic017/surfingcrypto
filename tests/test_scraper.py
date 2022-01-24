"""
test scraper module.
"""
import pytest
import pandas as pd
import os

from surfingcrypto.scraper import Scraper 
from surfingcrypto.config import config

@pytest.mark.parametrize('check_file',[False,True])
@pytest.mark.parametrize(
    'temp_test_env',
    [("config.json",),],
    indirect=True
    )
@pytest.mark.wip
def test_load_config(
    temp_test_env,
    check_file
    ):
    root=temp_test_env
    c=config(str(root/"config"))
    s=Scraper(c)
    assert isinstance(s.config,config)
    if check_file:
        s.run()
        assert os.path.isfile(root/"data"/"ts"/"BTC.csv")
