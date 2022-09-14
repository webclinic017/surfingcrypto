"""
scraping price data from the internet.
"""
from cryptocmd import CmcScraper
import datetime
import pandas as pd
import os
import traceback
import pathlib


class Scraper:
    """
    gets all data required by configuration.

    Arguments:
        config (:obj:`surfingcrypto.config.config`): package
            configuration object

    Attributes:
        config (:obj:`surfingcrypto.config.config`): package
            configuration object
        runs (:obj:`list` of :obj:`surfincrypto.scraper.UpdateHandler`): list
            of `UpdateHandler` objects executed
        errors (:obj:`list` of :obj:`surfincrypto.scraper.UpdateHandler`): list
            of `UpdateHandler` objects that have errors
        output (bool): Overall boolean output of process, aka if
            everything went well.
        output_verbose (str): Overall string description of output.


    """

    def __init__(self, config):
        self.config = config
        self.runs = []
        self.errors = []
        self.output_verbose = ""
        self.output = None

    def run(self):
        """runs the scraping process for all coins."""
        for key in self.config.scraping_req:
            # dates are utc unaware
            start = self.config.scraping_req[key]["start"].date()
            end_day = self.config.scraping_req[key]["end_day"].date()

            # rebrandings
            if key in self.config.rebrandings:
                key = self.config.rebrandings[key]

            path = (
                self.config.data_folder / "ts" / (key + "_" + self.config.fiat + ".csv")
            )

            c = UpdateHandler(key, self.config.fiat, start, end_day, path)

            self.runs.append(c)

        self._log()

    def _log(self):
        """
        produce a log of all executions.
        """
        for run in self.runs:
            if hasattr(run, "error"):
                self.errors.append(run)

        if len(self.errors) == 0:
            self.output_verbose = "Update successful."
            self.output = True
        else:
            self.output_verbose = (
                "Update failed." f" There are ({len(self.errors)}/{len(self.runs)}) errors."
            )
            self.output = False


