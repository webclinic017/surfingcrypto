import unittest 
from surfingcrypto.telegram_bot import Tg_notifications 
from surfingcrypto.config import config
import pandas as pd
import time
import pytest

@pytest.mark.skip
class TestTelegramBot(unittest.TestCase):

    def setUp(self):
        parent="/Users/giorgiocaizzi/Documents/GitHub/surfingcrypto/"
        self.c=config(parent+"config",parent+"data")
        self.tg=Tg_notifications(self.c)
    
    def test_loading_config(self):
        self.assertIsInstance(self.tg.token,str)

    def test_mode(self):
        self.assertIs(self.tg.channel_mode,False)
    

@pytest.mark.skip
class TestTelegramBotChannelMode(unittest.TestCase):

    def setUp(self):
        parent="/Users/giorgiocaizzi/Documents/GitHub/surfingcrypto/"
        self.c=config(parent+"config",parent+"data")
        self.tg=Tg_notifications(self.c,channel_mode=True)
    
    def test_loading_config(self):
        self.assertIsInstance(self.tg.token,str) 

    def test_mode(self):
        self.assertIs(self.tg.channel_mode,True)   

    def test_loading_users(self):
        self.assertIsInstance(self.tg.users,pd.DataFrame)  


if __name__ == '__main__':
    unittest.main()