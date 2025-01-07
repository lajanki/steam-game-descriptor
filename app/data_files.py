import json
import os.path
import yaml


# Read data files globally to avoid frequent file I/O
 
BASE = os.path.dirname(__file__)

with open(os.path.join(BASE, "data", "developers.txt")) as f:
	DEVELOPER_TEMPLATES = f.readlines()

with open(os.path.join(BASE, "data", "pos_tags.json")) as f:
	POS_MAP = json.load(f)
	
with open(os.path.join(BASE, "data", "tags.txt")) as f:
	TAGS = f.readlines()
	
with open(os.path.join(BASE, "data", "genres.yml")) as f:
	GENRES = yaml.safe_load(f)

with open(os.path.join(BASE, "data", "seeds.json")) as f:
	SEEDS = json.load(f)
