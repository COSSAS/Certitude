import logging
import sys
from importlib import resources
from pathlib import Path
from typing import Dict, Union

import yaml

import certitude.utils.data

logger = logging.getLogger(__name__)


def config(user_config: Union[Path, None] = None) -> Dict:
    if user_config:
        with open(user_config, "r") as config_stream:
            try:
                config = yaml.safe_load(config_stream)
                return config
            except yaml.YAMLError as e:
                logger.error(
                    "[!] Unable to load configuration file.",
                    exc_info=e,
                )
                sys.exit(1)
    else:
        with resources.open_text(
            certitude.utils.data, "config_default.yml"
        ) as config_stream:
            config = yaml.safe_load(config_stream)
        return config
