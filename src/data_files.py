import json
import os.path


# Read data files globally to avoid frequent file I/O
 

with open(os.path.join("data", "developers.txt")) as f:
	DEVELOPER_TEMPLATES = f.readlines()

with open(os.path.join("data", "pos_tags.json")) as f:
	POS_MAP = json.load(f)
	
with open(os.path.join("data", "tags.txt")) as f:
	TAGS = f.readlines()
	
with open(os.path.join("data", "seeds.json")) as f:
	SEEDS = json.load(f)
