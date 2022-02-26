"""
telegram bot API wrapper
"""
import telegram
import os
import pandas as pd


class Tg_notifications:
    """
    Wrapper of official telegram API to send notifications from a BOT initiaed manually with @BotFather.

    Arguments:
        configuration (:obj:`surfingcrypto.config.config`) : package configuration object
        channel_mode (bool) : init class in channel_bot, send to all chat_id contained in telegram_users.csv
        new_users_check (bool):  check for new users and add new ones to telegram_users.csv
    
    Attributes:
        token (str): token of telegram bot
        users (:obj:`pandas.DataFrame`): dataframe containing usernames and chat_id of known users following the bot
        updates (:obj:`pandas.DataFrame`): dataframe containing all updates fetched from bot
        channel_mode (bool): channel_mode is active
    
    """

    def __init__(
        self, configuration, channel_mode=False, new_users_check=True,
    ):

        self.error_log = []

        if hasattr(configuration, "telegram"):

            self.configuration = configuration

            self.channel_mode = channel_mode
            self.token = self.configuration.telegram["token"]

            # init official bot
            self.bot = telegram.Bot(token=self.token)
            self.getUpdates()

            if self.channel_mode:
                if os.path.isfile(
                    self.configuration.config_folder + "/telegram_users.csv"
                ):
                    self.users = pd.read_csv(
                        self.configuration.config_folder + "/telegram_users.csv"
                    )
                    self.users["date_joined"] = pd.to_datetime(
                        self.users["date_joined"]
                    )
                    if new_users_check:
                        print("### TELEGRAM BOT")
                        print("# Checking new users")
                        self.new_users()
                else:
                    raise FileNotFoundError(
                        "config folder contain a csv file containing usernames and chat IDs."
                    )

        else:
            raise ValueError("config.json file must contain a telegram bot token.")

    def getUpdates(self):
        """
        get updates from bot
        """
        self.updates = []
        for update in self.bot.getUpdates(timeout=2):
            i = {}
            i["username"] = update.message.from_user.username
            i["date"] = update.message.date
            i["chat_id"] = update.message.chat_id
            i["message"] = update.message.text
            self.updates.append(i)
        self.updates = pd.DataFrame(self.updates)
        return self.updates

    def new_users(self):
        """
        check if unknown users have interacted with the telegram bot.
        If the new users are found, they are automatically added to known users csv files.
        """
        if len(self.updates) >= 1:
            updates = self.updates.set_index("chat_id")[
                ["username", "date"]
            ].drop_duplicates()

            new_users_mask = ~updates.index.isin(self.users["chat_id"])
            if any(new_users_mask):
                new_users = updates[new_users_mask].reset_index()
                new_users.rename({"date": "date_joined"}, axis=1, inplace=True)
                self.users = self.users.append(new_users, ignore_index=True)
                self.users.sort_index(inplace=True)
                self.users.to_csv(
                    self.configuration.config_folder + "/telegram_users.csv",
                    index=False,
                )
                print("Users successfully added!")
            else:
                print("No new users.")
        else:
            print("No updates.")

    def send_message_to_all(self, message):
        """
        send message to all known users
        
        Arguments:
            message (str): string containing message to send
        """
        if self.channel_mode:
            for chat_id in self.users["chat_id"].tolist():
                self.send_message(message=message, chat_id=chat_id)
        else:
            raise ValueError("This method is available only in channel mode.")

    def send_message(
        self, message, chat_id,
    ):
        """
        send message to a specific user

        Arguments:
            message (str): string containing message to send
            chat_id (int): chat_id code of chat to send the message to
        """
        try:
            self.bot.sendMessage(chat_id=chat_id, text=message)
        except Exception as e:
            print("SendMessageError")
            self.error_log.append({"error": "SendMessageError", "e": e})

    def send_doc(self, document, chat_id, caption=""):
        """
        send document.
        """
        with open(document, "rb") as d:
            self.bot.send_document(chat_id=chat_id, document=d, caption=caption)

    def send_photo_to_all(self, photo):
        """
        send message to all known users
        
        Arguments:
            photo (str): string path to photo
        """
        if self.channel_mode:
            for chat_id in self.users["chat_id"].tolist():
                self.send_photo(photo=photo, chat_id=chat_id)
        else:
            raise ValueError("This method is available only in channel mode.")

    def send_photo(self, photo, chat_id, caption=""):
        """
        send photo.
    
        Arguments:
            photo (str): string path to photo
            chat_id (int): chat_id code of chat to send the message to

        """
        try:
            with open(photo, "rb") as p:
                self.bot.send_photo(chat_id=chat_id, photo=p, caption=caption)
        except Exception as e:
            print("SendPhotoError")
            self.error_log.append({"error": "SendPhotoError", "e": e})

