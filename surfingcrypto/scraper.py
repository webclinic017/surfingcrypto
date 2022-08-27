"""
scraping price data from the internet.
"""
from turtle import up
from cryptocmd import CmcScraper
import datetime
import pandas as pd
import os
import traceback


class Scraper:
    """
    gets all data required by configuration.

    Arguments:
        config (:obj:`surfingcrypto.config.config`): package
            configuration object
        verbose (bool): wether to log at the end of execution

    Attributes:
        config (:obj:`surfingcrypto.config.config`): package
            configuration object
        verbose (bool): wether to print log
        runs (:obj:`list` of :obj:`surfincrypto.scraper.CoinScraper`): list
            of `CoinScraper` objects
        errors (:obj:`list` of :obj:`surfincrypto.scraper.CoinScraper`): list
            of `CoinScraper` objects that have errors
        output (bool): Overall boolean output of process. If
            everything went well.
        output_descrition (str): Overall string description of output.


    """

    def __init__(self, config, verbose=True):
        self.config = config
        self.verbose = verbose

    def run(self):
        """runs the scraping process for all coins."""
        self.runs = []
        for key in self.config.scraping_req:
            # dates are utc unaware
            start = self.config.scraping_req[key]["start"].date()
            end_day = self.config.scraping_req[key]["end_day"].date()

            # rebrandings
            if key in self.config.rebrandings:
                key = self.config.rebrandings[key]

            path = (
                self.config.data_folder
                / "ts"
                / (key + "_" + self.config.fiat + ".csv")
            )

            c = UpdateHandler(key, self.config.fiat, start, end_day, path)

            self.runs.append(c)

        self._log()

    def _log(self):
        """
        produce a log of all executions.
        """
        length = len(self.runs)
        self.errors = []
        for run in self.runs:
            if hasattr(run, "error"):
                self.errors.append(run)

        if len(self.errors) == 0:
            self.output_description = "Update successful."
            self.output = True
        else:
            self.output_description = (
                "Update failed."
                f" There are ({len(self.errors)}/{length}) errors."
            )
            self.output = False

        if self.verbose:
            print(self.output_description)


class UpdateHandler:
    """
    Checks if the file exists, if not it sets the date boundaries
    for the price API wrappers exactly as passed with the
    `start` and `end_day` arguments.
    If local data already exists, it checks first and last element of datetime index
    and compares it with today's date. If required, it updates the `*.csv` file
    to today\'s date.

    Arguments:
        coin (str): symbol of crypto
        fiat (str): fiat of prices
        start (:obj:`datetime.datetime`):  start day
            from which is requested to scrape data
        end_day (:obj:`datetime.datetime`): end day of
            data requested, included
        path (str): path to csv file

    Attributes:
        coin (str): symbol of crypto
        fiat (str): fiat of prices
        start (:obj:`datetime.datetime`):  start day
            from which is requested to scrape data
        end_day (:obj:`datetime.datetime`): end day of
            data requested, included
        path (str): path to csv file
        left (:obj:`datetime.datetime` or :obj:`list` of `datetime.datetime`):
            left boundary (or boundaries, in case updating both sides of ts)
        right (:obj:`datetime.datetime` or :obj:`list` of `datetime.datetime`):
            right boundary (or boundaries, in case updating both sides of ts)
        df (:obj:`pandas.DataFrame`) : scraped df
        description (str): verbose description of result
        result (bool): outcome of scraping run
        error (:obj:`Excection`): generic error
    """

    def __init__(self, coin, fiat, start, end_day, path, apiwrapper="cmc"):
        self.coin = coin
        self.fiat = fiat
        self.apiwrapper = apiwrapper

        # dates are utc unaware
        self.start = start
        self.end_day = end_day

        self.path = path

        if apiwrapper == "cmc":
            self.apiwrapper = CMCutility
        else:
            raise NotImplementedError

        self._handle_update()

    def _get_updates(self,df:pd.DataFrame or None):
        updates=[df,]
        if isinstance(self.left,datetime.datetime) and isinstance(self.right,datetime.datetime):
            updates.append(self.apiwrapper(self.coin,l,r,self.fiat).get_data())

        elif isinstance(self.left,list) and isinstance(self.right,list):
            for l,r in zip(self.left,self.right):
                    updates.append(self.apiwrapper(self.coin,l,r,self.fiat).get_data())
        else:
            raise NotImplementedError
        
        df = pd.concat(updates)
        df.sort_index(inplace=True)
        return df

    def _handle_update(self):
        """
        gets the bounds of the dataframes to be downloaded 
        to fullfill update.
        """
        # check if exists
        if os.path.isfile(self.path):
            df, first, last = self._load_csv()

            first = first.date()
            last = last.date()

            if first == self.start and last == self.end_day:
                self.df = df
                self.description = (
                    f"DF: {self.coin} in {self.fiat}, already up to date."
                )
                self.result = True
            else:
                try:
                    self.left, self.right = self._get_required_bounds(
                        first, last
                    )
                    self.df = self._get_updates(df)
                    self.description = f"DF: {self.coin} in {self.fiat},"
                    " successfully updated."
                    self.result = True
                except:
                    self.description = (
                        f"DF: {self.coin} in {self.fiat}," " update failed."
                    )
                    self.result = False
                    self.error = traceback.format_exc()
        else:
            try:
                self.left, self.right = self.start, self.end_day
                self.df = self._get_updates(None)
                self.description = f"DF: {self.coin} in {self.fiat},"
                "  successfully downloaded."
                self.result = True
            except:
                self.description = (
                    f"DF: {self.coin} in {self.fiat} in {self.fiat},"
                    "  download failed."
                )
                self.result = False
                self.error = traceback.format_exc()

    def _load_csv(self):
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
        df.set_index("Date", inplace=True)
        first = pd.to_datetime(df.index.values[0])
        last = pd.to_datetime(df.index.values[-1])
        return df, first, last

    def _get_required_bounds(self, first, last):
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

        if (first == self.start or first < self.start) and last < self.end_day:
            # only to the end
            left, right = self.start, (first - datetime.timedelta(1))

        elif self.start < first and last == self.end_day:
            # only to the front
            left, right = self.start, (first - datetime.timedelta(1))

        elif self.start < first and last < self.end_day:
            left = [], right = []
            # end part
            left.append(last + datetime.timedelta(1))
            right.append(self.end_day)

            # front part
            left.append(self.start)
            right.append(first - datetime.timedelta(1))

        elif (first == self.start or first < self.start) and (
            self.end_day == last or self.end_day < last
        ):
            left, right = None, None
        else:
            raise NotImplementedError

        return left, right

    def __str__(self):
        errors = hasattr(self, "error")
        return (
            f"UpdateHandler({self.coin},"
            f" result={self.result},"
            f" error={errors},"
            ")"
        )

    def __repr__(self):
        errors = hasattr(self, "error")
        return (
            f"UpdateHandler({self.coin},"
            f" result={self.result},"
            f" error={errors},"
            ")"
        )


class CMCutility:
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

    def get_data(self) -> pd.DataFrame:
        cmc = CmcScraper(self.coin, self.left, self.right, fiat=self.fiat)
        if cmc.rows:
            scraped = cmc.get_dataframe()
        else:
            scraped = pd.DataFrame(columns=["Date"])
        return scraped

    def __str__(self):
        return (
            f"CmcScraper({self.coin},"
            f" start={self.start},"
            f" end_day={self.end_day},"
            ")"
        )

    def __repr__(self):
        return (
            f"CmcScraper({self.coin},"
            f" start={self.start},"
            f" end_day={self.end_day},"
            ")"
        )
