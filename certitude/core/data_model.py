import csv
import logging
import math
import multiprocessing as mp
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from urllib.parse import urlparse

import joblib
import pandas as pd
import whois
from pandas.core.frame import DataFrame
from sklearn.ensemble import RandomForestClassifier
from whois.exceptions import FailedParsingWhoisOutput, UnknownTld

from certitude.utils.cert import Certsearch
from certitude.utils.config import config
from certitude.utils.miscellaneous import (
    count_delimiters,
    dataframe_postprocessing,
    entropy,
)

logger = logging.getLogger(__name__)
mgr = mp.Manager()
ns = mgr.Namespace()
config = config()


class URL:
    def __init__(self, url: str) -> None:
        self.url = url
        self.valid_url = None
        try:
            logger.debug(self.url)
            self.parsed_url = urlparse(self.url)
            self.valid_url = True
        except Exception:
            logger.warning("[!] Unable to parse url. It will be ignored.")
            self.valid_url = False
        self.scheme = self.parsed_url.scheme
        self.netloc = self.parsed_url.netloc
        self.query = self.parsed_url.query
        self.path = self.parsed_url.path
        self.params = self.parsed_url.params
        self.fragment = self.parsed_url.fragment
        self.port = self.parsed_url.port
        self.certificate_collection = None
        self.features_dataframe = None
        self.valid = None

    def domains_separator(self) -> None:
        """separates domains within netloc"""
        self.domains_splitted = self.netloc.split(".")
        if self.domains_splitted[0] == "www":
            self.domains_splitted = self.domains_splitted[1:]
        # This is in case we do not get an error with domains_splitted[0]
        if len(self.domains_splitted) == 0:
            self.domains_splitted.append("")
        self.ft_dummy_domains = self.domains_splitted[0]

    def domains_features(self) -> None:
        """features based on subdomains of url"""
        self.ft_nr_of_domains = len(self.domains_splitted)
        self.ft_length_first_subdomain = len(self.domains_splitted[0])
        self.ft_length_tld = len(self.domains_splitted[-1])

    def netloc_features(self) -> None:
        """features based on main domain/hostname (netloc)"""
        self.ft_netloc_length = len(self.netloc)

    def query_features(self) -> None:
        """features based on url query section"""
        self.ft_query_length = len(self.query)

    def path_features(self) -> None:
        """features based on url path section"""
        self.ft_path_length = len(self.path)

    def combined_features(self) -> None:
        """features based on combined parts of url"""
        if self.ft_path_length > 0:
            self.ft_ratio_netloc_path = self.ft_netloc_length / self.ft_path_length
        else:
            self.ft_ratio_netloc_path = 0

    def count_signs(self) -> None:
        """feature count number of signs in url sections"""
        # count number of dots
        self.ft_nr_dots_query = self.query.count(".")
        self.ft_nr_dots_path = self.path.count(".")

        # count @ signs
        self.ft_nr_at_query = self.query.count("@")
        self.ft_nr_at_path = self.path.count("@")

        # count % signs
        self.ft_nr_percent_query = self.query.count("%")
        self.ft_nr_percent_path = self.path.count("%")

        # number of delimiters (e.g. '_', '&', etc.)
        self.ft_nr_del_query = count_delimiters(self.query)
        self.ft_nr_del_path = count_delimiters(self.path)

    def has_port(self) -> None:
        "Does the url contain a port?"
        self.ft_has_port = True
        if self.port is not None:
            if math.isnan(self.port):
                self.ft_has_port = False
        else:
            self.ft_has_port = False

    def contains_puny(self) -> None:
        "Does the url contain puny code?"
        self.ft_contains_puny = False
        puny = re.findall("--xn", self.netloc, re.IGNORECASE)
        if len(puny) > 0:
            self.ft_contains_puny = True

    def is_http(self) -> None:
        """feature is it http"""
        self.ft_is_http = False
        if self.scheme == "http":
            self.ft_is_http = True

    def entropy_features(self) -> None:
        """check entropy of different url sections"""
        # The domain right after tld. THIS DOES NOT WORK FOR
        # E.G. .co.uk tld.
        self.ft_domain_entropy = entropy(self.domains_splitted[0])
        self.ft_query_entropy = entropy(self.query)
        self.ft_path_entropy = entropy(self.path)

    def feature_extraction(self) -> None:
        """method containing all features"""
        self.domains_separator()
        self.domains_features()
        self.netloc_features()
        self.query_features()
        self.path_features()
        self.combined_features()
        self.count_signs()
        self.has_port()
        self.contains_puny()
        self.is_http()
        self.entropy_features()


