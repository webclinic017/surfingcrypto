import unittest 
from surfingcrypto.portfolio.portfolio_tracker import Tracker 
from surfingcrypto import Config
import pytest
import pandas as pd
@pytest.mark.skip
class TestTracker(unittest.TestCase):

    def setUp(self):
        parent="/Users/giorgiocaizzi/Documents/GitHub/surfingcrypto/"
        configuration=Config(parent+"config",parent+"data")

        portfolio_df = pd.read_csv('temp/std_df.csv')
        print(portfolio_df)
        self.portfolio_df = portfolio_df.rename(
            {
                "datetime":"Open date",
                "type":"Type",
                "symbol":"Symbol",
                "amount":"Qty",
                "spot_price":"Adj cost per share",
                "native_amount":"Adj cost"
            },
            axis=1
        )
        self.portfolio_df.drop("trade_id",axis=1,inplace=True)

        self.portfolio_df['Open date'] = pd.to_datetime(self.portfolio_df['Open date'])
        self.t=Tracker(self.portfolio_df,configuration=configuration)
        return 
    
    def test_init(self):
        self.assertIsInstance(self.t.portfolio_df,pd.DataFrame)



if __name__ == '__main__':
    unittest.main()