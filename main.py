"""
script to be run on ec2 istance
"""
import time
from surfingcrypto import Config,TS
from surfingcrypto.scraper import Scraper
from surfingcrypto.reporting.figures import CoinFigure
from surfingcrypto.telegram_bot import Tg_notifications

parent = "/home/ec2-user/surfingcrypto/" #to be used on ec2
# parent = "./" #to be used when local
#time of execution
timestr = time.strftime("%Y%m%d-%H%M%S")

c = Config(parent + "config")

telegram = True
if telegram:
    tg = Tg_notifications(c, channel_mode=True)

update = True
if update:
    s = Scraper(c)
    s.run()
    tg.send_message_to_all(message=s.output_description)

for coin in c.coins:
    ts=TS(c,coin=coin)
    fig = CoinFigure(
        ts,
        kind="ta",
        trendlines=False,
        coin=coin,
        graphstart="3m",
    )
    fig.save(c.temp_folder+"/"+coin+"_"+timestr+".jpeg")
    tg.send_message_to_all(ts.report_percentage_diff())
    tg.send_photo_to_all(c.temp_folder+"/"+coin+"_"+timestr+".jpeg")
