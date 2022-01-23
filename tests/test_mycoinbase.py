import unittest 
from surfingcrypto.coinbase import MyCoinbase 
from surfingcrypto.config import config
import pytest
import pandas as pd
@pytest.mark.skip
class TestMyCoinbase_active_accounts(unittest.TestCase):

    def setUp(self):
        parent="/Users/giorgiocaizzi/Documents/GitHub/surfingcrypto/"
        configuration=config(parent+"config",parent+"data")
        self.my_c=MyCoinbase(configuration=configuration)
        return 
    
    def test_inehritance(self):
        self.assertIsInstance(self.my_c.user["id"],str)
    
    def test_history(self):
        self.assertRaises(
            ValueError,
            self.my_c.history
            )
@pytest.mark.skip
class TestMyCoinbase_historic_accounts(unittest.TestCase):

    def setUp(self):
        parent="/Users/giorgiocaizzi/Documents/GitHub/surfingcrypto/"
        configuration=config(parent+"config",parent+"data")
        self.my_c=MyCoinbase(
            configuration=configuration,
            active_accounts=False,
            from_dict=True
            )
        return 
    
    def test_inehritance(self):
        self.assertIsInstance(self.my_c.user["id"],str)
    
    def test_history(self):
        self.my_c.history()
        self.assertIsInstance(
            self.my_c.my_coinbase,
            pd.DataFrame
            )

if __name__ == '__main__':
    unittest.main()