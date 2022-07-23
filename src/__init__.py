import logging
import os.path

logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)
ENV = os.getenv("ENV", "dev")
