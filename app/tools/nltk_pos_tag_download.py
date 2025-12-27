from collections import defaultdict
import json
import os.path

import nltk

from app.utils.json_set_encoder import SetEncoder


def create_pos_tag_mapping():
	"""Create a json mapping of POS tag -> word from the nltk Brown Corpus.
	https://www.nltk.org/book/ch02.html
	
	Requires setting up nltk module with the Brown Corpus data,
	>>> import nltk
	>>> nltk.download('brown')
	>>> nltk.download('universal_tagset')
	
	see
	https://www.nltk.org/install.html
	"""
	TAGS_TO_KEEP = [
		"NOUN",
		"ADJ",
		"VERB",
		"ADV",
		"NUM",
		"X"
	]
	OUTPUT_FILE = os.path.join("app", "data", "pos_tags.json")

	d = defaultdict(set)
	tags = nltk.corpus.brown.tagged_words(tagset="universal") 
	for token in tags:
		if token[1] not in TAGS_TO_KEEP:
			continue

		d[token[1]].add(token[0].strip("'"))
		
	with open(OUTPUT_FILE, "w") as f:
		json.dump(d, f, separators=(",", ":"), cls=SetEncoder)

	print(f"POS map saved as {OUTPUT_FILE}")