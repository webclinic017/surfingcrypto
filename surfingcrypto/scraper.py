"""
scraping price data from the internet.
"""
from cryptocmd import CmcScraper
import datetime
import pandas as pd
import os


class Scraper:
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
        configuration (:obj:`surfingcrypto.config.config`): package
            configuration object
        fiat (str): prices will be restituted in the selected fiat,
            defaults is `EUR`

    Attributes:
        config (:obj:`surfingcrypto.config.config`): package
            configuration object
        log_strings(:obj:`list` of :obj:`str`): list of log
            strings for output of process, one for each coin.
        log_bool (:obj:`list` of :obj:`bool`): list of boolean
            output of process, one for each coin.
        output (bool): Overall boolean output of process. If
            everything went well.
        output_descrition (str): Overall log string of ouput.

    """

    def __init__(self, configuration, fiat="EUR"):
        self.config = configuration
        self.fiat = fiat

    def run(self):
        """runs the scraping process."""
        descriptions = []
        result = []
        errors = []
        for key in self.config.scraping_req:

            end_day = self.config.scraping_req[key]["end_day"]
            start = self.config.scraping_req[key]["start"]
            path = self.config.data_folder + "/ts/" + key + ".csv"

            if os.path.isfile(path):
                df, last = self.load_csv(path)
                last = last.date()
                if last == end_day:
                    s = f"DF: {key} already up to date."
                    descriptions.append(s)
                    result.append(True)
                else:
                    try:
                        self.scrape_missing_data(last, end_day, key, path, df)
                        s = f"DF: {key} successfully updated."
                        descriptions.append(s)
                        result.append(True)
                    except Exception as e:
                        s = f"DF: {key} update failed."
                        descriptions.append(s)
                        result.append(False)
                        errors.append({"coin": key, "error": e})
            else:
                try:
                    self.scrape_alltime_data(start, end_day, key, path)
                    s = f"DF: {key} successfully downloaded."
                    descriptions.append(s)
                    result.append(True)
                except Exception as e:
                    s = f"DF: {key} download failed."
                    descriptions.append(s)
                    result.append(False)
                    errors.append({"coin": key, "error": e})

        self.log_strings = descriptions
        self.log_bool = result
        self.output = all(self.log_bool)
        self.errors = errors
        self.log()

    def scrape_alltime_data(self, start, end_day, key, path):
        """
        scrape all time data.

        Arguments:
            start (:obj:`datetime.datetime`):  start day
            end_day (:obj:`datetime.datetime`): end day
            key (str): symbol of crypto
            path (str): path to csv file
        """
        start = start.strftime("%d-%m-%Y")
        end_day = end_day.strftime("%d-%m-%Y")
        scraper = CmcScraper(key, start, end_day, fiat=self.fiat)
        scraped = scraper.get_dataframe()
        scraped.set_index("Date", inplace=True)
        scraped.sort_index(inplace=True)
        scraped.to_csv(path)

    def scrape_missing_data(self, last, end_day, key, path, df):
        """
        scrapes the missing data and concatenates it to existing df.

        Arguments:
            last (:obj:`datetime.datetime`): date parsed as string
                with d-m-Y format of last known price
            end_day (:obj:`datetime.datetime`):  date parsed
                as string with d-m-Y format for limiting the
                dowload of data to a specific date.
            key (str): symbol of crypto
            path (str): path to csv file
            df (:obj:`pandas.DataFrame`): dataframe of
                locally stored data
        """
        last = (last + datetime.timedelta(1)).strftime("%d-%m-%Y")
        end_day = end_day.strftime("%d-%m-%Y")
        scraper = CmcScraper(key, last, end_day, fiat=self.fiat)
        scraped = scraper.get_dataframe()
        scraped.set_index("Date", inplace=True)
        df = pd.concat([df, scraped])
        df.sort_index(inplace=True)
        df.to_csv(path)

    def load_csv(self, path):
        """
        load csv data from directory specified as `data_folder`
        in package config

        Arguments:
            path (str): path to csv file

        Return:
            last (str): date parsed as d-m-Y of last known price
            df (:obj:`pandas.DataFrame`): dataframe of locally stored data
        """
        df = pd.read_csv(path)
        df["Date"] = pd.to_datetime(df["Date"])
        df.set_index("Date", inplace=True)
        last = pd.to_datetime(df.index.values[-1])
        return df, last

    def log(self):
        """
        prints `output_description` for reading output.
        """
        if self.output:
            self.output_description = "Update successful."
        else:
            self.output_description = (
                "Update failed. Check log files for update"
            )
        print("### SCRAPER")
        print(self.output_description)
        [print(i) for i in self.log_strings]
