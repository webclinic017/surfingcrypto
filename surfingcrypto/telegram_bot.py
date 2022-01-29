from bob_telegram_tools.bot import TelegramBot
import matplotlib
import matplotlib.pyplot as plt
from numpy import matmul
import telegram
import json
import os
import pandas as pd
from telegram import message
from telegram import update
from surfingcrypto.config import config

class Tg_notifications:
    """
    Wrapper of official telegram API to send notifications from a BOT initiaed manually with @BotFather.

    Arguments:
		configuration (:obj:`surfingcrypto.config.config`) : package configuration object
        channel_mode (bool) : init class in channel_bot, send to all chat_id contained in telegram_users.csv
        get_updates (bool) : get all updates from bot
        new_users_check (bool):  check for new users and add new ones to telegram_users.csv
    
    Attributes:
        token (str): token of telegram bot
        users (:obj:`pandas.DataFrame`): dataframe containing usernames and chat_id of known users following the bot
        updates (:obj:`pandas.DataFrame`): dataframe containing all updates fetched from bot
        channel_mode (bool): channel_mode is active
    
    """

    def __init__(self,
        configuration,
        channel_mode=False,
        get_updates=True,
        new_users_check=True,
        ):

        self.error_log=[]

        if hasattr(configuration,"telegram"):
            
            self.configuration=configuration

            self.channel_mode=channel_mode
            self.token = self.configuration.config["telegram"]["token"]
            
            #init official bot
            self.bot=telegram.Bot(token=self.token)

            if self.channel_mode:
                if os.path.isfile(self.configuration.config_folder+"/telegram_users.csv"):
                    self.users=pd.read_csv(self.configuration.config_folder+"/telegram_users.csv")
                    self.users["date_joined"]=pd.to_datetime(self.users["date_joined"])
                    if get_updates:
                        #get updates
                        self.getUpdates()
                        if new_users_check:
                            print("### TELEGRAM BOT")
                            print("# Checking new users")
                            self.new_users()
                else:
                    raise FileNotFoundError("config folder contain a csv file containing usernames and chat IDs.")        
            
        else:
            raise ValueError("config.json file must contain a telegram bot token.")

    def getUpdates(self):
        """
        get updates from bot
        """
        self.updates=[]
        for update in self.bot.getUpdates(timeout=2):
            i={}
            i["username"]=update.message.from_user.username
            i["date"]=update.message.date
            i["chat_id"]=update.message.chat_id
            i["message"]=update.message.text
            self.updates.append(i)
        self.updates=pd.DataFrame(self.updates)
        return self.updates

    def new_users(self):
        """
        check if unknown users have interacted with the telegram bot.
        If the new users are found, they are automatically added to known users csv files.
        """
        if hasattr(self,"updates"):
            if len(self.updates)>=1:
                updates=self.updates.set_index("chat_id")[["username","date"]].drop_duplicates()
                
                new_users_mask=~updates.index.isin(self.users["chat_id"])
                if any(new_users_mask):
                    new_users=updates[new_users_mask].reset_index()
                    new_users.rename({"date":"date_joined"},axis=1,inplace=True)
                    self.users=self.users.append(new_users,ignore_index=True)
                    self.users.sort_index(inplace=True)
                    self.users.to_csv(self.configuration.config_folder+"/telegram_users.csv",index=False)
                    print("Users successfully added!")
                else:
                    print("No new users.")
            else:
                print("No updates.")
        # else:
        #     raise ValueError("get updates first!")
    
    def send_message_to_all(self,message):
        """
        send message to all known users
        
        Arguments:
            message (str): string containing message to send
        """
        if self.channel_mode:
            for chat_id in self.users["chat_id"].tolist():
                self.send_message(message=message,chat_id=chat_id)
        else:
            raise ValueError("This method is available only in channel mode.")

    def send_message(self,message,chat_id,):
        """
        send message to a specific user

        Arguments:
            chat_id (int): chat_id code of chat to send the message to
            message (str): string containing message to send
        """
        try:
            self.bot.sendMessage(chat_id=chat_id, text=message)
        except Exception as e:
            print("SendMessageError")
            self.error_log.append({

                "error":"SendMessageError",
                "e":e
            })


    def send_doc(self,document,caption,chat_id,):
        with open(document,"rb") as d:
            self.bot.send_document(chat_id=chat_id,document=d,caption=caption)

    #### eliminabile (se vedi come fa capisci e si può replicare)
    def send_plot_to_all(self,figure):
        """
        send plot to all known users

        Arguments:
            figure (:class:`matplotlib.figure.Figure`): matplotlib figure object to send
        
        """
        if self.channel_mode: 
            for chat_id in self.users["chat_id"].tolist():
                self.bob_bot=TelegramBot(token=self.token,user_ids=chat_id)
                self.bob_bot.send_plot(figure)
        else:
            raise ValueError("This method is available only in channel mode.")

    def send_plot(self,figure,chat_id):
        """
        send plot to specific user

        Arguments:
            chat_id (int): chat_id code of chat to send the plot to
            figure (:class:`matplotlib.figure.Figure`): matplotlib figure object to send
        
        """
        self.bob_bot=TelegramBot(token=self.token,user_ids=chat_id)
        self.bob_bot.send_plot(figure)
        self.bob_bot.clean_tmp_dir()
    ################################################################
    
    #specifico per coinfig
    def send_coinfig(self,figure=None,file=None,caption="",to="all"):
        """
        context handler to send figures from either matplotlib figure objects or local files
        """
        if file is None and figure is None:
            raise ValueError("Must specify either a Matplolib ax object or a path to a locally saved figure.")
        elif file is None and figure is not None:
            if to=="all":
                self.send_plot_to_all(figure)
            elif type(to) is int:
                self.send_plot(figure,chat_id=to)
            else:
                raise ValueError("Must be a string 'all' or an int ")
        else:
            if to=="all":
                raise ValueError("Not yet implemented")
            elif type(to) is int:
                self.send_doc(file,caption,chat_id=to)
            else:
                raise ValueError("Must be 'all' or an int representing chat_id")