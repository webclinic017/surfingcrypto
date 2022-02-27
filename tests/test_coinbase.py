import unittest 
from surfingcrypto.portfolio import MyCoinbase 
from surfingcrypto.portfolio.coinbase import CB 

from surfingcrypto import Config
from coinbase.wallet.client import Client
import pytest
## ?!? disable  unittest/suite.py:107: ResourceWarning: unclosed <ssl.SSLSocket 
@pytest.mark.skip
class TestCB(unittest.TestCase):

    def setUp(self):
        parent="/Users/giorgiocaizzi/Documents/GitHub/surfingcrypto/"
        configuration=Config(parent+"config",parent+"data")
        self.userid="c5a7488f-1fe7-5259-8f61-39bd873e1699"
        self.cb=CB(configuration)

    def test_loading_client(self):
        self.assertIsInstance(self.cb.client,Client)
    
    def test_loading_user(self):
        self.assertEqual(self.cb.user["id"],self.userid)  

    def test_get_accounts(self):
        self.assertIsInstance(self.cb.get_accounts(),list) 

    def test_get_transactions(self):
        accounts=self.cb.get_accounts()
        transactions=self.cb.get_transactions(accounts[0])
        self.assertIsInstance(transactions,list)

    def test_get_active_accounts(self):
        self.assertIsInstance(self.cb.get_active_accounts(),list)
        self.assertGreater(len(self.cb.get_active_accounts()),0)

    #takes forever
    def test_get_all_accounts_with_transactions(self):
        accounts=self.cb.get_all_accounts_with_transactions()
        self.assertIsInstance(
            accounts,
            tuple
        )
        pass

if __name__ == '__main__':
    unittest.main()