from surfingcrypto import Config,TS
from surfingcrypto.scraper import Scraper
from surfingcrypto.reporting.figures import CoinFigure
from surfingcrypto.telegram_bot import Tg_notifications

# parent = "/home/ec2-user/surfingcrypto/" #to be used on ec2
parent = "./" #to be used when local

c = Config(parent + "config")

telegram = True
if telegram:
    tg = Tg_notifications(c, channel_mode=True)

update = True
if update:
    s = Scraper(c)
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
    tg.send_message_to_all(fig.report_percentage_diff())
    tg.send_coinfig(figure=fig.f, to="all")
