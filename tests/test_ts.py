"""
test ts class
"""
import unittest
import pytest 
import pandas as pd

from surfingcrypto.ts import TS 
from surfingcrypto.config import config

@pytest.mark.skip
@pytest.mark.usefixtures("test_environment")
class TestTS(unittest.TestCase):

    def setUp(self):
        parent=str(self.test_env / "config")
        self.c=config(parent)
        self.ts=TS(configuration=self.c,coin="BTC")

    def test_ts_init(self):
        self.assertEqual(self.ts.coin,"BTC")

    def test_ts_df(self):
        self.assertIsInstance(self.ts.df,pd.DataFrame)
    
    def test_ta_params(self):
        self.assertEqual(self.ts.config.ts_params["sma"]["fast"],12)
        self.assertEqual(self.ts.config.ts_params["sma"]["slow"],26)


if __name__ == '__main__':
    unittest.main()