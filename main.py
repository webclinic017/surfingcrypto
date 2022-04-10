"""
script to be run on ec2 istance
"""
import datetime as dt
from pathlib import Path


from TelegramBotNotifications import TelegramBot

from surfingcrypto import Config, TS
from surfingcrypto.scraper import Scraper
from surfingcrypto.reporting.reporting import report_percentage_diff
from surfingcrypto.reporting.figures import ATHPlot, TaPlot
from surfingcrypto.portfolio import Portfolio


cwd = Path(__file__).resolve().parent

# time of execution
now = dt.datetime.today()
timestr = now.strftime("%Y%m%d-%H%M%S")

# config
c = Config(str(cwd) + "/config")

# coinbase portfolio
p = Portfolio("coinbase",configuration=c)

# update config for coins that are not specified in config
c.add_coins(p.coinbase.active_accounts)

# telegram bot in channel mode
tg = TelegramBot(c.telegram["token"], channel_mode=True,users_path=str(cwd) + "/config/telegram_users.csv")

# scrape required data
print("### Scraper")
s = Scraper(c)
s.run()
tg.send_message_to_all(
    message=s.output_description
)  # send scraper log to telegram


coins_to_plot = [x for x in set(p.coinbase.active_accounts+list(c.coins.keys())) if x!="USDC"]

# produce reports for each coin in configuration
for coin in coins_to_plot:
    # daily TA plots
    ts = TS(c, coin=coin)
    fig = TaPlot(trendlines=False, ts=ts, graphstart="6m")
    tmpname = c.temp_folder + "/" + coin + "_" + timestr + ".jpeg"
    fig.save(tmpname)
    tg.send_message_to_all(report_percentage_diff(ts.df,ts.coin))
    tg.send_photo_to_all(tmpname)

    # ATH(BTC) plot every monday
    if coin == "BTC" and now.weekday() == 0:
        ath = ATHPlot(ts, graphstart="1-1-2020")
        tmpname = c.temp_folder + "/" + coin + "_ATH_" + timestr + ".jpeg"
        ath.save(tmpname)
        tg.send_photo_to_all(tmpname)


tg.send_message_to_user(p.coinbase.live_value_report(), "admin")