class UpdateHandler:
    """
    Checks if the file exists, if not it sets the date boundaries
    for the price API wrappers exactly as passed with the
    `start` and `end_day` arguments.
    If local data already exists, it checks first and last element of datetime column
    "Date" and compares with update request.

    Arguments:
        coin (str): symbol of crypto
        fiat (str): fiat of prices
        start (:obj:`datetime.datetime`):  start day
            from which is requested to scrape data
        end_day (:obj:`datetime.datetime`): end day of
            data requested, included
        path (:obj:`pathlib.Path`): path to csv file

    Attributes:
        coin (str): symbol of crypto
        fiat (str): fiat of prices
        start (:obj:`datetime.datetime`):  start day
            from which is requested to scrape data
        end_day (:obj:`datetime.datetime`): end day of
            data requested, included
        path (:obj:`pathlib.Path`): path to csv file
        left (:obj:`datetime.datetime` or :obj:`list` of `datetime.datetime`):
            left boundary (or boundaries, in case updating both sides of ts)
        right (:obj:`datetime.datetime` or :obj:`list` of `datetime.datetime`):
            right boundary (or boundaries, in case updating both sides of ts)
        df (:obj:`pandas.DataFrame`) : scraped df, SORTED IN ? ORDER
        description (str): verbose description of result
        result (bool): outcome of scraping run
        error (:obj:`Excection`): generic error
    """

    def __init__(
        self,
        coin: str,
        fiat: str,
        start: datetime.datetime,
        end_day: datetime.datetime,
        path: pathlib.Path,
        apiwrapper="cmc",
    ):
        self.coin = coin
        self.fiat = fiat
        self.apiwrapper = apiwrapper

        # dates are utc unaware
        self.start = start
        self.end_day = end_day

        self.path = path

        # log
        self.description = None
        self.result = None
        self.error = None

        if apiwrapper == "cmc":
            self.apiwrapper = CMCutility
        else:
            raise NotImplementedError

        self._handle_update()

    def _handle_update(self) -> None:
        """
        gets the bounds of the dataframes to be downloaded
        to fullfill update.
        """
        # check if exists
        if os.path.isfile(self.path):
            df, first, last = self._load_csv()

            if (first <= self.start) and (self.end_day <= last):
                self.df = df
                self.description = f"{self.coin} in {self.fiat}, already up to date."
                self.result = True
            else:
                try:
                    self.left, self.right = self._get_required_bounds(first, last)
                    self.df = self._get_updates(df)
                    self.df.to_csv(self.path)
                    self.description = (
                        f"{self.coin} in {self.fiat}, successfully updated."
                    )
                    self.result = True
                except:
                    self.description = f"{self.coin} in {self.fiat}," " update failed."
                    self.result = False
                    self.error = traceback.format_exc()
        else:
            try:
                self.left, self.right = self.start, self.end_day
                self.df = self._get_updates(None)
                self.df.to_csv(self.path)
                self.description = (
                    f"{self.coin} in {self.fiat}, successfully downloaded."
                )
                self.result = True
            except:
                self.description = (
                    f"{self.coin} in {self.fiat}, download failed."
                )
                self.result = False
                self.error = traceback.format_exc()

    def _load_csv(self) -> tuple:
        """
        load local csv data from directory specified as `data_folder`
        in package config

        Return:
            df (:obj:`pandas.DataFrame`): dataframe of locally stored data
            first (:obj:`datetime.datetime`): first known price
            last (:obj:`datetime.datetime`): last known price
        """
        df = pd.read_csv(self.path)
        df["Date"] = pd.to_datetime(df["Date"])
        first = df["Date"].iloc[0]
        last = df["Date"].iloc[-1]
        return df, first, last

    def _get_required_bounds(
        self, first: datetime.datetime, last: datetime.datetime
    ) -> tuple:
        """
        finds info for the missing data in the local dataframe - represented
        by the `first` and `last` arguments - with respect to the
        request stored in `start` and `end_day` attribute

        Arguments:
            first (:obj:`datetime.datetime`): first known price
            last (:obj:`datetime.datetime`): last known price

        Raises:
            NotImplementedError: _description_

        Returns:
            tuple : 2-tuple of datetime or 2 lists of datetime,
                in case an update of both the front end and
                the last end is required.
        """
        # appending to front can cause exceptions because
        # coin data is available from a date that is later
        # than the start parameter


        # only to the front
        if self.start < first and last == self.end_day:
            left, right = self.start, (first - datetime.timedelta(1))

        # only to the end
        elif (first == self.start or first < self.start) and last < self.end_day:
            left, right = last + datetime.timedelta(1), self.end_day

        # both sides
        elif self.start < first and last < self.end_day:
            left, right = [], []
            # front part
            left.append(self.start)
            right.append(first - datetime.timedelta(1))
            # end part
            left.append(last + datetime.timedelta(1))
            right.append(self.end_day)

        else:  
            print(f"first: {first}, last: {last}")
            print(f"start: {self.start}, end: {self.end_day}")
            raise NotImplementedError

        return left, right

    def _get_updates(self, df: pd.DataFrame or None) -> pd.DataFrame:
        """returns dataframe of prices

        get updates using selected apiwrapper.

        The dataframe has default integer index.

        Args:
            df (pd.DataFrame or None): _description_

        Raises:
            NotImplementedError: _description_

        Returns:
            pd.DataFrame: _description_
        """
        updates = [
            df,
        ]
        # one side update
        if isinstance(self.left, datetime.date) and isinstance(
            self.right, datetime.date
        ):
            updates.append(
                self.apiwrapper(
                    self.coin, self.left, self.right, self.fiat
                ).scrape_data()
            )
        # two side update (lists)
        else:
            for l, r in zip(self.left, self.right):
                updates.append(
                    self.apiwrapper(self.coin, l, r, self.fiat).scrape_data()
                )

        #concat
        df = pd.concat(updates)
        # sort ascending, oldest to newest
        df.sort_values(by="Date", inplace=True)
        df.reset_index(inplace=True,drop=True)
        return df

    def __str__(self) -> str:
        errors = hasattr(self, "error")
        return f"UpdateHandler({self.coin}-{self.fiat}: {self.description})"

    def __repr__(self) -> str:
        errors = hasattr(self, "error")
        return f"UpdateHandler({self.coin}-{self.fiat}: {self.description})"


class CMCutility(CmcScraper):
    """
    wrapper of GitHub repo `cryptocmd`.

    Scrapes data from coinmarketcap.com.
    """

    def __init__(
        self,
        coin: str,
        left: datetime.datetime,
        right: datetime.datetime,
        fiat: str,
    ):
        self.coin = coin
        self.left = left.strftime("%d-%m-%Y")
        self.right = right.strftime("%d-%m-%Y")
        self.fiat = fiat
        self.response = None
        super().__init__(self.coin, self.left, self.right, fiat=self.fiat)

    def scrape_data(self) -> pd.DataFrame:
        try:
            scraped = self.get_dataframe()
            self.response = True
        except:
            scraped = pd.DataFrame(columns=["Date"])
            self.response = False
        return scraped

    def __str__(self):
        return (
            f"CmcScraper({self.coin}"
            f", left={self.left}"
            f", right={self.right}"
            f", response={self.response}"
            ")"
        )

    def __repr__(self):
        return (
            f"CmcScraper({self.coin}"
            f", left={self.left}"
            f", right={self.right}"
            f", response={self.response}"
            ")"
        )
