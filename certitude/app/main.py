import logging
import os
import sys
from importlib import resources
from pathlib import Path
from typing import Dict

import joblib
import whois

import certitude.utils.data
from certitude.core.data_model import (
    create_features_dataframe,
    process_url,
    train_model,
)
from certitude.utils.config import config

config = config()


def set_loglevel():
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=os.environ.get(key="LOG_LEVEL", default="INFO").upper(),
    )


set_loglevel()
logger = logging.getLogger(__name__)


def main(args: Dict) -> None:
    logger.debug(f"The arguments we received from you: {args}")

    try:
        whois.query("github.com")
    except FileNotFoundError:
        logger.critical("whois is not installed. Please install.")
        sys.exit(1)
    except whois.exceptions.WhoisCommandFailed:
        logger.critical("whois failed a basic test. The application may not work.")

    if args.verbose:
        set_loglevel(logging.DEBUG)

    logger.debug(f"These features are enabled in the config: {config['features']}")

    if args.train:
        if args.dataset:
            logger.info(f"Using user supplied dataset at {args.dataset}")
            dataset_path = args.dataset
        else:
            logger.warning(f"Using default dataset")
            with resources.path(certitude.utils.data, "default_dataset.csv") as path:
                dataset_path = Path(path)

        features_dataframe = create_features_dataframe(dataset_path, labeled=True)

        model_path = Path(args.train)
        train_model(features_dataframe, config["features"], model_path)

    if args.url:
        if "//" not in args.url:
            logging.critical(
                "url provided %s is not RFC 1808 compliant. You are probably missing http:// or https://",
                args.url,
            )
            logging.critical(
                "see https://docs.python.org/3/library/urllib.parse.html#url-parsing"
            )
            sys.exit(1)
        url_obj = process_url(args.url)

        model = load_model(args.model)

        if url_obj.features_dataframe is not None:
            if not url_obj.features_dataframe.empty:
                prediction = model.predict(
                    url_obj.features_dataframe[config["features"]]
                )

                if prediction[0] == 1:
                    result = "URL is Malicious"
                else:
                    result = "URL is Safe"

                logging.critical(f"{args.url}: {result}")
                return None
        logging.critical(f"{args.url} not found.")

    if args.batch:
        model = load_model(model=args.model)
        features_dataframe = create_features_dataframe(args.batch, model=model)


def load_model(model):
    if model:
        model = joblib.load(model)
        return model
    else:
        logging.critical(
            "url classification requested, but no model provided! You must pass a model with --model"
        )
        sys.exit(1)
        # logging.warning("no model was provided, will use default model")
        # with resources.path(
        #     certitude.utils.data, "default_model.pkl"
        # ) as model_path:
        #     model = joblib.load(model_path)
