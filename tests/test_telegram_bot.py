"""
test telegram bot
"""
import pytest
import asyncio
import telegram
from telethon import TelegramClient
import decouple
import pandas as pd
import pytest_asyncio

from surfingcrypto.telegram_bot import Tg_notifications
from surfingcrypto import Config


@pytest.mark.parametrize(
    "temp_test_env", [("config.json",)], indirect=["temp_test_env"]
)
def test_missing_configuration(temp_test_env):
    """test ValueError when no telegram is specified in config"""
    root = temp_test_env
    c = Config(str(root / "config"))
    with pytest.raises(ValueError):
        assert Tg_notifications(c)

@pytest.mark.parametrize(
    "temp_test_env", [("config_telegram.json",)], indirect=["temp_test_env"]
)
def test_init_testbot(temp_test_env):
    """initialize class with testbot"""
    root = temp_test_env
    c = Config(str(root / "config"))
    t = Tg_notifications(c)
    assert isinstance(t.configuration, Config)
    assert t.token == c.telegram["token"]
    assert t.channel_mode is False
    assert isinstance(t.bot,telegram.Bot)
    isinstance(t.updates,pd.DataFrame)


API_ID=decouple.config("TELEGRAM_API_ID")
API_HASH=decouple.config("TELEGRAM_API_HASH")

# client=TelegramClient('anon', API_ID, API_HASH)

# async def main():
#     await client.start()

# with client:
#     client.loop.run_until_complete(main())

@pytest.fixture
async def telegram_user():
    async def init():
        client=TelegramClient('anon', API_ID, API_HASH)
        await client.start()

        # This part is IMPORTANT, because it fills the entity cache.
        dialogs = await client.get_dialogs()

        destination_user_username='surfingcrypto_test_bot'
        entity=await client.get_entity(destination_user_username)
        await client.send_message(entity=entity,message="/start")
        await client.send_message(entity=entity,message="Ciao!")
    await init()

@pytest.mark.wip
@pytest_asyncio.fixture
@pytest.mark.parametrize(
    "temp_test_env", [("config_telegram.json",)], indirect=["temp_test_env"]
)
def test_init_testbot_channelmode(temp_test_env,telegram_user):
    """initialize class with testbot"""
    root = temp_test_env
    c = Config(str(root / "config"))
    telegram_user
    t = Tg_notifications(c)
    assert len(t.updates) > 0
    assert t.updates.loc[1,"message"]=="Ciao!"
    
    