class CertificateCollection:
    """class for the certificate collection class"""

    # setup initial state for some code we don't want to constantly rerun
    sql_tables_cert = None
    sql_tables_dom = None
    sql_tablenames_cert = None
    sql_tablenames_dom = None
    sql_db_cursor = None

    def __init__(self, url_object: URL) -> None:
        logger.debug("url_object netloc %s", url_object.netloc)
        self.c_name = url_object.netloc
        logger.debug("c_name %s", self.c_name)
        self.cert_df = Certsearch().find(self.c_name)
        self.ft_wildcard_cert = False

        if self.cert_df.empty:
            self.ft_no_certs_found = False
            logger.error(
                "No Cert Found for %s - skipping feature collection", self.c_name
            )
            raise LookupError
        else:
            self.ft_no_certs_found = True

    def certificate_features(self) -> None:
        """certificate features are computed in this method"""

        # FEATURE: Number of certificates found.
        # NOTE: to save bandwidth no searching beyond two pages with 10 per page.
        # adjust in tools.cert_grabber
        self.ft_nr_of_certs = self.cert_df.shape[0]

        # FEATURE: Age in days of most recent certificate since validity / expiry
        # certificates are ordered by when they were created
        # there is no created at date in the response only valid from.
        # We will just use the most recent valid from to determine age (it
        # could be minus in some cases)
        now = datetime.now()
        self.cert_df["Days since valid"] = (
            now
            - pd.to_datetime(self.cert_df["Valid from"], unit="ms").dt.to_pydatetime()
        )
        self.cert_df["Days since expiry"] = (
            now - pd.to_datetime(self.cert_df["Valid to"], unit="ms").dt.to_pydatetime()
        )

        self.ft_days_since_valid = self.cert_df["Days since valid"].iloc[0].days
        self.ft_days_since_expiry = self.cert_df["Days since expiry"].iloc[0].days

        # FEATURE: get mean age between start of cert validitys
        # Get mean age between certs (don't count duplicate validaty start
        # dates)
        day_range = []
        for timed_row in self.cert_df["Days since valid"]:
            if timed_row.days not in day_range:
                day_range.append(int(timed_row.days))

        self.ft_renewal_days_mean = sum(day_range) / len(day_range)

        # FEATURE: whois creation age, whether dnssec is used and also expiry
        # Whois lookup, technically not a cert feature but here anyway

        try:
            if not (domain := whois.query(self.c_name)):
                logger.error(f"No whois match for {self.c_name}")
                raise LookupError
        except FailedParsingWhoisOutput as e:
            logger.error(f"whois query failed for {self.c_name}: {e}")
            raise LookupError
        except UnknownTld as e:
            logger.error(f"whois query failed for {self.c_name}: {e}")
            raise LookupError

        if domain.creation_date:
            whois_creation_age_timedelta = datetime.now() - domain.creation_date
            self.ft_whois_creation_age_days = whois_creation_age_timedelta.days
        else:
            logger.debug("domain creation_date not found in whois for %s", self.c_name)
            if config["set_missing_whois_to_zero"]:
                self.ft_whois_creation_age_days = 0
            else:
                self.ft_whois_creation_age_days = None

        if domain.dnssec:
            self.ft_whois_dnssec = domain.dnssec
        else:
            logger.debug("domain dnssec not found in whois for %s", self.c_name)
            self.ft_whois_dnssec = False

        if domain.expiration_date:
            whois_expiry_timedelta = datetime.now() - domain.expiration_date
            self.ft_whois_expiry_days = whois_expiry_timedelta.days
        else:
            logger.debug(
                "domain expiration date not found in whois for %s", self.c_name
            )
            if config["set_missing_whois_to_zero"]:
                self.ft_whois_expiry_days = 0
            else:
                self.ft_whois_expiry_days = None

        # FEATURE: free certificate authority is used
        free_ca = [
            "Let's Encrypt Authority X3",
            "COMODO ECC Domain Validation Secure Server CA 2",
            "COMODO ECC Domain Validation Secure Server CA",
            "CloudFlare Inc ECC CA-2",
            "CloudFlare Inc ECC CA-3",
            "R3",
        ]
        if self.cert_df["CA"][0] in free_ca:
            self.ft_free_ca_issuer = True
        else:
            self.ft_free_ca_issuer = False

        # validity period feature
        # assign validity period but only perform on newest rows
        self.cert_df["Validity period"] = (
            pd.to_datetime(self.cert_df["Valid to"], unit="ms").dt.to_pydatetime()
            - pd.to_datetime(self.cert_df["Valid from"], unit="ms").dt.to_pydatetime()
        )
        # get valid period of first row as all rows should be the same
        self.ft_valid_period = self.cert_df["Validity period"].iloc[0].days

    def print_certificate_features(self):
        logger.debug("--------------------------")
        logger.debug("-----Certificate features:")
        logger.debug("--------------------------")
        logger.debug(
            "Number of certificates found for this URL : %s", str(self.ft_nr_of_certs)
        )


