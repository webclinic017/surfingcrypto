"""
test scraper module.
"""
import pytest
import pandas as pd

from surfingcrypto.scraper import Scraper 
from surfingcrypto.config import config


@pytest.mark.skip
def test_load_config(temp_test_env):
    c=config(str(temp_test_env/"config"))
    s=Scraper(c)
    assert isinstance(s.config,config)
