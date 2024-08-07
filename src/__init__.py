import logging
from dotenv import load_dotenv


# configure a logger
logger = logging.getLogger("main")
logger.setLevel(logging.INFO)

# create console handler
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)


# Load default environment variables. Will not override existing variables.
load_dotenv(".env.dev")