def process_url(url: str) -> URL:
    logger.debug(f"URL: {url}")
    try:
        url_obj = URL(url)
        logger.debug("url netloc %s", url_obj.netloc)
        url_obj.feature_extraction()
        cert_collection_obj = CertificateCollection(url_obj)
        cert_collection_obj.certificate_features()
        url_obj.certificate_collection = cert_collection_obj
    except LookupError:
        url_obj.valid = False
        return url_obj

    features_dataframe = dataframe_postprocessing(
        url_obj, url_obj.certificate_collection
    )
    url_obj.features_dataframe = features_dataframe
    url_obj.valid = True
    return url_obj


def process_url_dict(url_dict: Dict, training: bool = False) -> URL:
    url = url_dict[1]
    url_obj = process_url(url)
    if training:
        return url_obj
    if url_obj.features_dataframe is not None:
        if not url_obj.features_dataframe.empty:
            prediction = ns.model.predict(
                url_obj.features_dataframe[config["features"]]
            )
            if prediction[0]:
                result = "URL is Malicious"
            else:
                result = "URL is Safe"
            print(f"{url}: {result}")


def process_labeled_url_dict(url_dict: Dict) -> None:
    url_obj = process_url_dict(url_dict, True)

    if url_obj.valid:
        try:
            url_obj.features_dataframe["label"] = url_dict[2]
            ns.feature_df = ns.feature_df.append(url_obj.features_dataframe)
        except IndexError:
            logger.warning(
                f"No label was found for this URL. {url_obj.netloc} not added to the training dataframe."
            )
        logger.debug(f"Dataframe shape for this URL: {ns.feature_df.shape}")


def create_features_dataframe(
    urls_csv_path: Path, model: RandomForestClassifier = None, labeled: bool = False
) -> DataFrame:
    workers = max(mp.cpu_count() - 1, 1)
    logger.info(f"[+] Using {workers} workers")

    pool = mp.Pool(workers)

    ns.feature_df = pd.DataFrame()

    with open(urls_csv_path) as csvfile:
        reader = csv.reader(csvfile, delimiter=",")
        next(reader)  # Skip headers
        if labeled:
            pool.map(process_labeled_url_dict, reader)
        else:
            ns.model = model
            pool.map(process_url_dict, reader)
        pool.close()
        pool.join()
    return ns.feature_df


def train_model(labeled_dataset: DataFrame, features: List, model_path: Path) -> None:
    x_train = labeled_dataset[features]
    y_train = labeled_dataset["label"]

    n_estimators = 250
    min_samples_split = 10
    logger.debug(
        f"[*] Classifying dataframe using Random Forest ({n_estimators},{min_samples_split})..."
    )
    model = RandomForestClassifier(
        n_estimators=n_estimators, min_samples_split=min_samples_split
    )
    model.fit(x_train, y_train)

    logger.info(f"[*] Writing new model to {model_path}...")
    joblib.dump(model, model_path)
