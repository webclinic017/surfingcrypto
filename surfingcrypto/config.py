"""
package configuration
"""
import json
import os
from pathlib import Path
import datetime
import dateutil


class Config:
    """
    Class for the package configuration.
    Contains API keys and user-specified parametrization of execution.

    Arguments:
        coins (dict): coins
        data_folder (:obj:`pathlib.Path`) : path to datafolder
        secrets (dist): dictionary of secrets (such as API keys)

    Attributes:
        coins (dict): coins
        data_folder (str) : ABSOLUTE path to data folder

        coinbase (dict): coinbase user configuration
        telegram (dict): telegram user configuration

        coinbase_req (:obj:`dict` of :obj:`dict`) dictionary
            containing coinbase requirements
        data_folder (str) : ABSOLUTE path to data folder

        error_log (:obj:`list`): list of errors
        rebrandings (dict): dictionary of known rebrandings
        scraping_req (:obj:`dict` of :obj:`dict`)
            dictionary containing scraping params
    """

    def __init__(self, coins: dict, data_folder: Path, secrets=None):
        self.coins = coins
        if secrets:
            for key in secrets:
                setattr(self, key, secrets[key])

        self.data_folder = data_folder
        self._make_subdirs()

        self.rebrandings = {"CGLD": "CELO"}
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

    def _make_subdirs(self):
        """
        create data subdirectory structure.
        """
        # data folder
        if not os.path.isdir(self.data_folder):
            os.mkdir(self.data_folder)
        # data/ts subfolder
        if not os.path.isdir(self.data_folder / "ts"):
            os.mkdir(self.data_folder / "ts")
        # data/temp subfolder
        if not os.path.isdir(self.data_folder / "temp"):
            os.mkdir(self.data_folder / "temp")
        else:
            # clears temp folder
            for f in os.listdir(self.data_folder / "temp"):
                os.remove(self.data_folder / "temp" / f)
        # data/cache subfolder
        if not os.path.isdir(self.data_folder / "cache"):
            os.mkdir(self.data_folder / "cache")

    def _read_coinbase_requirements(self):
        """
        gets the requirements for coinbase portfolio tracking.
        """
        if os.path.isfile(
            self.data_folder / "cache" / "coinbase_accounts.json"
        ):
            with open(
                self.data_folder / "cache" / "coinbase_accounts.json", "rb"
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
            for account in self.coinbase_req["accounts"].values():
                if account["currency"] not in ["EUR"]:
                    # active account
                    if str(account["active"]) == "True":
                        start = dateutil.parser.parse(
                            account["timerange"]["1"],
                        ).replace(hour=0, minute=0, second=0, microsecond=0)
                        req[account["currency"]] = {
                            "start": start,
                            # timedelta is because today's close
                            # isnt yet realized
                            "end_day": (
                                datetime.datetime.now(datetime.timezone.utc)
                                + datetime.timedelta(-1)
                            ).replace(
                                hour=0, minute=0, second=0, microsecond=0
                            ),
                        }
                    # historic account
                    else:
                        req[account["currency"]] = {
                            "start": dateutil.parser.parse(
                                account["timerange"]["1"]
                            ).replace(
                                hour=0, minute=0, second=0, microsecond=0
                            ),
                            "end_day": dateutil.parser.parse(
                                account["timerange"]["0"]
                            ).replace(
                                hour=0, minute=0, second=0, microsecond=0
                            ),
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
                "start": datetime.datetime(
                    2017, 10, 1, tzinfo=datetime.timezone.utc
                ),
                # timedelta is because today's close isnt yet realized
                "end_day": datetime.datetime.now(
                    datetime.timezone.utc
                ).replace(hour=0, minute=0, second=0, microsecond=0)
                + datetime.timedelta(-1),
            }

        self.scraping_req = params

    def add_coins(self, coins: list) -> None:
        """add coins to `coins` attribute

        Args:
            coins (list): list of coin strings
        """
        # add coins to attribute
        for coin in coins:
            # avoid overrunning
            if coin not in self.coins:
                self.coins[coin] = ""
        # rerun
        self._set_scraping_parameters()
