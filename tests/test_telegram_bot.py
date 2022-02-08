"""
test telegram bot
"""
import pytest
import asyncio
import pytest_asyncio
import telegram
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import decouple
import pandas as pd
import random, string

from surfingcrypto.telegram_bot import Tg_notifications
from surfingcrypto import Config

API_ID = decouple.config("TELEGRAM_API_ID")
API_HASH = decouple.config("TELEGRAM_API_HASH")
PASSWORD = decouple.config("TELEGRAM_2FA_PASSWORD")
STRINGSESSION = decouple.config("TELETHON_STRINGSESSION")
USER_ID = decouple.config("TELEGRAM_USER_ID")


@pytest.fixture
async def telegram_user(request):
    """user to interact with bot programmatically"""
    client = TelegramClient(StringSession(STRINGSESSION), API_ID, API_HASH)

    async def init():
        await client.connect()
        return client

    yield await init()

    def finalizer():
        client.disconnect()

    request.addfinalizer(finalizer)


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
    assert isinstance(t.bot, telegram.Bot)
    isinstance(t.updates, pd.DataFrame)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "temp_test_env", [("config_telegram.json",)], indirect=["temp_test_env"]
)
async def test_init_testbot_and_get_updates(temp_test_env, telegram_user):
    """send unique text to bot and process updates correctly"""
    root = temp_test_env
    c = Config(str(root / "config"))
    # fixture
    client = telegram_user

    # it fills the entity cache.
    dialogs = await client.get_dialogs()
    entity = await client.get_entity("surfingcrypto_test_bot")

    unique_test_message = "".join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(10)
    )
    await client.send_message(entity=entity, message=unique_test_message)

    t = Tg_notifications(c)
    assert len(t.updates) > 0
    assert unique_test_message in t.updates["message"].tolist()

@pytest.mark.wip
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "temp_test_env", [("config_telegram.json","logo.jpg")], indirect=["temp_test_env"]
)
async def test_send_message_and_photo(temp_test_env, telegram_user):
    """send unique text to bot and process updates correctly"""
    root = temp_test_env
    c = Config(str(root / "config"))
    client = telegram_user
    t = Tg_notifications(c)

    # fetch id of user interacting with bot
    async for dialog in client.iter_dialogs():
        if dialog.name == "surfingcrypto_testbot":
            entity = dialog.entity
            # chat_id = dialog.message.from_id.user_id #randomdly resitutes attribute error
            break

    unique_test_message = "".join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(10)
    )
    t.send_message(unique_test_message, USER_ID)
    #it was the easieast to store it there given fixture
    t.send_photo(str(root/"config"/"logo.jpg"),USER_ID)

    i=0
    async for message in client.iter_messages(entity):
        if i==0 and message.media is not None:
            photo= True
        if str(message.raw_text) == unique_test_message:
            message = True
        i=+1
        
    assert photo is True
    assert photo is True


@pytest.mark.wip
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "temp_test_env", [("config_telegram.json",)], indirect=["temp_test_env"]
)
async def test_fail_send_message(temp_test_env, telegram_user):
    """send unique text to bot and process updates correctly"""
    root = temp_test_env
    c = Config(str(root / "config"))
    client = telegram_user
    t = Tg_notifications(c)
    assert len(t.error_log)==0
    t.send_message("FAILED MESSAGE", 0000000)
    assert isinstance(t.error_log[0],dict)

@pytest.mark.wip
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "temp_test_env", [("config_telegram.json",)], indirect=["temp_test_env"]
)
async def test_fail_send_photo(temp_test_env, telegram_user):
    """send unique text to bot and process updates correctly"""
    root = temp_test_env
    c = Config(str(root / "config"))
    client = telegram_user
    t = Tg_notifications(c)
    assert len(t.error_log)==0
    t.send_photo(str(root/"config"/"logo.jpg"), 0000000)
    assert isinstance(t.error_log[0],dict)

