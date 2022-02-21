"""
script to be run on ec2 istance
"""
import time
from pathlib import Path

from surfingcrypto import Config,TS
from surfingcrypto.scraper import Scraper
from surfingcrypto.reporting.figures import TaPlot
from surfingcrypto.telegram_bot import Tg_notifications


cwd = Path(__file__).resolve().parent 

#time of execution
timestr = time.strftime("%Y%m%d-%H%M%S")

c = Config(cwd + "config")

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
    fig = TaPlot(
        trendlines=False,
        ts=ts,
        graphstart="3m"
    )
    tmpname=c.temp_folder+"/"+coin+"_"+timestr+".jpeg"
    fig.save(tmpname)
    tg.send_message_to_all(ts.report_percentage_diff())
    tg.send_photo_to_all(tmpname)
