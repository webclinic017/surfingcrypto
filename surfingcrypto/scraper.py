"""
scraping price data from the internet.
"""
from cryptocmd import CmcScraper
import datetime
import pandas as pd
import os


class Scraper:
    """
    gets all data required by module configuration.

    Arguments:
        configuration (:obj:`surfingcrypto.config.config`): package
            configuration object
        fiat (str): prices will be restituted in the selected fiat,
            defaults is `EUR`
        log (bool): wether to log at the end of execution

    Attributes:
        config (:obj:`surfingcrypto.config.config`): package
            configuration object
        fiat (str): fiat symbol
        verbose (bool): wether to print log
        runs (:obj:`list` of :obj:`surfincrypto.scraper.CoinScraper) : 
            list of `CoinScraper` objects
        output (bool): Overall boolean output of process. If
            everything went well.
        output_descrition (str): Overall log string of ouput.


    """

    def __init__(self, configuration, fiat="EUR", verbose=True):
        self.config = configuration
        self.fiat = fiat
        self.verbose = verbose

    def run(self):
        """runs the scraping process."""
        self.runs = []
        for key in self.config.scraping_req:
            c = CoinScraper(key, self.config)
            self.runs.append(c)

        self._log()

    def _log(self):
        """
        produce a log of all executions.
        """
        length = len(self.runs)
        errors = []
        for run in self.runs:
            if hasattr(run, "error"):
                errors.append(run)

        if len(errors) == 0:
            self.output_description = "Update successful."
            self.output = True
        else:
            self.output_description = (
                "Update failed." f" There are ({len(errors)}/{length}) errors."
            )
            self.output = False

        if self.verbose:
            print(self.output_description)


class CoinScraper:
    """
    wrapper of GitHub repo `cryptocmd`.

    Scrapes data from coinmarketcap.com.

    It scrapes data for the crypto coins specified in the keys of the
    customizable coins.json file.Saves data in a `*.csv` file
    stored in `data/ts/`.
    Checks if the file exists, if not it is downloaded.
    If it exists, it check last element of datetime index and compares it
    with today's date. If required, it updates the `*.csv` file
    to today\'s date.

    Arguments:
        key (str): symbol of crypto
        configuration (:obj:`surfingcrypto.config.config`): package
            configuration object

    Attributes:
        key (str): symbol of crypto
        config (:obj:`surfingcrypto.config.config`): package
            configuration object
        start (:obj:`datetime.datetime`):  start day
        end_day (:obj:`datetime.datetime`): end day
        path (str): path to csv file
        description (str): verbose description of result
        result (bool): outcome of scraping run
        error (:obj:`Excection`): generic error
    """

    def __init__(self, key, configuration):
        self.key = key
        self.config = configuration
        self.start = self.config.scraping_req[key]["start"]
        self.end_day = self.config.scraping_req[key]["end_day"]
        self.path = self.config.data_folder + "/ts/" + key + ".csv"
        self._run()

    def _run(self):

        if os.path.isfile(self.path):
            df, last = self._load_csv()
            last = last.date()
            if last == self.end_day:
                s = f"DF: {self.key} already up to date."
                self.description = s
                self.result = True
            else:
                try:
                    self._scrape_missing_data(last, df)
                    s = f"DF: {self.key} successfully updated."
                    self.description = s
                    self.result = True
                except Exception as e:
                    s = f"DF: {self.key} update failed."
                    self.description = s
                    self.result = False
                    self.error = e
        else:
            try:
                self._scrape_alltime_data()
                s = f"DF: {self.key} successfully downloaded."
                self.description = s
                self.result = True
            except Exception as e:
                s = f"DF: {self.key} download failed."
                self.description = s
                self.result = False
                self.error = e

    def _scrape_alltime_data(self):
        """
        scrape all time data.
        """
        start = self.start.strftime("%d-%m-%Y")
        end_day = self.end_day.strftime("%d-%m-%Y")
        scraper = CmcScraper(self.key, start, end_day, fiat=self.fiat)
        scraped = scraper.get_dataframe()
        scraped.set_index("Date", inplace=True)
        scraped.sort_index(inplace=True)
        scraped.to_csv(self.path)

    def _scrape_missing_data(self, last, df):
        """
        scrapes the missing data and concatenates it to existing df.

        Arguments:
            last (:obj:`datetime.datetime`): date parsed as string
                with d-m-Y format of last known price
            df (:obj:`pandas.DataFrame`): dataframe of
                locally stored data
        """
        last = (last + datetime.timedelta(1)).strftime("%d-%m-%Y")
        end_day = self.end_day.strftime("%d-%m-%Y")
        scraper = CmcScraper(self.key, last, end_day, fiat=self.fiat)
        scraped = scraper.get_dataframe()
        scraped.set_index("Date", inplace=True)
        df = pd.concat([df, scraped])
        df.sort_index(inplace=True)
        df.to_csv(self.path)

    def _load_csv(self):
        """
        load csv data from directory specified as `data_folder`
        in package config

        Return:
            df (:obj:`pandas.DataFrame`): dataframe of locally stored data
            last (str): date parsed as d-m-Y of last known price
        """
        df = pd.read_csv(self.path)
        df["Date"] = pd.to_datetime(df["Date"])
        df.set_index("Date", inplace=True)
        last = pd.to_datetime(df.index.values[-1])
        return df, last

    def __str__(self):
        start = self.start.strftime("%d-%m-%Y")
        endday = self.end_day.strftime("%d-%m-%Y")
        error = hasattr(self, "error")
        return (
            f"CoinScraper({self.key},"
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
            f"CoinScraper({self.key},"
            f" start={start},"
            f" end_day={endday},"
            f" error={error},"
            ")"
        )

