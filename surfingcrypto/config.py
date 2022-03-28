"""
package configuration
"""
import json
import os
import pathlib
import datetime, pytz
import dateutil


class Config:
    """
    Class for the package configuration.
    Contains API keys and user-specified parametrization of execution.

    Note:
        `data_folder` is optional. If not specified checks if there
        is a data directory in the parent directory.
        If not, it will be created.

    Arguments:
        config_folder (str): ABSOLUTE path to config folder.
        data_folder (str,optional) : ABSOLUTE path to data folder

    Attributes:
        coinbase (dict): coinbase user configuration
        coinbase_req (:obj:`dict` of :obj:`dict`) dictionary
            containing coinbase requirements
        coins (dict): coins user configuration
        config_folder (str): ABSOLUTE path to config folder.
        data_folder (str) : ABSOLUTE path to data folder
        error_log (:obj:`list`): list of errors
        rebrandings (dict): dictionary of known rebrandings
        scraping_req (:obj:`dict` of :obj:`dict`)
            dictionary containing scraping params
        telegram (dict): telegram user configuration
        temp_folder (str,optional) : ABSOLUTE path to data folder
    """

    def __init__(self, config_folder, data_folder=None):
        self.config_folder = config_folder
        self._set_attributes()
        self._set_data_folder(data_folder)
        self._temp_dir()

        self.rebrandings = {"CGLD": "CELO"}

        # ERROR LOG
        self.error_log = []
        # DATA REQUIREMENTS
        self._set_requirements()

    def _set_requirements(self):
        """
        sets data requirements for scraping module.
        """
        self._read_coinbase_requirements()
        self._format_coinbase_req()
        self._set_scraping_parameters()

    def _set_attributes(self):
        """
        sets attributes based on what is specified in the config.json file.

        """
        # configuration folder
        if os.path.isdir(self.config_folder):
            if os.path.isfile(self.config_folder + "/config.json"):
                with open(self.config_folder + "/config.json", "r") as f:
                    dictionary = json.load(f)
                    for key in dictionary:
                        setattr(self, key, dictionary[key])
            else:
                raise FileNotFoundError(
                    "Configuration file `config.json` not found."
                )
        else:
            raise FileNotFoundError("Configuration folder not found.")

    def _set_data_folder(self, data_folder):
        """
        sets the directory to the data folder.

        Arguments:
            data_folder (str): path
        """
        # HANDLING DATA FOLDER
        if data_folder is None:
            self.data_folder = str(
                (pathlib.Path(self.config_folder).parent).joinpath("data")
            )
            self._make_data_directories()
        else:
            if os.path.isdir(data_folder):
                self.data_folder = data_folder
                self._make_data_directories()
            else:
                raise FileNotFoundError(
                    f"Data folder not found. \n {data_folder}"
                )

    def _make_data_directories(self):
        """
        create data subdirectory structure.
        """
        # data folder
        if not os.path.isdir(self.data_folder):
            os.mkdir(self.data_folder)
        # data/ts subfolder
        if not os.path.isdir(self.data_folder + "/ts"):
            os.mkdir(self.data_folder + "/ts")

    def _temp_dir(self):
        """
        Create temp directory for temporary storing plots to be sent.
        If alreay exist, empty folder.
        """
        # data/temp
        self.temp_folder = self.data_folder + "/temp"
        if not os.path.isdir(self.temp_folder):
            os.mkdir(self.temp_folder)
        else:
            for f in os.listdir(self.temp_folder):
                os.remove(self.temp_folder + "/" + f)

    def _read_coinbase_requirements(self):
        """
        gets the requirements for coinbase portfolio tracking.
        """
        if os.path.isfile(self.config_folder + "/coinbase_accounts.json"):
            with open(
                self.config_folder + "/coinbase_accounts.json", "rb"
            ) as f:
                self.coinbase_req = json.load(f)
        else:
            self.coinbase_req = None

    def _format_coinbase_req(self):
        """
        formats coinbase requirements parameteters to datetime
        """
        req = {}
        # first get - if possible - coinbase requirements
        if self.coinbase_req is not None:
            for account in self.coinbase_req["accounts"]:
                if account["currency"] not in ["EUR"]:
                    # active account
                    if float(account["balance"]) > 0.0:
                        start = dateutil.parser.parse(
                            account["timerange"]["1"],
                        ).replace(hour=0, minute=0, second=0, microsecond=0)
                        req[account["currency"]] = {
                            "start": start,
                            # timedelta is because today's close
                            # isnt yet realized
                            "end_day": (datetime.datetime.now(datetime.timezone.utc)+ datetime.timedelta(-1)).replace(hour=0, minute=0, second=0, microsecond=0),
                        }
                    # historic account
                    else:
                        req[account["currency"]] = {
                            "start": dateutil.parser.parse(
                                account["timerange"]["1"]
                            ).replace(hour=0, minute=0, second=0, microsecond=0),
                            "end_day": dateutil.parser.parse(
                                account["timerange"]["0"]
                            ).replace(hour=0, minute=0, second=0, microsecond=0),
                        }
            # store coinbase requirements paresed correctly
            # for portfolio tracker features
            self.coinbase_req = req

    def _set_scraping_parameters(self):
        """
        sets the parameteters for the `surfingcrypto.Scraper` module
        """
        if self.coinbase_req is not None:
            params = self.coinbase_req.copy()
        else:
            params = {}
        # then, overrun with the reporting requirements
        for coin in self.coins:
            params[coin] = {
                # first date from BTC history to be "relevant", if other coin means first
                # available
                "start": datetime.datetime(2017, 10, 1,tzinfo=datetime.timezone.utc),
                # timedelta is because today's close isnt yet realized
                "end_day": datetime.datetime.now(datetime.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
                + datetime.timedelta(-1),
            }

        self.scraping_req = params

    def add_coins(self,coins:list)->None:
        """add coins to `coins` attribute

        Args:
            coins (list): list of coin strings
        """
        #add coins to attribute
        for coin in coins:
            #avoid overrunning
            if coin not in self.coins:
                self.coins[coin]=""
        #rerun 
        self._set_scraping_parameters()
        

