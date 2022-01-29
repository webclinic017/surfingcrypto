import backtrader as bt

from surfingcrypto.ts import TS
from surfingcrypto.strategies import SmaCross,TestStrategy
from surfingcrypto.config import config

parent="/Users/giorgiocaizzi/Documents/GitHub/surfingcrypto/"
configuration=config(parent+"config",parent+"data")

cerebro = bt.Cerebro()  # create a "Cerebro" engine instance

# Create a data feed
ts=TS(configuration,coin="MATIC")
print(ts.df.loc["1-1-2021"])
data = bt.feeds.PandasData(dataname=ts.df.loc["1-1-2021":])# Add the data feed
cerebro.adddata(data)

cerebro.addstrategy(SmaCross)  # Add the trading strategy
cerebro.broker.setcash(10000.0)
print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
cerebro.run()  # run it all
print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
cerebro.plot()  # and plot it with a single command
