'''test reporting module'''

import pytest
import pandas as pd

from surfingcrypto.reporting.reporting import percentage_diff


@pytest.mark.wip
def test_percentage_diff():
    df=pd.read_csv("tests/fixtures/BTC_EUR.csv")
    assert percentage_diff(df, window=1) == (41659.188229395666 - 40925.54103342952)