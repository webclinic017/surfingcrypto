"""
test scraper module.
"""
import datetime
import pytest
import pandas as pd
import os

from surfingcrypto.scraper import Scraper 
from surfingcrypto.config import config

scenarios=[
    (("config.json",),False,),
    (("config.json",),True,),
    ((("config.json",),("BTC.csv",)),True,)
]

@pytest.mark.wip
@pytest.mark.parametrize(
    "temp_test_env,run",
    scenarios,
    indirect=["temp_test_env"]
    )
def test_overall_run(temp_test_env,run):
    root=temp_test_env
    
    c=config(str(root/"config"))
    s=Scraper(c)
    assert isinstance(s.config,config)
    if run:
        s.run()
        assert os.path.isfile(root/"data"/"ts"/"BTC.csv")
        df=pd.read_csv(root/"data"/"ts"/"BTC.csv")
        df["Date"]=pd.to_datetime(df["Date"])
        assert any(df["Date"].duplicated()) is False
        assert df["Date"].iat[-1].date()== datetime.datetime.utcnow().date()+datetime.timedelta(-1)
