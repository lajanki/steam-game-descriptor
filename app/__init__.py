import logging
import os

from dotenv import load_dotenv


# configure a logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# create console handler
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)


BASE = os.path.dirname(__file__)


# Load default environment variables. This will not override existing variables.
load_dotenv(".env.dev")