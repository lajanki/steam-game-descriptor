import logging
import os

try:
	import spacy
	SPACY_AVAILABLE = True
except ImportError:
	SPACY_AVAILABLE = False
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
load_dotenv("vars.dev.env")

# Load a pre-trained Spacy language model if available.
# Disable specific pipeline component to speedup similarity inference 
# https://spacy.io/usage/processing-pipelines#pipelines
if SPACY_AVAILABLE:
	nlp = spacy.load("en_core_web_md", exclude=["ner", "parser"])
else:
	nlp = None
	logger.warning("spaCy is not installed. NLP features are disabled.")
