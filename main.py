"""
script to be run on ec2 istance
"""
import datetime as dt
from pathlib import Path

from surfingcrypto import Config, TS
from surfingcrypto.scraper import Scraper
from surfingcrypto.reporting.figures import ATHPlot, TaPlot
from surfingcrypto.telegram_bot import Tg_notifications
from surfingcrypto.portfolio import MyCoinbase


cwd = Path(__file__).resolve().parent

# time of execution
now = dt.datetime.today()
timestr = now.strftime("%Y%m%d-%H%M%S")

# config
c = Config(str(cwd)+"/config")

# telegram bot in channel mode
tg = Tg_notifications(c, channel_mode=True)

# scrape required data
s = Scraper(c)
s.run()
tg.send_message_to_all(message=s.output_description)  # send scraper log to telegram

# produce reports for each coin in configuration
for coin in c.coins:
    # daily TA plots
    ts = TS(c, coin=coin)
    fig = TaPlot(trendlines=False, ts=ts, graphstart="3m")
    tmpname = c.temp_folder + "/" + coin + "_" + timestr + ".jpeg"
    fig.save(tmpname)
    tg.send_message_to_all(ts.report_percentage_diff())
    tg.send_photo_to_all(tmpname)

    # ATH(BTC) plot every monday
    if coin == "BTC" and now.weekday() == 0:
        ath = ATHPlot(ts, graphstart="1-1-2020")
        tmpname = c.temp_folder + "/" + coin + "_ATH_" + timestr + ".jpeg"
        ath.save(tmpname)
        tg.send_photo_to_all(tmpname)

cb=MyCoinbase(configuration=c)
tg.send_message_to_user(cb.mycoinbase_report(),"admin")