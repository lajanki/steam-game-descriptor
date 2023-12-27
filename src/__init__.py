import logging
import os.path

from dotenv import load_dotenv


logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)

load_dotenv(".env.dev")
