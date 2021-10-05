import json
import logging

import pandas as pd
import requests
from pandas.core.frame import DataFrame

logger = logging.getLogger(__name__)
# Usage:
# df = Certsearch().find("tno.nl")


class Certsearch:
    """class for certsearch called using Certsearch.find()"""

    def __init__(self) -> None:
        # include expired true, include subdomains false
        self.api = "https://transparencyreport.google.com/transparencyreport/api/v3/httpsreport/ct/certsearch?include_expired=true&include_subdomains=false&domain="
        self.api_key = "https://transparencyreport.google.com/transparencyreport/api/v3/httpsreport/ct/certsearch/page?p={key}"
        # only get 2 pages, max seems to be 50
        self.limit = 2

        self.parsed = ""
        self.result = ""
        self.next_key = ""
        self.df = pd.DataFrame()
        self.paginate_complete = False

    def pagination(self) -> None:
        """handles multiple pages of cert results"""
        counter = 1
        while self.next_key and counter < self.limit:
            counter += 1
            if self.next_key != "":
                key_url = self.api_key.format(key=self.next_key)
            elif self.next_key == "":
                pass
            try:
                r = requests.get(key_url)
                self.result = r.text
            except Exception as e:
                print(e)

            self.parse_result()
        else:
            self.paginate_complete = True

    def parse_result(self) -> None:
        """parse the results gotten from json to df"""
        # parse and skip first line
        self.parsed = json.loads(self.result.split("\n", 2)[2])
        # need this key in case of multiple pages, who knows maybe there is
        # only one page so try
        try:
            self.next_key = self.parsed[0][3][1]
        except BaseException:
            logger.warning("No results found for %s using Google cert search", self.dom)
            raise LookupError

        if self.parsed[0][1] is not None:
            for array in self.parsed[0][1]:
                a_series = pd.Series(array)
                self.df = self.df.append(a_series, ignore_index=True)
        else:
            logger.error(
                "Could not parse cert result for %s, certsearch API may be unavailable",
                self.dom,
            )

    def find(self, domain: str) -> DataFrame:
        """main method that makes our custom request to find certs"""
        self.dom = domain
        url = self.api + self.dom

        try:
            response = requests.get(url)
        except Exception as e:
            print(e)

        self.result = response.text
        self.parse_result()
        self.pagination()

        if self.df.empty is False:
            if len(self.df.columns) < 9:
                logger.critical("Less than 9 columns detected in: %s", self.dom)
                logger.critical("Dataframe for %s: %s", self.dom, self.df)

                # we don't want this confusing dataframe but also don't want to
                # crash again
                self.df = pd.DataFrame()
                return self.df

            self.df.columns = [
                "Unknown",
                "CN",
                "CA",
                "Valid from",
                "Valid to",
                "Details hash",
                "CT logs",
                "Unknown",
                "DNS names",
            ]

        return self.df
