import logging
import math

import pandas as pd
from pandas import DataFrame

logger = logging.getLogger(__name__)


def count_delimiters(my_string: str) -> int:
    """script used for counting delimiters in different parts of URL"""
    count = 0
    delimiters = [
        ";",
        "_",
        "?",
        "=",
        "&",
        "|",
        "$",
        "-",
        "_",
        ".",
        "+",
        "!",
        "*",
        "'",
        "(",
        ")",
    ]
    for letter in my_string:
        if letter in delimiters:
            count = count + 1
    return count


def entropy(string: str) -> float:
    "Calculates the Shannon entropy of a string"

    # get probability of chars in string
    prob = [float(string.count(c)) / len(string) for c in dict.fromkeys(list(string))]

    # calculate the entropy
    entropy_result = -sum([p * math.log(p) / math.log(2.0) for p in prob])

    return entropy_result


def entropy_ideal(length):
    "Calculates the ideal Shannon entropy of a string with given length"
    prob = 1.0 / length
    return -1.0 * length * prob * math.log(prob) / math.log(2.0)


def dataframe_postprocessing(url_object, cert_collection_object) -> DataFrame:
    """
    [TRAINING_MODUS ONLY]
    This function will be used in 'training_modus' to create a dataframe.
    The dataframe is created by adding a new row to it,
    everytime a URL is digested in the MagicURLBox stream.
    The dataframe will contain the a the following columns:
        - 'url_as_string' df_output = "./results/computed_feature_dataframes/fdf_{}_{}.pkl".format(
        fname, time_str
    )ow, i.e., url, in the dataframe.
    The idx will be generated in the main for every URL that is passed in the stream.
    """

    idx = [0]

    my_lex_dict = dict(
        filter(lambda item: "ft_" in item[0], url_object.__dict__.items())
    )
    my_lex_dict = {"lex_" + k: v for k, v in my_lex_dict.items()}  # add lex_ to keys
    df_lex = pd.DataFrame(my_lex_dict, index=idx)

    my_cert_dict = dict(
        filter(lambda item: "ft_" in item[0], cert_collection_object.__dict__.items())
    )
    my_cert_dict = {"cert_" + k: v for k, v in my_cert_dict.items()}
    df_cert = pd.DataFrame(my_cert_dict, index=idx)
    df_res = pd.concat([df_lex, df_cert], axis=1)

    df_res.insert(loc=0, column="url_as_string", value=url_object.url)

    return df_res
