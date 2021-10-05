import logging

logger = logging.getLogger(__name__)


class RandomForest:
    def __init__(self, url):
        self.url = url
        logger.error(f"Nothing but trees here. But thanks for the {self.url}")
        logger.debug("I'm a lonely debug message")
