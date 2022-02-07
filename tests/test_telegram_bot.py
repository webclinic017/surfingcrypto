"""
test telegram bot
"""
import pytest
import asyncio
import telegram
from telethon import TelegramClient
from telethon.errors import EmailUnconfirmedError
import decouple
import pandas as pd
import pytest_asyncio
import random,string

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
PASSWORD=decouple.config("TELEGRAM_2FA_PASSWORD")

@pytest.fixture
async def telegram_user():
    async def init():
        client=TelegramClient('anon', API_ID, API_HASH)
        await client.connect() 
        await client.sign_in(password=PASSWORD)
        return client
    return await init()

@pytest.mark.wip
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "temp_test_env", [("config_telegram.json",)], indirect=["temp_test_env"]
)
async def test_init_testbot_getting_test_updates(temp_test_env,telegram_user):
    """send unique text to bot and process updates correctly"""
    root = temp_test_env
    c = Config(str(root / "config"))
    client=telegram_user

    # This part is IMPORTANT, because it fills the entity cache.
    dialogs = await client.get_dialogs()
    entity=await client.get_entity('surfingcrypto_test_bot')

    await client.send_message(entity=entity,message="/start")

    unique_test_message=''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
    await client.send_message(entity=entity,message=unique_test_message)

    t = Tg_notifications(c)
    assert len(t.updates) > 0
    assert unique_test_message in t.updates["message"].tolist()

@pytest.mark.wip
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "temp_test_env", [("config_telegram.json",)], indirect=["temp_test_env"]
)
async def test_send_message(temp_test_env,telegram_user):
    """send unique text to bot and process updates correctly"""
    root = temp_test_env
    c = Config(str(root / "config"))
    client=telegram_user
    t = Tg_notifications(c)
    dialogs = await client.get_dialogs()
    entity=await client.get_entity('surfingcrypto_test_bot')
    print(entity.chat_id)




