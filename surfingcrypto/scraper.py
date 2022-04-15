"""
scraping price data from the internet.
"""
from cryptocmd import CmcScraper
import datetime
import pandas as pd
import os
import traceback


class Scraper:
    """
    gets all data required by module configuration.

    Arguments:
        configuration (:obj:`surfingcrypto.config.config`): package
            configuration object
        fiat (str): prices will be restituted in the selected fiat,
            defaults is `EUR`
        verbose (bool): wether to log at the end of execution

    Attributes:
        config (:obj:`surfingcrypto.config.config`): package
            configuration object
        fiat (str): fiat symbol
        verbose (bool): wether to print log
        runs (:obj:`list` of :obj:`surfincrypto.scraper.CoinScraper`): list
            of `CoinScraper` objects
        errors (:obj:`list` of :obj:`surfincrypto.scraper.CoinScraper`): list
            of `CoinScraper` objects that have errors
        output (bool): Overall boolean output of process. If
            everything went well.
        output_descrition (str): Overall string description of output.


    """

    def __init__(self, configuration, fiat="EUR", verbose=True):
        self.config = configuration
        self.fiat = fiat
        self.verbose = verbose

    def run(self):
        """runs the scraping process."""
        self.runs = []
        for key in self.config.scraping_req:

            # dates are utc unaware
            start = self.config.scraping_req[key]["start"].date()
            end_day = self.config.scraping_req[key]["end_day"].date()

            if key in self.config.rebrandings:
                key = self.config.rebrandings[key]

            path = self.config.data_folder + "/ts/" + key + ".csv"
            c = CoinScraper(key, self.fiat, start, end_day, path)
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


class CoinScraper:
    """
    wrapper of GitHub repo `cryptocmd`.

    Scrapes data from coinmarketcap.com.

    It scrapes data for the crypto coin specified.
    Saves data in a `*.csv` file
    stored at the provided path.
    Checks if the file exists, if not it is downloaded.
    If it exists, it check last element of datetime index and compares it
    with today's date. If required, it updates the `*.csv` file
    to today\'s date.

    Arguments:
        coin (str): symbol of crypto
        fiat (str): fiat of prices
        start (:obj:`datetime.datetime`):  start day
        end_day (:obj:`datetime.datetime`): end day
        path (str): path to csv file

    Attributes:
        coin (str): symbol of crypto
        fiat (str): fiat of prices
        start (:obj:`datetime.datetime`):  start day
        end_day (:obj:`datetime.datetime`): end day
        path (str): path to csv file
        description (str): verbose description of result
        result (bool): outcome of scraping run
        error (:obj:`Excection`): generic error
    """

    def __init__(self, coin, fiat, start, end_day, path):
        self.coin = coin
        self.fiat = fiat

        # dates are utc unaware
        self.start = start
        self.end_day = end_day

        self.path = path

        self._run()

    def _run(self):

        if os.path.isfile(self.path):
            df, first, last = self._load_csv()

            first = first.date()
            last = last.date()

            if first == self.start and last == self.end_day:
                self.description = f"DF: {self.coin} already up to date."
                self.result = True
            else:
                try:
                    self._scrape_missing_data(first, last, df)
                    self.description = f"DF: {self.coin} successfully updated."
                    self.result = True
                except:
                    self.description = f"DF: {self.coin} update failed."
                    self.result = False
                    self.error = traceback.format_exc()
        else:
            try:
                self._scrape_alltime_data()
                self.description = f"DF: {self.coin} successfully downloaded."
                self.result = True
            except:
                self.description = f"DF: {self.coin} download failed."
                self.result = False
                self.error = traceback.format_exc()

    def _scrape_alltime_data(self):
        """
        scrape all time data.
        """
        start = self.start.strftime("%d-%m-%Y")
        end_day = self.end_day.strftime("%d-%m-%Y")
        scraper = CmcScraper(self.coin, start, end_day, fiat=self.fiat)
        scraped = scraper.get_dataframe()
        scraped.set_index("Date", inplace=True)
        scraped.sort_index(inplace=True)
        scraped.to_csv(self.path)

    def _scrape_missing_data(self, first, last, df):
        """
        scrapes the missing data and concatenates it to existing df.

        Arguments:
            first (:obj:`datetime.datetime`): date parsed as string
                with d-m-Y format of first known price
            last (:obj:`datetime.datetime`): date parsed as string
                with d-m-Y format of last known price
            df (:obj:`pandas.DataFrame`): dataframe of
                locally stored data
        """
        # appending to front can cause exceptions because
        # coin data is available from a date that is later
        # than the start parameter

        if (first == self.start or first < self.start) and last < self.end_day:
            # only to the end
            scraper = self._append_to_end(last)
            scraped = scraper.get_dataframe()

        elif self.start < first and last == self.end_day:
            # only to the front
            scraper = self._append_to_front(first)
            if scraper.rows:
                scraped = scraper.get_dataframe()
            else:
                scraped = pd.DataFrame(columns=["Date"])

        elif self.start < first and last < self.end_day:
            # end
            scraper = self._append_to_end(last)
            scraped_last = scraper.get_dataframe()

            # front
            scraper = self._append_to_front(first)
            if scraper.rows:
                scraped_first = scraper.get_dataframe()
            else:
                scraped_first = pd.DataFrame(columns=["Date"])

            # concat
            scraped = pd.concat([scraped_last, scraped_first])

        elif (first == self.start or first < self.start) and (
            self.end_day == last or self.end_day < last
        ):
            # i have what is needed
            # i add nothing
            scraped = pd.DataFrame(columns=["Date"])

        else:
            raise NotImplementedError

        scraped.set_index("Date", inplace=True)
        df = pd.concat([df, scraped])
        df.sort_index(inplace=True)
        df.to_csv(self.path)

    def _append_to_front(self, first: datetime) -> CmcScraper:
        start = self.start.strftime("%d-%m-%Y")
        day_before_first = (first - datetime.timedelta(1)).strftime("%d-%m-%Y")
        scraper = CmcScraper(
            self.coin, start, day_before_first, fiat=self.fiat
        )

        return scraper

    def _append_to_end(self, last: datetime) -> CmcScraper:
        day_after_last = (last + datetime.timedelta(1)).strftime("%d-%m-%Y")
        end_day = self.end_day.strftime("%d-%m-%Y")
        scraper = CmcScraper(
            self.coin, day_after_last, end_day, fiat=self.fiat
        )
        return scraper

    def _load_csv(self):
        """
        load csv data from directory specified as `data_folder`
        in package config

        Return:
            df (:obj:`pandas.DataFrame`): dataframe of locally stored data
            first (_type_): date parsed as d-m-Y of first known price
            last (_type_): date parsed as d-m-Y of last known price
        """
        df = pd.read_csv(self.path)
        df["Date"] = pd.to_datetime(df["Date"])
        df.set_index("Date", inplace=True)
        first = pd.to_datetime(df.index.values[0])
        last = pd.to_datetime(df.index.values[-1])
        return df, first, last

    def __str__(self):
        start = self.start.strftime("%d-%m-%Y")
        endday = self.end_day.strftime("%d-%m-%Y")
        error = hasattr(self, "error")
        return (
            f"CoinScraper({self.coin},"
            f" start={start},"
            f" end_day={endday},"
            f" error={error},"
            ")"
        )

    def __repr__(self):
        start = self.start.strftime("%d-%m-%Y")
        endday = self.end_day.strftime("%d-%m-%Y")
        error = hasattr(self, "error")
        return (
            f"CoinScraper({self.coin},"
            f" start={start},"
            f" end_day={endday},"
            f" error={error},"
            ")"
        )

