import logging

from dotenv import load_dotenv


logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)

# Load default environment variables. Will not override existing variables.
load_dotenv(".env.dev")
