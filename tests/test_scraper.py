"""
test scraper module.
"""
import datetime
import pytest
import pandas as pd
import os

from surfingcrypto.scraper import Scraper 
from surfingcrypto.config import config

# @pytest.mark.parametrize(
#     'temp_config',
#     [("config.json","BTC.csv"),],
#     indirect=True
#     )
def test():
    pass

scenarios=[
    (("config.json",),False,()),
    (("config.json",),True,()),
    (("config.json",),True,("BTC.csv",))
]


@pytest.mark.parametrize(
    "temp_config,run,temp_data",
    scenarios,
    indirect=["temp_config","temp_data"]
    )
def test_overall_run(temp_config,run,temp_data):
    root=temp_config
    temp_data
    c=config(str(root/"config"))
    s=Scraper(c)
    assert isinstance(s.config,config)
    if run:
        s.run()
        assert os.path.isfile(root/"data"/"ts"/"BTC.csv")
        df=pd.read_csv(root/"data"/"ts"/"BTC.csv")
        df["Date"]=pd.to_datetime(df["Date"])
        assert not any(df["Date"].duplicated())
        assert df["Date"].iat[-1].date()==datetime.date.today()+datetime.timedelta(-1)
